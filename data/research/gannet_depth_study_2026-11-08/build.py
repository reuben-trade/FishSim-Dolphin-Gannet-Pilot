"""Frozen gannet-only depth treatments; construct zero model steps."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PRIOR=ROOT/'research/exposed_replication_2026-11-08'
CURRENT=ROOT/'research/herding_study_2026-11-07'
OLD=ROOT/'research/overnight_workload_2026-11-08'
sys.path[:0]=[str(HERE),str(OLD),str(CURRENT),str(ROOT),str(ROOT/'lib')]
import setup_v2 as setup
from committed_encounter import CommittedEncounter
from gannet import DensePatchGannetPlanner, VERSION as GANNET_VERSION

DT=.00125
DURATION=36.
SEEDS=(39063501,39063502)
POLICIES=('baseline','depth8','depth11')
TARGET_DEPTHS={'baseline':None,'depth8':8.,'depth11':11.}
REFERENCE_REACH=12.-6./(np.pi/2)-.25


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def translated_school(initial, treatment):
    """Translate z only; never regenerate, clip, or alter habitat preferences."""
    if treatment not in TARGET_DEPTHS:raise ValueError('Use declared initial-depth treatments')
    target=TARGET_DEPTHS[treatment]
    if target is None:return initial
    positions=initial.positions.copy()
    positions[:,2]+=(-float(target)-float(positions[:,2].mean()))
    if np.any(positions[:,2]>-.3):raise ValueError('Translated school violates .3 surface clearance')
    return replace(initial,positions=positions)


def build(seed,policy,capture_seed=61001,presence='G'):
    seed=int(seed)
    if seed not in SEEDS or policy not in POLICIES or presence not in ('G','none'):
        raise ValueError('Use declared schools, initial-depth treatments and G/none')
    if capture_seed not in (61001,61002):raise ValueError('Use declared capture streams')
    if capture_seed==61002 and policy!='baseline':raise ValueError('Second capture stream is baseline-only')
    prior_case=PRIOR/'results/full_36T_v1/cases'/f's{seed}_exposed_DG_c{capture_seed}'
    prior_sources=json.loads((prior_case/'source_manifest.json').read_text())
    for path,digest in prior_sources.items():
        if sha(path)!=digest:raise RuntimeError('Completed replication source changed: '+path)
    prior_config=json.loads((prior_case/'config.json').read_text())
    preparation_path=PRIOR/'checkpoints/manifest.json'
    preparation=json.loads(preparation_path.read_text())
    checkpoint=preparation['checkpoints'][str(seed)]
    if preparation['status']!='complete' or checkpoint['screen_status']!='passed':
        raise RuntimeError('Fresh school preparation is not complete/passed')
    if sha(checkpoint['path'])!=checkpoint['sha256']:raise RuntimeError('School checkpoint changed')
    declaration_path=CURRENT/'v2_numeric_execution_v1.json'
    declaration=json.loads(declaration_path.read_text())
    if sha(declaration_path)!=prior_config['original_declaration_sha256']:
        raise RuntimeError('Original shared configuration changed')
    native=declaration['native']
    if preparation['native']['sha256']!=native['sha256'] or sha(native['path'])!=native['sha256']:
        raise RuntimeError('Frozen native fish implementation changed')
    if sha(HERE/'gannet.py')!=sha(PRIOR/'gannet.py') or sha(HERE/'gannet.py')!=prior_config['selected_policy_source_sha256']['gannet.py']:
        raise RuntimeError('Gannet source differs from completed mixed replication')
    initial_base=setup._legacy_setup().read_school(checkpoint['path'])
    initial=translated_school(initial_base,policy)
    parameters=setup.ControllerParameters.from_dict(declaration['controller_parameters'])
    original,metadata=setup.build(initial,school_seed=seed,capture_seed=capture_seed,
        condition=presence,dt=DT,parameters=parameters)
    raw=original._engine
    raw.actors=tuple(replace(a,config=replace(a.config,sense_radius=1e9)) for a in raw.actors)
    if any(a.state.species!='G' or a.capture_probability!=.7 for a in raw.actors):
        raise RuntimeError('Only unchanged q=.7 gannets may be instantiated')
    if len(raw.actors)!=(3 if presence=='G' else 0) or len(initial.prey_ids)!=160:
        raise RuntimeError('Declared fish/gannet counts changed')
    raw.actor_planners={a.state.actor_id:DensePatchGannetPlanner(seed=int(np.random.SeedSequence(
        [seed,int(capture_seed),8111,*map(ord,a.state.actor_id)]).generate_state(1)[0])) for a in raw.actors}
    engine=CommittedEncounter(raw)
    metadata=deepcopy(metadata)
    depth=-initial.positions[:,2]
    metadata.update(study=HERE.name,policy=policy,depth_treatment=policy,presence=presence,
        dolphin_policy_executed=False,dolphin_count=0,shared_gannet_policy=GANNET_VERSION,
        gannet_source_sha256=sha(HERE/'gannet.py'),gannet_prior_source=str(PRIOR/'gannet.py'),
        geometry='point',contact_model='original_swept_oral_point_body',capture_probability=.7,
        counts={'fish':160,'D':0,'G':len(raw.actors)},school_seed=seed,capture_seed=capture_seed,
        dt=DT,duration=DURATION,scenario=asdict(engine.scenario),
        requested_mean_depth=TARGET_DEPTHS[policy],actual_initial_mean_depth=float(depth.mean()),
        original_mean_depth=float(-initial_base.positions[:,2].mean()),
        vertical_translation=float(initial.positions[:,2].mean()-initial_base.positions[:,2].mean()),
        initial_depth_min=float(depth.min()),initial_depth_max=float(depth.max()),
        target_depth_reference=REFERENCE_REACH,initial_reference_accessible_fraction=float(np.mean(depth<=REFERENCE_REACH)),
        school_translation='fish z only; shape, IDs, headings, clock and habitat setpoint retained',
        depth_interpretation='initial-depth transient; unchanged habitat preference5 and deadband2 permit relaxation',
        bird_observation='global current underwater fish within detection depth12',
        bird_targeting='unchanged DBSCAN eps2/min_samples4; accessible-count weighted cluster',
        actors=[dict(state=asdict(a.state),config=asdict(a.config),mouth=asdict(a.mouth),capture_probability=a.capture_probability) for a in raw.actors],
        controller_initial_state={who:p.state_dict() for who,p in raw.actor_planners.items()},
        checkpoint_path=checkpoint['path'],checkpoint_sha256=checkpoint['sha256'],
        preparation_manifest_path=str(preparation_path),preparation_manifest_sha256=sha(preparation_path),
        native_sha256=native['sha256'],original_declaration_sha256=sha(declaration_path),
        units='uncalibrated model units',developmental=True,numerical_convergence='not established')
    return engine,metadata
