"""Optional local angular crowd avoidance around each sensed prey patch.

Ordinary radial tracking, fixed-axis circulation and short-range body spacing
remain. An additional drift uses only sensed peer bearings about this actor's
own patch centre; it does not read a shared centre, assigned sector or metric.
This is an engineering proposal, not a biologically calibrated dolphin rule.
"""
from dataclasses import dataclass
import math
import numpy as np

from .local_axis_pressure import axis_pressure_step
from .local_pressure import PressureConfig,PressureStep,_cap,_points
from .predators import turn_toward

POLICY_VERSION='local_patch_angular_crowd_draft_v1'
GEOMETRY_EPSILON=1e-12


@dataclass(frozen=True)
class AngularCrowdConfig:
    enabled: bool=False
    observation_radius: float=25.

    def __post_init__(self):
        if not isinstance(self.enabled,bool):raise ValueError('enabled must be boolean')
        if isinstance(self.observation_radius,(bool,np.bool_)) or not math.isfinite(self.observation_radius) or self.observation_radius<=0:
            raise ValueError('observation_radius must be finite and positive')


def angular_crowd_velocity(position,centre,peer_positions,*,observation_radius=25.,spacing_speed=2.):
    """Pure bearing cue; weights are averaged over all eligible sensed peers.

    For unit radial u and peer bearing b, each contribution is
    -max(0,u.b)*(b-(u.b)*u). Its norm is at most1/2, so the mean times
    spacing_speed has norm at most spacing_speed/2. Opposite-hemisphere peers
    remain in the mean denominator with zero contribution. Peers at the patch
    centre have undefined bearing and are excluded explicitly.
    """
    p,c=np.asarray(position,float),np.asarray(centre,float)
    if p.shape!=(3,) or c.shape!=(3,) or not np.isfinite([p,c]).all():raise ValueError('finite position and centre required')
    if isinstance(observation_radius,(bool,np.bool_)) or not math.isfinite(observation_radius) or observation_radius<=0:raise ValueError('positive finite observation radius required')
    if isinstance(spacing_speed,(bool,np.bool_)) or not math.isfinite(spacing_speed) or spacing_speed<0:raise ValueError('nonnegative finite spacing speed required')
    peers=_points(peer_positions,'peer_positions')
    distance=np.linalg.norm(peers-p,axis=1);sensed=distance<=observation_radius
    offset=peers-c;length=np.linalg.norm(offset,axis=1)
    degenerate=sensed&(length<=GEOMETRY_EPSILON)
    eligible=sensed&~degenerate
    radial=p-c;radius=float(np.linalg.norm(radial))
    if not np.isfinite(distance).all() or not np.isfinite(length).all() or not math.isfinite(radius):
        raise ValueError('finite derived peer and radial distances required')
    diagnostic=dict(angular_input_peer_count=len(peers),angular_sensed_peer_count=int(sensed.sum()),
        angular_eligible_peer_count=int(eligible.sum()),angular_degenerate_peer_count=int(degenerate.sum()),
        angular_coincident_actor_peer_count=int(np.sum(sensed&(distance<=GEOMETRY_EPSILON))),
        angular_observation_radius=float(observation_radius),angular_speed_bound=float(spacing_speed/2.),
        angular_patch_centre=c.tolist(),angular_decline_reason=None)
    if radius<=GEOMETRY_EPSILON:
        diagnostic.update(angular_decline_reason='actor_at_patch_centre',angular_same_hemisphere_peer_count=0,
                          angular_radial_dot=0.,angular_proposed_velocity=[0.,0.,0.])
        return np.zeros(3),diagnostic
    u=radial/radius
    if not np.any(eligible):
        diagnostic.update(angular_decline_reason='no_eligible_peers',angular_same_hemisphere_peer_count=0,
                          angular_radial_dot=0.,angular_proposed_velocity=[0.,0.,0.])
        return np.zeros(3),diagnostic
    bearings=offset[eligible]/length[eligible,None]
    dot=bearings@u;weight=np.maximum(0.,dot)
    projected=bearings-dot[:,None]*u
    projected[distance[eligible]<=GEOMETRY_EPSILON]=0.
    drift=-spacing_speed*np.mean(weight[:,None]*projected,axis=0)
    # Numerical roundoff only; no renormalization or chosen symmetry breaker.
    drift=_cap(drift,spacing_speed/2.)
    diagnostic.update(angular_same_hemisphere_peer_count=int((weight>0.).sum()),
        angular_radial_dot=float(u@drift),angular_proposed_velocity=drift.tolist())
    if spacing_speed==0.:diagnostic['angular_decline_reason']='zero_gain'
    return drift,diagnostic


