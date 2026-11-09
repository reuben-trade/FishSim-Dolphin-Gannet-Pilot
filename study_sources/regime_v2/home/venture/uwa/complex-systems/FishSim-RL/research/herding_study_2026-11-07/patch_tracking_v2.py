"""Deterministic tracker of connected components in one local prey observation.

No native model, global observer, targeting assignment or RNG is used. All
persistent information is explicit in TrackerState and serializable as JSON.
"""
from dataclasses import asdict, dataclass, replace
import math

import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components


@dataclass(frozen=True)
class TrackerParameters:
    link_radius: float=2.
    minimum_patch_size: int=4
    overlap_fraction: float=.5
    visibility_grace: float=.5
    lateral_scale: float=3.

    def __post_init__(self):
        if type(self.minimum_patch_size) is not int or self.minimum_patch_size<1:
            raise ValueError('minimum_patch_size must be a positive integer')
        for name in ('link_radius','visibility_grace','lateral_scale'):
            value=getattr(self,name)
            if isinstance(value,bool) or not math.isfinite(value) or value<=0:raise ValueError(name+' must be finite and positive')
        if not 0<self.overlap_fraction<=1:raise ValueError('overlap_fraction must be in(0,1]')


@dataclass(frozen=True)
class TrackerState:
    epoch: int=0
    member_ids: tuple=()
    last_seen_time: float|None=None
    last_centre: tuple|None=None
    last_velocity: tuple|None=None
    last_forward: tuple|None=None
    last_forward_time: float|None=None
    side_coefficient: float=0.

    def state_dict(self):
        return dict(schema_version=1,**asdict(self))

    @classmethod
    def from_state_dict(cls,value):
        value=dict(value)
        if value.pop('schema_version',None)!=1:raise ValueError('Unsupported tracker state version')
        if set(value)!=set(cls.__dataclass_fields__):raise ValueError('Unexpected tracker state fields')
        for key in ('member_ids','last_centre','last_velocity','last_forward'):
            if value[key] is not None:value[key]=tuple(value[key])
        state=cls(**value)
        if type(state.epoch) is not int or state.epoch<0 or tuple(sorted(set(state.member_ids)))!=state.member_ids:
            raise ValueError('Invalid tracker epoch/membership')
        for key in ('last_seen_time','last_forward_time'):
            v=getattr(state,key)
            if v is not None and (not math.isfinite(v) or v<0):raise ValueError('Invalid tracker clock')
        for key in ('last_centre','last_velocity','last_forward'):
            v=getattr(state,key)
            if v is not None and (np.asarray(v).shape!=(3,) or not np.isfinite(v).all()):raise ValueError('Invalid tracker vector')
        if not math.isfinite(state.side_coefficient) or not -1<=state.side_coefficient<=1:raise ValueError('Invalid side coefficient')
        return state


@dataclass(frozen=True)
class PatchView:
    prey_ids: tuple
    positions: tuple
    velocities: tuple
    centre: tuple
    flow: tuple
    forward: tuple
    side_coefficient: float
    epoch: int


def clear_tracker(state):
    return TrackerState(epoch=state.epoch)


def visible_components(state,observation,config,parameters):
    if observation.actor_id!=state.actor_id or observation.time!=state.time:
        raise ValueError('Observation must match actor and exact clock')
    x=np.asarray(observation.positions,float).reshape(-1,3)
    v=np.asarray(observation.velocities,float).reshape(-1,3)
    ids=np.asarray(observation.prey_ids)
    if x.shape!=v.shape or ids.shape!=(len(x),) or ids.dtype.kind not in 'iu' and len(ids):
        raise ValueError('Prey arrays/IDs differ')
    if not np.isfinite(x).all() or not np.isfinite(v).all() or len(np.unique(ids))!=len(ids) or np.any(ids<0):
        raise ValueError('Prey data must be finite with unique nonnegative IDs')
    visible=(np.linalg.norm(x-np.asarray(state.position),axis=1)<=config.sense_radius)&(x[:,2]<=config.surface_z)
    rows=np.flatnonzero(visible);rows=rows[np.argsort(ids[rows])]
    x,v,ids=x[rows],v[rows],ids[rows]
    if len(x)<parameters.minimum_patch_size:return [],len(x)
    pairs=cKDTree(x).query_pairs(parameters.link_radius,output_type='ndarray')
    if len(pairs):
        a=np.r_[pairs[:,0],pairs[:,1]];b=np.r_[pairs[:,1],pairs[:,0]]
        graph=coo_matrix((np.ones(len(a)),(a,b)),shape=(len(x),len(x))).tocsr()
        _,labels=connected_components(graph,directed=False)
    else:labels=np.arange(len(x))
    result=[]
    for label in np.unique(labels):
        mask=labels==label
        if np.sum(mask)<parameters.minimum_patch_size:continue
        positions=x[mask];velocity=v[mask];identities=ids[mask]
        result.append(dict(ids=tuple(int(i) for i in identities),x=positions,v=velocity,
            centre=positions.mean(axis=0),flow=velocity.mean(axis=0)))
    return result,len(x)


