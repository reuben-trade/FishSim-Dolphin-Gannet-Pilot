"""Pure geometric existence and bounded-motion fixtures for the proposed rule.

Prey move on prescribed rigid trajectories. This module never constructs a
native school and supplies no evidence about prey response or feeding benefit.
"""
from dataclasses import dataclass, asdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT))


@dataclass(frozen=True)
class GeometryParameters:
    link_radius: float=2.
    minimum_patch_size: int=4
    core_quantile: float=.9
    stand_off: float=2.5
    below_offset: float=2.5
    lateral_scale: float=3.
    tracking_gain: float=1.
    surface_margin: float=.3
    entry_tolerance: float=1.
    threat_radius: float=4.5
    sensing_radius: float=25.


def largest_local_patch(position,positions,ids,parameters=GeometryParameters()):
    x=np.asarray(positions,float);ids=np.asarray(ids,dtype=np.int64)
    visible=(np.linalg.norm(x-np.asarray(position),axis=1)<=parameters.sensing_radius)&(x[:,2]<=0.)
    rows=np.flatnonzero(visible);rows=rows[np.argsort(ids[rows])]
    local=x[rows]
    if len(local)<parameters.minimum_patch_size:return np.array([],dtype=np.int64)
    pairs=cKDTree(local).query_pairs(parameters.link_radius,output_type='ndarray')
    if len(pairs):
        a=np.r_[pairs[:,0],pairs[:,1]];b=np.r_[pairs[:,1],pairs[:,0]]
        graph=coo_matrix((np.ones(len(a)),(a,b)),shape=(len(local),len(local))).tocsr()
        _,labels=connected_components(graph,directed=False)
    else:labels=np.arange(len(local))
    candidates=[np.flatnonzero(labels==label) for label in np.unique(labels)]
    candidates=[c for c in candidates if len(c)>=parameters.minimum_patch_size]
    if not candidates:return np.array([],dtype=np.int64)
    chosen=min(candidates,key=lambda c:(-len(c),np.linalg.norm(local[c].mean(axis=0)-position),int(ids[rows[c]].min())))
    return rows[chosen]


def proposal(position,heading,positions,velocity,*,side_coefficient=None,parameters=GeometryParameters()):
    """Initial-selection geometry only; persistent patch tracking is separate."""
    p=np.asarray(position,float);x=np.asarray(positions,float)
    rows=largest_local_patch(p,x,np.arange(len(x)),parameters)
    if not len(rows):return None
    patch=x[rows];centre=patch.mean(axis=0)
    flow=np.asarray(velocity,float)
    if flow.shape==(3,):flow=np.broadcast_to(flow,x.shape)
    flow=flow[rows].mean(axis=0)
    forward=flow.copy();forward[2]=0.
    if np.linalg.norm(forward)<=1e-12:
        forward=np.asarray(heading,float).copy();forward[2]=0.
    if np.linalg.norm(forward)<=1e-12:forward=np.array([1.,0.,0.])
    forward/=np.linalg.norm(forward);lateral=np.array([-forward[1],forward[0],0.])
    extent=float(np.quantile((patch-centre)@forward,parameters.core_quantile))
    width=float(np.quantile(abs((patch-centre)@lateral),parameters.core_quantile))
    side=float(np.tanh((p-centre)@lateral/parameters.lateral_scale)) if side_coefficient is None else float(side_coefficient)
    goal=centre+forward*(extent+parameters.stand_off)+lateral*(side*(width+parameters.stand_off))
    goal[2]=min(centre[2]-parameters.below_offset,-parameters.surface_margin)
    return dict(goal=goal,centre=centre,forward=forward,lateral=lateral,front_core=extent,
                flow=flow,patch=patch,patch_rows=rows,side_coefficient=side)


def entry_witness(geometry,parameters=GeometryParameters()):
    """Independent ball-intersection witness, including the forward halfspace.

    The forward stand-off exceeds tolerance, so the complete goal ball lies in
    front of the core. Intersection with an open threat ball exists iff the
    nearest patch fish is less than tolerance+threat-radius from the goal.
    """
    goal,patch=geometry['goal'],geometry['patch']
    distance=np.linalg.norm(patch-goal,axis=1);row=int(np.argmin(distance));nearest=float(distance[row])
    threshold=parameters.entry_tolerance+parameters.threat_radius
    if not parameters.stand_off>parameters.entry_tolerance:
        raise ValueError('This analytic witness requires forward margin above tolerance')
    feasible=nearest<threshold
    point=None
    if feasible:
        move=min(parameters.entry_tolerance,nearest)
        point=goal+(patch[row]-goal)*(move/nearest) if nearest>0 else goal.copy()
        assert np.linalg.norm(point-goal)<=parameters.entry_tolerance+1e-10
        assert np.linalg.norm(point-patch[row])<parameters.threat_radius
        assert (point-geometry['centre'])@geometry['forward']>=geometry['front_core']-1e-10
        assert point[2]<=0.
    return dict(feasible=feasible,waypoint_nearest_patch_distance=nearest,
                maximum_allowed_distance=threshold,witness=None if point is None else point.tolist())


def analytic_ellipsoid(a=12.,b=4.,c=3.,spacing=1.5):
    axes=[np.arange(-math.floor(radius/spacing),math.floor(radius/spacing)+1)*spacing for radius in (a,b,c)]
    x=np.array([(u,v,w) for u in axes[0] for v in axes[1] for w in axes[2]
                if (u/a)**2+(v/b)**2+(w/c)**2<=1.+1e-12],float)
    x[:,2]-=6.
    return x


