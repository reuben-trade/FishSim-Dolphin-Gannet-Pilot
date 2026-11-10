"""One original initialization, versioned dolphin planners and committed memory.

Caller owns the canonical lock and source/input/resource freeze before build.
Keep the reviewed contact-logging context active throughout actual stepping and
acknowledgement. This setup does not enable acceleration or run native steps.
"""
from __future__ import annotations

from collections.abc import Mapping
import copy
from dataclasses import asdict
import hashlib
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
LEGACY=ROOT/'research/herding_study_2026-11-06'
LEGACY_SETUP_SHA256='4a6f7bb22abe1b45de66f192bf8f54fe1090738d2c51de2916907d1c6313156f'
SETUP_VERSION='original_initialization_committed_patch_pressure_v2'
HISTORICAL_LAUNCH_RADIUS=6.
sys.path[:0]=[str(HERE),str(ROOT)]
from committed_encounter import CommittedEncounter
from controller_v2 import ControllerParameters,DolphinPlanner,VERSION

CONDITIONS={'none':(None,''),'G':(None,'G'),'pursuit_D':('pursuit','D'),
            'pursuit_DG':('pursuit','DG'),'herding_D':('pressure','D'),'herding_DG':('pressure','DG')}


def _legacy_setup():
    path=LEGACY/'study_setup.py'
    if hashlib.sha256(path.read_bytes()).hexdigest()!=LEGACY_SETUP_SHA256:
        raise RuntimeError('The frozen original initialization source changed')
    name='_nov6_original_setup_for_patch_pressure_v2'
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module
        previous=list(sys.path)
        try:spec.loader.exec_module(module)
        finally:sys.path[:]=previous
    return sys.modules[name]


def _legacy_build(initial,**kwargs):
    """Retain the original short-name policy import while restoring caller paths."""
    if 'policy' in sys.modules and Path(sys.modules['policy'].__file__).resolve()!=LEGACY/'policy.py':
        raise RuntimeError('A different policy module would replace original initialization')
    previous=list(sys.path);sys.path[:0]=[str(LEGACY),str(ROOT),str(ROOT/'lib')]
    try:return _legacy_setup().build(initial,**kwargs)
    finally:sys.path[:]=previous


def _intervention(value):
    if value is None:return None
    if not isinstance(value,Mapping) or not set(value)<={'remove_prey','predator_cues'}:
        raise ValueError('Only explicit remove_prey/predator_cues diagnostic flags are permitted')
    if any(type(flag) is not bool for flag in value.values()):
        raise ValueError('Diagnostic intervention flags must be exact booleans')
    return dict(value)


def controller_snapshot(engine):
    """Ordinary committed checkpoint; pending proposals remain diagnostic-only."""
    if not isinstance(engine,CommittedEncounter):raise TypeError('CommittedEncounter required for controller checkpoints')
    if engine.acknowledgement_failed:raise RuntimeError('Failed acknowledgement forbids an ordinary checkpoint')
    planners=engine.actor_planners
    if set(planners)!=set(engine._planners) or any(planner is not engine._planners[name] for name,planner in planners.items()):
        raise RuntimeError('Registered planner changed after adapter construction')
    actors={actor.state.actor_id:actor.state for actor in engine.actors if actor.state.species=='D'}
    if set(planners)!=set(actors):raise RuntimeError('Controller checkpoint must cover exactly the dolphin actors')
    result={}
    for identity,planner in planners.items():
        snapshot=planner.state_dict()
        if snapshot['pending'] is not None:raise RuntimeError('Unacknowledged proposal forbids an ordinary checkpoint')
        if snapshot['committed'] is not None and snapshot['committed']!=asdict(actors[identity]):
            raise RuntimeError('Controller committed actor differs from the physical actor')
        result[identity]=snapshot
    return result


def build(initial,*,school_seed,capture_seed,condition,dt,parameters=None,diagnostic_intervention=None):
    """Preserve actors, school, ownership and RNG objects from one legacy build.

    Diagnostic flags change only existing underlying-engine switches. With
    remove_prey=False, successful contacts use the existing temporary
    availability-lock mechanism: they still draw, close bouts and incur handling,
    but do not consume prey and must never be reported as food.
    """
    if condition not in CONDITIONS:raise ValueError('Use one of the original six conditions')
    parameters=ControllerParameters() if parameters is None else parameters
    if not isinstance(parameters,ControllerParameters):raise TypeError('Explicit ControllerParameters required')
    if parameters.launch_radius!=HISTORICAL_LAUNCH_RADIUS:
        raise ValueError('Shared launch radius must remain exactly the historical6')
    intervention=_intervention(diagnostic_intervention)
    engine,original=_legacy_build(initial,school_seed=school_seed,capture_seed=capture_seed,condition=condition,dt=dt)
    if parameters.geometry.threat_radius!=engine.scenario.threat_radius:
        raise ValueError('Controller proximity radius must match actual prey threat sensing radius')
    if any(actor.state.species=='D' and parameters.geometry.sensing_radius!=actor.config.sense_radius for actor in engine.actors):
        raise ValueError('Controller sensing radius must match actual dolphin observation radius')
    tactic,_species=CONDITIONS[condition]
    engine.actor_planners={actor.state.actor_id:DolphinPlanner(tactic=tactic,parameters=parameters)
                           for actor in engine.actors if actor.state.species=='D'}
    if intervention is not None:
        for name,value in intervention.items():setattr(engine,name,value)
    # Assign flags above: setting them on this delegating proxy would shadow,
    # rather than update, the actual engine's removal/cue switches.
    committed=CommittedEncounter(engine)
    metadata=copy.deepcopy(original)
    metadata['legacy_initialization']={name:copy.deepcopy(original[name]) for name in (
        'tactic','dolphin_policy_version','dolphin_policy_parameters','initialization')}
    metadata.update(setup_version=SETUP_VERSION,dolphin_policy_version=VERSION,
        dolphin_policy_parameters=asdict(parameters),tactic=tactic,
        initialization='One unchanged original build; matched starts/readiness/travel; replaced dolphin planners with post-resolution acknowledgement',
        diagnostic_intervention=intervention,remove_prey=engine.remove_prey,predator_cues=engine.predator_cues,
        virtual_capture=not engine.remove_prey,
        capture_interpretation=('Actual unique prey removals are modelled food.' if engine.remove_prey else
            'Virtual successes are temporary availability locks, not food or prey consumed; capture/tie draws, bout closure and handling still occur.'),
        cue_interpretation=('Original predator threat cues enabled.' if engine.predator_cues else
            'Prey predator threat cues disabled as an explicit diagnostic intervention; actor observations remain unchanged.'),
        shared_contracts=dict(launch_radius=HISTORICAL_LAUNCH_RADIUS,prey_threat_radius=engine.scenario.threat_radius,
                              dolphin_sensing_radius=parameters.geometry.sensing_radius),
        acceleration_enabled_by_setup=False,controller_initial_state=controller_snapshot(committed))
    return committed,metadata
