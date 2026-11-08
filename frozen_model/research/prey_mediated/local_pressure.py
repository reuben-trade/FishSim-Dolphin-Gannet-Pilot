"""Formation-only local patch circulation, with no capture or feeding gate.

Every actor reads the same step-start arrays, then filters prey by its own
sensing radius. A nearest visible fish defines a small visible patch. The
actor follows a waypoint outside that patch, adds tangential movement around
it, and matches the patch's observed velocity. Nearby peer repulsion is an
explicit same-species channel. There are no assigned sectors, shared school
centre, shape score, persistent floor, learned policy or prey removal.

This first version circulates principally around the gravity axis; it does
not guarantee three-dimensional coverage. Nearest-target/patch changes can
move the waypoint abruptly. Position uses bounded-turn endpoint-heading Euler
motion. Surface holds are explicit, with no reflection or teleportation.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .predators import turn_toward


POLICY_VERSION = 'local_patch_circulation_v1'


@dataclass(frozen=True)
class PressureConfig:
    sense_radius: float = 25.
    patch_radius: float = 6.
    stand_off: float = 2.5
    tracking_gain: float = 1.
    tracking_speed: float = 3.
    tangent_speed: float = 2.
    orbit_sign: int = 1
    spacing_radius: float = 5.
    spacing_speed: float = 2.
    max_speed: float = 6.
    turn_rate: float = math.pi/2
    search_speed: float = 3.
    surface_z: float = 0.
    surface_layer: float = 1.
    surface_margin: float = .3

    def __post_init__(self):
        for name in ('sense_radius', 'patch_radius', 'stand_off', 'tracking_gain',
                     'tracking_speed', 'spacing_radius', 'max_speed', 'turn_rate',
                     'surface_layer', 'surface_margin'):
            if not np.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(name+' must be finite and positive')
        for name in ('tangent_speed', 'spacing_speed', 'search_speed'):
            if not np.isfinite(getattr(self, name)) or getattr(self, name) < 0:
                raise ValueError(name+' must be finite and nonnegative')
        if self.orbit_sign not in (-1, 1) or not np.isfinite(self.surface_z):
            raise ValueError('orbit_sign must be -1/+1 and surface_z finite')


@dataclass(frozen=True)
class PressureStep:
    position: np.ndarray
    heading: np.ndarray
    diagnostics: dict


def _unit(vector, fallback):
    length = np.linalg.norm(vector)
    return vector/length if length > 1e-12 else np.array(fallback, dtype=float)


def _cap(vector, limit):
    return vector*min(1., limit/max(float(np.linalg.norm(vector)), 1e-30))


def _points(value, name):
    array = np.asarray(value, dtype=float)
    if array.size == 0:
        array = np.empty((0, 3))
    if array.ndim != 2 or array.shape[1] != 3 or not np.isfinite(array).all():
        raise ValueError(name+' must be finite shape (N, 3)')
    return array


def pressure_step(position, heading, fish_positions, fish_velocities, prey_ids,
                  peer_positions, dt, config: PressureConfig = PressureConfig()):
    """Return one actor's proposed step; peer_positions excludes this actor.

    Prey IDs must be unique integers. They resolve equal-distance target ties
    independently of row order. Invisible prey and peers outside spacing range
    cannot affect the proposal. Distinct coincident peers contribute no invented
    direction, and their count is reported as an unresolved spacing degeneracy.
    No peer IDs, target assignments or other actors' decisions are read.
    """
    p, h = np.asarray(position, float), np.asarray(heading, float)
    if p.shape != (3,) or h.shape != (3,) or not np.isfinite([p, h]).all():
        raise ValueError('position and heading must be finite 3-vectors')
    if p[2] > config.surface_z or not np.isclose(np.linalg.norm(h), 1., rtol=0, atol=1e-8):
        raise ValueError('actor must be underwater with a unit heading')
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError('dt must be finite and positive')
    x, v = _points(fish_positions, 'fish_positions'), _points(fish_velocities, 'fish_velocities')
    peers = _points(peer_positions, 'peer_positions')
    ids = np.asarray(prey_ids)
    if v.shape != x.shape or ids.shape != (len(x),) or ids.dtype.kind not in 'iu' or len(np.unique(ids)) != len(ids):
        raise ValueError('velocities and unique integer prey IDs must match fish rows')
    distance = np.linalg.norm(x-p, axis=1)
    visible = (distance <= config.sense_radius) & (x[:, 2] <= config.surface_z)
    selected, patch_ids, waypoint = None, np.empty(0, dtype=ids.dtype), None
    flow, tracking, tangent, outward = (np.zeros(3) for _ in range(4))
    if np.any(visible):
        rows = np.flatnonzero(visible)
        selected_row = rows[np.lexsort((ids[rows], distance[rows]))[0]]
        selected = int(ids[selected_row])
        patch = visible & (np.linalg.norm(x-x[selected_row], axis=1) <= config.patch_radius)
        patch_ids = np.sort(ids[patch])
        centre, flow = x[patch].mean(axis=0), v[patch].mean(axis=0)
        outward = _unit(p-centre, -h)
        edge = float(np.max((x[patch]-centre)@outward))
        waypoint = centre+outward*(edge+config.stand_off)
        waypoint[2] = min(waypoint[2], config.surface_z-config.surface_margin)
        tracking = _cap(config.tracking_gain*(waypoint-p), config.tracking_speed)
        tangent_axis = np.cross(np.array([0., 0., 1.]), outward)
        if np.linalg.norm(tangent_axis) <= 1e-12:
            # At a vertical pole use sensed prey flow projected into its tangent
            # plane, then own heading, then a fixed horizontal symmetry fallback.
            tangent_axis = flow-outward*(flow@outward)
            if np.linalg.norm(tangent_axis) <= 1e-12:
                tangent_axis = h-outward*(h@outward)
            if np.linalg.norm(tangent_axis) <= 1e-12:
                tangent_axis = np.array([1., 0., 0.])
        tangent = config.orbit_sign*config.tangent_speed*_unit(tangent_axis, [1., 0., 0.])
        desired_velocity = flow+tracking+tangent
    else:
        desired_velocity = config.search_speed*h
    peer_delta = p-peers
    peer_distance = np.linalg.norm(peer_delta, axis=1)
    near = (peer_distance > 0.) & (peer_distance < config.spacing_radius)
    spacing = np.zeros(3)
    if np.any(near):
        spacing = config.spacing_speed*np.sum(peer_delta[near]/peer_distance[near, None]
                    *(1.-peer_distance[near, None]/config.spacing_radius), axis=0)
        spacing = _cap(spacing, config.spacing_speed)
    desired_velocity = desired_velocity+spacing
    surface_weight = float(np.clip(1.-(config.surface_z-p[2])/config.surface_layer, 0., 1.))
    desired_velocity[2] -= config.max_speed*surface_weight
    desired_velocity = _cap(desired_velocity, config.max_speed)
    speed = float(np.linalg.norm(desired_velocity))
    new_heading = np.asarray(turn_toward(h, desired_velocity, config.turn_rate*dt)) if speed > 1e-12 else h.copy()
    duration = float(dt)
    surface_hold = bool(speed*new_heading[2] > 0. and p[2]+speed*new_heading[2]*dt > config.surface_z)
    if surface_hold:
        duration = max(0., (config.surface_z-p[2])/(speed*new_heading[2]))
    new_position = p+speed*new_heading*duration
    if surface_hold:
        new_position[2] = config.surface_z
    diagnostics = dict(policy=POLICY_VERSION, target_id=selected,
        visible_ids=np.sort(ids[visible]).tolist(), patch_ids=patch_ids.tolist(),
        visible_count=int(visible.sum()), local_patch_count=int(len(patch_ids)),
        waypoint=None if waypoint is None else waypoint.tolist(), observed_patch_velocity=flow.tolist(),
        radial_direction=outward.tolist(), tracking_velocity=tracking.tolist(), tangent_velocity=tangent.tolist(),
        spacing_velocity=spacing.tolist(), local_peer_count=int(near.sum()),
        coincident_peer_count=int(np.sum(peer_distance == 0.)),
        desired_velocity=desired_velocity.tolist(), commanded_speed=speed,
        actual_speed=float(np.linalg.norm(new_position-p)/dt), surface_hold=surface_hold, boundary_hold=surface_hold,
        surface_hold_duration=float(dt-duration))
    return PressureStep(new_position, new_heading, diagnostics)
