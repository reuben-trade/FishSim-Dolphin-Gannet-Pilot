"""Independent local feeding planner for existing pressure dolphins.

Returns ordinary PredatorStep plans; Encounter still owns contact ordering,
private capture draws, virtual availability and real prey removal. Launch
conditions are explicit engineering assumptions, not biological calibration.
The supplied pressure stepper is unchanged. Handling permits non-biting
pressure movement from the next step after a contact's remainder-step hold.
"""
from dataclasses import dataclass, replace
import math

import numpy as np

from .contacts import LinearSegment, TimeWindow
from .local_pressure import PressureConfig, pressure_step
from .predators import (MotionPiece, PredatorStep, Transition, advance,
                        intercept_point, observe)


POLICY_VERSION = 'local_pressure_independent_feeding_v1'


@dataclass(frozen=True)
class FeedingConfig:
    enabled: bool = True
    launch_radius: float = 6.
    front_dot_min: float = 0.
    flow_epsilon: float = 1e-8

    def __post_init__(self):
        if not isinstance(self.enabled, bool):
            raise ValueError('enabled must be a boolean')
        for name in ('launch_radius', 'flow_epsilon'):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(name+' must be finite and positive')
        if not math.isfinite(self.front_dot_min) or not -1 <= self.front_dot_min <= 1:
            raise ValueError('front_dot_min must be in [-1,1]')


