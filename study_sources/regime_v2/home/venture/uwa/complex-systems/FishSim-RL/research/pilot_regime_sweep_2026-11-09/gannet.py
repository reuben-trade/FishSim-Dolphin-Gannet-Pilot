"""Global dense-cluster targeting; original bird motion and contacts.

Only a free bird's decision target changes. Active plunge/pursuit, ascent,
recovery, capture probability and all kinematic limits use the old code.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'research/herding_study_2026-11-07')]
from research.prey_mediated.predators import Transition, advance, observe

VERSION = 'global_dbscan_size_weighted_gannet_target_v1'
LINK_RADIUS = 2.
DENSITY_RADIUS = 2.
MIN_SAMPLES = 4


def dense_clusters(positions, *, eps=LINK_RADIUS, min_samples=MIN_SAMPLES):
    """Small deterministic DBSCAN, including each point in its neighbour count.

    Input rows are stable-ID ordered by observe(). Connected core points form
    clusters; an ambiguous border point belongs to the first such cluster.
    No cluster count or forced assignment of isolated fish is imposed.
    """
    x = np.asarray(positions, dtype=float).reshape(-1, 3)
    if eps <= 0 or isinstance(min_samples, bool) or int(min_samples) != min_samples or min_samples < 1:
        raise ValueError('Positive radius and positive integer min_samples required')
    if not np.isfinite(x).all():
        raise ValueError('Finite positions required')
    near = np.sum((x[:, None, :] - x[None, :, :]) ** 2, axis=2) <= eps ** 2
    core = near.sum(axis=1) >= min_samples
    labels = np.full(len(x), -1, dtype=int)
    count = 0
    for start in np.flatnonzero(core):
        if labels[start] != -1:
            continue
        labels[start] = count
        stack = [int(start)]
        while stack:
            row = stack.pop()
            for neighbour in np.flatnonzero(near[row]):
                if labels[neighbour] != -1:
                    continue
                labels[neighbour] = count
                if core[neighbour]:
                    stack.append(int(neighbour))
        count += 1
    return [np.flatnonzero(labels == label) for label in range(count)], labels


def select_dense_target(state, observation, config, *, rng=None):
    """Sample a dense cluster by accessible fish count, then aim at its density peak.

    The planner supplies its private target RNG. A fixed default seed makes this
    standalone helper reproducible for diagnostics. Accessibility is a coarse
    current-position travel/depth check, never a guarantee of mouth contact.
    Full observation is provided by the builder's global sensing radius; the
    inherited underwater detection-depth restriction is retained.
    """
    rng = np.random.default_rng(0) if rng is None else rng
    local = observe(state, observation.positions, observation.velocities,
                    np.asarray(observation.prey_ids, dtype=np.int64), config)
    x = np.asarray(local.positions, dtype=float).reshape(-1, 3)
    ids = np.asarray(local.prey_ids, dtype=np.int64)
    patches, labels = dense_clusters(x)
    depth_limit = config.max_dive_depth - config.speed / config.turn_rate - config.ascent_margin
    depth = config.surface_z - x[:, 2]
    horizontal = np.linalg.norm(x[:, :2] - np.asarray(state.position)[:2], axis=1)
    travel = (horizontal + max(0., state.position[2] - config.surface_z)) / config.air_speed + depth / config.speed
    accessible = (depth <= depth_limit) & (travel <= config.bout_duration)
    neighbours = np.sum(np.sum((x[:, None, :] - x[None, :, :]) ** 2, axis=2)
                        <= DENSITY_RADIUS ** 2, axis=1) - 1
    candidates = [(patch, patch[accessible[patch]]) for patch in patches if np.any(accessible[patch])]
    diagnostic = dict(version=VERSION, visible_count=len(x), patch_count=len(patches),
        noise_count=int(np.sum(labels == -1)), eligible_patch_count=len(candidates),
        accessible_count=int(accessible.sum()), clustering_radius=LINK_RADIUS,
        minimum_samples=MIN_SAMPLES, density_radius=DENSITY_RADIUS,
        eligible_patch_sizes=[len(patch) for patch, _ in candidates],
        eligible_patch_accessible_counts=[len(rows) for _, rows in candidates])
    if not candidates:
        rows = np.flatnonzero(accessible)
        if not len(rows):
            return None, dict(diagnostic, reason='no_accessible_target', selection_probabilities=[])
        patch = rows
        reason = 'fallback_densest_accessible_neighbourhood'
        probabilities = []
        selected_patch = None
    else:
        weights = np.array([len(rows) for _, rows in candidates], dtype=float)
        probabilities = (weights / weights.sum()).tolist()
        selected_patch = int(rng.choice(len(candidates), p=probabilities))
        patch, rows = candidates[selected_patch]
        reason = 'global_size_weighted_dense_patch_target'
    row = min(rows, key=lambda i: (-int(neighbours[i]),
        float(np.linalg.norm(x[i] - np.asarray(state.position))), int(ids[i])))
    return int(ids[row]), dict(diagnostic, patch_size=len(patch),
        patch_ids=ids[patch].tolist(), patch_centre=x[patch].mean(axis=0).tolist(),
        target_position=x[row].tolist(), target_neighbours=int(neighbours[row]),
        target_id=int(ids[row]), reason=reason, selected_patch=selected_patch,
        selection_probabilities=probabilities)


class DensePatchGannetPlanner:
    """Choose once per free targeting cycle and commit only realized memory."""
    def __init__(self, seed=0):
        self._need_selection = True
        self._pending = None
        self._committed = None
        self.last_diagnostics = {}
        self._target_rng = np.random.default_rng(seed)

    def __call__(self, state, observation, dt, config, *, local_peer_positions=()):
        if self._pending is not None:
            raise RuntimeError('Gannet proposal requires commit_step(actual)')
        if state.species != 'G' or config.species != 'G':
            raise ValueError('Shared gannet planner requires species G')
        if observation.actor_id != state.actor_id or observation.time != state.time:
            raise ValueError('Gannet observation must match actor and clock')
        local = observe(state, observation.positions, observation.velocities,
            np.asarray(observation.prey_ids, dtype=np.int64), config)
        proposed = state
        selected = False
        targeting_attempted = False
        planning_observation = local
        # Random selection belongs to the proposal until actual motion commits.
        proposal_rng = np.random.default_rng(0)
        proposal_rng.bit_generator.state = deepcopy(self._target_rng.bit_generator.state)
        free = state.mode in ('search', 'orient', 'recovery') and state.time >= state.ready_at - 1e-12
        need = self._need_selection or state.target_id not in local.prey_ids
        diagnostic = dict(version=VERSION, selected=False, time=state.time,
                          input_mode=state.mode, visible_count=len(local.prey_ids))
        if free and need:
            targeting_attempted = True
            target, detail = select_dense_target(state, local, config, rng=proposal_rng)
            diagnostic.update(detail)
            if target is not None:
                proposed = replace(state, target_id=target)
                selected = True
                diagnostic.update(selected=True)
            else:
                proposed = replace(state, target_id=None)
                planning_observation = replace(local, prey_ids=(), positions=(), velocities=())
                diagnostic['withheld_no_accessible_target'] = True
        plan = advance(proposed, planning_observation, dt, config)
        # The original integrator can end recovery (or finish ascent and an
        # already elapsed recovery) and launch within this same proposal.
        # Detect that pure provisional transition, then repeat only the pure
        # predator proposal with the current local target already prepared.
        # No fish step, random draw, motion clock or recovery is repeated.
        becomes_free = any(e.reason == 'recovery_complete' for e in plan.transitions)
        if not targeting_attempted and need and becomes_free:
            targeting_attempted = True
            target, detail = select_dense_target(state, local, config, rng=proposal_rng)
            diagnostic.update(detail)
            if target is not None:
                proposed = replace(state, target_id=target)
                plan = advance(proposed, local, dt, config)
                selected = True
                diagnostic.update(selected=True, selection_prepared_for_free_boundary=True)
            else:
                proposed = replace(state, target_id=None)
                planning_observation = replace(local, prey_ids=(), positions=(), velocities=())
                plan = advance(proposed, planning_observation, dt, config)
                diagnostic['withheld_no_accessible_target'] = True
        # The engine validates original physical state identity. Selection is
        # an instantaneous decision and changes no actual motion endpoint.
        transitions = plan.transitions
        if selected:
            transitions = (Transition(state.time, state.mode, state.mode,
                'gannet_global_dense_target_selected', state.bout_id, proposed.target_id),) + transitions
        plan = replace(plan, before=state, transitions=transitions)
        self._pending = dict(before=state, proposed=plan, selected=selected,
                             diagnostics=diagnostic,
                             target_rng_state=deepcopy(proposal_rng.bit_generator.state))
        self.last_diagnostics = deepcopy(diagnostic)
        return plan

    def commit_step(self, actual):
        pending = self._pending
        if pending is None:
            raise RuntimeError('No gannet proposal awaits acknowledgement')
        proposed = pending['proposed']
        if actual.before != pending['before'] or actual.state.time != proposed.state.time:
            raise ValueError('Actual gannet step does not match proposed identity/clock')
        if not actual.contact_resolved and actual != proposed:
            raise ValueError('Unresolved gannet step changed after proposal')
        if actual.state.mode in ('ascent', 'recovery'):
            self._need_selection = True
        elif pending['selected']:
            self._need_selection = False
        self._committed = asdict(actual.state)
        self._target_rng.bit_generator.state = deepcopy(pending['target_rng_state'])
        self.last_diagnostics = deepcopy(pending['diagnostics'])
        self.last_diagnostics['committed_mode'] = actual.state.mode
        self._pending = None
        return deepcopy(self.last_diagnostics)

    def state_dict(self):
        return dict(version=VERSION, need_selection=self._need_selection,
            target_rng_state=deepcopy(self._target_rng.bit_generator.state),
            committed=deepcopy(self._committed), pending=None if self._pending is None else
            dict(before=asdict(self._pending['before']), proposed=asdict(self._pending['proposed']),
                 selected=self._pending['selected'], diagnostics=deepcopy(self._pending['diagnostics']),
                 target_rng_state=deepcopy(self._pending['target_rng_state'])),
            last_diagnostics=deepcopy(self.last_diagnostics))

    def load_state_dict(self, snapshot):
        """Restore only a completed snapshot; pending physical proposals are not replayed."""
        if self._pending is not None or snapshot.get('pending') is not None:
            raise ValueError('Cannot load an uncommitted gannet snapshot')
        if snapshot.get('version') != VERSION:
            raise ValueError('Gannet snapshot version mismatch')
        rng = np.random.default_rng(0)
        rng.bit_generator.state = deepcopy(snapshot['target_rng_state'])
        self._target_rng = rng
        self._need_selection = bool(snapshot['need_selection'])
        self._committed = deepcopy(snapshot['committed'])
        self.last_diagnostics = deepcopy(snapshot['last_diagnostics'])
