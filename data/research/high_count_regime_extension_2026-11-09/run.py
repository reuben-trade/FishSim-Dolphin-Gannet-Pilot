"""Bounded matched simple-cycle pilot; food follows actual resolved motion.

The runner never changes the common physical engine. Samples are retrospective
diagnostics. Bird entries are recorded for analysis, never delivered as inputs
to the dolphin controllers.
"""
from __future__ import annotations

import os
for _name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_name] = '1'

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
import fcntl
import gzip
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time
from zoneinfo import ZoneInfo

import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V2 = ROOT / 'research/herding_study_2026-11-07'
OLD = ROOT / 'research/overnight_workload_2026-11-08'
ACCOUNTING = ROOT / 'research/adaptive_v2_completion_2026-11-08'
sys.path[:0] = [str(HERE), str(ACCOUNTING), str(OLD), str(V2), str(ROOT), str(ROOT/'lib')]
from accounting_v2 import AccountingV2, audit_summary
from workload_common import clean, containment, sha, write_json
from controller_v2 import shared_launch_guard
from research.prey_mediated.predators import observe

from cases import (SEEDS, DT, DURATION, CAPTURE_SEED, BULK, all_cases, decode, execution_stages, smoke_cases)
from common import reserve
POLICIES = tuple(sorted({case.policy for case in all_cases()}))
SCHOOLS = SEEDS
from horizons import horizon_record, species_projection
REFERENCE_REACH=12.-6./(np.pi/2)-.25
from cadence import SAMPLE_STEPS,PROGRESS_STEPS,sample_due,progress_due


def stamp():
    return datetime.now(ZoneInfo('Australia/Perth')).isoformat()


def jsonline(handle, value):
    handle.write(json.dumps(clean(value), allow_nan=False, separators=(',', ':'))+'\n')