class PressureFeedingPlanner:
    """One callable per dolphin; only last_diagnostics is mutable logging state.

    Personal behavioural state is entirely in the supplied PredatorState.
    Inputs contain local observations and peer positions, never a full school
    or another actor's decisions. Inputs are filtered again defensively.
    ``enabled=False`` prevents new bouts; an already active bout completes
    normally. Disabled replay therefore starts with no active bout.
    """
    def __init__(self, pressure_config=PressureConfig(), feeding_config=FeedingConfig(),
                 *, pressure_stepper=pressure_step, peer_observation_radius=None):
        if not isinstance(pressure_config, PressureConfig) or not isinstance(feeding_config, FeedingConfig):
            raise TypeError('explicit pressure and feeding configurations required')
        if not callable(pressure_stepper):
            raise TypeError('pressure_stepper must be callable')
        if peer_observation_radius is not None:
            if (isinstance(peer_observation_radius,(bool,np.bool_))
                or not isinstance(peer_observation_radius,(int,float,np.integer,np.floating))
                or not math.isfinite(peer_observation_radius)
                or peer_observation_radius < pressure_config.spacing_radius):
                raise ValueError('peer observation radius must be finite and at least body spacing radius')
        self.peer_observation_radius = peer_observation_radius
        self.pressure_config = pressure_config
        self.feeding_config = feeding_config
        self.pressure_stepper = pressure_stepper
        self.last_diagnostics = None

    def __call__(self, state, observation, dt, config, *, local_peer_positions=()):
        pc, fc = self.pressure_config, self.feeding_config
        if state.species != 'D' or config.species != 'D':
            raise ValueError('this planner only supports dolphins')
        if observation.actor_id != state.actor_id or observation.time != state.time:
            raise ValueError('observation must match the actor and exact clock')
        if not math.isfinite(dt) or not 0 < dt < min(config.handling_duration, config.miss_recovery_duration):
            raise ValueError('dt must be positive and strictly shorter than personal recovery')
        for ordinary, pressure in (('speed', 'max_speed'), ('turn_rate', 'turn_rate'),
                                   ('sense_radius', 'sense_radius'), ('surface_z', 'surface_z'),
                                   ('spacing_radius', 'spacing_radius')):
            if getattr(config, ordinary) != getattr(pc, pressure):
                raise ValueError('predator and pressure '+ordinary+' must match')
        if state.mode == 'attack' and (state.target_id is None or state.bout_start is None):
            raise ValueError('an active attack requires a target and personal bout clocks')
        if state.mode != 'attack' and state.bout_start is not None:
            raise ValueError('only an attack may carry active bout clocks')
        peers = np.asarray(local_peer_positions, float)
        if peers.size == 0:
            peers = np.empty((0, 3))
        if peers.ndim != 2 or peers.shape[1:] != (3,) or not np.isfinite(peers).all():
            raise ValueError('local_peer_positions must be finite shape (N,3)')
        peer_distance = np.linalg.norm(peers-np.asarray(state.position), axis=1)
        observation_radius = pc.spacing_radius if self.peer_observation_radius is None else self.peer_observation_radius
        pressure_peers = peers[peer_distance <= observation_radius]
        peers = peers[peer_distance <= pc.spacing_radius]
        local = observe(state, observation.positions, observation.velocities,
                        observation.prey_ids, config,
                        conspecific_positions=peers if config.spacing_enabled else None)
        diagnostic = dict(policy=POLICY_VERSION, actor_id=state.actor_id, time=state.time,
            input_mode=state.mode, ready_at=state.ready_at, feeding_enabled=fc.enabled,
            observed_count=len(local.prey_ids), local_peer_count=len(peers),
            attack_spacing_enabled=config.spacing_enabled, attack_spacing_gain=config.spacing_gain,
            launch_radius=fc.launch_radius, front_dot_min=fc.front_dot_min,
            launch_allowed=False, launch_reason='active_bout', pressure=None,
            pressure_boundary_hold=False, proposed_pressure_boundary_hold=None)
        if self.peer_observation_radius is not None:
            diagnostic.update(peer_observation_radius=self.peer_observation_radius,
                pressure_peer_observed_count=len(pressure_peers),body_peer_observed_count=len(peers))
        if state.mode == 'attack':
            plan = advance(state, local, dt, config)
            diagnostic.update(target_id=state.target_id, bout_id=state.bout_id,
                              output_mode=plan.state.mode)
            self.last_diagnostics = diagnostic
            return plan

        pressure = self.pressure_stepper(state.position, state.heading,
            local.positions, local.velocities, np.asarray(local.prey_ids, dtype=np.int64),
            pressure_peers, dt, pc)
        diagnostic['pressure'] = pressure.diagnostics
        target = pressure.diagnostics['target_id']
        flow = np.asarray(pressure.diagnostics['observed_patch_velocity'], float)
        norm = float(np.linalg.norm(flow))
        front = (None if norm <= fc.flow_epsilon else
                 float(np.asarray(pressure.diagnostics['radial_direction']) @ (flow/norm)))
        distance = lead = turn_time = residual = None
        range_ok = intercept_ok = budget_ok = False
        if target is not None:
            row = local.prey_ids.index(target)
            position, velocity = local.positions[row], local.velocities[row]
            distance = float(np.linalg.norm(np.asarray(position)-state.position))
            goal, lead = intercept_point(state.position, position, velocity,
                                         config.speed, config.intercept_horizon)
            delta = np.asarray(goal)-state.position
            goal_distance = float(np.linalg.norm(delta))
            direction = delta/goal_distance if goal_distance > 1e-12 else np.asarray(state.heading)
            turn_time = math.acos(float(np.clip(np.asarray(state.heading)@direction, -1., 1.)))/config.turn_rate
            residual = goal_distance-config.speed*lead
            range_ok = distance <= fc.launch_radius
            intercept_ok = abs(residual) <= 1e-8
            budget_ok = lead+turn_time <= config.bout_duration
        ready = state.time >= state.ready_at
        front_ok = front is None or front >= fc.front_dot_min
        checks = ((fc.enabled, 'disabled'), (ready, 'personal_recovery'),
                  (target is not None, 'no_local_target'), (front_ok, 'behind_local_flow'),
                  (range_ok, 'outside_launch_radius'), (intercept_ok, 'intercept_outside_horizon'),
                  (budget_ok, 'insufficient_bout_budget'))
        reason = next((reason for passed, reason in checks if not passed), 'local_launch')
        diagnostic.update(target_id=target, range=distance, front_dot=front,
            flow_front_undefined=norm <= fc.flow_epsilon, predicted_lead=lead,
            predicted_turn_time=turn_time, intercept_residual=residual,
            range_ok=range_ok, intercept_ok=intercept_ok, budget_ok=budget_ok,
            personally_ready=ready, launch_allowed=reason == 'local_launch', launch_reason=reason)
        events = []
        working = state
        if state.mode == 'search' or (state.mode == 'recovery' and ready):
            events.append(Transition(state.time, state.mode, 'position',
                'recovery_complete' if state.mode == 'recovery' else 'local_pressure',
                state.bout_id, state.target_id))
            working = replace(state, mode='position', mode_since=state.time, target_id=None)
        if reason == 'local_launch':
            launched = replace(working, mode='attack', mode_since=state.time,
                target_id=target, bout_id=state.bout_id+1, bout_start=state.time,
                bout_deadline=state.time+config.bout_duration, last_outcome=None)
            events.append(Transition(state.time, working.mode, 'attack', 'launch',
                                     launched.bout_id, target))
            proposed = advance(launched, local, dt, config)
            plan = replace(proposed, before=state, transitions=tuple(events)+proposed.transitions)
        else:
            final = replace(working, position=tuple(pressure.position), heading=tuple(pressure.heading),
                            time=state.time+dt, target_id=None)
            piece = MotionPiece(LinearSegment(state.time, final.time, state.position, final.position),
                state.heading, final.heading, working.mode, state.bout_id, None, None,
                TimeWindow(state.time, final.time), pressure.diagnostics['boundary_hold'])
            if pressure.diagnostics['boundary_hold']:
                events.append(Transition(state.time, working.mode, working.mode,
                    'pressure_surface_hold', state.bout_id, None))
            plan = PredatorStep(state, final, (piece,), tuple(events))
        diagnostic.update(bout_id=plan.state.bout_id, output_mode=plan.state.mode,
            proposed_pressure_boundary_hold=pressure.diagnostics['boundary_hold'],
            pressure_boundary_hold=bool(reason != 'local_launch'
                                       and pressure.diagnostics['boundary_hold']))
        if self.peer_observation_radius is not None:
            diagnostic.update(pressure_proposal_selected=reason != 'local_launch',
                pressure_proposed_path_velocity=((pressure.position-np.asarray(state.position))/dt).tolist(),
                selected_plan_path_velocity=((np.asarray(plan.state.position)-state.position)/dt).tolist())
            if 'angular_proposed_velocity' in pressure.diagnostics:
                diagnostic['angular_proposal_selected'] = reason != 'local_launch'
        self.last_diagnostics = diagnostic
        return plan
