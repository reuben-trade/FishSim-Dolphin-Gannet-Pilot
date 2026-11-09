"""Optional exact helper acceleration, separately validated before native use.

Array conversion follows the previously verified arithmetic. Component labels
are memoized by the exact ordered float64 coordinates; sensing, component means,
membership selection and controller memory still execute on every observation.
The cache has at most32 entries, is process-private, and is cleared on exit.
"""
from collections import OrderedDict
from contextlib import contextmanager
import hashlib
import importlib.util
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(HERE),str(ROOT)]
import controller_v2 as C
import patch_tracking_v2 as T
from research.prey_mediated import encounter, predators

PINS={
    'research/herding_study_2026-11-06/acceleration.py':'bd54f20e75fb785bf542042b1efb79e5e2960ee6c843abb60ffc4120c83b2a36',
    'research/herding_study_2026-11-07/controller_v2.py':'0d820fedf70845fce1470fb5334e68c5186e8d1f44bb781748dac8dee9988a6b',
    'research/herding_study_2026-11-07/patch_tracking_v2.py':'4379646a6fd37272c0db800c760b53034fe5865e2d7f506851069a2a0069b668',
}
ORIGINAL_COMPONENTS=T.visible_components
ORIGINAL_OBSERVE=predators.observe
ORIGINAL_TARGETS=predators._targets


def verify_sources():
    for name,digest in PINS.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError('Unreviewed acceleration dependency: '+name)


def helper_module():
    verify_sources()
    name='_nov6_array_helpers_for_v2_acceleration'
    if name not in sys.modules:
        path=ROOT/'research/herding_study_2026-11-06/acceleration.py'
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);sys.modules[name]=module
        spec.loader.exec_module(module)
    module=sys.modules[name];module.verify_sources()
    return module


class ComponentCache:
    """Only geometry-dependent graph labels are shared between observations."""
    def __init__(self):
        self.cache=OrderedDict();self.hits=0;self.misses=0

    def labels(self,x,radius):
        # Shape and dtype are fixed by visible_components below, nevertheless
        # include shape in the key so the dependency is explicit.
        key=(x.shape,float(radius),x.tobytes())
        if key in self.cache:
            self.hits+=1;self.cache.move_to_end(key);return self.cache[key]
        self.misses+=1
        pairs=T.cKDTree(x).query_pairs(radius,output_type='ndarray')
        if len(pairs):
            a=np.r_[pairs[:,0],pairs[:,1]];b=np.r_[pairs[:,1],pairs[:,0]]
            graph=T.coo_matrix((np.ones(len(a)),(a,b)),shape=(len(x),len(x))).tocsr()
            _,labels=T.connected_components(graph,directed=False)
        else:labels=np.arange(len(x))
        labels.setflags(write=False)
        self.cache[key]=labels
        if len(self.cache)>32:self.cache.popitem(last=False)
        return labels

    def visible_components(self,state,observation,config,parameters):
        # Keep the reviewed validation, sensing, sorting and mean arithmetic.
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
        labels=self.labels(x,parameters.link_radius)
        result=[]
        for label in np.unique(labels):
            mask=labels==label
            if np.sum(mask)<parameters.minimum_patch_size:continue
            positions=x[mask];velocity=v[mask];identities=ids[mask]
            result.append(dict(ids=tuple(int(i) for i in identities),x=positions,v=velocity,
                centre=positions.mean(axis=0),flow=velocity.mean(axis=0)))
        return result,len(x)


@contextmanager
def accelerated():
    helpers=helper_module();legacy=C.frozen_policy();cache=ComponentCache()
    bindings=((predators,'observe',helpers.observe,ORIGINAL_OBSERVE),
              (predators,'_targets',helpers.targets,ORIGINAL_TARGETS),
              (encounter,'observe',helpers.observe,ORIGINAL_OBSERVE),
              (legacy,'observe',helpers.observe,ORIGINAL_OBSERVE),
              (C,'observe',helpers.observe,ORIGINAL_OBSERVE),
              (T,'visible_components',cache.visible_components,ORIGINAL_COMPONENTS))
    previous=[]
    for module,name,replacement,original in bindings:
        current=getattr(module,name)
        if current is not original:
            raise RuntimeError('Unexpected helper binding: '+module.__name__+'.'+name)
        previous.append((module,name,current))
    try:
        for module,name,replacement,_ in bindings:setattr(module,name,replacement)
        yield cache
    finally:
        for module,name,original in reversed(previous):setattr(module,name,original)
        cache.cache.clear()
