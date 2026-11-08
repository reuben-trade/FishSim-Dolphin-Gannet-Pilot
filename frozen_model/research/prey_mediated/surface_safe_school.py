"""Experimental local surface-priority steering; not a safety guarantee.

The trigger uses each fish's depth and upward heading, with a conservative
continuous pitch-rise envelope evaluated at the baseline turn rate. Active
fish temporarily replace social/escape cues with a forward/downward surface
cue and bounded faster turning. This deliberately overrides the usual
separation cap: avoiding the surface takes priority while the guard is active.

The native engine is unchanged. Its existing explicit reflection fallback is
retained, counted and exposed as a guard failure. An already shallow, upward
state may be impossible to save with fixed speed and bounded turning. The
class name does not certify that all such states stay underwater.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .reactive_school import ReactiveSchool, reactive_controls


GUARD_VERSION = 'anticipatory_surface_priority_v1'


@dataclass(frozen=True)
class SurfaceGuardConfig:
    safety_factor: float = 1.5
    margin: float = .25
    turn_multiplier: float = 4.
    external_gain: float = 3.

    def __post_init__(self):
        for name in ('safety_factor', 'margin', 'turn_multiplier', 'external_gain'):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not np.isfinite(value) or value <= 0:
                raise ValueError(name+' must be finite and positive')
        if self.turn_multiplier < 1 or .6*self.external_gain <= 1:
            raise ValueError('guard must retain baseline turning and overpower unit upward repulsion')


@dataclass(frozen=True)
class SurfaceGuardDiagnostics:
    active: np.ndarray
    depth: np.ndarray
    heading_z: np.ndarray
    rise_envelope: np.ndarray
    trigger_depth: np.ndarray
    minimum_next_step_rise: np.ndarray
    unavoidable_next_step: np.ndarray
    applied_alignment: np.ndarray
    applied_attraction: np.ndarray
    applied_turning: np.ndarray
    applied_external: np.ndarray
    repulsion_override: np.ndarray
    reflected_ids: np.ndarray


class SurfaceSafeSchool(ReactiveSchool):
    """Drop-in research school with observable local guard and applied controls.

    last_response contains the actual ReactiveControls used. For guarded rows,
    CueFields.route/depth/threat are zero because they are replaced, and the
    surface/raw/combined arrays contain the guard vector. threat_strength still
    reports sensed proximity. These are overridden cues, not vector cancellation.
    last_surface_guard contains detached step-start diagnostics and reflected
    stable IDs. With no active guard, movement delegates exactly to ReactiveSchool.
    """
    def __init__(self, config, state=None, *, seed=0, guard_config=SurfaceGuardConfig()):
        if not isinstance(guard_config, SurfaceGuardConfig):
            raise TypeError('guard_config must be a SurfaceGuardConfig')
        self.guard_config = guard_config
        super().__init__(config, state, seed=seed)

    def load_state(self, state):
        super().load_state(state)
        self.last_surface_guard = None

    def step(self, threat_positions=None):
        config, guard = self.config, self.guard_config
        x, h = self.positions, self.directions
        depth = config.surface_z-x[:, 2]
        upward = np.clip(h[:, 2], 0., 1.)
        rise = config.speed/config.turn_rate*(1.-np.sqrt(np.maximum(0., 1.-upward**2)))
        trigger = guard.safety_factor*rise+guard.margin+config.speed*config.dt
        active = (h[:, 2] > 0.) & (depth <= trigger)
        # Under endpoint-heading Euler motion, even the steepest allowed pitch
        # turn cannot clear this step if its minimum upward displacement exceeds
        # available depth. This is a one-step impossibility flag, not a general
        # certificate for all future motion or the trigger's continuous envelope.
        remaining_pitch = np.maximum(0., np.arcsin(upward)-config.turn_rate*guard.turn_multiplier*config.dt)
        minimum_rise = config.speed*config.dt*np.sin(remaining_pitch)
        unavoidable = minimum_rise > depth+1e-12
        if not np.any(active):
            fields = super().step(threat_positions)
            controls = self.last_response
        else:
            normal = self._build_controls(x, threat_positions)
            horizontal = h.copy(); horizontal[:, 2] = 0.
            length = np.linalg.norm(horizontal, axis=1)
            np.divide(horizontal, length[:, None], out=horizontal, where=length[:, None] > 1e-12)
            horizontal[length <= 1e-12] = np.asarray(config.route_direction)
            guard_vector = guard.external_gain*(.8*horizontal-np.array([0., 0., .6]))
            components = {name: getattr(normal.fields, name).copy()
                          for name in ('route', 'depth', 'surface', 'threat', 'raw', 'combined', 'capped')}
            for name in ('route', 'depth', 'threat'):
                components[name][active] = 0.
            for name in ('surface', 'raw', 'combined'):
                components[name][active] = guard_vector[active]
            components['capped'][active] = False
            fields = replace(normal.fields, **components)
            alignment, attraction = normal.alignment.copy(), normal.attraction.copy()
            turning, caps = normal.turning.copy(), normal.external_caps.copy()
            alignment[active] = 0.; attraction[active] = 0.
            turning[active] = guard.turn_multiplier; caps[active] = guard.external_gain
            controls = replace(normal, fields=fields, alignment=alignment, attraction=attraction,
                               turning=turning, external_caps=caps)
            self._school.reset_controls()
            gains = np.linalg.norm(fields.combined, axis=1)
            for i in np.flatnonzero((gains > 0.) | (turning != 1.)):
                self._school.set_agent_control(int(i), float(alignment[i]), float(attraction[i]),
                    float(turning[i]), fields.combined[i].tolist(), float(gains[i]))
            self._school.move()
            # The inherited model's fallback remains visible; do not claim that
            # finite steering saves infeasible starts or silently hide a breach.
            moved = self.positions
            reflected = moved[:, 2] > config.surface_z
            self.last_reflected_ids = self._ids[reflected].copy()
            if np.any(reflected):
                directions = self.directions
                moved[reflected, 2] = 2*config.surface_z-moved[reflected, 2]
                directions[reflected, 2] *= -1
                self._school.load_positions(moved.T)
                self._school.load_velocities(directions.T)
                self.surface_reflections += int(reflected.sum())
            self.time += config.dt
            self.step_index += 1
            self.last_response = controls
        self.last_surface_guard = SurfaceGuardDiagnostics(
            active.copy(), depth.copy(), h[:, 2].copy(), rise.copy(), trigger.copy(),
            minimum_rise.copy(), unavoidable.copy(), controls.alignment.copy(),
            controls.attraction.copy(), controls.turning.copy(), fields.combined.copy(),
            (active & controls.repulsion).copy(), self.last_reflected_ids.copy())
        return fields
