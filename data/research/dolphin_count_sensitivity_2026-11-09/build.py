"""Pure matched preparation, followed by an explicit native-construction boundary.

Only the nested dolphin population varies at selected H/G regimes. No native school is constructed by
prepare_case(), and it is safe for the pre-review software checks.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, replace
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V2 = ROOT/'research/herding_study_2026-11-07'
OLD = ROOT/'research/overnight_workload_2026-11-08'
sys.path[:0] = [str(HERE), str(OLD), str(V2), str(ROOT), str(ROOT/'lib')]
import setup_v2 as setup
from cases import Case, CAPTURE_SEED, DT, DURATION, SEEDS, decode, prior_case
from regime_controller import SimpleHerdStrikePlanner, VERSION as DOLPHIN_VERSION
from gannet import DensePatchGannetPlanner, VERSION as GANNET_VERSION
from committed_encounter import CommittedEncounter


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(v) for v in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, np.generic):
        return value.item()
    return value


def validate_sealed_case(path):
    path = Path(path)
    seal = json.loads((path/'completion.json').read_text())
    if seal.get('status') != 'complete' or any(sha(path/name) != digest for name, digest in seal['files'].items()):
        raise RuntimeError('Prior completed-case seal changed: '+str(path))
    summary = json.loads((path/'summary.json').read_text())
    if summary['dt'] != DT or abs(summary['actual_duration']-DURATION) > 1e-7 or summary['native_steps'] != round(DURATION/DT):
        raise RuntimeError('Prior anchor is not the full original coarse36T encounter')
    audit = json.loads((path/'audit.json').read_text())
    if audit.get('errors'):
        raise RuntimeError('Prior anchor failed its physical accounting audit')
    return seal


def school_input(seed):
    declaration_path = V2/'v2_numeric_execution_v1.json'
    declaration = json.loads(declaration_path.read_text())
    if seed in SEEDS[:2]:
        entry = declaration['checkpoints'][str(seed)]
        preparation_path = None
    else:
        preparation_path = ROOT/'research/exposed_replication_2026-11-08/checkpoints/manifest.json'
        preparation = json.loads(preparation_path.read_text())
        entry = preparation['checkpoints'][str(seed)]
        if preparation['status'] != 'complete' or entry['screen_status'] != 'passed':
            raise RuntimeError('Frozen preparation/stability screen changed')
        if preparation['native']['sha256'] != declaration['native']['sha256']:
            raise RuntimeError('Preparation and feeding native binary differ')
    if sha(entry['path']) != entry['sha256']:
        raise RuntimeError('Frozen school checkpoint changed')
    if sha(declaration['native']['path']) != declaration['native']['sha256']:
        raise RuntimeError('Frozen native binary changed')
    initial = setup._legacy_setup().read_school(entry['path'])
    if len(initial.prey_ids) != 160 or abs(initial.time-20.) > 1e-8:
        raise RuntimeError('Unexpected saved school size or starting time')
    return initial, declaration, entry, declaration_path, preparation_path


def _seed_words(identity):
    digest = hashlib.sha256(identity.encode()).digest()
    return [int.from_bytes(digest[i:i+4], 'little') for i in range(0, 16, 4)]


def initial_private_streams(seed, actor_ids):
    engine_seed = int(np.random.SeedSequence([int(seed), CAPTURE_SEED, 7104]).generate_state(1)[0])
    return engine_seed, clean(dict(capture_rng={identity: np.random.default_rng(np.random.SeedSequence(
        [engine_seed, 7101, *_seed_words(identity)])).bit_generator.state for identity in actor_ids},
        tie_rng=np.random.default_rng(np.random.SeedSequence([engine_seed, 7102])).bit_generator.state))


@dataclass
class PreparedCase:
    case: Case
    initial: object
    scenario: object
    actors: tuple
    planners: dict
    engine_seed: int
    metadata: dict
    api: object

    def receipt(self):
        _, streams = initial_private_streams(self.case.school_seed, [a.state.actor_id for a in self.actors])
        return clean(dict(actors=[asdict(a.state) for a in self.actors],
            actor_policy={a.state.actor_id: dict(config=asdict(a.config), mouth=asdict(a.mouth),
                capture_probability=a.capture_probability) for a in self.actors},
            ownership=dict(prey_ids=self.initial.prey_ids, captured_ids=[], closed_bouts=[], time=self.initial.time),
            capture_rng=streams['capture_rng'], tie_rng=streams['tie_rng'],
            controllers={who: p.state_dict() for who, p in self.planners.items()}))


def prepare_case(case):
    """Prepare pure states/planners without constructing or stepping native fish."""
    if not isinstance(case, Case):
        raise TypeError('A prespecified Case is required')
    initial, declaration, checkpoint, declaration_path, preparation_path = school_input(case.school_seed)
    # This unchanged archived function reads inputs and creates only Python
    # states. The original builder used exactly the same reference object.
    legacy = setup._legacy_setup().load_legacy()
    reference = legacy.prepare_seed(190001, dt=DT, dolphin_retry=.75)
    parameters = setup.ControllerParameters.from_dict(declaration['controller_parameters'])
    if case.dolphins:
        parameters = replace(parameters, pressure_minimum=float(case.herding_minimum))
    shift = initial.positions.mean(axis=0)-reference.initial.positions.mean(axis=0)
    shift[2] = 0.
    original = {a.state.actor_id: a for a in reference.actors}
    roster = [(f'D{i:02d}', f'D{i % 12:02d}') for i in range(case.dolphin_count)] if case.dolphins else []
    # New IDs reuse the three original launch locations. Readiness follows the
    # original stable-ID formula; no extra staggering parameter is introduced.
    roster += [(f'G{i}', f'G{i % 3}') for i in range(case.gannets)]
    actors, delays = [], {}
    for identity, template_id in roster:
        template = original[template_id]
        state = replace(template.state, actor_id=identity)
        delay = float(np.random.default_rng(np.random.SeedSequence(
            [case.school_seed, 7103, *_seed_words(identity)])).uniform(0., template.config.handling_duration))
        state = replace(state, position=tuple(np.asarray(state.position)+shift),
            time=initial.time, mode='recovery', mode_since=initial.time,
            ready_at=initial.time+delay, target_id=None, bout_id=0,
            bout_start=None, bout_deadline=None, last_outcome=None)
        config = replace(template.config, sense_radius=1e9) if state.species == 'G' else template.config
        actors.append(replace(template, state=state, config=config))
        delays[identity] = delay
    actors = tuple(sorted(actors, key=lambda a: a.state.actor_id))
    if any(a.capture_probability != .7 for a in actors):
        raise RuntimeError('Conditional oral contact success changed')
    if any(a.config.spacing_enabled for a in actors):
        raise RuntimeError('Original point-body no-spacing assumption changed')
    scenario = replace(reference.scenario, dt=DT)
    if parameters.geometry.threat_radius != scenario.threat_radius:
        raise RuntimeError('Controller and physical threat radii differ')
    planners = {a.state.actor_id: SimpleHerdStrikePlanner(policy='exposed', parameters=parameters)
                for a in actors if a.state.species == 'D'}
    planners.update({a.state.actor_id: DensePatchGannetPlanner(seed=int(np.random.SeedSequence(
        [case.school_seed, CAPTURE_SEED, 8111, *map(ord, a.state.actor_id)]).generate_state(1)[0]))
        for a in actors if a.state.species == 'G'})
    engine_seed, _ = initial_private_streams(case.school_seed, [a.state.actor_id for a in actors])
    metadata = case.asdict()
    metadata.update(study=HERE.name, policy=case.policy,
        dt=DT, duration=DURATION, minimum_herding_duration=case.herding_minimum,
        dolphin_target_policy='exposed', dolphin_policy_version=DOLPHIN_VERSION,
        dolphin_policy_parameters=asdict(parameters) if case.dolphins else None,
        shared_gannet_policy=GANNET_VERSION, capture_probability=.7,
        geometry='point', contact_model='original_swept_oral_point_body',
        counts=dict(fish=160, D=case.dolphin_count, G=case.gannets),
        native_sha256=declaration['native']['sha256'], native=declaration['native'],
        checkpoint_path=checkpoint['path'], checkpoint_sha256=checkpoint['sha256'],
        original_declaration_sha256=sha(declaration_path),
        preparation_manifest_path=str(preparation_path) if preparation_path else None,
        preparation_manifest_sha256=sha(preparation_path) if preparation_path else None,
        start_shift=shift.tolist(), readiness_delays=delays, engine_seed=engine_seed,
        cycle_rule='continuous local pressure proximity for H, one feasible exposed-prey strike, ordinary recovery, herd again',
        coupling_scheduler='none; no gannet-event or count input to dolphin controllers',
        target_selection='lowest visible neighbour count, interception difficulty, distance and prey ID; dense fish eligible',
        exposure_neighbour_radius=2., monitoring_interval=.1,
        bird_observation='all current underwater fish within unchanged detection depth',
        bird_targeting='unchanged DBSCAN eps2/min_samples4; accessible-count weighted patch, densest accessible fish',
        bird_roster='nested stable IDs G0 through G(N-1); actor Gi uses original launch site G(i modulo3); for N divisible by3 each site has N/3 birds, including N24/N36 with8/12 per site',
        dolphin_roster='nested stable IDs D00 through D23; Di starts at original D(i modulo12) slot; original D00 through D11 unchanged',
        dolphin_count_scope='12 fixed starting slots with two point dolphins per slot at D24; no extra spatial coverage, collision, avoidance or learned coordination',
        bird_count_scope='number and local multiplicity in a fixed three-location point-body layout; no collision or avoidance model',
        stochastic_initialization='original stable-ID readiness/private capture/tie/target formulas; no additional timing parameter',
        remove_prey=True, predator_cues=True, units='uncalibrated model units',
        developmental=True, numerical_convergence='not established; original coarse-grid exploratory map',
        controller_initial_state={who: p.state_dict() for who, p in planners.items()},
        actors=[dict(state=asdict(a.state), config=asdict(a.config), mouth=asdict(a.mouth),
                    capture_probability=a.capture_probability) for a in actors])
    return PreparedCase(case, initial, scenario, actors, planners, engine_seed, clean(metadata), reference.api)


def build(seed, policy, capture_seed=CAPTURE_SEED, presence='DG', stage='initialization'):
    """Explicit native construction, zero steps; runner must own review gates."""
    from evidence import require_approval
    require_approval(stage)
    if capture_seed != CAPTURE_SEED:
        raise ValueError('Only the frozen capture-stream label61001 is permitted')
    prepared = prepare_case(decode(seed, policy, presence))
    raw = prepared.api.Encounter(prepared.scenario, prepared.initial, prepared.actors,
        seed=prepared.engine_seed, remove_prey=True, predator_cues=True,
        school_factory=prepared.api.SurfaceSafeSchool, actor_planners=prepared.planners)
    engine = CommittedEncounter(raw)
    return engine, deepcopy(prepared.metadata)