@contextmanager
def logging_context():
    name = '_quick_pilot_actual_contact_logging'
    spec = importlib.util.spec_from_file_location(name, ROOT/'research/project_finish_2026-11-06/contact_logging_v2.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    with module.encounter_logging():
        yield


def snapshot(engine):
    """Serialized committed engine; includes private streams and every planner."""
    own = engine.ownership
    return clean(dict(actors=[asdict(a.state) for a in engine.actors],
        actor_policy={a.state.actor_id:dict(config=asdict(a.config), mouth=asdict(a.mouth),
            capture_probability=a.capture_probability) for a in engine.actors},
        ownership=dict(prey_ids=own.prey_ids, captured_ids=sorted(own.captured_ids),
            closed_bouts=sorted(own.closed_bouts), time=own.time),
        capture_rng={who:rng.bit_generator.state for who,rng in engine.capture_rngs.items()},
        tie_rng=engine.tie_rng.bit_generator.state,
        controllers={who:p.state_dict() for who,p in engine.actor_planners.items()}))


def local_geometry(x, velocity):
    x = np.asarray(x, float).reshape(-1, 3)
    velocity = np.asarray(velocity, float).reshape(-1, 3)
    if not len(x):
        return dict(count=0, r90=None, rg=None, outward_speed90=None,
            outward_fraction=None, components=0, largest_component_fraction=None,
            mean_neighbours=None)
    centre, flow = x.mean(0), velocity.mean(0)
    radial = x-centre
    radius = np.linalg.norm(radial, axis=1)
    outward = np.sum(radial*(velocity-flow), axis=1)/np.maximum(radius, 1e-12)
    tree = cKDTree(x)
    pairs = tree.query_pairs(2., output_type='ndarray')
    graph = csr_matrix((np.ones(len(pairs)), (pairs[:,0], pairs[:,1])), shape=(len(x), len(x)))
    count, labels = connected_components(graph, directed=False)
    return dict(count=len(x), r90=float(np.quantile(radius,.9)),
        rg=float(np.sqrt(np.mean(radius**2))),
        outward_speed90=float(np.quantile(np.maximum(outward,0.),.9)),
        outward_fraction=float(np.mean(outward>.3)), components=int(count),
        largest_component_fraction=float(np.bincount(labels).max()/len(x)),
        mean_neighbours=float(np.mean([len(v)-1 for v in tree.query_ball_point(x,2.)])))


def visible_sample(actor, school, speed):
    local = observe(actor.state, school.positions, school.directions*speed,
        school.prey_ids, actor.config)
    x = np.asarray(local.positions,float).reshape(-1,3)
    v = np.asarray(local.velocities,float).reshape(-1,3)
    # All guards are evaluated only on the observer's currently visible fish.
    eligible=[]
    near=np.flatnonzero(np.linalg.norm(x-np.asarray(actor.state.position),axis=1)<=6.)
    for i in near:
        okay, diagnostic = shared_launch_guard(actor.state,x[i],v[i],actor.config,6.)
        if okay:
            eligible.append((int(local.prey_ids[i]),diagnostic))
    metrics=local_geometry(x,v)
    metrics.update(visible_count=len(x), feasible_count=len(eligible),
        feasible_ids=[who for who,_ in eligible],
        target_id=actor.state.target_id)
    if actor.state.target_id in local.prey_ids:
        row=local.prey_ids.index(actor.state.target_id)
        metrics['target_neighbours']=int(np.sum(np.linalg.norm(x-x[row],axis=1)<=2.)-1)
        metrics['target_distance']=float(np.linalg.norm(x[row]-actor.state.position))
    return metrics


def physical_category(actor, planner):
    state=actor.state
    if state.mode=='recovery':
        return 'handling' if state.last_outcome=='capture' else 'recovery'
    if state.mode=='attack':
        return 'attack'
    phase=getattr(getattr(planner,'controller_state',None),'phase','')
    return 'containment' if phase in ('maintain','opportunity') else 'approach'


def frame_sample(engine, initial_ids, origin):
    school=engine.school.state()
    mapping={int(w):i for i,w in enumerate(initial_ids)}
    x=np.zeros((len(initial_ids),3)); v=np.zeros_like(x); alive=np.zeros(len(initial_ids),bool)
    rows=[mapping[int(w)] for w in school.prey_ids]
    x[rows]=school.positions;v[rows]=school.directions;alive[rows]=True
    frame=dict(time=school.time-origin, positions=x, directions=v, alive=alive,
        predator_positions=np.asarray([a.state.position for a in engine.actors]),
        predator_modes=np.asarray([a.state.mode for a in engine.actors],dtype='U12'),
        target_ids=np.asarray([-1 if a.state.target_id is None else a.state.target_id for a in engine.actors]),
        dolphin_phases=np.asarray([getattr(getattr(engine.actor_planners.get(a.state.actor_id),'controller_state',None),'phase','not_dolphin') for a in engine.actors],dtype='U16'))
    return frame


def point_on_step(step, clock):
    for piece in step.pieces:
        if piece.body.start-1e-10<=clock<=piece.body.end+1e-10:
            duration=piece.body.end-piece.body.start
            alpha=0. if duration<=0 else np.clip((clock-piece.body.start)/duration,0.,1.)
            return np.asarray(piece.body.before)+alpha*(np.asarray(piece.body.after)-piece.body.before)
    return np.asarray(step.state.position)


def water_entries(result, engine, seen, origin):
    """Find real downward surface crossings on resolved G motion, never plans."""
    configs={a.state.actor_id:a.config for a in engine.actors}
    records=[]
    for step in result.predator_steps:
        if step.before.species!='G':continue
        config=configs[step.before.actor_id]
        candidates=[(e.time,point_on_step(step,e.time),e.bout_id) for e in step.transitions if e.reason=='water_entry']
        for p in step.pieces:
            if (p.mode=='plunge' and p.body.before[2]>config.surface_z
                    and p.body.after[2]<=config.surface_z and p.heading_after[2]<0):
                candidates.append((p.body.end,np.asarray(p.body.after),p.bout_id))
        for clock,position,bout in candidates:
            key=(step.before.actor_id,bout)
            if key in seen:continue
            seen.add(key)
            records.append(dict(kind='water_entry',event_id=f'{key[0]}:bout{bout}',
                actor_id=key[0],bout_id=bout,time=float(clock),elapsed=float(clock-origin),
                position=position.tolist(),scheduled=False,realized=True))
    return sorted(records,key=lambda r:(r['time'],r['actor_id']))


def response_cohort(event, result, prior_sample, speed):
    """Local entry cohort; event-state interpolation has <=one-dt resolution."""
    school=result.before
    delta=event['time']-school.time
    x=school.positions+school.directions*speed*delta
    keep=np.linalg.norm(x-np.asarray(event['position']),axis=1)<=6.
    ids=school.prey_ids[keep]
    entry_x=x[keep];entry_v=school.directions[keep]*speed
    record=dict(event,cohort_ids=ids.tolist(),entry_positions=entry_x.tolist(),
        entry_velocities=entry_v.tolist(),entry_count=len(ids),
        entry_geometry=local_geometry(entry_x,entry_v),
        fish_position_resolution='constant-velocity interpolation within one actual dt; post samples are actual states',
        sample_interval=.1)
    if prior_sample is not None:
        ptime,pids,px,pv=prior_sample
        index={int(w):i for i,w in enumerate(pids)}
        rows=[index[int(w)] for w in ids if int(w) in index]
        record['pre_time']=ptime
        record['pre_offset']=ptime-event['time']
        record['pre_geometry']=local_geometry(px[rows],pv[rows])
        record['pre_ids']=[int(w) for w in ids if int(w) in index]
        record['pre_positions']=px[rows].tolist()
        record['pre_velocities']=pv[rows].tolist()
    return record


def response_sample(cohort, school, speed, origin):
    index={int(w):i for i,w in enumerate(school.prey_ids)}
    common=[int(w) for w in cohort['cohort_ids'] if int(w) in index]
    rows=[index[w] for w in common]
    entry_index={int(w):i for i,w in enumerate(cohort['cohort_ids'])}
    entry_rows=[entry_index[w] for w in common]
    entry_x=np.asarray(cohort['entry_positions'],float).reshape(-1,3)
    entry_v=np.asarray(cohort['entry_velocities'],float).reshape(-1,3)
    result=dict(kind='fish_response',event_id=cohort['event_id'],
        actor_id=cohort['actor_id'],time=school.time,elapsed=school.time-origin,
        offset=school.time-cohort['time'],entry_count=cohort['entry_count'],
        surviving_count=len(rows),cohort_ids=common,
        geometry=local_geometry(school.positions[rows],school.directions[rows]*speed),
        matched_entry_geometry=local_geometry(entry_x[entry_rows],entry_v[entry_rows]))
    if 'pre_ids' in cohort:
        pre_index={int(w):i for i,w in enumerate(cohort['pre_ids'])}
        pre_rows=[pre_index[w] for w in common if w in pre_index]
        result['matched_pre_geometry']=local_geometry(np.asarray(cohort['pre_positions'],float).reshape(-1,3)[pre_rows],
            np.asarray(cohort['pre_velocities'],float).reshape(-1,3)[pre_rows])
    return result


from evidence import source_manifest, verify_source_freeze, require_approval


def stream_helpers():
    name='_quick_pilot_original_stream_replay'
    if name not in sys.modules:
        path=OLD/'v2_engineering_probe_2026-11-08/v2_native_probe.py'
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module
        spec.loader.exec_module(module)
    return sys.modules[name]



def write_horizon_checkpoint(directory,nominal,record,events,initial,final,tie_records,school,bindings):
    """Standalone exact event-order prefix and audit survive later run failure."""
    prefix=f'checkpoint_{nominal:g}T'
    files=[]
    path=directory/(prefix+'.json');write_json(path,record);files.append(path)
    path=directory/(prefix+'.events.jsonl.gz')
    with gzip.open(path,'wt') as handle:
        for event in events:jsonline(handle,event)
    files.append(path)
    path=directory/(prefix+'.streams.json')
    write_json(path,dict(initial=initial,final=final,tie_records=tie_records));files.append(path)
    path=directory/(prefix+'.school.npz');np.savez_compressed(path,**asdict(school));files.append(path)
    write_json(directory/(prefix+'.seal.json'),dict(status='complete',nominal_horizon_T=nominal,
        observed_native_duration_T=record['observed_native_duration_T'],
        files={path.name:sha(path) for path in files},source_sha256=bindings,
        event_order='original committed accounting event sequence, no sorting or interpolation'))


def bird_accessibility(actor,school):
    c=actor.config;position=np.asarray(actor.state.position);depth=c.surface_z-school.positions[:,2]
    visible=(depth>=0)&(depth<=c.detection_depth)
    horizontal=np.linalg.norm(school.positions[:,:2]-position[:2],axis=1)
    travel=(horizontal+max(0.,position[2]-c.surface_z))/c.air_speed+depth/c.speed
    accessible=visible&(depth<=c.max_dive_depth-c.speed/c.turn_rate-c.ascent_margin)&(travel<=c.bout_duration)
    return dict(visible_count=int(visible.sum()),coarse_accessible_count=int(accessible.sum()),
        coarse_accessible_fraction=float(accessible.mean()) if len(accessible) else 0.,reference_depth=REFERENCE_REACH,
        free=actor.state.mode in ('search','orient','recovery') and actor.state.time>=actor.state.ready_at-1e-12)

def run_case(seed, policy, output, duration=36., capture_seed=61001, accelerate=True, presence='DG'):
    from build import build
    require_approval('smoke' if duration==4. else 'full')
    case=decode(seed,policy,presence)
    if duration not in (4.,36.):raise ValueError('Only declared smoke/full horizons are allowed')
    if duration==4. and case not in smoke_cases():raise ValueError('Unplanned smoke case')
    if case not in all_cases():raise ValueError('Retained outcomes are reused; never rerun as new cells')
    from acceleration_v2 import accelerated
    from contextlib import nullcontext
    directory=Path(output)/'cases'/f's{seed}_{policy}_{presence}_c{capture_seed}'
    directory.mkdir(parents=True,exist_ok=False)
    started=time.monotonic()
    reserve(directory)
    engine,metadata=build(seed,policy,capture_seed=capture_seed,presence=presence,stage='smoke' if duration==4. else 'full')
    initial=engine.school.state();origin=initial.time;steps=round(duration/DT)
    assert abs(steps*DT-duration)<1e-12
    bindings=source_manifest()
    metadata.update(duration=duration,dt=DT,capture_seed=capture_seed,
        school_seed=seed,policy=policy,presence=presence,contact_model='point',
        controller_monitor_interval=.1,trajectory_interval=.1,
        reference_capture_probability=.7,developmental=True,
        acceleration='reviewed_exact_helper_acceleration_v2' if accelerate else 'none')
    write_json(directory/'config.json',metadata)
    write_json(directory/'source_manifest.json',bindings)
    initial_receipt=snapshot(engine)
    write_json(directory/'initial_engine.json',initial_receipt)
    np.savez_compressed(directory/'initial_school.npz',**asdict(initial))
    initial_shared={k:v for k,v in initial_receipt.items() if k!='controllers'}
    write_json(directory/'initial_shared.json',initial_shared)
    helpers=stream_helpers()
    tie=helpers.PermutationRecorder(engine.tie_rng)
    engine._engine.tie_rng=tie
    accounting=AccountingV2(engine);frames=[];school_metrics=[]
    opportunity_cursors={who:0 for who in engine.actor_planners}
    seen_entries=set();cohorts=[];prior_sample=None
    attack_bouts={};available=Counter();exposure=Counter();with_recent_event=Counter()
    semantic_time={a.state.actor_id:Counter() for a in engine.actors if a.state.species=='D'}
    nearby_events={a.state.actor_id:[] for a in engine.actors if a.state.species=='D'}
    actual_steps=0;depletion_elapsed=None;horizons={}
    try:
        with logging_context(),(accelerated() if accelerate else nullcontext()), \
                gzip.open(directory/'events.jsonl.gz','wt') as event_file, \
                gzip.open(directory/'monitor.jsonl.gz','wt') as monitor_file, \
                gzip.open(directory/'opportunities.jsonl.gz','wt') as opportunity_file, \
                gzip.open(directory/'bird_events.jsonl.gz','wt') as bird_file, \
                gzip.open(directory/'responses.jsonl.gz','wt') as response_file:
            for number in range(steps+1):
                school=engine.school.state()
                if sample_due(number,steps):
                    elapsed=school.time-origin;frames.append(frame_sample(engine,initial.prey_ids,origin))
                    global_metrics=containment(school,initial_count=len(initial.prey_ids),
                        initial_centre=initial.positions.mean(0),initial_time=origin,speed=engine.scenario.speed)
                    global_metrics.update(time=school.time,elapsed=elapsed)
                    school_metrics.append(global_metrics)
                    sample_dt=min(.1,max(0.,duration-elapsed))
                    for actor in engine.actors:
                        if actor.state.species=='G':
                            jsonline(monitor_file,dict(time=school.time,elapsed=elapsed,actor_id=actor.state.actor_id,
                                physical_mode=actor.state.mode,target_id=actor.state.target_id,ready_at=actor.state.ready_at,
                                diagnostics=engine.actor_planners[actor.state.actor_id].last_diagnostics,**bird_accessibility(actor,school)))
                        if actor.state.species!='D':continue
                        who=actor.state.actor_id;planner=engine.actor_planners[who]
                        metrics=visible_sample(actor,school,engine.scenario.speed)
                        free=actor.state.mode not in ('attack','recovery') or (actor.state.mode=='recovery' and actor.state.time>=actor.state.ready_at-1e-12)
                        active=getattr(planner,'active_opportunity',None)
                        latest=[e for e in nearby_events[who] if 0<=school.time-e['time']<=2.+1e-10]
                        row=dict(time=school.time,elapsed=elapsed,actor_id=who,
                            physical_mode=actor.state.mode,mode=actor.state.mode,
                            phase=getattr(getattr(planner,'controller_state',None),'phase',''),
                            opportunity_active=active is not None,last_outcome=actor.state.last_outcome,
                            category=physical_category(actor,planner),ready_at=actor.state.ready_at,
                            free=free,**metrics,diagnostics=planner.last_diagnostics,
                        opportunity_metrics=getattr(planner,'last_opportunity_metrics',{}),
                            cycle_pressure_started=getattr(getattr(planner,'controller_state',None),'maintenance_started',None),
                            active_opportunity=active,recent_gannet_events=latest,
                            attack_available_no_launch=bool(free and metrics['feasible_count']>0),
                            sampled_free_feasible=bool(free and metrics['feasible_count']>0))
                        jsonline(monitor_file,row)
                        if row['attack_available_no_launch']:available[who]+=sample_dt
                        if active is not None:exposure[who]+=sample_dt
                        if latest:with_recent_event[who]+=sample_dt
                    for cohort in cohorts:
                        if -.001<=school.time-cohort['time']<=2.1:
                            jsonline(response_file,response_sample(cohort,school,engine.scenario.speed,origin))
                    prior_sample=(school.time,school.prey_ids.copy(),school.positions.copy(),school.directions.copy()*engine.scenario.speed)
                if progress_due(number,steps):
                    progress=dict(status='complete' if number==steps else 'running',
                        at=stamp(),pid=os.getpid(),school_seed=seed,policy=policy,presence=presence,capture_seed=capture_seed,
                        native_steps=number,elapsed=school.time-origin,
                        wall_seconds=time.monotonic()-started,
                        estimated_remaining_seconds=(time.monotonic()-started)*(steps-number)/max(number,1),
                        species={s:dict(captures=sum(v['captures'] for who,v in accounting.snapshot().items() if who.startswith(s))) for s in 'DG'},
                        cycle_launches_total=sum(v['launches'] for who,v in accounting.snapshot().items() if who.startswith('D')))
                    write_json(directory/'progress.json',progress)
                    reserve(directory)
                    assert sum(p.stat().st_size for p in directory.iterdir() if p.is_file())<=100*2**20,'Case exceeds100MiB cap'
                if number in {round(36./DT),steps}:
                    nominal=number*DT
                    per_now=accounting.snapshot()
                    partial=dict(actual_duration=school.time-origin,per_actor=per_now,remove_prey=True,
                        initial_count=len(initial.prey_ids),final_count=engine.school.n)
                    interim_audit=audit_summary(partial,accounting.events,nominal)
                    captures_now=[e for e in accounting.events if e['kind']=='oral' and e['closes_bout'] and e['status']=='captured']
                    removed_now={e['prey_id'] for e in captures_now}
                    if len(removed_now)!=len(captures_now) or set(map(int,school.prey_ids))!=set(map(int,initial.prey_ids))-removed_now:
                        interim_audit['errors'].append('Unique actual removals differ at horizon')
                    if interim_audit['errors']:raise RuntimeError(interim_audit)
                    helpers.replay_streams(initial_receipt,snapshot(engine),
                        [e for e in accounting.events if e['kind']=='oral'],tie.records)
                    record=horizon_record(nominal_T=nominal,observed_T=school.time-origin,
                        initial_count=len(initial.prey_ids),final_count=engine.school.n,per_actor=per_now,
                        native_steps=actual_steps,structure=school_metrics[-1])
                    record['physical_accounting_audit']=interim_audit
                    record['private_capture_and_tie_replay']='passed'
                    for who,values in semantic_time.items():record['per_actor'][who]['behaviour_time']=clean(values)
                    horizons[str(nominal)]=record
                    write_horizon_checkpoint(directory,nominal,record,accounting.events,
                        initial_receipt,snapshot(engine),tie.records,engine.school.state(),bindings)
                if number==steps:break
                phases={a.state.actor_id:getattr(getattr(engine.actor_planners.get(a.state.actor_id),'controller_state',None),'phase','not_dolphin') for a in engine.actors}
                result=engine.step();actual_steps+=1
                for step in result.predator_steps:
                    if step.before.species=='D':
                        for p in step.pieces:
                            dt=p.body.end-p.body.start
                            if p.mode=='recovery':
                                latest_outcome=step.before.last_outcome
                                for transition in step.transitions:
                                    if transition.time<=p.body.start+1e-12 and transition.after=='recovery':
                                        latest_outcome=transition.reason
                                category='handling' if latest_outcome=='capture' else 'recovery'
                            elif p.mode=='attack':category='attack'
                            else:category='containment' if phases.get(step.before.actor_id) in ('maintain','opportunity') else 'approach'
                            semantic_time[step.before.actor_id][category]+=dt
                    for transition in step.transitions:
                        if transition.reason=='launch':
                            attack_bouts[(step.before.actor_id,transition.bout_id)]=dict(time=transition.time,target_id=transition.target_id)
                for event in accounting.add(engine,result,phases):
                    if 'time' in event:event['elapsed']=event['time']-origin
                    elif event['kind']=='oral':event['elapsed']=event['contact']['time']-origin
                    if event.get('reason')=='gannet_global_dense_target_selected':
                        event['targeting_diagnostics']=engine.actor_planners[event['actor_id']].last_diagnostics
                    jsonline(event_file,event)
                entries=water_entries(result,engine,seen_entries,origin)
                actual_by_id={s.before.actor_id:s for s in result.predator_steps}
                for event in entries:
                    cohort=response_cohort(event,result,prior_sample,engine.scenario.speed)
                    cohorts.append(cohort);jsonline(bird_file,cohort)
                    for actor in engine.actors:
                        if actor.state.species!='D':continue
                        dposition=point_on_step(actual_by_id[actor.state.actor_id],event['time'])
                        distance=float(np.linalg.norm(dposition-event['position']))
                        if distance>actor.config.sense_radius:continue
                        detected=dict(event,detection_distance=distance,
                            detected_by=actor.state.actor_id,delivery_time=actor.state.time)
                        nearby_events[actor.state.actor_id].append(detected)
                        jsonline(bird_file,dict(detected,kind='dive_detection',controller_input=False))
                for who,planner in engine.actor_planners.items():
                    records=getattr(planner,'opportunity_events',[])
                    for event in records[opportunity_cursors[who]:]:
                        jsonline(opportunity_file,dict(event,actor_id=who,elapsed=event['time']-origin))
                    opportunity_cursors[who]=len(records)
                if not engine.school.n:
                    depletion_elapsed=engine.school.time-origin
                    break  # no native zero-prey dynamics are claimed or required for feeding counts
            for who,planner in engine.actor_planners.items():
                if getattr(planner,'active_opportunity',None) is not None:
                    planner._end(engine.school.time,'encounter_end')
                    for event in planner.opportunity_events[opportunity_cursors[who]:]:
                        jsonline(opportunity_file,dict(event,actor_id=who,elapsed=event['time']-origin))
                    opportunity_cursors[who]=len(planner.opportunity_events)
        final=engine.school.state()
        observed_duration=final.time-origin
        if not frames or abs(frames[-1]['time']-observed_duration)>1e-9:
            frames.append(frame_sample(engine,initial.prey_ids,origin))
            metrics=containment(final,initial_count=len(initial.prey_ids),initial_centre=initial.positions.mean(0),initial_time=origin,speed=engine.scenario.speed)
            metrics.update(time=final.time,elapsed=observed_duration);school_metrics.append(metrics)
        per=accounting.snapshot()
        for who,row in per.items():
            if who.startswith('D'):
                row.update(behaviour_time=semantic_time[who],
                    sampled_attack_available_not_launching_T=available[who],
                    sampled_free_feasible_T=available[who],
                    sampled_opportunity_exposure_T=exposure[who],
                    sampled_recent_gannet_event_T=with_recent_event[who],
                    sampled_no_recent_gannet_event_T=(duration-with_recent_event[who] if depletion_elapsed is None else max(0.,observed_duration-with_recent_event[who])),
                    sampled_no_opportunity_T=(duration-exposure[who] if depletion_elapsed is None else max(0.,observed_duration-exposure[who])))
        summary=dict(status='complete',at=stamp(),school_seed=seed,policy=policy,presence=presence,
            capture_seed=capture_seed,dt=DT,actual_duration=final.time-origin,
            planned_duration=duration,nominal_elapsed_T=duration,native_steps=actual_steps,
            native_absorbing_termination=depletion_elapsed is not None,depletion_elapsed_T=depletion_elapsed,
            initial_count=len(initial.prey_ids),final_count=engine.school.n,
            remove_prey=True,contact_model='point',capture_probability=.7,
            per_actor=per,wall_seconds=time.monotonic()-started,
            water_entries=len(cohorts),developmental=True,
            numerical_convergence='not_established')
        summary['species']={s:dict(count=sum(a.state.species==s for a in engine.actors),
            captures=sum(v['captures'] for who,v in per.items() if who.startswith(s)),
            launches=sum(v['launches'] for who,v in per.items() if who.startswith(s)),
            contacts=sum(v['contacts'] for who,v in per.items() if who.startswith(s))) for s in 'DG'}
        final_receipt=snapshot(engine)
        oral=[e for e in accounting.events if e['kind']=='oral']
        helpers.replay_streams(initial_receipt,final_receipt,oral,tie.records)
        audit=audit_summary(summary,accounting.events,observed_duration)
        audit['private_capture_and_tie_stream_replay']='passed'
        removed={e['prey_id'] for e in accounting.events if e['kind']=='oral' and e['closes_bout'] and e['status']=='captured'}
        if set(map(int,final.prey_ids))!=set(map(int,initial.prey_ids))-removed:
            audit['errors'].append('Unique actual removals differ from final live IDs')
        if actual_steps!=round(observed_duration/DT):audit['errors'].append('Actual native step count differs')
        if depletion_elapsed is None and actual_steps!=steps:audit['errors'].append('Incomplete nondepleted horizon')
        if depletion_elapsed is not None and (engine.school.n!=0 or len(removed)!=len(initial.prey_ids)):
            audit['errors'].append('Invalid absorbing depletion termination')
        audit['nominal_horizon_T']=duration
        audit['observed_native_duration_T']=observed_duration
        audit['native_absorbing_termination']=depletion_elapsed is not None
        for who,values in semantic_time.items():
            if abs(sum(values.values())-observed_duration)>1e-7:audit['errors'].append(who+' semantic time budget')
        for p,h in bindings.items():
            if sha(p)!=h:audit['errors'].append('Source changed during case: '+p)
        audit['status']='passed' if not audit['errors'] else 'failed'
        assert not audit['errors'],audit
        if depletion_elapsed is not None:
            for nominal in sorted({h for h in (36.,duration) if h>=observed_duration-1e-7}):
                record=horizon_record(nominal_T=nominal,observed_T=observed_duration,
                    initial_count=len(initial.prey_ids),final_count=0,per_actor=per,native_steps=actual_steps,
                    structure=school_metrics[-1],terminal=True)
                record['physical_accounting_audit']=audit
                record['private_capture_and_tie_replay']='passed'
                horizons[str(nominal)]=record
                write_horizon_checkpoint(directory,nominal,record,accounting.events,
                    initial_receipt,final_receipt,tie.records,final,bindings)
        write_json(directory/'horizons.json',horizons)
        write_json(directory/'summary.json',summary)
        write_json(directory/'audit.json',audit)
        write_json(directory/'school_metrics.json',school_metrics)
        write_json(directory/'final_engine.json',final_receipt)
        write_json(directory/'tie_stream_calls.json',tie.records)
        np.savez_compressed(directory/'final_school.npz',**asdict(final))
        np.savez_compressed(directory/'trajectories.npz',prey_ids=initial.prey_ids,
            actor_ids=np.asarray([a.state.actor_id for a in engine.actors]),
            **{k:np.asarray([f[k] for f in frames]) for k in frames[0]})
        write_json(directory/'completion.json',dict(status='complete',at=stamp(),
            files={p.name:sha(p) for p in directory.iterdir() if p.is_file()}))
        return summary
    except BaseException as error:
        write_json(directory/'failure.json',dict(status='partial',at=stamp(),error=repr(error),
            native_steps=actual_steps,actual_duration=engine.school.time-origin,
            wall_seconds=time.monotonic()-started))
        raise


def _execute_wave(cases, output, duration, workers, completed):
    if not cases:
        return
    with ProcessPoolExecutor(max_workers=workers) as pool:
        pending={pool.submit(run_case, c.school_seed, c.policy, str(output), duration,
                             CAPTURE_SEED, True, c.presence): c for c in cases}
        for future in as_completed(pending):
            case=pending[future]
            summary=future.result()
            completed.append(dict(case=case.asdict(), species=summary['species'],
                                  wall_seconds=summary['wall_seconds']))
            write_json(output/'status.json',dict(status='running',complete=len(completed),
                planned=5 if duration==4. else 48, at=stamp(), cases=completed))
            print(json.dumps(dict(complete=len(completed),case=case.name,species=summary['species'])),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--plan',action='store_true');mode.add_argument('--smoke',action='store_true');mode.add_argument('--execute',action='store_true')
    parser.add_argument('--output',type=Path);parser.add_argument('--workers',type=int,choices=(1,2,3),default=3)
    args=parser.parse_args()
    if args.plan:
        print(json.dumps(dict(status='plan_only',native_constructions=0,native_steps=0,new_cases=48,retained_cases=60,
            independent_schools=4,full_maximum_native_steps=1382400,smoke_maximum_native_steps=16000,
            all_stage_maximum_native_steps=1398400,stages=[dict(name=n,cases=len(c)) for n,c in execution_stages()])))
        return
    stage='smoke' if args.smoke else 'full';require_approval(stage)
    expected=BULK/('smoke_4T_v1' if args.smoke else 'full_36T_v1')
    output=(args.output or expected).resolve()
    if output!=expected.resolve():parser.error('Exact frozen phase output required')
    if output.exists():parser.error('Fresh outputs only; no automatic retries')
    reserve(output);output.mkdir(parents=True)
    completed=[];duration=4. if args.smoke else 36.
    write_json(output/'execution.json',dict(status='running',at=stamp(),mode=stage,duration=duration,workers=args.workers,
        maximum_native_steps=16000 if args.smoke else 1382400,protocol_sha256=sha(HERE/'protocol.json'),
        frozen_sources_sha256=sha(HERE/'frozen_sources.json')))
    try:
        with open(ROOT/'research/herding_gannet_paired_pilot_2026-11-08/native.lock','a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            stages=(('smokes',smoke_cases()),) if args.smoke else execution_stages()
            for name,cells in stages:
                _execute_wave(cells,output,duration,args.workers,completed)
                write_json(output/(name+'_stage.json'),dict(status='complete',at=stamp(),cases=[c.name for c in cells]))
            verify_source_freeze()
            write_json(output/'status.json',dict(status='complete',at=stamp(),complete=len(completed),
                planned=5 if args.smoke else 48,cases=completed,
                total_native_steps=sum(read_summary_steps(output,c['case']['case_name']) for c in completed)))
    except BaseException as error:
        write_json(output/'status.json',dict(status='failed_or_partial',at=stamp(),complete=len(completed),
            planned=5 if args.smoke else 48,error=repr(error),cases=completed,
            interpretation='Retain failures and partial cases; no replacement or automatic retry'))
        raise

def read_summary_steps(output,name):return json.loads((output/'cases'/name/'summary.json').read_text())['native_steps']

if __name__=='__main__':main()
