"""Individual, deterministic local predator mechanics in uncalibrated model units.

No school metrics, native simulation, interspecies information or RNG are used.
The caller supplies one common step-start fish snapshot to every observer.
Decision targets persist while visible; interception assumes constant observed
prey velocity for a bounded horizon. Patch-edge positioning is an encoded local
herding tendency, not emergent coordination. Same-species spacing is opt-in.

Movement uses bounded endpoint turning and a straight endpoint-heading Euler
translation, subdivided at clocks, water crossings and habitat limits. A boundary
time solve recomputes heading and displacement for the same duration. The angular
increment is <=2 atan(turn_rate*duration/2), so contacts' normalized-linear heading
interpolation is also rate-bounded. Actual heading endpoints are returned for its
mouth-chord approximation. Turning
paths require dt sensitivity; straight intercepts have exact swept contacts.
Boundary stops preserve position and finite heading rate, with explicit events.
They are fallbacks, not unreported reflections. Contact response holds the rest
of the current step; ascent/continued recovery starts on the next call. This
within-step approximation likewise requires numerical sensitivity checks.
Gannet locomotion uses the medium of each actual motion piece. At the surface,
its endpoint heading chooses the side it enters; a level surface piece uses the
water speed. Uncommitted water entry triggers an explicit emergency ascent with
no bite window, rather than continuing aerial search below the surface.
Targetless dolphin search at the surface turns toward the local horizontal
tangent, preventing a permanent upward-facing boundary hold. The usual finite
turn bound applies; this uses only its own heading and the water surface.
Gannet flight_height is a preferred search/orientation altitude, not a ceiling.
Ascent is split exactly there for its state transition; subsequent aerial turns
retain finite motion and may overshoot that altitude.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math
from numbers import Integral, Real

import numpy as np

from .contacts import LinearSegment, TimeWindow


def _number(x, name, *, positive=False, nonnegative=False):
    if isinstance(x, (bool,np.bool_)) or not isinstance(x, Real) or not math.isfinite(x):
        raise ValueError(name+' must be finite and real')
    if (positive and x<=0) or (nonnegative and x<0):
        raise ValueError(name+' is outside its permitted range')
    return float(x)


def _vector(x, name, *, unit=False):
    value=np.asarray(x,float)
    if value.shape!=(3,) or not np.isfinite(value).all():
        raise ValueError(name+' must be a finite 3-vector')
    if unit and not np.isclose(np.linalg.norm(value),1.,atol=1e-8,rtol=0):
        raise ValueError(name+' must be unit length')
    return tuple(float(v) for v in value)


def _unit(x, fallback=(1.,0.,0.)):
    x=np.asarray(x,float); norm=np.linalg.norm(x)
    return x/norm if norm>1e-12 else np.asarray(fallback,float)


def turn_toward(heading, desired, angle):
    """Deterministic shortest-arc turn; antipodal inputs use a local fixed axis."""
    h=_unit(heading); d=_unit(desired,h)
    theta=math.acos(float(np.clip(h@d,-1.,1.)))
    if theta<=angle or theta<1e-12: return tuple(d)
    tangent=d-h*(h@d)
    if np.linalg.norm(tangent)<1e-12:
        axis=np.eye(3)[int(np.argmin(abs(h)))]; tangent=axis-h*(h@axis)
    result=h*math.cos(angle)+_unit(tangent)*math.sin(angle)
    return tuple(_unit(result))


@dataclass(frozen=True)
class PredatorConfig:
    species: str = 'D'
    dolphin_policy: str = 'direct'
    speed: float = 6.
    air_speed: float = 10.
    turn_rate: float = math.pi/2
    sense_radius: float = 25.
    patch_radius: float = 3.
    edge_margin: float = 1.
    edge_tolerance: float = 1.
    positioning_budget: float = 4.
    intercept_horizon: float = 3.
    bout_duration: float = 6.
    handling_duration: float = 2.
    miss_recovery_duration: float = 1.
    surface_z: float = 0.
    flight_height: float = 3.
    plunge_horizontal_radius: float = 6.
    detection_depth: float = 12.
    max_dive_depth: float = 12.
    ascent_margin: float = .25
    spacing_enabled: bool = False
    spacing_radius: float = 2.
    spacing_gain: float = .5
    max_motion_interval: float = .05

    def __post_init__(self):
        if self.species not in ('D','G','S') or self.dolphin_policy not in ('direct','patch_edge'):
            raise ValueError('supported species/policies are D/G/S and direct/patch_edge')
        for name in ('speed','air_speed','turn_rate','sense_radius','patch_radius','edge_margin',
                     'edge_tolerance','positioning_budget','intercept_horizon','bout_duration',
                     'handling_duration','miss_recovery_duration','flight_height','plunge_horizontal_radius',
                     'detection_depth','max_dive_depth','spacing_radius','max_motion_interval'):
            _number(getattr(self,name),name,positive=True)
        for name in ('ascent_margin','spacing_gain'): _number(getattr(self,name),name,nonnegative=True)
        _number(self.surface_z,'surface_z')
        if not isinstance(self.spacing_enabled,bool): raise ValueError('spacing_enabled must be boolean')
        if self.species=='G' and self.max_dive_depth<=self.speed/self.turn_rate+self.ascent_margin:
            raise ValueError('max_dive_depth must exceed the proactive turning/ascent margin')


@dataclass(frozen=True)
class PredatorState:
    actor_id: str
    species: str
    position: tuple[float,float,float]
    heading: tuple[float,float,float]
    time: float = 0.
    mode: str = 'search'
    mode_since: float = 0.
    target_id: int | None = None
    bout_id: int = 0
    bout_start: float | None = None
    bout_deadline: float | None = None
    ready_at: float = 0.
    last_outcome: str | None = None

    def __post_init__(self):
        if not isinstance(self.actor_id,str) or not self.actor_id or self.species not in ('D','G','S'):
            raise ValueError('a stable actor ID and D/G/S species are required')
        modes={'D':{'search','position','attack','recovery'},
               'G':{'search','orient','plunge','pursuit','ascent','recovery'},
               'S':{'search','position','orient','attack','recovery'}}
        if self.mode not in modes[self.species]: raise ValueError('mode does not belong to this species')
        for key in ('time','mode_since','ready_at'): _number(getattr(self,key),key,nonnegative=True)
        if self.mode_since>self.time: raise ValueError('mode_since cannot be in the future')
        for name in ('bout_id','target_id'):
            value=getattr(self,name)
            if value is None and name=='target_id': continue
            if isinstance(value,(bool,np.bool_)) or not isinstance(value,Integral) or value<0:
                raise ValueError(name+' must be a nonnegative integer')
        if (self.bout_start is None)!=(self.bout_deadline is None): raise ValueError('bout clocks must be paired')
        if self.bout_start is not None:
            _number(self.bout_start,'bout_start',nonnegative=True)
            _number(self.bout_deadline,'bout_deadline',nonnegative=True)
            if not self.bout_start<=self.time<=self.bout_deadline+1e-10:
                raise ValueError('active bout clocks must contain the state time')
        for name in ('position','heading'):
            object.__setattr__(self,name,_vector(getattr(self,name),name,unit=name=='heading'))


def initial_predator(actor_id, position, heading, config, *, time=0.):
    """Caller-specified geometry only; no implicit school centre or assigned slot."""
    state=PredatorState(actor_id,config.species,position,heading,time=time,mode_since=time,ready_at=time)
    z=state.position[2]
    if config.species in ('D','S') and z>config.surface_z: raise ValueError('D/S must start at/below water')
    if config.species=='G' and z<config.surface_z: raise ValueError('G search must start at/above water')
    return state


@dataclass(frozen=True)
class LocalObservation:
    actor_id: str
    time: float
    prey_ids: tuple[int,...]
    positions: tuple[tuple[float,float,float],...]
    velocities: tuple[tuple[float,float,float],...]
    spacing_vector: tuple[float,float,float]


def observe(state, fish_positions, fish_velocities, prey_ids, config, *, conspecific_positions=None):
    """Copy/filter one step-start snapshot; stable ID order resolves equal distances."""
    if state.species!=config.species: raise ValueError('state/config species mismatch')
    x=np.asarray(fish_positions,float); v=np.asarray(fish_velocities,float); ids=np.asarray(prey_ids)
    if x.shape==(0,): x=x.reshape(0,3)
    if v.shape==(0,): v=v.reshape(0,3)
    if x.ndim!=2 or x.shape[1:]!=(3,) or v.shape!=x.shape or not np.isfinite(x).all() or not np.isfinite(v).all():
        raise ValueError('finite live fish positions/velocities with shape (N,3) required')
    if ids.size==0: ids=ids.astype(np.int64)
    if ids.shape!=(len(x),) or ids.dtype.kind not in 'iu' or np.any(ids<0) or len(np.unique(ids))!=len(ids):
        raise ValueError('unique nonnegative stable prey IDs required')
    distance=np.linalg.norm(x-np.asarray(state.position),axis=1)
    depth=config.surface_z-x[:,2]
    visible=(distance<=config.sense_radius)&(depth>=0)
    if config.species=='G': visible &= depth<=config.detection_depth
    index=np.flatnonzero(visible);index=index[np.argsort(ids[index])]
    spacing=np.zeros(3)
    if conspecific_positions is not None:
        if not config.spacing_enabled: raise ValueError('same-species observation requires explicit spacing_enabled')
        others=np.asarray(conspecific_positions,float)
        if others.shape==(0,): others=others.reshape(0,3)
        if others.ndim!=2 or others.shape[1:]!=(3,) or not np.isfinite(others).all():
            raise ValueError('conspecific positions must be finite (N,3)')
        delta=np.asarray(state.position)-others; d=np.linalg.norm(delta,axis=1)
        near=(d>1e-12)&(d<config.spacing_radius)
        if np.any(near): spacing=np.sum(delta[near]/d[near,None]*(1-d[near,None]/config.spacing_radius),axis=0)
    return LocalObservation(state.actor_id,state.time,tuple(int(i) for i in ids[index]),
        tuple(tuple(float(c) for c in row) for row in x[index]),
        tuple(tuple(float(c) for c in row) for row in v[index]),tuple(float(c) for c in spacing))


def intercept_point(position, target, velocity, speed, horizon):
    """Earliest constant-velocity intercept, clipped to a declared finite horizon."""
    p=np.asarray(position,float); q=np.asarray(target,float); v=np.asarray(velocity,float)
    r=q-p; a=float(v@v-speed*speed); b=float(2*r@v); c=float(r@r)
    roots=[]
    if abs(a)<1e-12:
        if b<0: roots=[-c/b]
    else:
        discriminant=b*b-4*a*c
        if discriminant>=0:
            root=math.sqrt(discriminant); roots=[(-b-root)/(2*a),(-b+root)/(2*a)]
    positive=[t for t in roots if t>=0 and math.isfinite(t)]
    lead=min(positive) if positive else np.linalg.norm(r)/speed
    lead=min(horizon,max(0.,lead))
    return tuple(q+lead*v),float(lead)


def _targets(observation, time):
    elapsed=time-observation.time
    return {i:(np.asarray(x)+elapsed*np.asarray(v),np.asarray(v))
            for i,x,v in zip(observation.prey_ids,observation.positions,observation.velocities)}


def patch_edge_goal(state, observation, config):
    """Only target-neighbour prey within patch_radius contribute to this goal."""
    targets=_targets(observation,state.time)
    if state.target_id not in targets: raise ValueError('patch edge requires a locally visible retained target')
    target,velocity=targets[state.target_id]
    patch=np.array([p for p,_ in targets.values() if np.linalg.norm(p-target)<=config.patch_radius])
    centre=patch.mean(axis=0)
    radial=_unit(np.asarray(state.position)-centre,_unit(-velocity,-np.asarray(state.heading)))
    extent=max(0.,float(np.max((patch-centre)@radial)))
    return tuple(centre+radial*(extent+config.edge_margin)),len(patch)


@dataclass(frozen=True)
class Transition:
    time: float
    before: str
    after: str
    reason: str
    bout_id: int
    target_id: int | None


@dataclass(frozen=True)
class MotionPiece:
    body: LinearSegment
    heading_before: tuple[float,float,float]
    heading_after: tuple[float,float,float]
    mode: str
    bout_id: int
    target_id: int | None
    bite_window: TimeWindow | None
    water_window: TimeWindow | None
    boundary_hold: bool = False


@dataclass(frozen=True)
class PredatorStep:
    before: PredatorState
    state: PredatorState
    pieces: tuple[MotionPiece,...]
    transitions: tuple[Transition,...]
    contact_resolved: bool = False


def _transition(state, mode, reason, events, **changes):
    events.append(Transition(state.time,state.mode,mode,reason,state.bout_id,state.target_id))
    return replace(state,mode=mode,mode_since=state.time,**changes)


def _finish(state, config, reason, events):
    return _transition(state,'recovery' if state.species in ('D','S') else 'ascent',reason,events,
                       target_id=None,bout_start=None,bout_deadline=None,
                       ready_at=state.time+config.miss_recovery_duration,last_outcome=reason)


def _launch(state, config, events):
    state=replace(state,bout_id=state.bout_id+1,bout_start=state.time,
                  bout_deadline=state.time+config.bout_duration,last_outcome=None)
    return _transition(state,'attack' if state.species=='D' else 'plunge','launch',events)


def _resolve_mode(state, observation, config, events):
    if (state.species=='G' and state.mode in ('search','orient','recovery')
            and (state.position[2]<config.surface_z
                 or (state.position[2]==config.surface_z and state.heading[2]<0))):
        return _transition(state,'ascent','uncommitted_water_entry',events,
                           target_id=None,bout_start=None,bout_deadline=None,
                           ready_at=max(state.ready_at,state.time+config.miss_recovery_duration),
                           last_outcome='uncommitted_water_entry')
    targets=_targets(observation,state.time)
    if state.bout_deadline is not None:
        if state.time>=state.bout_deadline-1e-12: return _finish(state,config,'timeout',events)
        if state.target_id not in targets: return _finish(state,config,'target_not_visible',events)
    if state.species=='S':
        # The local shark adapter owns positioning/orientation/readiness.
        # Shared motion only executes a committed upward opportunity, then
        # ordinary non-biting recovery for the unused fraction of this step.
        if state.mode=='attack':
            if state.position[2]>=config.surface_z:
                return _finish(state,config,'shark_surface_reached',events)
            if state.target_id not in targets:
                return _finish(state,config,'target_not_visible',events)
            target,velocity=targets[state.target_id]
            goal,_=intercept_point(state.position,target,velocity,config.speed,config.intercept_horizon)
            if goal[2]<=state.position[2] or state.heading[2]<=0.:
                return _finish(state,config,'shark_upward_opportunity_lost',events)
        return state
    if state.mode=='recovery' and state.time>=state.ready_at-1e-12:
        state=_transition(state,'search','recovery_complete',events)
    if state.mode in ('search','position','orient'):
        if state.target_id not in targets:
            if not targets:
                if state.mode!='search': state=_transition(state,'search','no_local_target',events,target_id=None)
                return state
            selected=min(targets,key=lambda i:(np.linalg.norm(targets[i][0]-state.position),i))
            state=replace(state,target_id=selected)
        if state.mode=='search':
            if state.species=='D':
                if config.dolphin_policy=='direct': return _launch(state,config,events)
                return _transition(state,'position','local_patch_selected',events)
            return _transition(state,'orient','local_prey_detected',events)
        if state.mode=='position':
            goal,_=patch_edge_goal(state,observation,config)
            if np.linalg.norm(np.asarray(goal)-state.position)<=config.edge_tolerance:
                return _launch(state,config,events)
            if state.time-state.mode_since>=config.positioning_budget-1e-12:
                return _launch(state,config,events)
        if state.mode=='orient':
            target,_=targets[state.target_id]
            if np.linalg.norm((target-np.asarray(state.position))[:2])<=config.plunge_horizontal_radius:
                return _launch(state,config,events)
    if state.species=='G':
        if state.mode=='plunge' and state.position[2]<=config.surface_z:
            return _transition(state,'pursuit','water_entry',events)
        if state.mode=='pursuit' and config.surface_z-state.position[2]>=config.max_dive_depth-config.speed/config.turn_rate-config.ascent_margin:
            return _finish(state,config,'ascent_depth_margin',events)
        if state.mode=='ascent' and state.position[2]>=config.surface_z+config.flight_height-1e-12:
            return _transition(state,'recovery','flight_height_reached',events)
    return state


def _medium_speed(state, config, heading=None):
    """Speed for a piece's starting medium and its actual side at the surface.

    Non-surface pieces are split at a crossing before the speed is changed.
    For interception prediction, the current heading supplies the surface side;
    candidate motion then selects its speed using the bounded endpoint heading.
    """
    if state.species in ('D','S'): return config.speed
    z=state.position[2]
    direction=state.heading if heading is None else heading
    if z>config.surface_z or (z==config.surface_z and direction[2]>0):
        return config.air_speed
    return config.speed


def _goal_speed(state, observation, config):
    p=np.asarray(state.position); targets=_targets(observation,state.time)
    if state.mode=='recovery': return np.asarray(state.heading),0.
    if state.mode=='ascent':
        return np.array([0.,0.,1.]),_medium_speed(state,config)
    if state.mode=='position':
        goal,_=patch_edge_goal(state,observation,config); desired=np.asarray(goal)-p; speed=config.speed
    elif state.mode in ('attack','plunge','pursuit','orient'):
        target,velocity=targets[state.target_id]
        speed=_medium_speed(state,config)
        goal,_=intercept_point(p,target,velocity,speed,config.intercept_horizon)
        goal=np.asarray(goal)
        if state.mode=='orient': goal[2]=config.surface_z+config.flight_height
        desired=goal-p
    else:
        speed=_medium_speed(state,config)
        desired=np.asarray(state.heading).copy()
        if state.species=='G':
            horizontal=_unit([*desired[:2],0.])
            desired=np.array([*horizontal[:2],config.surface_z+config.flight_height-p[2]])
        elif p[2]==config.surface_z and desired[2]>0:
            desired=_unit([*desired[:2],0.])
    if config.spacing_enabled:
        desired=_unit(desired,state.heading)+config.spacing_gain*np.asarray(observation.spacing_vector)
    return desired,speed


def _piece(state, end, after, hafter, config, *, boundary_hold=False):
    body=LinearSegment(state.time,end,state.position,after)
    bite=(TimeWindow(state.bout_start,state.bout_deadline)
          if state.mode in ('attack','plunge','pursuit') and state.bout_start is not None else None)
    z0,z1=state.position[2],after[2]; surface=config.surface_z
    if z0<=surface and z1<=surface: water=TimeWindow(state.time,end)
    elif z0==surface: water=TimeWindow(state.time,state.time)
    elif z1==surface: water=TimeWindow(end,end)
    else: water=None
    return MotionPiece(body,state.heading,hafter,state.mode,state.bout_id,state.target_id,bite,water,boundary_hold)


def advance(state, observation, dt, config):
    """Return a full path proposal; chronological contact resolution happens later.

    Timeout at the endpoint is provisional: apply_contact at that exact deadline
    replaces it, so valid boundary contacts precede timeout as contacts requires.
    """
    _number(dt,'dt',positive=True)
    if state.species!=config.species or observation.actor_id!=state.actor_id or observation.time!=state.time:
        raise ValueError('observation must belong to this actor and exact step-start clock')
    if state.species=='S' and state.mode not in ('attack','recovery'):
        raise ValueError('S search/position/orient motion requires its local planner')
    if ((state.species in ('D','S') and state.position[2]>config.surface_z)
            or (state.species=='G' and state.position[2]<config.surface_z-config.max_dive_depth)):
        raise ValueError('initial state violates the physical habitat boundary')
    before=state; end=state.time+dt; pieces=[]; events=[]
    while state.time<end-1e-13:
        # Resolve zero-time mode transitions before advancing the physical clock.
        for _ in range(8):
            previous=state;state=_resolve_mode(state,observation,config,events)
            if state==previous: break
        desired,speed=_goal_speed(state,observation,config)
        h=min(end-state.time,config.max_motion_interval,math.pi/(4*config.turn_rate))
        for deadline in (state.bout_deadline,state.ready_at if state.mode=='recovery' else None,
                         state.mode_since+config.positioning_budget if state.mode=='position' else None):
            if deadline is not None and deadline>state.time+1e-12: h=min(h,deadline-state.time)
        start=np.asarray(state.position)
        def candidate(duration):
            actual=turn_toward(state.heading,desired,2*math.atan(config.turn_rate*duration/2))
            actual_speed=0. if speed==0 else _medium_speed(state,config,actual)
            return actual,start+actual_speed*duration*np.asarray(actual)
        heading,after=candidate(h)
        boundary_hold=False; limit=None; crossing=None
        # Split a true water crossing BEFORE changing the locomotion speed.
        if state.species=='G' and (start[2]-config.surface_z)*(after[2]-config.surface_z)<0:
            crossing=config.surface_z
        if state.species in ('D','S') and after[2]>config.surface_z: limit=config.surface_z
        if state.species=='G' and after[2]<config.surface_z-config.max_dive_depth:
            limit=config.surface_z-config.max_dive_depth
        ceiling=config.surface_z+config.flight_height
        if state.species=='G' and state.mode=='ascent' and after[2]>ceiling:
            # Above-cruise initial states descend normally; do not snap to altitude.
            if start[2]<=ceiling: limit=ceiling
            elif after[2]>start[2]: limit=start[2]
        boundary=crossing if crossing is not None else limit
        if boundary is not None:
            if start[2]!=boundary:
                # Solve the endpoint-heading Euler map, not the old endpoint chord.
                lower,upper=0.,h; initial_sign=start[2]-boundary
                for _ in range(60):
                    middle=(lower+upper)/2
                    _,point=candidate(middle)
                    if (point[2]-boundary)*initial_sign>0: lower=middle
                    else: upper=middle
                h=upper;heading,after=candidate(h);after[2]=boundary  # root-roundoff only
            elif limit is not None:
                after=start.copy();boundary_hold=True
                events.append(Transition(state.time,state.mode,state.mode,'habitat_boundary_hold',state.bout_id,state.target_id))
        stop=min(end,state.time+h)
        pieces.append(_piece(state,stop,tuple(after),heading,config,boundary_hold=boundary_hold))
        # Resolve deadlines in the next zero-time pass; dataclass allows rounding.
        state=replace(state,position=tuple(after),heading=heading,time=stop)
    state=replace(state,time=end)
    # Persist endpoint transitions, including provisional timeout/water entry.
    for _ in range(8):
        previous=state;state=_resolve_mode(state,observation,config,events)
        if state==previous: break
    return PredatorStep(before,state,tuple(pieces),tuple(events))


def apply_contact(step, success, time, config):
    """Close the first eligible contact; replace timeout and hold step remainder.

    Caller supplies contacts' chronological, privately randomized success/miss.
    Contact time must belong to an active bite+water piece. No RNG is consumed.
    The replacement plan is marked resolved, preventing another adapter call.
    G handling/recovery time runs concurrently with ascent: readiness requires
    both reaching flight height and reaching ready_at. Ascent never bites.
    """
    if step.contact_resolved: raise ValueError('contact already resolved for this step')
    if step.before.species!=config.species: raise ValueError('state/config species mismatch')
    if not isinstance(success,(bool,np.bool_)): raise ValueError('success must be boolean')
    _number(time,'contact time',nonnegative=True)
    eligible=[p for p in step.pieces if p.bite_window is not None and p.water_window is not None
              and p.body.start<=time<=p.body.end and p.bite_window.open<=time<=p.bite_window.close
              and p.water_window.open<=time<=p.water_window.close]
    if not eligible: raise ValueError('contact time is outside an active underwater bout')
    selected=eligible[0];u=(time-selected.body.start)/(selected.body.end-selected.body.start)
    position=tuple(np.asarray(selected.body.before)+u*(np.asarray(selected.body.after)-selected.body.before))
    heading=tuple(_unit(np.asarray(selected.heading_before)+u*(np.asarray(selected.heading_after)-selected.heading_before)))
    mode='recovery' if step.before.species in ('D','S') else 'ascent'
    duration=config.handling_duration if success else config.miss_recovery_duration
    final=replace(step.state,position=position,heading=heading,mode=mode,mode_since=time,
                  bout_id=selected.bout_id,target_id=None,bout_start=None,bout_deadline=None,
                  ready_at=time+duration,last_outcome='capture' if success else 'contact_miss')
    pieces=[]
    for p in step.pieces:
        if p.body.end<=time: pieces.append(p)
        elif p.body.start<time:
            water=(TimeWindow(max(p.water_window.open,p.body.start),time)
                   if p.water_window is not None and p.water_window.open<=time else None)
            pieces.append(replace(p,body=LinearSegment(p.body.start,time,p.body.before,position),
                                  heading_after=heading,water_window=water))
            break
        else: break
    if time<step.state.time:
        held=replace(final,time=time)
        pieces.append(_piece(held,step.state.time,position,heading,config))
    events=[e for e in step.transitions if e.time<time or (e.time==time and e.reason=='launch')]
    events.append(Transition(time,selected.mode,mode,final.last_outcome,selected.bout_id,selected.target_id))
    return PredatorStep(step.before,final,tuple(pieces),tuple(events),True)