def update_tracker(memory,state,observation,config,parameters=TrackerParameters(),*,seen_at=None):
    # Constant-velocity projection within an observed step is not a fresh
    # sighting. Store the centre at the input-observation clock so later stale
    # propagation cannot extend visibility or double-count that translation.
    seen_at=state.time if seen_at is None else seen_at
    if not math.isfinite(seen_at) or not 0<=seen_at<=state.time:
        raise ValueError('Sighting clock must not exceed the decision clock')
    components,visible_count=visible_components(state,observation,config,parameters)
    diagnostic=dict(visible_count=visible_count,candidate_components=len(components),current=False,
                    handoff=False,overlap=0,overlap_fraction=0.,stale=False)
    if not components:
        age=None if memory.last_seen_time is None else state.time-memory.last_seen_time
        stale=age is not None and 0<=age<parameters.visibility_grace
        diagnostic.update(stale=stale,unavailable_age=age,epoch=memory.epoch,
            stale_search_centre=None if not stale else (np.asarray(memory.last_centre)+age*np.asarray(memory.last_velocity)).tolist())
        return memory,None,diagnostic
    old=set(memory.member_ids)
    overlaps=[len(old&set(c['ids'])) for c in components]
    if old and max(overlaps)>0:
        chosen=min(range(len(components)),key=lambda i:(-overlaps[i],-len(components[i]['ids']),
            np.linalg.norm(components[i]['centre']-state.position),min(components[i]['ids'])))
    else:
        chosen=min(range(len(components)),key=lambda i:(-len(components[i]['ids']),
            np.linalg.norm(components[i]['centre']-state.position),min(components[i]['ids'])))
    patch=components[chosen];overlap=overlaps[chosen]
    fraction=0. if not old else overlap/len(old)
    handoff=not old or fraction<parameters.overlap_fraction
    epoch=memory.epoch+int(handoff)
    horizontal=patch['flow'].copy();horizontal[2]=0.
    forward_time=memory.last_forward_time
    if np.linalg.norm(horizontal)>1e-12:
        forward=horizontal/np.linalg.norm(horizontal);forward_time=seen_at;fallback=None
    elif (not handoff and memory.last_forward is not None and forward_time is not None
          and state.time-forward_time<parameters.visibility_grace):
        forward=np.asarray(memory.last_forward);fallback='recent_observed_flow'
    else:
        forward=np.asarray(state.heading).copy();forward[2]=0.
        fallback='own_heading'
        if np.linalg.norm(forward)<=1e-12:forward=np.array([1.,0.,0.]);fallback='fixed_positive_x'
        forward/=np.linalg.norm(forward);forward_time=None
    lateral=np.array([-forward[1],forward[0],0.])
    side=float(np.tanh((np.asarray(state.position)-patch['centre'])@lateral/parameters.lateral_scale)) if handoff else memory.side_coefficient
    stored_centre=patch['centre']-(state.time-seen_at)*patch['flow']
    new=TrackerState(epoch,patch['ids'],float(seen_at),tuple(stored_centre),tuple(patch['flow']),
        tuple(forward),forward_time,side)
    view=PatchView(patch['ids'],tuple(map(tuple,patch['x'].tolist())),tuple(map(tuple,patch['v'].tolist())),
        tuple(patch['centre']),tuple(patch['flow']),tuple(forward),side,epoch)
    diagnostic.update(current=True,handoff=handoff,overlap=overlap,overlap_fraction=fraction,
                      epoch=epoch,selected_ids=list(patch['ids']),flow_fallback=fallback,unavailable_age=0.)
    return new,view,diagnostic
