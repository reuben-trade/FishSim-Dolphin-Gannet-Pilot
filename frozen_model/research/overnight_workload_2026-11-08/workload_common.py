"""Retrospective containment measures and resolved dolphin time accounting.

These global metrics are analysis only; the adaptive planner never receives them.
All lengths, times, thresholds and velocities are uncalibrated model units.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components


def clean(value):
    if isinstance(value, dict): return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)): return [clean(v) for v in value]
    if isinstance(value, np.ndarray): return clean(value.tolist())
    if isinstance(value, np.generic): return clean(value.item())
    if isinstance(value, float) and not np.isfinite(value): return None
    return value


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(clean(value), indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def containment(state, *, initial_count, initial_centre, initial_time, speed=3.,
                envelope_radius=18., link_radius=2.):
    """Keep survival, moving-envelope retention and cohesion distinct.

    The reference envelope translates +x at the declared swim speed from its
    initial centroid. Outward speed subtracts the contemporaneous mean flow;
    outward fraction counts radial speed > .3. Connectivity uses radius2.
    Contained is a descriptive predeclared gate, never numerical acceptance.
    """
    x, v = np.asarray(state.positions), np.asarray(state.directions)*speed
    n = len(x)
    if n == 0:
        return dict(n_live=0, survival_fraction=0., envelope_retention=0.,
                    largest_component_fraction=0., largest_component_retention=0.,
                    contained=False, r90=None, rg=None, outward_fraction=None,
                    outward_p90=None, mean_depth=None, centroid=None)
    centre, flow = x.mean(axis=0), v.mean(axis=0)
    radial = x-centre
    radius = np.linalg.norm(radial, axis=1)
    outward = np.sum(radial*(v-flow), axis=1)/np.maximum(radius, 1e-12)
    pairs = cKDTree(x).query_pairs(link_radius, output_type='ndarray')
    graph = csr_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])), shape=(n, n))
    _, labels = connected_components(graph, directed=False)
    largest = int(np.bincount(labels).max())
    reference = np.asarray(initial_centre) + np.array([speed*(state.time-initial_time), 0., 0.])
    envelope = np.linalg.norm(x-reference, axis=1) <= envelope_radius
    r90 = float(np.quantile(radius, .9))
    outward_fraction = float(np.mean(outward > .3))
    outward_p90 = float(np.quantile(np.maximum(outward, 0.), .9))
    result = dict(n_live=n, survival_fraction=n/initial_count,
        envelope_retention=float(envelope.sum()/initial_count),
        largest_component_fraction=largest/n, largest_component_retention=largest/initial_count,
        r90=r90, rg=float(np.sqrt(np.mean(radius**2))),
        outward_fraction=outward_fraction, outward_p90=outward_p90,
        mean_depth=float(-centre[2]), centroid=centre.tolist(), mean_velocity=flow.tolist(),
        polarization=float(np.linalg.norm(state.directions.mean(axis=0))),
        contained=bool(r90 <= 14. and largest/n >= .9 and outward_fraction <= .15 and outward_p90 <= .4))
    return result


def behaviour_category(phase, mode, adaptive_mode=None):
    if mode == 'recovery': return 'recovering'
    if mode == 'attack' or phase == 'attack': return 'hunting'
    if adaptive_mode == 'hunt': return 'hunting'
    if phase in ('maintain', 'opportunity'): return 'herding'
    return 'positioning'


class Accounting:
    """Integrate actual resolved motion, including within-step contact recovery."""
    def __init__(self, engine):
        self.per = {a.state.actor_id:dict(time=Counter(), distance=Counter(),
                    physical_mode_time=Counter(), phases=Counter(), captures=0,
                    virtual_successes=0, contacts=0, launches=0, reasons=Counter())
                    for a in engine.actors}
        self.events = []

    def add(self, engine, result, phases_before):
        new_events = []
        for step in result.predator_steps:
            who = step.before.actor_id
            row = self.per[who]
            planner = engine.actor_planners.get(who)
            diagnostic = {} if planner is None else (planner.last_diagnostics or {})
            all_changes = sorted(diagnostic.get('phase_events', []), key=lambda e:e['time'])
            # Adaptive contain/hunt decisions are distinct from v2 physical
            # phases. Keep their events, but never substitute them for a phase.
            changes = [e for e in all_changes if not e.get('reason','').startswith('adaptive_v1_')]
            phase = phases_before.get(who, 'not_dolphin')
            amode = diagnostic.get('adaptive_mode')
            for piece in step.pieces:
                low, high = piece.body.start, piece.body.end
                cuts = sorted({low, high, *[e['time'] for e in changes if low < e['time'] < high]})
                distance = float(np.linalg.norm(np.asarray(piece.body.after)-piece.body.before))
                for left, right in zip(cuts, cuts[1:]):
                    actual_phase = phase
                    for event in changes:
                        if event['time'] <= left+1e-12: actual_phase=event['after']
                    dt = right-left
                    category = behaviour_category(actual_phase, piece.mode, amode)
                    row['time'][category] += dt
                    row['distance'][category] += distance*dt/(high-low)
                    row['physical_mode_time'][piece.mode] += dt
                    row['phases'][actual_phase] += dt
            for event in step.transitions:
                row['reasons'][event.reason] += 1
                row['launches'] += event.reason == 'launch'
                if event.reason != 'habitat_boundary_hold':
                    new_events.append(dict(kind='transition', actor_id=who, **asdict(event)))
            for event in all_changes:
                record=dict(kind='phase', actor_id=who, **event)
                if event.get('reason','').startswith('adaptive_v1_'):
                    record.update(adaptive_metrics=diagnostic.get('adaptive_metrics'),
                        adaptive_stable_since=diagnostic.get('adaptive_stable_since'),
                        adaptive_mode=diagnostic.get('adaptive_mode'),
                        adaptive_reason=diagnostic.get('adaptive_reason'))
                new_events.append(record)
        for outcome in result.contacts:
            if outcome.status == 'bout_closed': continue
            proposal = outcome.proposal
            row = self.per[proposal.actor_id]
            if outcome.closes_bout:
                row['contacts'] += 1
                if outcome.status == 'captured':
                    row['captures' if engine.remove_prey else 'virtual_successes'] += 1
            new_events.append(dict(kind='oral', actor_id=proposal.actor_id, bout_id=proposal.bout_id,
                prey_id=proposal.prey_id, status=outcome.status, closes_bout=outcome.closes_bout,
                draw=outcome.draw, contact=asdict(proposal.contact)))
        self.events.extend(new_events)
        return new_events

    def snapshot(self): return clean(self.per)


def audit_summary(summary, events, expected_duration):
    """Independent conservation/time identities, not a physical replay claim."""
    errors=[]
    actual=summary['actual_duration']
    if abs(actual-expected_duration)>1e-7: errors.append('incomplete physical horizon')
    captures=Counter()
    for event in events:
        if event['kind']=='oral' and event['closes_bout'] and event['status']=='captured':
            captures[event['actor_id']]+=1
    for who,row in summary['per_actor'].items():
        if abs(sum(row['time'].values())-actual)>1e-7: errors.append(who+' time budget')
        if abs(sum(row['physical_mode_time'].values())-actual)>1e-7: errors.append(who+' physical mode budget')
        counted=row['captures'] if summary['remove_prey'] else row['virtual_successes']
        if counted!=captures[who]: errors.append(who+' event captures')
    if summary['remove_prey']:
        if summary['initial_count']-summary['final_count'] != sum(captures.values()): errors.append('removal conservation')
    elif summary['initial_count']!=summary['final_count']: errors.append('nonlethal prey loss')
    return dict(status='passed' if not errors else 'failed', errors=errors,
                scope='independent time, event tally and removal conservation; no native re-simulation')