def angular_pressure_step(position,heading,fish_positions,fish_velocities,prey_ids,
                          peer_positions,dt,config=PressureConfig(),*,orbit_axis=(0.,0.,1.),
                          angular_config=AngularCrowdConfig()):
    """Axis-pressure proposal plus an optional bounded tangent-plane drift.

    Disabled returns the exact existing object/diagnostics. Enabled zero drift
    preserves its position/heading arrays exactly while adding observer fields.
    All motion fields here describe proposals; a feeding launch may discard
    them. The future runner must observe Encounter's committed paths separately.
    """
    if not isinstance(angular_config,AngularCrowdConfig):raise TypeError('explicit AngularCrowdConfig required')
    base=axis_pressure_step(position,heading,fish_positions,fish_velocities,prey_ids,
                            peer_positions,dt,config,orbit_axis=orbit_axis)
    if not angular_config.enabled:return base
    diagnostic=dict(base.diagnostics)
    diagnostic.update(policy=POLICY_VERSION,angular_base_policy=base.diagnostics['policy'],
        angular_enabled=True,angular_base_desired_velocity=base.diagnostics['desired_velocity'],
        angular_base_movement_velocity=((base.position-np.asarray(position))/dt).tolist())
    if diagnostic['target_id'] is None:
        peers=_points(peer_positions,'peer_positions')
        peer_distance=np.linalg.norm(peers-np.asarray(position),axis=1)
        sensed=peer_distance<=angular_config.observation_radius
        diagnostic.update(angular_decline_reason='no_visible_patch',angular_proposed_velocity=[0.,0.,0.],
            angular_input_peer_count=len(peers),angular_sensed_peer_count=int(sensed.sum()),
            angular_eligible_peer_count=0,angular_degenerate_peer_count=0,angular_same_hemisphere_peer_count=0,
            angular_coincident_actor_peer_count=int(np.sum(sensed&(peer_distance<=GEOMETRY_EPSILON))),angular_patch_centre=None,
            angular_observation_radius=angular_config.observation_radius,angular_speed_bound=config.spacing_speed/2.,angular_radial_dot=0.)
        drift=np.zeros(3)
    else:
        x=np.asarray(fish_positions,float);ids=np.asarray(prey_ids)
        centre=x[np.isin(ids,diagnostic['patch_ids'])].mean(axis=0)
        drift,extra=angular_crowd_velocity(position,centre,peer_positions,
            observation_radius=angular_config.observation_radius,spacing_speed=config.spacing_speed)
        diagnostic.update(extra)
    if not np.any(drift):
        diagnostic.update(angular_postcap_desired_velocity_delta=[0.,0.,0.],
            angular_proposed_movement_velocity=diagnostic['angular_base_movement_velocity'],
            angular_proposed_movement_velocity_delta=[0.,0.,0.])
        return PressureStep(base.position,base.heading,diagnostic)

    p,h=np.asarray(position,float),np.asarray(heading,float)
    desired=(np.asarray(diagnostic['observed_patch_velocity'])+
        np.asarray(diagnostic['tracking_velocity'])+np.asarray(diagnostic['tangent_velocity']))
    desired=desired+np.asarray(diagnostic['spacing_velocity'])
    desired=desired+drift
    surface_weight=float(np.clip(1.-(config.surface_z-p[2])/config.surface_layer,0.,1.))
    desired[2]-=config.max_speed*surface_weight
    desired=_cap(desired,config.max_speed)
    speed=float(np.linalg.norm(desired))
    new_heading=np.asarray(turn_toward(h,desired,config.turn_rate*dt)) if speed>GEOMETRY_EPSILON else h.copy()
    duration=float(dt)
    surface_hold=bool(speed*new_heading[2]>0. and p[2]+speed*new_heading[2]*dt>config.surface_z)
    if surface_hold:duration=max(0.,(config.surface_z-p[2])/(speed*new_heading[2]))
    new_position=p+speed*new_heading*duration
    if surface_hold:new_position[2]=config.surface_z
    movement=(new_position-p)/dt
    diagnostic.update(desired_velocity=desired.tolist(),commanded_speed=speed,
        actual_speed=float(np.linalg.norm(new_position-p)/dt),surface_hold=surface_hold,boundary_hold=surface_hold,
        surface_hold_duration=float(dt-duration),
        angular_postcap_desired_velocity_delta=(desired-np.asarray(base.diagnostics['desired_velocity'])).tolist(),
        angular_proposed_movement_velocity=movement.tolist(),
        angular_proposed_movement_velocity_delta=(movement-np.asarray(diagnostic['angular_base_movement_velocity'])).tolist())
    return PressureStep(new_position,new_heading,diagnostic)
