"""Isolated matched point-contact pilot using the accepted V2 school bank."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CURRENT = ROOT / 'research/herding_study_2026-11-07'
OLD = ROOT / 'research/overnight_workload_2026-11-08'
sys.path[:0] = [str(HERE), str(OLD), str(CURRENT), str(ROOT), str(ROOT / 'lib')]
import setup_v2 as setup
from controllers import SimpleHerdStrikePlanner, VERSION as DOLPHIN_VERSION
from committed_encounter import CommittedEncounter
from gannet import DensePatchGannetPlanner, VERSION as GANNET_VERSION

DT = .00125
DURATION = 72.
SEEDS = tuple(range(39064501, 39064509))
POLICIES = ('exposed',)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(seed, policy, capture_seed=61001, presence='DG'):
    """Construct zero steps; callers own execution and fresh output paths."""
    seed = int(seed)
    if seed not in SEEDS or policy not in POLICIES or presence not in ('D', 'G', 'DG'):
        raise ValueError('Use the eight fixed fresh schools and exposed policy')
    if capture_seed != 61001:
        raise ValueError('Use the sole prespecified capture stream61001')
    declaration_path = CURRENT / 'v2_numeric_execution_v1.json'
    declaration = json.loads(declaration_path.read_text())
    preparation_path = HERE/'checkpoints/manifest.json'
    preparation = json.loads(preparation_path.read_text())
    checkpoint = preparation['checkpoints'][str(seed)]
    if preparation['status'] != 'complete' or checkpoint['screen_status'] != 'passed':
        raise RuntimeError('Fresh school preparation/stability screen has not passed')
    if sha(checkpoint['path']) != checkpoint['sha256']:
        raise RuntimeError('The existing reproducible school checkpoint changed')
    native = declaration['native']
    if preparation['native']['sha256'] != native['sha256']:
        raise RuntimeError('Fresh preparation and feeding use different native binaries')
    if sha(native['path']) != native['sha256']:
        raise RuntimeError('The accepted native fish implementation changed')
    initial = setup._legacy_setup().read_school(checkpoint['path'])
    parameters = setup.ControllerParameters.from_dict(declaration['controller_parameters'])
    prior = ROOT/'research/simple_herd_strike_pilot_2026-11-08'
    for name in ('controllers.py','gannet.py'):
        if sha(HERE/name) != sha(prior/name):
            raise RuntimeError('Selected exposed policy/gannet model changed during replication: '+name)
    condition = 'G' if presence == 'G' else 'herding_' + presence
    original, metadata = setup.build(initial, school_seed=seed,
        capture_seed=capture_seed, condition=condition, dt=DT, parameters=parameters)
    raw = original._engine
    # Full current underwater prey visibility for birds only. Physical depth,
    # turning, travel, dive, contact and recovery limits remain independent.
    raw.actors = tuple(replace(a, config=replace(a.config, sense_radius=1e9))
        if a.state.species == 'G' else a for a in raw.actors)
    if any(actor.capture_probability != .7 for actor in raw.actors):
        raise RuntimeError('Matched original predator contact probability is not .7')
    counts = {species: sum(a.state.species == species for a in raw.actors) for species in 'DG'}
    if len(initial.prey_ids) != 160 or counts != {'D': 12 if 'D' in presence else 0, 'G': 3 if 'G' in presence else 0}:
        raise RuntimeError('Matched reference fish/predator counts changed')
    dolphin_planners = {a.state.actor_id: SimpleHerdStrikePlanner(policy=policy, parameters=parameters)
        for a in raw.actors if a.state.species == 'D'}
    raw.actor_planners = {**dolphin_planners,
        **{a.state.actor_id: DensePatchGannetPlanner(seed=int(np.random.SeedSequence(
            [int(seed), int(capture_seed), 8111, *map(ord, a.state.actor_id)]).generate_state(1)[0]))
           for a in raw.actors if a.state.species == 'G'}}
    engine = CommittedEncounter(raw)
    metadata = deepcopy(metadata)
    metadata.update(study='longer_replication_2026-11-09', policy=policy,
        presence=presence,
        dolphin_policy_version=DOLPHIN_VERSION,
        geometry='point', contact_model='original_swept_oral_point_body',
        shared_gannet_policy=GANNET_VERSION, capture_probability=.7,
        counts={'fish': 160, **counts}, school_seed=seed, capture_seed=capture_seed,
        dt=DT, duration=DURATION, minimum_herding_duration=parameters.pressure_minimum, monitoring_interval=.1,
        coupling_scheduler='none; identical dolphin rule +/-G; no bird-event inputs',
        cycle_rule='continuous local pressure proximity for 2T, one feasible strike, recovery, herd again',
        target_selection='nearest feasible' if policy=='nearest' else 'soft lowest neighbour count then interception difficulty; all dense fish remain eligible',
        exposure_neighbour_radius=2.,
        bird_observation='all current underwater fish within detection depth, no angular or range restriction',
        bird_targeting='DBSCAN eps2/min_samples4; accessible-count weighted cluster; densest accessible fish',
        actors=[dict(state=asdict(a.state), config=asdict(a.config), mouth=asdict(a.mouth),
                     capture_probability=a.capture_probability) for a in raw.actors],
        checkpoint_sha256=checkpoint['sha256'], native_sha256=native['sha256'],
        checkpoint_path=checkpoint['path'],
        preparation_manifest_path=str(preparation_path.resolve()), preparation_manifest_sha256=sha(preparation_path),
        selection_pilot=str(prior),selected_policy_source_sha256={name:sha(HERE/name) for name in ('controllers.py','gannet.py')},
        original_declaration_sha256=sha(declaration_path),
        controller_initial_state={who: planner.state_dict() for who, planner in raw.actor_planners.items()},
        units='uncalibrated model units', developmental=True,
        numerical_convergence='not tested in this policy-selection pilot')
    return engine, metadata
