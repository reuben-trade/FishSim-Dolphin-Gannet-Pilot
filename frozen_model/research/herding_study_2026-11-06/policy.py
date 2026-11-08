"""Matched local dolphin tactics for a new, explicitly versioned experiment.

Both tactics share observations, target retention, launch eligibility, bounded
locomotion, stationary handling, and the existing committed attack mechanics.
Only their non-biting positioning and the herder's pressure interval differ.
Fish see ordinary dolphin positions; no tactic label reaches the school.

This is an engineering hypothesis, not a calibrated biological controller.
There is no assigned global centre, sector, interspecies cue, random draw, or
hidden behavioural state. PredatorState holds all persistent state. For the
herder, search means approaching containment and position means maintaining it.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math

import numpy as np

from research.prey_mediated.contacts import LinearSegment, TimeWindow
from research.prey_mediated.predators import (
    LocalObservation, MotionPiece, PredatorStep, Transition, advance,
    intercept_point, observe, turn_toward,
)


POLICY_VERSION = "matched_local_pursuit_below_patch_herding_v1"
EPSILON = 1e-12


@dataclass(frozen=True)
class HerdingConfig:
    # Shared attack eligibility. These are policy assumptions, not capabilities.
    launch_radius: float = 6.
    patch_radius: float = 6.
    stand_off: float = 2.5
    below_offset: float = 2.5
    waypoint_tolerance: float = 1.
    release_tolerance: float = 2.
    pressure_duration: float = .5
    positioning_budget: float = 4.
    tracking_gain: float = 1.
    tracking_speed: float = 3.
    tangent_speed: float = 1.5
    surface_margin: float = .3

    def __post_init__(self):
        for name, value in self.__dict__.items():
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, float)):
                raise ValueError(name + " must be a finite real number")
            if not math.isfinite(value) or value <= 0:
                raise ValueError(name + " must be finite and positive")
        if self.release_tolerance < self.waypoint_tolerance:
            raise ValueError("release_tolerance must be at least waypoint_tolerance")


def _unit(vector, fallback):
    vector = np.asarray(vector, float)
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm > EPSILON else np.asarray(fallback, float)


def _cap(vector, bound):
    vector = np.asarray(vector, float)
    return vector * min(1., bound / max(float(np.linalg.norm(vector)), EPSILON))


def _at_time(observation, time):
    elapsed = time - observation.time
    positions = np.asarray(observation.positions, float).reshape(-1, 3)
    velocities = np.asarray(observation.velocities, float).reshape(-1, 3)
    return replace(observation, time=time,
        positions=tuple(map(tuple, positions + elapsed * velocities)))


class DolphinPlanner:
    """Stateless tactic apart from replaceable diagnostic telemetry.

    Both tactics retain the nearest locally visible fish until its loss or an
    attack's completion. Herding first seeks a below/side local-patch waypoint,
    then spends pressure_duration there before attempting a shared-eligible
    capture. If an approach lasts positioning_budget without reaching the
    waypoint, it may take an otherwise eligible opportunity. This declared
    fallback prevents an unconditional refusal to feed; it does not teleport
    the dolphin or guarantee a launch. Lost containment restarts positioning.
    """
    def __init__(self, tactic="pursuit", herding_config=HerdingConfig()):
        if tactic not in ("pursuit", "herding"):
            raise ValueError("tactic must be pursuit or herding")
        if not isinstance(herding_config, HerdingConfig):
            raise TypeError("an explicit HerdingConfig is required")
        self.tactic = tactic
        self.herding_config = herding_config
        self.last_diagnostics = None

    @staticmethod
    def _transition(state, mode, reason, events, **changes):
        events.append(Transition(state.time, state.mode, mode, reason,
                                 state.bout_id, state.target_id))
        return replace(state, mode=mode, mode_since=state.time, **changes)

    def _geometry(self, state, observation):
        hc = self.herding_config
        positions = np.asarray(observation.positions, float).reshape(-1, 3)
        velocities = np.asarray(observation.velocities, float).reshape(-1, 3)
        row = observation.prey_ids.index(state.target_id)
        target, velocity = positions[row], velocities[row]
        patch = np.linalg.norm(positions - target, axis=1) <= hc.patch_radius
        centre = positions[patch].mean(axis=0)
        flow = velocities[patch].mean(axis=0)
        horizontal = np.asarray(state.position) - centre
        horizontal[2] = 0.
        fallback = -flow.copy(); fallback[2] = 0.
        if np.linalg.norm(fallback) <= EPSILON:
            fallback = -np.asarray(state.heading); fallback[2] = 0.
        radial = _unit(horizontal, _unit(fallback, (1., 0., 0.)))
        extent = max(0., float(np.max((positions[patch] - centre) @ radial)))
        waypoint = centre + radial * (extent + hc.stand_off)
        waypoint[2] = centre[2] - hc.below_offset
        return target, velocity, waypoint, flow, radial, tuple(
            prey_id for prey_id, keep in zip(observation.prey_ids, patch) if keep)

    def _resolve(self, state, observation, config, events):
        hc = self.herding_config
        diagnostic = dict(policy=POLICY_VERSION, tactic=self.tactic,
            actor_id=state.actor_id, time=state.time, input_mode=state.mode,
            observed_count=len(observation.prey_ids), target_id=state.target_id,
            launch_allowed=False, launch_reason="no_local_target", containment=False,
            pressure_elapsed=0., waypoint=None, waypoint_error=None, patch_ids=[])
        if state.mode == "attack":
            diagnostic["launch_reason"] = "active_bout"
            return state, diagnostic, None
        if state.mode == "recovery":
            if state.time < state.ready_at - EPSILON:
                diagnostic["launch_reason"] = "personal_recovery"
                return state, diagnostic, np.zeros(3)
            state = self._transition(state, "search", "recovery_complete", events,
                                     target_id=None)
        if state.target_id not in observation.prey_ids:
            if state.target_id is not None or state.mode != "search":
                state = self._transition(state, "search", "no_local_target", events,
                                         target_id=None)
            if observation.prey_ids:
                row = min(range(len(observation.prey_ids)), key=lambda i: (
                    np.linalg.norm(np.asarray(observation.positions[i])-state.position),
                    observation.prey_ids[i]))
                state = self._transition(state,
                    "position" if self.tactic == "pursuit" else "search",
                    "local_target_selected", events,
                    target_id=observation.prey_ids[row])
        if state.target_id is None:
            desired = np.asarray(state.heading, float).copy()
            if state.position[2] == config.surface_z and desired[2] > 0.:
                desired[2] = 0.
            return state, diagnostic, config.speed * _unit(desired, (1., 0., 0.))

        target, velocity, waypoint, flow, radial, patch_ids = self._geometry(state, observation)
        waypoint[2] = min(waypoint[2], config.surface_z-hc.surface_margin)
        error = float(np.linalg.norm(waypoint-state.position))
        if self.tactic == "herding":
            if state.mode == "position" and error > hc.release_tolerance:
                state = self._transition(state, "search", "containment_position_lost", events)
            elif state.mode == "search" and error <= hc.waypoint_tolerance:
                state = self._transition(state, "position", "containment_position_reached", events)
        elapsed = max(0., state.time-state.mode_since)
        pressure_ready = self.tactic == "herding" and state.mode == "position" and elapsed >= hc.pressure_duration-EPSILON
        fallback_ready = self.tactic == "herding" and state.mode == "search" and elapsed >= hc.positioning_budget-EPSILON
        tactic_ready = self.tactic == "pursuit" or pressure_ready or fallback_ready
        goal, lead = intercept_point(state.position, target, velocity,
                                     config.speed, config.intercept_horizon)
        delta = np.asarray(goal)-state.position
        distance = float(np.linalg.norm(target-state.position))
        goal_distance = float(np.linalg.norm(delta))
        direction = _unit(delta, state.heading)
        turn_time = math.acos(float(np.clip(np.asarray(state.heading)@direction, -1., 1.)))/config.turn_rate
        residual = goal_distance-config.speed*lead
        eligible = ((distance <= hc.launch_radius, "outside_launch_radius"),
                    (abs(residual) <= 1e-8, "intercept_outside_horizon"),
                    (lead+turn_time <= config.bout_duration, "insufficient_bout_budget"),
                    (tactic_ready, "maintaining_pressure" if state.mode == "position" else "seeking_containment"))
        reason = next((reason for passed, reason in eligible if not passed), "local_launch")
        diagnostic.update(target_id=state.target_id, range=distance,
            predicted_lead=lead, predicted_turn_time=turn_time, intercept_residual=residual,
            waypoint=waypoint.tolist(), waypoint_error=error, patch_ids=list(patch_ids),
            containment=self.tactic == "herding" and state.mode == "position",
            pressure_elapsed=elapsed if self.tactic == "herding" and state.mode == "position" else 0.,
            positioning_elapsed=elapsed if self.tactic == "herding" and state.mode == "search" else 0.,
            positioning_budget_fallback=fallback_ready,
            launch_allowed=reason == "local_launch", launch_reason=reason)
        if reason == "local_launch":
            launched = replace(state, bout_id=state.bout_id+1,
                bout_start=state.time, bout_deadline=state.time+config.bout_duration,
                last_outcome=None)
            state = self._transition(launched, "attack", "launch", events)
            return state, diagnostic, None
        if self.tactic == "pursuit":
            desired_velocity = config.speed*direction
        else:
            tracking = _cap(hc.tracking_gain*(waypoint-state.position), hc.tracking_speed)
            tangent = hc.tangent_speed*np.cross((0., 0., 1.), radial) if state.mode == "position" else np.zeros(3)
            desired_velocity = flow+tracking+tangent
        if config.spacing_enabled:
            desired_velocity = desired_velocity + config.speed*config.spacing_gain*np.asarray(observation.spacing_vector)
        return state, diagnostic, _cap(desired_velocity, config.speed)

    @staticmethod
    def _move(state, desired_velocity, duration, config):
        speed = min(config.speed, float(np.linalg.norm(desired_velocity)))
        start = np.asarray(state.position)

        def candidate(elapsed):
            heading = (turn_toward(state.heading, desired_velocity,
                2*math.atan(config.turn_rate*elapsed/2)) if speed > EPSILON else state.heading)
            return heading, start + speed*elapsed*np.asarray(heading)

        heading, after = candidate(duration)
        hold = False
        if after[2] > config.surface_z:
            if start[2] == config.surface_z:
                after = start.copy(); hold = True
            else:
                lower, upper = 0., duration
                for _ in range(60):
                    middle = (lower+upper)/2
                    _, point = candidate(middle)
                    if point[2] < config.surface_z: lower = middle
                    else: upper = middle
                duration = upper
                heading, after = candidate(duration)
                after[2] = config.surface_z
        end = state.time+duration
        final = replace(state, position=tuple(after), heading=heading, time=end)
        piece = MotionPiece(LinearSegment(state.time, end, state.position, final.position),
            state.heading, final.heading, state.mode, state.bout_id, state.target_id,
            None, TimeWindow(state.time, end), hold)
        return final, piece

    def __call__(self, state, observation, dt, config, *, local_peer_positions=()):
        if state.species != "D" or config.species != "D" or config.dolphin_policy != "direct":
            raise ValueError("matched planner requires a direct-mechanics dolphin configuration")
        if observation.actor_id != state.actor_id or observation.time != state.time:
            raise ValueError("observation must belong to the actor and exact step-start clock")
        if (isinstance(dt, (bool, np.bool_)) or not math.isfinite(dt)
                or not 0 < dt < min(config.handling_duration, config.miss_recovery_duration)):
            raise ValueError("dt must be positive and shorter than personal recovery")
        if state.position[2] > config.surface_z:
            raise ValueError("dolphin must be at or below the common water surface")
        if state.mode == "attack" and (state.target_id is None or state.bout_start is None):
            raise ValueError("an attack requires a target and personal bout clocks")
        if state.mode != "attack" and state.bout_start is not None:
            raise ValueError("only an attack may carry active bout clocks")
        peers = np.asarray(local_peer_positions, float).reshape(-1, 3)
        if not np.isfinite(peers).all():
            raise ValueError("local peers must be finite")
        # Defensively filter even if called outside Encounter. Both tactics get
        # the same observation model and same body-spacing channel.
        local = observe(state, observation.positions, observation.velocities,
            np.asarray(observation.prey_ids, dtype=np.int64), config,
            conspecific_positions=peers if config.spacing_enabled else None)
        before, working = state, state
        end = state.time+dt
        pieces, events = [], []
        while True:
            current = _at_time(local, working.time)
            working, diagnostic, desired = self._resolve(working, current, config, events)
            diagnostic["output_mode"] = working.mode
            diagnostic["policy_mode"] = ("containment" if diagnostic["containment"] else
                "positioning" if self.tactic == "herding" and working.mode == "search" and working.target_id is not None else
                working.mode)
            self.last_diagnostics = diagnostic
            if working.time >= end-EPSILON:
                working = replace(working, time=end)
                break
            remaining = end-working.time
            if working.mode == "attack":
                attack = advance(working, current, remaining, config)
                pieces.extend(attack.pieces); events.extend(attack.transitions)
                working = attack.state
                self.last_diagnostics["output_mode"] = working.mode
                break
            duration = min(remaining, config.max_motion_interval,
                           math.pi/(4*config.turn_rate))
            if working.mode == "recovery":
                duration = min(duration, working.ready_at-working.time)
            elif self.tactic == "herding" and working.target_id is not None:
                clock = working.mode_since + (self.herding_config.pressure_duration
                    if working.mode == "position" else self.herding_config.positioning_budget)
                if clock > working.time+EPSILON:
                    duration = min(duration, clock-working.time)
            working, piece = self._move(working, desired, duration, config)
            pieces.append(piece)
            if piece.boundary_hold:
                events.append(Transition(piece.body.start, piece.mode, piece.mode,
                    "habitat_boundary_hold", piece.bout_id, piece.target_id))
        return PredatorStep(before, working, tuple(pieces), tuple(events))
