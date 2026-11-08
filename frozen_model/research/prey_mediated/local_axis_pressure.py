"""Draft local circulation about an explicit world-fixed motion-preference axis.

The +z default delegates exactly to the existing pressure controller. Other
axes change only its tangential velocity; patch selection, tracking, peer
spacing and the physical horizontal water surface retain their original rules.
An axis preference is imposed by the caller, not an emergent role or a spatial
slot. This file does not select a cohort or claim three-dimensional enclosure.
"""
from __future__ import annotations

import numpy as np

from .local_pressure import PressureConfig, PressureStep, _cap, _unit, pressure_step
from .predators import turn_toward


POLICY_VERSION = 'local_patch_axis_circulation_draft_v1'


def normalized_orbit_axis(value):
    axis = np.asarray(value, dtype=float)
    if axis.shape != (3,) or not np.isfinite(axis).all():
        raise ValueError('orbit_axis must be a finite three-vector')
    length = float(np.linalg.norm(axis))
    if not np.isfinite(length) or length <= 1e-12:
        raise ValueError('orbit_axis must have finite norm greater than 1e-12')
    return axis / length


def axis_pressure_step(position, heading, fish_positions, fish_velocities,
                       prey_ids, peer_positions, dt,
                       config: PressureConfig = PressureConfig(), *,
                       orbit_axis=(0., 0., 1.)):
    """The ordinary stepper signature plus one bindable local preference.

    Bind an actor-specific axis with functools.partial. The exact +z return,
    including diagnostics, is the original PressureStep. Record configured axes
    in the caller's manifest; extra axis diagnostics appear only off +z.
    """
    axis = normalized_orbit_axis(orbit_axis)
    base = pressure_step(position, heading, fish_positions, fish_velocities,
                         prey_ids, peer_positions, dt, config)
    if np.array_equal(axis, [0., 0., 1.]):
        return base
    diagnostic = dict(base.diagnostics)
    diagnostic.update(policy=POLICY_VERSION, base_policy=base.diagnostics['policy'],
        orbit_axis=axis.tolist(), tangent_pole_degenerate=False,
        tangent_fallback='none', base_tangent_velocity=base.diagnostics['tangent_velocity'])
    # No sensed patch means no circulation; search and local spacing replay.
    if diagnostic['target_id'] is None:
        return PressureStep(base.position, base.heading, diagnostic)

    p, h = np.asarray(position, float), np.asarray(heading, float)
    radial = np.asarray(diagnostic['radial_direction'])
    flow = np.asarray(diagnostic['observed_patch_velocity'])
    tracking = np.asarray(diagnostic['tracking_velocity'])
    spacing = np.asarray(diagnostic['spacing_velocity'])
    tangent_axis = np.cross(axis, radial)
    if np.linalg.norm(tangent_axis) <= 1e-12:
        diagnostic['tangent_pole_degenerate'] = True
        diagnostic['tangent_fallback'] = 'local_flow'
        tangent_axis = flow - radial * (flow @ radial)
        if np.linalg.norm(tangent_axis) <= 1e-12:
            diagnostic['tangent_fallback'] = 'own_heading'
            tangent_axis = h - radial * (h @ radial)
        if np.linalg.norm(tangent_axis) <= 1e-12:
            diagnostic['tangent_fallback'] = 'fixed_perpendicular'
            basis = np.eye(3)[int(np.argmin(np.abs(radial)))]
            tangent_axis = basis - radial * (basis @ radial)
    tangent = config.orbit_sign * config.tangent_speed * _unit(tangent_axis, [1., 0., 0.])

    # Preserve original operation order and motion/surface equations. The
    # preference axis never rotates gravity or the actual surface normal.
    desired_velocity = flow + tracking + tangent
    desired_velocity = desired_velocity + spacing
    surface_weight = float(np.clip(1.-(config.surface_z-p[2])/config.surface_layer, 0., 1.))
    desired_velocity[2] -= config.max_speed * surface_weight
    desired_velocity = _cap(desired_velocity, config.max_speed)
    speed = float(np.linalg.norm(desired_velocity))
    new_heading = np.asarray(turn_toward(h, desired_velocity, config.turn_rate*dt)) if speed > 1e-12 else h.copy()
    duration = float(dt)
    surface_hold = bool(speed*new_heading[2] > 0. and p[2]+speed*new_heading[2]*dt > config.surface_z)
    if surface_hold:
        duration = max(0., (config.surface_z-p[2])/(speed*new_heading[2]))
    new_position = p + speed*new_heading*duration
    if surface_hold:
        new_position[2] = config.surface_z
    diagnostic.update(tangent_velocity=tangent.tolist(), desired_velocity=desired_velocity.tolist(),
        commanded_speed=speed, actual_speed=float(np.linalg.norm(new_position-p)/dt),
        surface_hold=surface_hold, boundary_hold=surface_hold,
        surface_hold_duration=float(dt-duration))
    return PressureStep(new_position, new_heading, diagnostic)
