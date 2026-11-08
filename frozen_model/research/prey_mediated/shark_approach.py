"""Independent below-patch approach and upward-launched shark interception.

All defaults are engineering settings in model units, not shark calibration.
Use with the reviewed S-support patch and the existing Encounter planner seam.
One shark initially: this version applies no peer spacing and rejects attack
spacing. It never supplies a fish floor, global school centre or team gate.
"""
from dataclasses import dataclass, replace
import math

import numpy as np

from .contacts import LinearSegment, TimeWindow
from .predators import (MotionPiece, PredatorStep, Transition, advance,
                        intercept_point, observe, turn_toward)


POLICY_VERSION = 'local_shark_below_patch_v1'


@dataclass(frozen=True)
class SharkApproachConfig:
    patch_radius: float = 6.
    below_clearance: float = 2.5
    waypoint_tolerance: float = 1.
    tracking_gain: float = 1.
    tracking_speed: float = 3.
    orient_speed: float = 3.
    search_speed: float = 3.
    minimum_below: float = .5
    launch_radius: float = 6.
    launch_alignment_cos: float = .8
    surface_layer: float = 1.

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            value = getattr(self, name)
            if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
                raise ValueError(name+' must be finite and positive')
        if self.launch_alignment_cos > 1:
            raise ValueError('launch_alignment_cos must be <= 1')


def _cap(vector, maximum):
    return vector*min(1., maximum/max(float(np.linalg.norm(vector)), 1e-30))


def _nonbiting_motion(before, working, desired, dt, config, events):
    """Bounded endpoint-heading path; a surface crossing is root-split, then held.

    Every segment uses the ordinary nlerp-safe heading-angle bound. The held
    remainder can still turn; only root-roundoff is snapped to the surface.
    """
    velocity = _cap(np.asarray(desired, float), config.speed)
    speed = float(np.linalg.norm(velocity))
    start = np.asarray(before.position)
    finish = before.time+dt

    def candidate(duration):
        heading = (turn_toward(before.heading, velocity, 2*math.atan(config.turn_rate*duration/2))
                   if speed > 1e-12 else before.heading)
        return tuple(heading), start+speed*duration*np.asarray(heading)

    heading, endpoint = candidate(dt)
    pieces, held_time = [], 0.

    def piece(t0, t1, x0, x1, h0, h1, hold=False):
        return MotionPiece(LinearSegment(t0, t1, tuple(x0), tuple(x1)), tuple(h0), tuple(h1),
            working.mode, working.bout_id, working.target_id, None, TimeWindow(t0, t1), hold)

    if endpoint[2] > config.surface_z:
        duration = 0.
        if start[2] < config.surface_z:
            low, high = 0., dt
            for _ in range(60):
                middle = (low+high)/2
                if candidate(middle)[1][2] < config.surface_z:
                    low = middle
                else:
                    high = middle
            duration = high
            at_surface_heading, endpoint = candidate(duration)
            endpoint[2] = config.surface_z
            pieces.append(piece(before.time, before.time+duration, start, endpoint,
                                before.heading, at_surface_heading))
        else:
            endpoint = start.copy()
            at_surface_heading = before.heading
        held_time = dt-duration
        heading = (turn_toward(at_surface_heading, velocity, 2*math.atan(config.turn_rate*held_time/2))
                   if speed > 1e-12 else at_surface_heading)
        if held_time > 0.:
            pieces.append(piece(before.time+duration, finish, endpoint, endpoint,
                                at_surface_heading, heading, True))
        events.append(Transition(before.time+duration, working.mode, working.mode,
                                 'shark_surface_hold', working.bout_id, working.target_id))
    else:
        pieces.append(piece(before.time, finish, start, endpoint, before.heading, heading))
    final = replace(working, time=finish, position=tuple(endpoint), heading=tuple(heading))
    return PredatorStep(before, final, tuple(pieces), tuple(events)), speed, held_time


