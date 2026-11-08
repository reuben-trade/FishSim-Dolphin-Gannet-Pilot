"""Optional causal G launch deferral around unchanged dense targeting/physics.

No model construction or native stepping occurs on import. There is no oscillator.
Only an already legal orient-to-plunge transition can be deferred.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import importlib.util
from pathlib import Path
import sys
from types import FunctionType

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research.prey_mediated import predators

VERSION = 'committed_local_dolphin_launch_gannet_deferral_v1'
DENSE_PATH = ROOT/'research/exposed_replication_2026-11-08/gannet.py'
DENSE_SHA = '718942e1a02587da927a78410e0bde54219f265551f8e4e7755f9aefced1e086'
PREDATOR_SHA = 'ec0d77f4a678466f570ecf8cf99555f9edb23f6b7ae26851937214eaa71eac06'
EPS = 1e-10


@dataclass(frozen=True)
class Cue:
    actor_id: str
    bout_id: int
    time: float
    position: tuple
    target_id: int
    target_position: tuple
    published_at: float


def target_context(state, observation):
    targets = predators._targets(observation, state.time)
    if state.target_id not in targets:
        return None
    target = np.asarray(targets[state.target_id][0])
    cohort = [int(who) for who, (point, _) in targets.items()
              if np.linalg.norm(np.asarray(point)-target) <= 2.]
    return target, cohort


def qualification(state, target, cue, step_start):
    age = float(state.time-cue.time)
    distance = float(np.linalg.norm(np.asarray(state.position)-cue.position))
    region_distance = float(np.linalg.norm(target-cue.target_position))
    reason = ('uncommitted_or_future_cue' if cue.published_at > step_start+EPS or age < -EPS
              else 'cue_expired' if age > 2.+EPS
              else 'peer_outside_12' if distance > 12.
              else 'target_region_outside_4' if region_distance > 4.
              else 'qualified')
    return reason == 'qualified', dict(cue_age=age, peer_distance_3d=distance,
        target_region_distance_3d=region_distance, qualification=reason)


def decide(state, observation, cues, memory, *, lag, step_start):
    """Pure gate. Caller invokes this only after original plunge prerequisites."""
    if lag not in (0., 1., 2.):
        raise ValueError('Only predeclared lags0/1/2T')
    if state.species != 'G' or state.mode != 'orient' or state.time < state.ready_at-EPS:
        raise ValueError('Gate accepts only a physically ready original G orient launch')
    current = deepcopy(memory)
    opportunity = state.bout_id+1
    if current is not None and current['opportunity'] != opportunity:
        current = None
    context = target_context(state, observation)
    if context is None:
        raise ValueError('Original legal launch must have a visible retained target')
    target, cohort = context
    row = dict(kind='timing_gate', actor_id=state.actor_id, time=state.time,
        opportunity=opportunity, target_id=state.target_id, position=list(state.position),
        target_position=target.tolist(), cohort_ids=cohort, original_legal=True,
        ready_at=state.ready_at, lag_T=lag, original_mode=state.mode)
    if current is None:
        candidates=[]
        for cue in cues:
            okay, detail=qualification(state,target,cue,step_start)
            if okay:candidates.append((cue,detail))
        if not candidates:
            return True, None, dict(row, allow=True, reason='no_qualified_committed_local_cue')
        cue, detail=min(candidates,key=lambda v:(-v[0].time,v[0].actor_id,v[0].bout_id))
        current=dict(opportunity=opportunity, target_id=state.target_id, cue=asdict(cue),
            first_eligible_at=state.time, requested_release=cue.time+lag,
            status='waiting', ever_deferred=False)
    else:
        cue=Cue(**current['cue'])
        okay, detail=qualification(state,target,cue,step_start)
        if current['status'] == 'waiting' and (not okay or current['target_id'] != state.target_id):
            current['status']='cancelled'
            current['cancellation']=('target_changed' if current['target_id'] != state.target_id
                                     else detail['qualification'])
    if current['status'] == 'waiting' and state.time >= current['requested_release']-EPS:
        current['status']='released'
    allow=current['status'] != 'waiting'
    if not allow:current['ever_deferred']=True
    reason=('waiting_for_committed_launch_lag' if not allow else
            'cancelled_'+current['cancellation'] if current['status']=='cancelled' else
            'requested_release_reached')
    return allow,current,dict(row,**detail,allow=allow,reason=reason,
                             timing=deepcopy(current))


def advance_with_gate(state, observation, dt, config, gate):
    """Clone function bindings only; execute the original integrator bytecode."""
    namespace=dict(predators.advance.__globals__)
    original_launch=predators._launch
    def launch(current, settings, events):
        if current.species=='G' and current.mode=='orient' and not gate(current, observation):
            return current
        return original_launch(current, settings, events)
    namespace['_launch']=launch
    namespace['_resolve_mode']=FunctionType(predators._resolve_mode.__code__,namespace)
    cloned=FunctionType(predators.advance.__code__,namespace)
    return cloned(state,observation,dt,config)


def point_on_step(step, clock):
    for piece in step.pieces:
        if piece.body.start-EPS <= clock <= piece.body.end+EPS:
            duration=piece.body.end-piece.body.start
            alpha=0. if duration<=0 else np.clip((clock-piece.body.start)/duration,0.,1.)
            return np.asarray(piece.body.before)+alpha*(np.asarray(piece.body.after)-piece.body.before)
    return np.asarray(step.state.position)


class TimingBus:
    def __init__(self, raw, *, enabled=False, lag=1., emit=None):
        if lag not in (0.,1.,2.):raise ValueError('Only declared lags0/1/2T')
        self.raw=raw;self.enabled=bool(enabled);self.lag=float(lag)
        self.emit=emit or (lambda row:None)
        self.cues=[];self.memories={};self.launches={};self.entries=set()
        self.in_step=False;self.failed=False;self.records=[]

    def begin_step(self):
        if self.failed or self.in_step:raise RuntimeError('Timing bus is failed or uncommitted')
        self.in_step=True
        self.before=self.raw.school.state()
        self.step_start=self.before.time
        self.staged={};self.histories={}

    def stage_actor(self, actual, memory, history):
        if not self.in_step:raise RuntimeError('Timing acknowledgement outside step')
        terminals=[e.time for e in actual.transitions if e.reason in ('capture','contact_miss')]
        cutoff=min(terminals) if actual.contact_resolved and terminals else actual.state.time
        kept=[item for item in history if item[0]<=cutoff+EPS]
        self.staged[actual.before.actor_id]=deepcopy(kept[-1][1] if kept else memory)
        self.histories[actual.before.actor_id]=deepcopy([item[2] for item in kept])

    def finalize(self,result):
        if not self.in_step:raise RuntimeError('No staged timing step')
        rows=[]
        for who,memory in self.staged.items():
            self.memories[who]=memory
            history=self.histories[who]
            previous=None
            for row in history:
                identity=(row['time'],row['reason'])
                if identity!=previous:rows.append(row)
                previous=identity
        before=result.before
        lookup={int(w):i for i,w in enumerate(before.prey_ids)}
        for step in result.predator_steps:
            who=step.before.actor_id
            for event in step.transitions:
                if event.reason!='launch':continue
                position=point_on_step(step,event.time)
                if step.before.species=='D':
                    index=lookup.get(event.target_id)
                    if index is None:raise RuntimeError('Committed D launch target absent at step start')
                    target=before.positions[index]+before.directions[index]*self.raw.scenario.speed*(event.time-before.time)
                    cue=Cue(who,event.bout_id,event.time,tuple(position),int(event.target_id),
                            tuple(target),result.after.time)
                    self.cues.append(cue)
                    rows.append(dict(kind='committed_dolphin_cue',**asdict(cue)))
                else:
                    memory=deepcopy(self.memories.get(who))
                    if memory is not None and memory['opportunity']!=event.bout_id:memory=None
                    row=dict(kind='actual_gannet_launch',actor_id=who,bout_id=event.bout_id,
                        time=event.time,position=position.tolist(),target_id=event.target_id,
                        timing=memory,realized=True,
                        launch_lag=None if memory is None else event.time-memory['cue']['time'])
                    self.launches[(who,event.bout_id)]=row;rows.append(row)
            candidates=[(e.time,point_on_step(step,e.time),e.bout_id)
                        for e in step.transitions if e.reason=='water_entry']
            if step.before.species=='G':
                for piece in step.pieces:
                    if piece.mode=='plunge' and piece.body.before[2]>0 and piece.body.after[2]<=0 and piece.heading_after[2]<0:
                        candidates.append((piece.body.end,np.asarray(piece.body.after),piece.bout_id))
                for when,position,bout in candidates:
                    key=(who,bout)
                    if key in self.entries:continue
                    self.entries.add(key);launch=self.launches.get(key)
                    memory=None if launch is None else launch['timing']
                    rows.append(dict(kind='actual_gannet_water_entry',actor_id=who,bout_id=bout,
                        time=when,position=np.asarray(position).tolist(),realized=True,
                        cue_relative_water_entry_lag=None if memory is None else when-memory['cue']['time'],
                        timing=deepcopy(memory),interpretation='surface crossing, not prey-region arrival'))
        self.cues=[c for c in self.cues if result.after.time-c.time<=2.+EPS]
        self.in_step=False
        for row in sorted(rows,key=lambda r:(r['time'],r.get('actor_id',''),r['kind'])):
            self.records.append(row);self.emit(deepcopy(row))

    def state_dict(self):
        if self.in_step:raise RuntimeError('Snapshot requires a committed timing step')
        return dict(version=VERSION,enabled=self.enabled,lag=self.lag,failed=self.failed,
            cues=[asdict(c) for c in self.cues],memories=deepcopy(self.memories),
            launches=[deepcopy(v) for _,v in sorted(self.launches.items())],entries=sorted(self.entries))


class TimedGannet:
    def __init__(self, original, bus):
        if hashlib.sha256(DENSE_PATH.read_bytes()).hexdigest()!=DENSE_SHA:
            raise RuntimeError('Dense targeting source changed')
        self.bus=bus;self.pending=False
        name='_local_timing_dense_'+str(id(self))
        spec=importlib.util.spec_from_file_location(name,DENSE_PATH)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module
        spec.loader.exec_module(module)
        self.original=module.DensePatchGannetPlanner()
        self.original.load_state_dict(original.state_dict())
        module.advance=self._advance

    def __getattr__(self,name):return getattr(self.original,name)

    def _advance(self,state,observation,dt,config):
        # Dense targeting can discard its first provisional recovery-boundary
        # advance. Restart from committed timing memory for every invocation.
        self.proposed=deepcopy(self.before_memory);self.history=[]
        if not self.bus.enabled:return predators.advance(state,observation,dt,config)
        def gate(current,obs):
            allow,memory,row=decide(current,obs,self.bus.cues,self.proposed,
                lag=self.bus.lag,step_start=self.bus.step_start)
            self.proposed=memory
            self.history.append((current.time,deepcopy(memory),row))
            return allow
        return advance_with_gate(state,observation,dt,config,gate)

    def __call__(self,state,observation,dt,config,**kwargs):
        if self.pending or not self.bus.in_step:raise RuntimeError('Invalid timing proposal boundary')
        self.before_memory=deepcopy(self.bus.memories.get(state.actor_id))
        self.proposed=deepcopy(self.before_memory);self.history=[]
        plan=self.original(state,observation,dt,config,**kwargs)
        self.pending=True
        return plan

    def commit_step(self,actual):
        if not self.pending:raise RuntimeError('No timing proposal to acknowledge')
        self.original.commit_step(actual)
        self.bus.stage_actor(actual,self.before_memory,self.history)
        self.pending=False

    def state_dict(self):return self.original.state_dict()


class TimedEncounter:
    def __init__(self,committed,bus):self.committed=committed;self.bus=bus
    def __getattr__(self,name):return getattr(self.committed,name)
    def step(self,**kwargs):
        self.bus.begin_step()
        try:
            result=self.committed.step(**kwargs)
            self.bus.finalize(result)
            return result
        except BaseException:
            self.bus.failed=True
            raise


def install(engine,*,enabled=False,lag=1.,emit=None):
    if hashlib.sha256(Path(predators.__file__).read_bytes()).hexdigest()!=PREDATOR_SHA:
        raise RuntimeError('Original physical integrator changed')
    raw=engine._engine
    bus=TimingBus(raw,enabled=enabled,lag=lag,emit=emit)
    raw.actor_planners={who:TimedGannet(planner,bus) if who.startswith('G') else planner
                        for who,planner in raw.actor_planners.items()}
    cls=type(engine)
    return TimedEncounter(cls(raw),bus),bus
