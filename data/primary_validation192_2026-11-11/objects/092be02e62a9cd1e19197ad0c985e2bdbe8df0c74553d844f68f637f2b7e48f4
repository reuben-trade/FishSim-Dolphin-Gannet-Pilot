"""Paired, explicitly initialized mixed-species feeding encounters.

``prepare_seed`` reads/pins inputs and constructs only pure Python state.
``build_condition`` is the explicit native-construction boundary; it never
steps an encounter. Scientific modules and historical artifacts are unchanged.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from functools import partial
import hashlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "research/prey_mediated"
BASELINE_PATH = B / "BASELINE_V1.json"
REFERENCE = B / "results/short_angular_physical_g3_v1"
REFERENCE_SEED = 190001
SEEDS = (190000, 190001, 190002, 190003)
CONDITIONS = ("none", "D", "G", "S", "DG", "DS", "GS", "DGS")
ACTOR_IDS = tuple(f"D{i:02d}" for i in range(12)) + ("G0", "G1", "G2", "S0")
G_STARTS = ((60., 0., 3.), (60., -6., 3.), (60., 6., 3.))
S_START = (45., 0., -12.)
NATIVE_SHA256 = "eb8654a520304cc429aced67c7e3706db8d2ef1449c5e1327a682a479b10a558"
POLICY_VERSION = "paired_historical_feeding_mixed_v1"
SOURCE_NAMES = ("scenario.py", "reactive_school.py", "surface_safe_school.py", "predators.py",
                "contacts.py", "encounter.py", "virtual_capture.py", "local_pressure.py",
                "pressure_feeding.py", "local_angular_crowd.py", "local_axis_pressure.py",
                "shark_approach.py", "metrics.py")


def clean(value):
    import numpy as np
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(item) for item in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def model_api():
    """Import pure model definitions; no extension or school is constructed."""
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "lib"))
    import numpy as np
    from research.prey_mediated.contacts import MouthGeometry
    from research.prey_mediated.encounter import Actor, Encounter
    from research.prey_mediated.local_angular_crowd import AngularCrowdConfig, angular_pressure_step
    from research.prey_mediated.local_pressure import PressureConfig
    from research.prey_mediated.predators import PredatorConfig, initial_predator
    from research.prey_mediated.pressure_feeding import FeedingConfig, PressureFeedingPlanner
    from research.prey_mediated.scenario import ScenarioConfig, SchoolState
    from research.prey_mediated.shark_approach import SharkApproachConfig, SharkApproachPlanner
    from research.prey_mediated.surface_safe_school import SurfaceSafeSchool
    return SimpleNamespace(**locals())


def condition_species(condition):
    if condition not in CONDITIONS:
        raise ValueError(f"condition must be one of {CONDITIONS}")
    return frozenset() if condition == "none" else frozenset(condition)


def actor_seed_words(identity):
    digest = hashlib.sha256(identity.encode()).digest()
    return [int.from_bytes(digest[i:i + 4], "little") for i in range(0, 16, 4)]


def initial_delay(seed, identity, handling_duration, *, phase_seed=0, initial_phase="staggered"):
    """Stable-ID independent readiness offsets, shared by every presence arm."""
    import numpy as np
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed must be an accepted archived school seed")
    if type(phase_seed) is not int or phase_seed < 0:
        raise ValueError("phase_seed must be a nonnegative integer")
    if initial_phase not in ("staggered", "synchronous"):
        raise ValueError("initial_phase must be staggered or synchronous")
    if identity not in ACTOR_IDS:
        raise ValueError("unknown actor identity")
    if not math.isfinite(handling_duration) or handling_duration <= 0:
        raise ValueError("positive finite handling duration required")
    if initial_phase == "synchronous":
        return 0.
    rng = np.random.default_rng(np.random.SeedSequence([seed, 7103, phase_seed, *actor_seed_words(identity)]))
    return float(rng.uniform(0., handling_duration))


def expected_rng_states(seed, identities):
    import numpy as np
    captures = {identity: np.random.default_rng(np.random.SeedSequence(
        [seed, 7101, *actor_seed_words(identity)])).bit_generator.state for identity in identities}
    tie = np.random.default_rng(np.random.SeedSequence([seed, 7102])).bit_generator.state
    return clean(dict(capture_rng=captures, tie_rng=tie))


@dataclass(frozen=True)
class PreparedSeed:
    seed: int
    scenario: object
    initial: object
    actors: tuple
    policy: dict
    metadata: dict
    api: object


def _school(api, entry):
    path = ROOT / entry["checkpoint"]
    if sha(path) != entry["sha256"]:
        raise RuntimeError("Archived school hash changed: " + str(path))
    with api.np.load(path, allow_pickle=False) as archive:
        values = {key: archive[key].item() if archive[key].ndim == 0 else archive[key] for key in archive.files}
    school = api.SchoolState(**values)
    if len(school.prey_ids) != 160 or school.time != 20. or school.step_index != 4000:
        raise RuntimeError("Unexpected accepted-school count or clock")
    return school


def prepare_seed(seed, *, dt=.005, dolphin_retry=.75, phase_seed=0, initial_phase="staggered",
                 handling_overrides=None):
    """Prepare a school and all16 actors without invoking a native constructor.

    Starts are the historical starts translated only in XY by the difference
    between this school's and seed190001's initial centroid. Depths and the
    common surface are retained. All sixteen readiness offsets are generated
    before selecting a species subset, independent of that selection.
    """
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("seed must be one of the four accepted development schools")
    if isinstance(dt, bool) or not isinstance(dt, (int, float)) or not math.isfinite(dt) or not 0 < dt <= .005:
        raise ValueError("dt must be finite in (0,.005]")
    if isinstance(dolphin_retry, bool) or not isinstance(dolphin_retry, (int, float)) or not math.isfinite(dolphin_retry) or dolphin_retry <= dt:
        raise ValueError("dolphin retry must exceed dt")
    if handling_overrides is not None and (not isinstance(handling_overrides, dict)
            or not set(handling_overrides) <= {"D", "G", "S"}):
        raise ValueError("handling_overrides must map only D/G/S species")
    handling = dict(D=2., G=2., S=2.)
    for species, value in (handling_overrides or {}).items():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= dt:
            raise ValueError("handling durations must be finite and exceed dt")
        handling[species] = float(value)
    api = model_api()
    baseline = json.loads(BASELINE_PATH.read_text())
    entries = {entry["seed"]: entry for entry in baseline["development_checkpoints"]}
    if tuple(sorted(entries)) != SEEDS:
        raise RuntimeError("Accepted school list changed")
    initial = _school(api, entries[seed])
    reference_school = _school(api, entries[REFERENCE_SEED])
    historical = json.loads((REFERENCE / "manifest.json").read_text())
    if historical["config"] != baseline["scenario"]:
        raise RuntimeError("Historical feeding and accepted-school scenarios differ")
    scenario = replace(api.ScenarioConfig(**baseline["scenario"]), dt=float(dt))
    native = json.loads((REFERENCE / "native.json").read_text())
    if native["sha256"] != NATIVE_SHA256 or sha(native["path"]) != NATIVE_SHA256:
        raise RuntimeError("Pinned native binary changed; no rebuild is allowed")
    shift = initial.positions.mean(axis=0) - reference_school.positions.mean(axis=0)
    shift[2] = 0.
    d_config = replace(api.PredatorConfig(**historical["predator_config"]),
                       handling_duration=handling["D"], miss_recovery_duration=float(dolphin_retry))
    g_config = replace(api.PredatorConfig(**historical["gannet_config"]), handling_duration=handling["G"])
    s_config = api.PredatorConfig(species="S", speed=6., turn_rate=math.pi / 2,
        sense_radius=25., intercept_horizon=3., bout_duration=6., handling_duration=handling["S"],
        miss_recovery_duration=1., surface_z=0., spacing_enabled=False, spacing_radius=5.,
        max_motion_interval=.05)
    configs = dict(D=d_config, G=g_config, S=s_config)
    states, delays, actors = {}, {}, []
    definitions = [(identity, "D", position) for identity, position in zip(ACTOR_IDS[:12], historical["dolphin_starts"])]
    definitions += [(identity, "G", position) for identity, position in zip(("G0", "G1", "G2"), G_STARTS)]
    definitions += [("S0", "S", S_START)]
    for identity, species, position in definitions:
        config = configs[species]
        translated = tuple(api.np.asarray(position, float) + shift)
        state = api.initial_predator(identity, translated, (1., 0., 0.), config, time=initial.time)
        delay = initial_delay(seed, identity, config.handling_duration, phase_seed=phase_seed, initial_phase=initial_phase)
        if initial_phase == "staggered":
            state = replace(state, mode="recovery", ready_at=initial.time + delay, last_outcome=None)
        actors.append(api.Actor(state, config, api.MouthGeometry(.4, .3, scenario.surface_z), .7))
        states[identity], delays[identity] = asdict(state), delay
    pressure = api.PressureConfig(**historical["pressure_config"])
    feeding = replace(api.FeedingConfig(**historical["feeding_config"]), front_dot_min=-1.)
    angular = api.AngularCrowdConfig(**historical["angular_config"])
    approach = api.SharkApproachConfig()
    policy = dict(pressure_config=asdict(pressure), feeding_config=asdict(feeding),
        angular_config=asdict(angular), shark_approach_config=asdict(approach),
        circulation_signs=historical["circulation_signs"], orbit_axes=historical["orbit_axes"],
        planner_peer_observation_radii={identity: 25. for identity in ACTOR_IDS[:12]},
        species_configs={species: asdict(config) for species, config in configs.items()},
        capture_probability=.7, mouth=asdict(api.MouthGeometry(.4, .3, scenario.surface_z)),
        target_refresh_enabled=False)
    input_paths = {"baseline": BASELINE_PATH, "historical_manifest": REFERENCE / "manifest.json",
        "native_pin": REFERENCE / "native.json", "school_checkpoint": ROOT / entries[seed]["checkpoint"],
        "reference_school_checkpoint": ROOT / entries[REFERENCE_SEED]["checkpoint"]}
    metadata = dict(policy_version=POLICY_VERSION, seed=seed, phase_seed=phase_seed,
        initial_phase=initial_phase, initial_readiness_delay=delays,
        successful_handling_by_species=handling,
        readiness_rule="stable-ID independent uniform[0,successful_handling), initialized in recovery with no prior food",
        horizontal_start_shift=shift.tolist(), surface_and_start_depths_unshifted=True,
        native=dict(path=native["path"], sha256=NATIVE_SHA256),
        input_sha256={str(path.relative_to(ROOT)): sha(path) for path in input_paths.values()},
        scenario=asdict(scenario), policy=policy, all_actor_states=states,
        all_initial_random_states=expected_rng_states(seed, ACTOR_IDS),
        interpretation="Historical constant-speed point-fish model; handling overrides are explicit engineering sensitivities, with no ecological clock or species-specific recovery calibration.")
    return PreparedSeed(seed, scenario, initial, tuple(actors), policy, clean(metadata), api)


def make_planners(prepared, condition):
    """Construct fresh pure planners; none are shared between encounters."""
    allowed, api, policy = condition_species(condition), prepared.api, prepared.policy
    planners, peer_radii = {}, {}
    if "D" in allowed:
        for identity, sign, axis in zip(ACTOR_IDS[:12], policy["circulation_signs"], policy["orbit_axes"]):
            planners[identity] = api.PressureFeedingPlanner(
                replace(api.PressureConfig(**policy["pressure_config"]), orbit_sign=sign),
                api.FeedingConfig(**policy["feeding_config"]),
                pressure_stepper=partial(api.angular_pressure_step, orbit_axis=tuple(axis),
                    angular_config=api.AngularCrowdConfig(**policy["angular_config"])),
                peer_observation_radius=25.)
            peer_radii[identity] = 25.
    if "S" in allowed:
        planners["S0"] = api.SharkApproachPlanner(api.SharkApproachConfig(**policy["shark_approach_config"]))
    return planners, peer_radii


def selected_actors(prepared, condition):
    allowed = condition_species(condition)
    return tuple(actor for actor in prepared.actors if actor.state.species in allowed)


def engine_snapshot(engine, counts=None):
    """Complete behavior, configuration, ownership and actual private/tie RNGs."""
    own = engine.ownership
    return clean(dict(actors=[asdict(actor.state) for actor in engine.actors],
        actor_policy={actor.state.actor_id: dict(config=asdict(actor.config), mouth=asdict(actor.mouth),
            capture_probability=actor.capture_probability) for actor in engine.actors},
        counts={} if counts is None else deepcopy(counts),
        ownership=dict(prey_ids=own.prey_ids, captured_ids=sorted(own.captured_ids),
            closed_bouts=sorted(own.closed_bouts), time=own.time),
        capture_rng={identity: deepcopy(rng.bit_generator.state) for identity, rng in engine.capture_rngs.items()},
        tie_rng=deepcopy(engine.tie_rng.bit_generator.state)))


def build_condition(prepared, condition):
    """Explicit native construction; caller owns lock, duration and stepping."""
    if not isinstance(prepared, PreparedSeed):
        raise TypeError("prepare_seed result required")
    api = prepared.api
    actors = selected_actors(prepared, condition)
    planners, radii = make_planners(prepared, condition)
    engine = api.Encounter(prepared.scenario, prepared.initial, actors, seed=prepared.seed,
        remove_prey=True, predator_cues=True, school_factory=api.SurfaceSafeSchool,
        actor_planners=planners, planner_peer_observation_radii=radii)
    loaded = engine.school.state()
    for key in ("positions", "prey_ids", "time", "step_index", "surface_reflections"):
        if not api.np.array_equal(getattr(loaded, key), getattr(prepared.initial, key)):
            raise RuntimeError("Initial checkpoint field changed on native load: " + key)
    heading_change = float(api.np.max(abs(loaded.directions - prepared.initial.directions), initial=0.))
    if heading_change > 1e-10:
        raise RuntimeError("Initial heading normalization exceeds declared bound")
    receipt = engine_snapshot(engine)
    expected = expected_rng_states(prepared.seed, [actor.state.actor_id for actor in engine.actors])
    if receipt["capture_rng"] != expected["capture_rng"] or receipt["tie_rng"] != expected["tie_rng"]:
        raise RuntimeError("Initial private/tie streams changed")
    if receipt["actors"] != clean([asdict(actor.state) for actor in sorted(actors, key=lambda a: a.state.actor_id)]):
        raise RuntimeError("Actor initial states changed")
    metadata = dict(prepared.metadata, condition=condition, species=sorted(condition_species(condition)),
        actor_ids=[actor.state.actor_id for actor in engine.actors],
        actor_species=[actor.state.species for actor in engine.actors],
        actor_counts={species: sum(actor.state.species == species for actor in engine.actors) for species in "DGS"},
        initial_heading_normalization_max_absolute_change=heading_change)
    return SimpleNamespace(engine=engine, planners=planners, initial=prepared.initial,
        scenario=prepared.scenario, metadata=clean(metadata), initial_engine=receipt,
        actor_ids=tuple(actor.state.actor_id for actor in engine.actors),
        actor_species=tuple(actor.state.species for actor in engine.actors))


def scientific_source_paths():
    return [Path(__file__).resolve(), *(B / name for name in SOURCE_NAMES)]
