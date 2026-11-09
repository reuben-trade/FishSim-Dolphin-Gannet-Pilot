"""Local herd for a declared positive duration, strike once, recover, and repeat.

Only prey selection differs between nearest and exposed. Pressure is actual
proximity to any currently observed fish; fragmentation never removes feeding
permission. The shared fixed planner owns movement, attacks and actual commits.
"""
from __future__ import annotations

import copy
from dataclasses import replace
from pathlib import Path
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT/'research/herding_study_2026-11-07'), str(ROOT)]
from controller_v2 import (DolphinPlanner, ControllerParameters, ControllerState,
                           geometry_for_patch, shared_launch_guard, EPSILON)
from patch_tracking_v2 import update_tracker
from research.prey_mediated.predators import Transition

VERSION = 'simple_continuous_proximity_herdH_one_strike_regime_v1'
POLICIES = ('nearest', 'exposed')
HERDING_MINIMA = (1., 2., 3.)
NEIGHBOUR_RADIUS = 2.


class SimpleHerdStrikePlanner(DolphinPlanner):
    def __init__(self, policy='nearest', parameters=ControllerParameters()):
        if policy not in POLICIES:
            raise ValueError('Use nearest or exposed')
        if parameters.pressure_minimum not in HERDING_MINIMA:
            raise ValueError('Use a prespecified herding minimum: 1T, 2T or 3T')
        super().__init__(tactic='pressure', parameters=parameters)
        self.policy = policy
        self.opportunity_events = []
        self.active_opportunity = None

    def _candidates(self, state, observation, config):
        x = np.asarray(observation.positions, float).reshape(-1, 3)
        v = np.asarray(observation.velocities, float).reshape(-1, 3)
        if not len(x):
            return [], np.empty(0, dtype=int)
        counts = np.asarray(cKDTree(x).query_ball_point(x, NEIGHBOUR_RADIUS,
                            return_length=True))-1
        distances = np.linalg.norm(x-np.asarray(state.position), axis=1)
        rows = []
        for i in np.flatnonzero(distances <= self.parameters.launch_radius):
            eligible, guard = shared_launch_guard(state, x[i], v[i], config,
                                                   self.parameters.launch_radius)
            if eligible:
                rows.append((int(i), guard))
        if self.policy == 'nearest':
            rows.sort(key=lambda r: (float(distances[r[0]]), observation.prey_ids[r[0]]))
        else:
            rows.sort(key=lambda r: (int(counts[r[0]]),
                r[1]['predicted_lead']+r[1]['predicted_turn_time'],
                float(distances[r[0]]), observation.prey_ids[r[0]]))
        return rows, counts

    def _resolve(self, memory, state, observation, config, events, phase_events, seen_at):
        diagnostic = dict(policy=VERSION, cycle_policy=self.policy, actor_id=state.actor_id,
            time=state.time, observation_time=seen_at, observed_count=len(observation.prey_ids),
            launch_allowed=False, launch_reason='pressure_not_ready', current_patch=False,
            actual_proximity=False, pressure_started=memory.maintenance_started,
            pressure_elapsed=0., target_id=state.target_id,
            selected_neighbor_count=None, feasible_min_neighbor_count=None, feasible_count=0)
        if state.mode == 'attack':
            diagnostic['launch_reason'] = 'active_bout'
            return memory, state, None, diagnostic
        if state.mode == 'recovery':
            if memory.phase != 'recovery':
                memory = self._recovery_memory(memory, state.mode_since)
            if state.time < state.ready_at-EPSILON:
                diagnostic['launch_reason'] = 'personal_recovery'
                return memory, state, np.zeros(3), diagnostic
            memory, state = self._phase(memory, state, 'acquire', 'recovery_complete', events, phase_events)

        tracker, patch, tracking = update_tracker(memory.tracker, state, observation,
            config, self.parameters.tracker, seen_at=seen_at)
        memory = replace(memory, tracker=tracker, attempt_started=None, attempt_deadline=None,
                         withdrawal_direction=None)
        x = np.asarray(observation.positions, float).reshape(-1, 3)
        nearest = float(np.linalg.norm(x-np.asarray(state.position), axis=1).min()) if len(x) else None
        proximity = nearest is not None and nearest < self.parameters.geometry.threat_radius
        diagnostic.update(tracker=tracking, current_patch=patch is not None,
            patch_ids=list(tracker.member_ids), patch_epoch=tracker.epoch,
            actual_proximity=proximity, nearest_visible_prey=nearest)
        if patch is not None:
            geometry = geometry_for_patch(state, patch, config, self.parameters.geometry)
            desired = geometry['desired_velocity']
            diagnostic.update(waypoint=geometry['waypoint'].tolist(),
                waypoint_error=geometry['waypoint_error'])
        else:
            # Searching for the next patch is non-biting movement. Current
            # isolated fish still count as pressure and remain strike targets.
            desired = np.asarray(state.heading, float).copy()
            if state.position[2] >= config.surface_z and desired[2] > 0.:
                desired[2] = 0.
            norm = float(np.linalg.norm(desired))
            desired = config.speed*desired/norm if norm > EPSILON else np.zeros(3)

        if not proximity:
            if memory.maintenance_started is not None:
                began = memory.maintenance_started
                memory, state = self._phase(memory, state, 'approach', 'cycle_pressure_reset',
                    events, phase_events, maintenance_started=None, opportunity_target=None)
                phase_events[-1].update(pressure_started=began,
                    pressure_elapsed=max(0., state.time-began), cycle_reason='no_current_near_prey')
            elif memory.phase != 'approach':
                memory, state = self._phase(memory, state, 'approach', 'cycle_search', events, phase_events,
                    maintenance_started=None, opportunity_target=None)
            diagnostic.update(pressure_started=None, pressure_elapsed=0., launch_reason='no_current_near_prey')
            return memory, state, desired, diagnostic

        if memory.maintenance_started is None:
            memory, state = self._phase(memory, state, 'maintain', 'cycle_pressure_start',
                events, phase_events, maintenance_started=state.time, opportunity_target=None)
            phase_events[-1].update(pressure_started=state.time, pressure_elapsed=0.,
                cycle_reason='current_near_prey', nearest_visible_prey=nearest)
        began = memory.maintenance_started
        elapsed = max(0., state.time-began)
        diagnostic.update(pressure_started=began, pressure_elapsed=elapsed)
        if elapsed < self.parameters.pressure_minimum-EPSILON:
            return memory, state, desired, diagnostic

        rows, counts = self._candidates(state, observation, config)
        minimum = min((int(counts[i]) for i, _ in rows), default=None)
        diagnostic.update(feasible_count=len(rows), feasible_min_neighbor_count=minimum,
                          launch_reason='no_current_feasible_target')
        if not rows:
            return memory, state, desired, diagnostic
        i, guard = rows[0]
        target = observation.prey_ids[i]
        chosen = int(counts[i])
        launched = replace(state, mode='attack', mode_since=state.time,
            target_id=target, bout_id=state.bout_id+1, bout_start=state.time,
            bout_deadline=state.time+config.bout_duration, last_outcome=None)
        memory = replace(memory, phase='attack', phase_started=state.time,
                         maintenance_started=None, opportunity_target=target)
        events.append(Transition(state.time, state.mode, 'attack', 'launch', launched.bout_id, target))
        phase_events.append(dict(time=state.time, before='maintain', after='attack',
            reason='launch', patch_epoch=tracker.epoch, patch_ids=list(tracker.member_ids),
            target_id=target, bout_id=launched.bout_id, attempt_started=None, attempt_deadline=None,
            cycle_launch=True, pressure_started=began, pressure_elapsed=elapsed,
            selected_neighbor_count=chosen, feasible_min_neighbor_count=minimum,
            feasible_count=len(rows)))
        diagnostic.update(guard, launch_allowed=True, target_id=target,
                          selected_neighbor_count=chosen)
        return memory, launched, None, diagnostic

    def commit_step(self, actual):
        diagnostic = super().commit_step(actual)
        actual_launches={(e.bout_id,e.target_id,e.time) for e in actual.transitions if e.reason=='launch'}
        for event in diagnostic.get('phase_events', []):
            if event.get('cycle_launch'):
                if (event['bout_id'], event['target_id'], event['time']) not in actual_launches:
                    continue
                kind='cycle_launch'
            elif event['reason'] in ('cycle_pressure_start','cycle_pressure_reset'):
                kind=event['reason']
            else:
                continue
            self.opportunity_events.append(dict(kind=kind, policy=self.policy,
                **{k:copy.deepcopy(v) for k,v in event.items()
                   if k not in ('before','after','cycle_launch')}))
        return diagnostic

    def state_dict(self):
        value=super().state_dict()
        value['simple']=dict(version=VERSION, policy=self.policy,
                            herding_minimum=self.parameters.pressure_minimum,
                            opportunity_events=copy.deepcopy(self.opportunity_events))
        return value

    def load_state_dict(self, value):
        value=copy.deepcopy(value)
        custom=value.pop('simple')
        if (custom['version']!=VERSION or custom['policy']!=self.policy
                or custom['herding_minimum']!=self.parameters.pressure_minimum):
            raise ValueError('Simple herd-strike snapshot policy/version mismatch')
        super().load_state_dict(value)
        self.opportunity_events=custom['opportunity_events']
        self.active_opportunity=None
