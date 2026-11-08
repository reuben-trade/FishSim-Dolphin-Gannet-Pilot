"""Local patch-pressure candidate with an explicit proposal/commit boundary.

This module does not construct a native school, resolve contact, or draw RNG.
Pursuit delegates exactly to the frozen November 6 controller. Pressure uses
the same bounded motion and committed attacks, with a separately stored local
tracker and prospective non-biting phase rules. See controller_spec_v2.md.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import copy
import hashlib
import importlib.util
import math
from pathlib import Path
import sys

import numpy as np

from research.prey_mediated.contacts import LinearSegment, TimeWindow
from research.prey_mediated.predators import (
    MotionPiece, PredatorConfig, PredatorState, PredatorStep, Transition, advance,
    intercept_point, observe,
)

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path: sys.path.insert(0, str(HERE))
from geometry_feasibility_v2 import GeometryParameters
from patch_tracking_v2 import (
    TrackerParameters, TrackerState, clear_tracker, update_tracker,
)

VERSION = 'local_patch_pressure_v2'
EPSILON = 1e-12
LEGACY_SHA256 = 'b0a2ad6f570d0dc7d1d0a80bf3ac148fd26c180a98b288b5fae8af1fed5f291d'


def frozen_policy():
    """Load the verified shared movement and exact historical pursuit policy."""
    name = '_nov6_policy_for_local_patch_v2'
    if name not in sys.modules:
        path = Path(__file__).resolve().parents[1] / 'herding_study_2026-11-06/policy.py'
        if hashlib.sha256(path.read_bytes()).hexdigest() != LEGACY_SHA256:
            raise RuntimeError('The frozen pursuit/movement source has changed')
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


@dataclass(frozen=True)
class ControllerParameters:
    tracker: TrackerParameters = field(default_factory=TrackerParameters)
    geometry: GeometryParameters = field(default_factory=GeometryParameters)
    approach_budget: float = 16.
    pressure_minimum: float = 2.
    maintenance_maximum: float = 4.
    withdrawal_duration: float = 1.
    release_tolerance: float = 2.
    launch_radius: float = 6.

    def __post_init__(self):
        if not isinstance(self.tracker, TrackerParameters) or not isinstance(self.geometry, GeometryParameters):
            raise ValueError('Explicit tracker and geometry parameter objects are required')
        for name in ('approach_budget', 'pressure_minimum', 'maintenance_maximum',
                     'withdrawal_duration', 'release_tolerance', 'launch_radius'):
            value = getattr(self, name)
            if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
                raise ValueError(name + ' must be finite and positive')
        for name, value in asdict(self.geometry).items():
            if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
                raise ValueError('geometry.' + name + ' must be finite and positive')
        if not 0 < self.geometry.core_quantile <= 1:
            raise ValueError('core_quantile must be in (0,1]')
        if self.maintenance_maximum <= self.pressure_minimum:
            raise ValueError('Maintenance maximum must exceed pressure minimum')
        if self.release_tolerance < self.geometry.entry_tolerance:
            raise ValueError('Release tolerance cannot be smaller than entry tolerance')
        for name in ('link_radius', 'minimum_patch_size', 'lateral_scale'):
            if getattr(self.tracker, name) != getattr(self.geometry, name):
                raise ValueError('Tracker and geometry disagree on ' + name)

    @classmethod
    def from_dict(cls, value):
        value = dict(value)
        value['tracker'] = TrackerParameters(**value['tracker'])
        value['geometry'] = GeometryParameters(**value['geometry'])
        return cls(**value)


@dataclass(frozen=True)
class ControllerState:
    phase: str = 'acquire'
    phase_started: float = 0.
    attempt_started: float | None = None
    attempt_deadline: float | None = None
    maintenance_started: float | None = None
    opportunity_target: int | None = None
    withdrawal_direction: tuple | None = None
    tracker: TrackerState = field(default_factory=TrackerState)

    def state_dict(self):
        result = asdict(self)
        result['tracker'] = self.tracker.state_dict()
        return result

    @classmethod
    def from_dict(cls, value):
        value = dict(value)
        value['tracker'] = TrackerState.from_state_dict(value['tracker'])
        if value['withdrawal_direction'] is not None:
            value['withdrawal_direction'] = tuple(value['withdrawal_direction'])
        result = cls(**value)
        if result.phase not in ('acquire', 'approach', 'maintain', 'opportunity', 'attack', 'recovery', 'withdraw'):
            raise ValueError('Unknown controller phase')
        for key in ('phase_started', 'attempt_started', 'attempt_deadline', 'maintenance_started'):
            v = getattr(result, key)
            if v is not None and (not math.isfinite(v) or v < 0):
                raise ValueError('Invalid controller clock')
        if (result.attempt_started is None) != (result.attempt_deadline is None):
            raise ValueError('Attempt clocks must be paired')
        if result.attempt_started is not None and result.attempt_deadline < result.attempt_started:
            raise ValueError('Attempt deadline precedes start')
        if result.opportunity_target is not None and (type(result.opportunity_target) is not int or result.opportunity_target < 0):
            raise ValueError('Invalid opportunity target')
        direction = result.withdrawal_direction
        if direction is not None and (np.asarray(direction).shape != (3,) or not np.isfinite(direction).all()
                                      or abs(np.linalg.norm(direction)-1.) > 1e-8):
            raise ValueError('Invalid withdrawal direction')
        return result


def geometry_for_patch(state, patch, config, parameters=GeometryParameters()):
    """Use only one CURRENT selected local patch, with its epoch-fixed side."""
    x = np.asarray(patch.positions, float)
    centre, flow, forward = map(np.asarray, (patch.centre, patch.flow, patch.forward))
    lateral = np.array([-forward[1], forward[0], 0.])
    extent = float(np.quantile((x-centre) @ forward, parameters.core_quantile))
    width = float(np.quantile(abs((x-centre) @ lateral), parameters.core_quantile))
    goal = centre + forward*(extent+parameters.stand_off) + lateral*(patch.side_coefficient*(width+parameters.stand_off))
    goal[2] = min(centre[2]-parameters.below_offset, config.surface_z-parameters.surface_margin)
    position = np.asarray(state.position)
    nearest = float(np.linalg.norm(x-position, axis=1).min())
    error = float(np.linalg.norm(goal-position))
    ahead = float((position-centre) @ forward) >= extent
    desired = flow+parameters.tracking_gain*(goal-position)
    desired *= min(1., config.speed/max(float(np.linalg.norm(desired)), EPSILON))
    return dict(waypoint=goal, waypoint_error=error, local_core_front=extent,
                ahead_local_core=bool(ahead), nearest_patch_prey=nearest,
                actual_proximity=nearest < parameters.threat_radius,
                entry=bool(error <= parameters.entry_tolerance and ahead and nearest < parameters.threat_radius),
                desired_velocity=desired,
                waypoint_nearest_prey=float(np.linalg.norm(x-goal, axis=1).min()))


def shared_launch_guard(state, target, velocity, config, radius=6.):
    """Exact arithmetic/order of the inherited pursuit's shared launch guards."""
    goal, lead = intercept_point(state.position, target, velocity, config.speed, config.intercept_horizon)
    delta = np.asarray(goal)-state.position
    distance = float(np.linalg.norm(np.asarray(target)-state.position))
    goal_distance = float(np.linalg.norm(delta))
    direction = delta/goal_distance if goal_distance > EPSILON else np.asarray(state.heading, float)
    turn_time = math.acos(float(np.clip(np.asarray(state.heading) @ direction, -1., 1.)))/config.turn_rate
    residual = goal_distance-config.speed*lead
    tests = ((distance <= radius, 'outside_launch_radius'),
             (abs(residual) <= 1e-8, 'intercept_outside_horizon'),
             (lead+turn_time <= config.bout_duration, 'insufficient_bout_budget'))
    reason = next((reason for passed, reason in tests if not passed), 'local_launch')
    return reason == 'local_launch', dict(launch_reason=reason, range=distance,
        predicted_lead=lead, predicted_turn_time=turn_time, intercept_residual=residual)