def frozen_motion():
    name='_nov6_motion_for_v2_feasibility'
    if name not in sys.modules:
        path=ROOT/'research/herding_study_2026-11-06/policy.py'
        spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module;spec.loader.exec_module(module)
    return sys.modules[name].DolphinPlanner._move


def prescribed_moving_fixture(positions,start,*,duration=20.,dt=.02,velocity=(3.,0.,0.),parameters=GeometryParameters()):
    """A prescribed moving extended patch, not a reactive fish simulation."""
    from research.prey_mediated.predators import PredatorConfig,initial_predator
    config=PredatorConfig();move=frozen_motion()
    state=initial_predator('D_fixture',start,(1.,0.,0.),config)
    origin=np.asarray(positions,float);flow=np.asarray(velocity,float)
    side=None;first_entry=None;consecutive=0.;maximum=0.;sustained_at=None;physical_checks=0
    for _ in range(round(duration/dt)):
        x=origin+state.time*flow
        geometry=proposal(state.position,state.heading,x,flow,side_coefficient=side,parameters=parameters)
        if geometry is None:
            desired=config.speed*np.asarray(state.heading);consecutive=0.
        else:
            if side is None:side=geometry['side_coefficient']
            nearest=float(np.linalg.norm(geometry['patch']-state.position,axis=1).min())
            enters=(np.linalg.norm(geometry['goal']-state.position)<=parameters.entry_tolerance and
                    (np.asarray(state.position)-geometry['centre'])@geometry['forward']>=geometry['front_core'] and
                    nearest<parameters.threat_radius)
            if enters:
                first_entry=state.time if first_entry is None else first_entry
                consecutive+=dt;maximum=max(maximum,consecutive)
                if consecutive>=2.-1e-10:sustained_at=state.time+dt;break
            else:consecutive=0.
            desired=geometry['flow']+parameters.tracking_gain*(geometry['goal']-state.position)
            desired*=min(1.,config.speed/max(float(np.linalg.norm(desired)),1e-12))
        before=state;state,piece=move(state,desired,dt,config)
        elapsed=piece.body.end-piece.body.start
        distance=float(np.linalg.norm(np.asarray(piece.body.after)-piece.body.before))
        angle=math.acos(float(np.clip(np.asarray(piece.heading_before)@piece.heading_after,-1.,1.)))
        assert distance<=config.speed*elapsed+1e-9
        assert angle<=config.turn_rate*elapsed+1e-9
        assert state.position[2]<=0. and piece.bite_window is None
        physical_checks+=3
    return dict(initial_fish=len(origin),extents=np.ptp(origin,axis=0).tolist(),start=list(start),
        prescribed_velocity=flow.tolist(),dt=dt,first_entry=first_entry,
        maximum_consecutive_pressure=maximum,sustained_two_units_at=sustained_at,
        physical_checks=physical_checks,native_steps=0,
        interpretation='Rigid prescribed moving-patch execution only; no prey response, food or containment validation.')


def generate_receipt():
    parameters=GeometryParameters();saved=[];inputs={}
    base=ROOT/'research/herding_study_2026-11-06/results/development_coarse_v1/cases'
    for seed in (39061001,39061002,39061003,39061004):
        directory=base/f's{seed}_c61001_d0.005_herding_DG'
        config=json.loads((directory/'config.json').read_text())
        with np.load(directory/'initial_school.npz',allow_pickle=False) as data:
            x=data['positions'];velocities=3.*data['directions']
        for path in (directory/'config.json',directory/'initial_school.npz'):
            inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        for actor in config['actors']:
            if actor['state']['species']!='D':continue
            assert actor['mouth']['radius']==.4 and actor['mouth']['forward_offset']==.3
            geometry=proposal(actor['state']['position'],actor['state']['heading'],x,velocities,parameters=parameters)
            saved.append(dict(school_seed=seed,actor_id=actor['state']['actor_id'],**entry_witness(geometry,parameters)))
    moving=[]
    for name,shape in [('elongated_ellipsoid',(12.,4.,3.)),('slender_ellipsoid',(18.,3.,1.5))]:
        x=analytic_ellipsoid(*shape)
        for y in (-7.,-3.,0.,3.,7.):
            moving.append(dict(fixture=name,**prescribed_moving_fixture(x,(-18.,y,-5.),parameters=parameters)))
    return dict(status='passed' if all(r['feasible'] for r in saved) and all(r['sustained_two_units_at'] is not None and r['first_entry']<16. for r in moving) else 'geometry_not_established',
        native_steps=0,parameters=asdict(parameters),input_sha256=inputs,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        saved_static_geometries=saved,saved_velocity_rule='Exact retained float64 headings times baseline speed3',prescribed_moving_fixtures=moving,
        scope='Initial saved geometry is evaluated before staggered readiness expires. Prescribed moving fixtures use immediate readiness and rigid prey; they do not establish reactive retention or feeding performance. Full controller handoff/time-budget and state-replay tests remain separate.')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    receipt=generate_receipt()
    with args.output.open('x') as stream:json.dump(receipt,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=receipt['status'],saved_geometries=len(receipt['saved_static_geometries']),moving_fixtures=len(receipt['prescribed_moving_fixtures']),native_steps=0)))