class SharkApproachPlanner:
    """Per-shark callable; mutable diagnostics never enter subsequent decisions."""
    def __init__(self, approach_config=SharkApproachConfig()):
        if not isinstance(approach_config, SharkApproachConfig):
            raise TypeError('approach_config must be SharkApproachConfig')
        self.approach_config = approach_config
        self.last_diagnostics = None

    def __call__(self, state, observation, dt, config, *, local_peer_positions=()):
        ac = self.approach_config
        if state.species != 'S' or config.species != 'S':
            raise ValueError('SharkApproachPlanner requires species S')
        if config.spacing_enabled:
            raise ValueError('shark v1 requires spacing_enabled=False; peer spacing is not implemented')
        if observation.actor_id != state.actor_id or observation.time != state.time:
            raise ValueError('observation must match the actor and exact clock')
        if not math.isfinite(dt) or not 0 < dt <= config.max_motion_interval:
            raise ValueError('dt must be positive and no larger than max_motion_interval')
        if dt >= min(config.handling_duration, config.miss_recovery_duration):
            raise ValueError('dt must be shorter than personal recovery')
        if state.position[2] > config.surface_z:
            raise ValueError('shark must be underwater')
        if state.mode == 'attack' and (state.target_id is None or state.bout_start is None):
            raise ValueError('active attack requires personal target and bout clocks')
        if state.mode != 'attack' and state.bout_start is not None:
            raise ValueError('non-attack state cannot carry live bout clocks')
        peers = np.asarray(local_peer_positions, float)
        if peers.size == 0:
            peers = np.empty((0, 3))
        if peers.ndim != 2 or peers.shape[1:] != (3,) or not np.isfinite(peers).all():
            raise ValueError('peer positions must be finite shape (N,3)')
        local_peer_count = int(np.sum(np.linalg.norm(peers-state.position, axis=1) <= config.spacing_radius))
        local = observe(state, observation.positions, observation.velocities, observation.prey_ids, config)
        diag = dict(policy=POLICY_VERSION, actor_id=state.actor_id, time=state.time,
            input_mode=state.mode, observed_count=len(local.prey_ids), local_peer_count=local_peer_count,
            peer_spacing_applied=False, ready_at=state.ready_at, launch_allowed=False,
            launch_reason='active_bout', patch_ids=[], waypoint=None, target_id=state.target_id)
        if state.mode == 'attack':
            plan = advance(state, local, dt, config)
            diag.update(output_mode=plan.state.mode, bout_id=plan.state.bout_id)
            self.last_diagnostics = diag
            return plan

        p, heading = np.asarray(state.position), np.asarray(state.heading)
        x = np.asarray(local.positions, float).reshape(-1, 3)
        v = np.asarray(local.velocities, float).reshape(-1, 3)
        ids = np.asarray(local.prey_ids, dtype=np.int64)
        target = state.target_id if state.target_id in local.prey_ids else None
        if target is None and len(ids):
            target = int(ids[np.lexsort((ids, np.linalg.norm(x-p, axis=1)))[0]])
        ready = state.time >= state.ready_at
        working, events = state, []

        def transition(mode, reason):
            nonlocal working
            if working.mode != mode:
                events.append(Transition(state.time, working.mode, mode, reason,
                                         working.bout_id, target))
                working = replace(working, mode=mode, mode_since=state.time)

        if working.mode == 'recovery' and ready:
            transition('position' if target is not None else 'search', 'recovery_complete')
        if target is None:
            if working.mode != 'recovery':
                transition('search', 'no_local_target')
            working = replace(working, target_id=None)
            desired = ac.search_speed*heading
            diag.update(target_id=None, launch_reason='no_local_target', personally_ready=ready)
        else:
            row = local.prey_ids.index(target)
            patch = np.linalg.norm(x-x[row], axis=1) <= ac.patch_radius
            centre, flow = x[patch].mean(axis=0), v[patch].mean(axis=0)
            waypoint = np.array([centre[0], centre[1], x[patch, 2].min()-ac.below_clearance])
            goal, lead = intercept_point(p, x[row], v[row], config.speed, config.intercept_horizon)
            delta = np.asarray(goal)-p
            goal_distance = float(np.linalg.norm(delta))
            direction = delta/goal_distance if goal_distance > 1e-12 else heading
            alignment = float(np.clip(heading@direction, -1., 1.))
            turn_time = math.acos(alignment)/config.turn_rate
            distance = float(np.linalg.norm(x[row]-p))
            below = float(x[row, 2]-p[2])
            waypoint_distance = float(np.linalg.norm(waypoint-p))
            residual = goal_distance-config.speed*lead
            if working.mode == 'search':
                transition('position', 'local_patch_selected')
            replaced_orient_target = (working.mode == 'orient' and state.target_id is not None
                                      and target != state.target_id)
            if replaced_orient_target:
                # Orientation belongs to the retained target. A replacement
                # requires an ordinary non-biting positioning step, including
                # when its waypoint already happens to be within tolerance.
                transition('position', 'retained_target_lost')
            if working.mode == 'orient' and (below < ac.minimum_below or distance > ac.launch_radius):
                transition('position', 'upward_approach_lost')
            if (working.mode == 'position' and not replaced_orient_target and ready
                    and waypoint_distance <= ac.waypoint_tolerance
                    and below >= ac.minimum_below):
                transition('orient', 'below_patch_reached')
            checks = ((ready, 'personal_recovery'), (working.mode == 'orient', 'positioning'),
                (below >= ac.minimum_below, 'insufficient_below_clearance'),
                (delta[2] > 0. and heading[2] > 0., 'not_upward'),
                (distance <= ac.launch_radius, 'outside_launch_radius'),
                (alignment >= ac.launch_alignment_cos, 'orienting'),
                (abs(residual) <= 1e-8, 'intercept_outside_horizon'),
                (lead+turn_time <= config.bout_duration, 'insufficient_bout_budget'))
            reason = next((why for passed, why in checks if not passed), 'local_launch')
            working = replace(working, target_id=target)
            diag.update(target_id=target, target_changed=target != state.target_id,
                patch_ids=ids[patch].tolist(), waypoint=waypoint.tolist(),
                local_patch_velocity=flow.tolist(), waypoint_distance=waypoint_distance,
                target_range=distance, below_target=below, intercept=tuple(goal),
                predicted_lead=lead, predicted_turn_time=turn_time, intercept_residual=residual,
                launch_alignment=alignment, personally_ready=ready,
                launch_allowed=reason == 'local_launch', launch_reason=reason)
            if reason == 'local_launch':
                launched = replace(working, mode='attack', mode_since=state.time,
                    bout_id=state.bout_id+1, bout_start=state.time,
                    bout_deadline=state.time+config.bout_duration, last_outcome=None)
                events.append(Transition(state.time, working.mode, 'attack', 'launch', launched.bout_id, target))
                proposed = advance(launched, local, dt, config)
                plan = replace(proposed, before=state, transitions=tuple(events)+proposed.transitions)
                diag.update(output_mode=plan.state.mode, bout_id=plan.state.bout_id)
                self.last_diagnostics = diag
                return plan
            desired = (flow+ac.orient_speed*direction if working.mode == 'orient' else
                       flow+_cap(ac.tracking_gain*(waypoint-p), ac.tracking_speed))
        surface_weight = float(np.clip(1.-(config.surface_z-p[2])/ac.surface_layer, 0., 1.))
        desired = np.asarray(desired).copy()
        desired[2] -= config.speed*surface_weight
        plan, speed, held = _nonbiting_motion(state, working, desired, dt, config, events)
        diag.update(output_mode=plan.state.mode, bout_id=plan.state.bout_id,
            desired_velocity=_cap(desired, config.speed).tolist(), commanded_speed=speed,
            surface_hold_duration=held, actual_upward_heading=float(plan.state.heading[2]))
        self.last_diagnostics = diag
        return plan