def _at_time(observation, time):
    positions = np.asarray(observation.positions, float).reshape(-1, 3)
    velocities = np.asarray(observation.velocities, float).reshape(-1, 3)
    return replace(observation, time=time,
        positions=tuple(map(tuple, (positions+(time-observation.time)*velocities).tolist())))


def _step_from_dict(value):
    def state(v):
        v = dict(v)
        for key in ('position', 'heading'): v[key] = tuple(v[key])
        return PredatorState(**v)
    pieces = []
    for raw in value['pieces']:
        p = dict(raw); body = dict(p['body'])
        for key in ('before', 'after'): body[key] = tuple(body[key])
        p['body'] = LinearSegment(**body)
        for key in ('heading_before', 'heading_after'): p[key] = tuple(p[key])
        for key in ('bite_window', 'water_window'):
            p[key] = None if p[key] is None else TimeWindow(**p[key])
        pieces.append(MotionPiece(**p))
    return PredatorStep(state(value['before']), state(value['state']), tuple(pieces),
        tuple(Transition(**t) for t in value['transitions']), value['contact_resolved'])


class DolphinPlanner:
    """One actor's local planner. Every proposal REQUIRES commit_step(actual).

    The adapter must acknowledge Encounter's resolved step before calling this
    planner again or taking an ordinary diagnostic checkpoint. Pending proposals
    are nevertheless serializable, so interruptions cannot hide state.
    """
    def __init__(self, tactic='pressure', parameters=ControllerParameters()):
        if tactic not in ('pursuit', 'pressure'): raise ValueError('Use pursuit or pressure')
        if not isinstance(parameters, ControllerParameters): raise TypeError('Explicit ControllerParameters required')
        self.tactic, self.parameters = tactic, parameters
        self._legacy = frozen_policy().DolphinPlanner('pursuit')
        self._memory = ControllerState()
        self._committed = None
        self._pending = None
        self.last_diagnostics = None

    @property
    def controller_state(self):
        return self._memory

    def state_dict(self):
        pending = None if self._pending is None else dict(
            step=asdict(self._pending['step']), memory=self._pending['memory'].state_dict(),
            config=asdict(self._pending['config']), diagnostics=copy.deepcopy(self._pending['diagnostics']))
        return dict(schema_version=1, version=VERSION, tactic=self.tactic,
            legacy_sha256=LEGACY_SHA256, parameters=asdict(self.parameters),
            memory=self._memory.state_dict(),
            committed=None if self._committed is None else asdict(self._committed),
            pending=pending, last_diagnostics=copy.deepcopy(self.last_diagnostics))

    def load_state_dict(self, value):
        value = copy.deepcopy(value)
        expected = {'schema_version', 'version', 'tactic', 'legacy_sha256', 'parameters',
                    'memory', 'committed', 'pending', 'last_diagnostics'}
        if set(value) != expected or value['schema_version'] != 1 or value['version'] != VERSION:
            raise ValueError('Unsupported controller snapshot')
        if value['legacy_sha256'] != LEGACY_SHA256 or value['tactic'] != self.tactic:
            raise ValueError('Controller source/tactic mismatch')
        if ControllerParameters.from_dict(value['parameters']) != self.parameters:
            raise ValueError('Controller parameter mismatch')
        memory = ControllerState.from_dict(value['memory'])
        committed = value['committed']
        if committed is not None:
            committed['position'], committed['heading'] = tuple(committed['position']), tuple(committed['heading'])
            committed = PredatorState(**committed)
        pending = value['pending']
        if pending is not None:
            pending = dict(step=_step_from_dict(pending['step']),
                memory=ControllerState.from_dict(pending['memory']), config=PredatorConfig(**pending['config']),
                diagnostics=pending['diagnostics'])
            if committed is not None and pending['step'].before != committed:
                raise ValueError('Pending proposal is not from the committed actor state')
        self._memory, self._committed, self._pending = memory, committed, pending
        self.last_diagnostics = value['last_diagnostics']

    def _phase(self, memory, state, phase, reason, events, phase_events, **changes):
        old = memory.phase
        memory = replace(memory, phase=phase, phase_started=state.time, **changes)
        mode = {'acquire': 'search', 'approach': 'search', 'maintain': 'position',
                'opportunity': 'position', 'attack': 'attack', 'recovery': 'recovery',
                'withdraw': 'search'}[phase]
        target = memory.opportunity_target if phase == 'opportunity' else state.target_id if phase == 'attack' else None
        events.append(Transition(state.time, state.mode, mode, 'controller_v2_'+reason,
                                 state.bout_id, target))
        state = replace(state, mode=mode, mode_since=state.time, target_id=target)
        phase_events.append(dict(time=state.time, before=old, after=phase, reason=reason,
            patch_epoch=memory.tracker.epoch, patch_ids=list(memory.tracker.member_ids),
            target_id=target, attempt_started=memory.attempt_started,
            attempt_deadline=memory.attempt_deadline))
        return memory, state

    def _withdraw(self, memory, state, config, reason, events, phase_events):
        delta = np.asarray(state.heading, float).copy()
        if memory.tracker.last_centre is not None:
            delta = np.asarray(state.position)-memory.tracker.last_centre
        # The direction is fixed now; it never follows an unseen patch.
        if state.position[2] >= config.surface_z-self.parameters.geometry.surface_margin:
            delta[2] = min(delta[2], -self.parameters.geometry.surface_margin)
        norm = float(np.linalg.norm(delta))
        direction = tuple(delta/norm) if norm > EPSILON else (0., 0., -1.)
        return self._phase(memory, state, 'withdraw', reason, events, phase_events,
            maintenance_started=None, opportunity_target=None, withdrawal_direction=direction,
            tracker=clear_tracker(memory.tracker))

    @staticmethod
    def _recovery_memory(memory, time):
        return ControllerState(phase='recovery', phase_started=time, tracker=clear_tracker(memory.tracker))

    def _resolve(self, memory, state, observation, config, events, phase_events, seen_at):
        p = self.parameters
        diagnostic = dict(policy=VERSION, tactic=self.tactic, actor_id=state.actor_id,
            time=state.time, observation_time=seen_at, observed_count=len(observation.prey_ids), launch_allowed=False,
            launch_reason='pressure_not_ready', waypoint=None, waypoint_error=None,
            pressure_elapsed=0., current_patch=False, entry=False, actual_proximity=False)
        if state.mode == 'attack':
            return memory, state, None, diagnostic
        if state.mode == 'recovery':
            if memory.phase != 'recovery': memory = self._recovery_memory(memory, state.mode_since)
            if state.time < state.ready_at-EPSILON:
                diagnostic['launch_reason'] = 'personal_recovery'
                return memory, state, np.zeros(3), diagnostic
            memory, state = self._phase(memory, state, 'acquire', 'recovery_complete', events, phase_events)
        if memory.phase == 'withdraw':
            if state.time < memory.phase_started+p.withdrawal_duration-EPSILON:
                return memory, state, config.speed*np.asarray(memory.withdrawal_direction), diagnostic
            memory, state = self._phase(memory, state, 'acquire', 'withdrawal_complete', events, phase_events,
                attempt_started=None, attempt_deadline=None, maintenance_started=None,
                opportunity_target=None, withdrawal_direction=None, tracker=clear_tracker(memory.tracker))

        tracker, patch, tracking = update_tracker(memory.tracker, state, observation, config, p.tracker, seen_at=seen_at)
        memory = replace(memory, tracker=tracker)
        diagnostic.update(tracker=tracking, current_patch=patch is not None,
            patch_ids=list(tracker.member_ids), patch_epoch=tracker.epoch)
        if tracking['handoff']:
            # Handoffs cannot renew the enclosing attempt allowance.
            if memory.attempt_started is None:
                memory = replace(memory, attempt_started=state.time, attempt_deadline=state.time+p.approach_budget)
            memory, state = self._phase(memory, state, 'approach', 'patch_acquired_or_handoff', events, phase_events,
                maintenance_started=None, opportunity_target=None)

        if memory.phase in ('acquire', 'approach') and memory.attempt_deadline is not None and state.time >= memory.attempt_deadline-EPSILON:
            memory, state = self._withdraw(memory, state, config, 'approach_timeout', events, phase_events)
            return memory, state, config.speed*np.asarray(memory.withdrawal_direction), diagnostic

        if patch is None:
            if memory.phase in ('maintain', 'opportunity'):
                memory, state = self._phase(memory, state, 'approach', 'patch_unavailable', events, phase_events,
                    maintenance_started=None, opportunity_target=None)
                if memory.attempt_deadline is not None and state.time >= memory.attempt_deadline-EPSILON:
                    memory, state = self._withdraw(memory, state, config, 'approach_timeout', events, phase_events)
                    return memory, state, config.speed*np.asarray(memory.withdrawal_direction), diagnostic
            if tracker.last_seen_time is not None and not tracking['stale']:
                memory, state = self._withdraw(memory, state, config, 'visibility_grace_expired', events, phase_events)
                return memory, state, config.speed*np.asarray(memory.withdrawal_direction), diagnostic
            if tracking['stale']:
                desired = np.asarray(tracking['stale_search_centre'])-state.position
            else:
                desired = np.asarray(state.heading, float).copy()
                if state.position[2] == config.surface_z and desired[2] > 0.: desired[2] = 0.
            norm = float(np.linalg.norm(desired))
            desired = config.speed*desired/norm if norm > EPSILON else np.zeros(3)
            return memory, state, desired, diagnostic

        geometry = geometry_for_patch(state, patch, config, p.geometry)
        diagnostic.update({k: v.tolist() if isinstance(v, np.ndarray) else v
                           for k, v in geometry.items() if k != 'desired_velocity'})
        release = geometry['waypoint_error'] > p.release_tolerance or not geometry['actual_proximity']
        if memory.phase in ('maintain', 'opportunity') and release:
            memory, state = self._phase(memory, state, 'approach', 'pressure_geometry_lost', events, phase_events,
                maintenance_started=None, opportunity_target=None)
            if memory.attempt_deadline is not None and state.time >= memory.attempt_deadline-EPSILON:
                memory, state = self._withdraw(memory, state, config, 'approach_timeout', events, phase_events)
                return memory, state, config.speed*np.asarray(memory.withdrawal_direction), diagnostic
        if memory.phase == 'approach' and geometry['entry']:
            memory, state = self._phase(memory, state, 'maintain', 'pressure_entry', events, phase_events,
                maintenance_started=state.time, opportunity_target=None)
        if memory.phase in ('maintain', 'opportunity'):
            elapsed = max(0., state.time-memory.maintenance_started)
            diagnostic['pressure_elapsed'] = elapsed
            # A bounded opportunity may finish after the approach deadline, but
            # the four-unit maximum has precedence over a new launch at its end.
            if elapsed >= p.maintenance_maximum-EPSILON:
                memory, state = self._withdraw(memory, state, config, 'maintenance_timeout', events, phase_events)
                return memory, state, config.speed*np.asarray(memory.withdrawal_direction), diagnostic
            if memory.phase == 'maintain' and elapsed >= p.pressure_minimum-EPSILON:
                memory, state = self._phase(memory, state, 'opportunity', 'pressure_minimum_met', events, phase_events)
            if memory.phase == 'opportunity':
                target = memory.opportunity_target
                if target not in observation.prey_ids:
                    row = min(range(len(observation.prey_ids)), key=lambda i: (
                        np.linalg.norm(np.asarray(observation.positions[i])-state.position), observation.prey_ids[i]))
                    target = observation.prey_ids[row]
                    memory = replace(memory, opportunity_target=target)
                    state = replace(state, target_id=target)
                    phase_events.append(dict(time=state.time, before='opportunity', after='opportunity',
                        reason='local_target_selected', patch_epoch=tracker.epoch,
                        patch_ids=list(tracker.member_ids), target_id=target,
                        attempt_started=memory.attempt_started, attempt_deadline=memory.attempt_deadline))
                    events.append(Transition(state.time, state.mode, state.mode,
                        'controller_v2_local_target_selected', state.bout_id, target))
                row = observation.prey_ids.index(target)
                eligible, launch = shared_launch_guard(state, observation.positions[row], observation.velocities[row], config, p.launch_radius)
                diagnostic.update(launch, launch_allowed=eligible, target_id=target)
                if eligible:
                    memory = replace(memory, phase='attack', phase_started=state.time)
                    launched = replace(state, mode='attack', mode_since=state.time,
                        bout_id=state.bout_id+1, bout_start=state.time,
                        bout_deadline=state.time+config.bout_duration, last_outcome=None)
                    events.append(Transition(state.time, state.mode, 'attack', 'launch', launched.bout_id, target))
                    phase_events.append(dict(time=state.time, before='opportunity', after='attack',
                        reason='launch', patch_epoch=tracker.epoch, patch_ids=list(tracker.member_ids),
                        target_id=target, attempt_started=memory.attempt_started, attempt_deadline=memory.attempt_deadline))
                    return memory, launched, None, diagnostic
        return memory, state, geometry['desired_velocity'], diagnostic

    def __call__(self, state, observation, dt, config, *, local_peer_positions=()):
        if self._pending is not None: raise RuntimeError('commit_step(actual) is required before another proposal')
        if self._committed is not None and state != self._committed:
            raise ValueError('Input actor differs from the last committed state')
        if self.tactic == 'pursuit':
            step = self._legacy(state, observation, dt, config, local_peer_positions=local_peer_positions)
            diagnostic = copy.deepcopy(self._legacy.last_diagnostics)
            diagnostic.update(adapter_version=VERSION, phase_events=[])
            memory = self._memory
        else:
            if state.species != 'D' or config.species != 'D' or config.dolphin_policy != 'direct':
                raise ValueError('A direct-mechanics dolphin is required')
            if config.spacing_enabled: raise ValueError('The declared candidate keeps body spacing disabled')
            if config.sense_radius != self.parameters.geometry.sensing_radius:
                raise ValueError('Candidate and shared sensing radius differ')
            if observation.actor_id != state.actor_id or observation.time != state.time:
                raise ValueError('Observation must match actor and exact step-start clock')
            if isinstance(dt, (bool, np.bool_)) or not math.isfinite(dt) or not 0 < dt < min(config.handling_duration, config.miss_recovery_duration):
                raise ValueError('dt must be positive and shorter than personal recovery')
            if state.position[2] > config.surface_z: raise ValueError('Dolphin must be underwater')
            if state.mode == 'attack' and (state.target_id is None or state.bout_start is None):
                raise ValueError('Attack requires target and bout clocks')
            if state.mode != 'attack' and state.bout_start is not None:
                raise ValueError('Only attack can carry bout clocks')
            peers = np.asarray(local_peer_positions, float).reshape(-1, 3)
            if not np.isfinite(peers).all(): raise ValueError('Peers must be finite')
            local = observe(state, observation.positions, observation.velocities,
                np.asarray(observation.prey_ids, dtype=np.int64), config)
            memory, working = self._memory, state
            pieces, events, phase_events = [], [], []
            end = state.time+dt
            for _ in range(10000):
                current = _at_time(local, working.time)
                memory, working, desired, diagnostic = self._resolve(memory, working, current, config, events, phase_events, local.time)
                if working.time >= end-EPSILON:
                    working = replace(working, time=end)
                    break
                if working.mode == 'attack':
                    attack = advance(working, current, end-working.time, config)
                    pieces.extend(attack.pieces); events.extend(attack.transitions)
                    working = attack.state
                    if working.mode == 'recovery':
                        memory = self._recovery_memory(memory, working.mode_since)
                        phase_events.append(dict(time=working.mode_since, before='attack', after='recovery',
                            reason=working.last_outcome, patch_epoch=memory.tracker.epoch,
                            patch_ids=[], target_id=None, attempt_started=None, attempt_deadline=None))
                    break
                duration = min(end-working.time, config.max_motion_interval, math.pi/(4*config.turn_rate))
                clocks = []
                if working.mode == 'recovery': clocks.append(working.ready_at)
                elif memory.phase == 'withdraw': clocks.append(memory.phase_started+self.parameters.withdrawal_duration)
                elif memory.phase in ('acquire', 'approach'):
                    if memory.attempt_deadline is not None: clocks.append(memory.attempt_deadline)
                    if not diagnostic.get('current_patch') and memory.tracker.last_seen_time is not None:
                        clocks.append(memory.tracker.last_seen_time+self.parameters.tracker.visibility_grace)
                elif memory.phase in ('maintain', 'opportunity'):
                    clocks.append(memory.maintenance_started+(self.parameters.pressure_minimum
                        if memory.phase == 'maintain' else self.parameters.maintenance_maximum))
                duration = min([duration]+[clock-working.time for clock in clocks if clock > working.time+EPSILON])
                previous_time = working.time
                working, piece = frozen_policy().DolphinPlanner._move(working, desired, duration, config)
                if working.time <= previous_time: raise RuntimeError('Non-biting movement failed to advance time')
                pieces.append(piece)
                if piece.boundary_hold:
                    events.append(Transition(piece.body.start, piece.mode, piece.mode,
                        'habitat_boundary_hold', piece.bout_id, piece.target_id))
            else: raise RuntimeError('Controller substep limit exceeded')
            diagnostic.update(policy_mode=memory.phase, phase_started=memory.phase_started,
                attempt_started=memory.attempt_started, attempt_deadline=memory.attempt_deadline,
                phase_events=phase_events, output_mode=working.mode, time=working.time)
            step = PredatorStep(state, working, tuple(pieces), tuple(events))
        self._pending = dict(step=step, memory=memory, config=config, diagnostics=diagnostic)
        self.last_diagnostics = copy.deepcopy(diagnostic)
        return step

    def commit_step(self, actual):
        if self._pending is None: raise RuntimeError('No proposal is awaiting acknowledgement')
        proposal = self._pending['step']
        if not isinstance(actual, PredatorStep) or actual.before != proposal.before or actual.state.time != proposal.state.time:
            raise ValueError('Resolved step does not belong to this proposal')
        if actual.contact_resolved:
            # Validate the whole replacement against the unchanged contact
            # adapter, instead of accepting an arbitrary recovery endpoint.
            from research.prey_mediated.predators import apply_contact
            terminal = [e for e in actual.transitions if e.reason in ('capture', 'contact_miss')]
            if len(terminal) != 1: raise ValueError('Resolved contact must have one terminal event')
            terminal = terminal[0]
            # Config is retained in pending snapshots; no private physics state.
            config = self._pending['config']
            if apply_contact(proposal, terminal.reason == 'capture', terminal.time, config) != actual:
                raise ValueError('Resolved contact differs from shared contact mechanics')
            if actual.state.mode != 'recovery' or not proposal.before.time <= terminal.time <= actual.state.time:
                raise ValueError('Invalid committed contact recovery')
            memory = self._recovery_memory(self._pending['memory'], terminal.time)
            diagnostic = copy.deepcopy(self._pending['diagnostics'])
            diagnostic['phase_events'] = [e for e in diagnostic.get('phase_events', []) if e['time'] <= terminal.time]
            diagnostic['phase_events'].append(dict(time=terminal.time, before='attack', after='recovery',
                reason=terminal.reason, patch_epoch=memory.tracker.epoch, patch_ids=[], target_id=None,
                attempt_started=None, attempt_deadline=None))
            diagnostic.update(policy_mode='recovery', phase_started=terminal.time, pressure_elapsed=0.,
                patch_ids=[], current_patch=False, attempt_started=None, attempt_deadline=None,
                committed_contact_time=terminal.time, output_mode='recovery', time=actual.state.time)
        else:
            if actual != proposal: raise ValueError('An unresolved acknowledgement must exactly match its proposal')
            memory, diagnostic = self._pending['memory'], self._pending['diagnostics']
        self._memory, self._committed = memory, actual.state
        self.last_diagnostics = copy.deepcopy(diagnostic)
        self._pending = None
        return self.last_diagnostics
