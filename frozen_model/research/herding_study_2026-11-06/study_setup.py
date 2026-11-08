"""New matched tactic study; archived modules and native binary are read-only."""
from dataclasses import asdict, replace
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(HERE), str(ROOT), str(ROOT / 'lib')]


def load_legacy():
    name = '_herding_archived_setup'
    if name not in sys.modules:
        path = ROOT / 'research/multispecies_feeding_study_2026-11-05/model_setup.py'
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


CONDITIONS = {'none': (None, ''), 'G': (None, 'G'),
              'pursuit_D': ('pursuit', 'D'), 'pursuit_DG': ('pursuit', 'DG'),
              'herding_D': ('herding', 'D'), 'herding_DG': ('herding', 'DG')}


def build(initial, *, school_seed, capture_seed, condition, dt):
    """Construct only after caller obtains shared lock and resource budget.

    All conditions share the saved fish checkpoint, horizontal start translation,
    fixed depths, actor capabilities and independent initial readiness offsets.
    Capture repeats change capture/tie streams, not school or readiness.
    """
    import numpy as np
    from policy import DolphinPlanner, HerdingConfig, POLICY_VERSION
    legacy = load_legacy()
    reference = legacy.prepare_seed(190001, dt=dt, dolphin_retry=.75)
    api = reference.api
    tactic, species = CONDITIONS[condition]
    shift = initial.positions.mean(axis=0) - reference.initial.positions.mean(axis=0)
    shift[2] = 0.
    actors, delays = [], {}
    for actor in reference.actors:
        state = actor.state
        if state.species not in species:
            continue
        rng = np.random.default_rng(np.random.SeedSequence(
            [int(school_seed), 7103, *legacy.actor_seed_words(state.actor_id)]))
        delay = float(rng.uniform(0, actor.config.handling_duration))
        state = replace(state, position=tuple(np.asarray(state.position) + shift),
                        time=initial.time, mode='recovery', mode_since=initial.time,
                        ready_at=initial.time + delay, target_id=None, bout_id=0,
                        bout_start=None, bout_deadline=None, last_outcome=None)
        actors.append(replace(actor, state=state))
        delays[state.actor_id] = delay
    planners = {a.state.actor_id: DolphinPlanner(tactic=tactic)
                for a in actors if a.state.species == 'D'}
    scenario = replace(reference.scenario, dt=dt)
    engine_seed = int(np.random.SeedSequence([int(school_seed), int(capture_seed), 7104]).generate_state(1)[0])
    engine = api.Encounter(scenario, initial, actors, seed=engine_seed,
                           remove_prey=True, predator_cues=True,
                           school_factory=api.SurfaceSafeSchool, actor_planners=planners)
    loaded = engine.school.state()
    if not np.array_equal(loaded.positions, initial.positions):
        raise AssertionError('Saved starting positions changed')
    if np.max(abs(loaded.directions-initial.directions), initial=0) > 1e-10:
        raise AssertionError('Unexpected checkpoint heading change')
    metadata = dict(condition=condition, tactic=tactic, school_seed=int(school_seed),
                    capture_seed=int(capture_seed), engine_seed=engine_seed, dt=dt,
                    start_shift=shift.tolist(), readiness_delays=delays,
                    actors=[dict(state=asdict(a.state), config=asdict(a.config),
                                 mouth=asdict(a.mouth), capture_probability=a.capture_probability)
                            for a in engine.actors],
                    native=reference.metadata['native'],
                    dolphin_policy_version=POLICY_VERSION, dolphin_policy_parameters=asdict(HerdingConfig()),
                    observations='Same local prey/conspecific filters for both dolphin tactics',
                    initialization='Matched starts; travel into containment is included')
    return engine, metadata


def archived_initial(seed=190001):
    return load_legacy().prepare_seed(seed).initial


def read_school(path):
    import numpy as np
    from research.prey_mediated.scenario import SchoolState
    with np.load(path, allow_pickle=False) as f:
        return SchoolState(**{k: f[k].item() if f[k].ndim == 0 else f[k] for k in f.files})
