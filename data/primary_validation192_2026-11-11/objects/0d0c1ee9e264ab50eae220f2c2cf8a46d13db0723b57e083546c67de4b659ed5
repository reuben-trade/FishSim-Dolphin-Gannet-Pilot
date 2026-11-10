"""Research-only deterministic local threat response; no trained policy.

The fixed profile is inspired by the existing FULL_ESCAPE example. With
w = maximum local proximity weight, social gains become (1-.75*w, 1-.5*w)
and the native turn multiplier becomes 1+3*w. Escape gain is 3, with a total
external-vector cap of 3 for exposed fish. A fish in the native repulsion
branch instead keeps a cap <= .8, so the external vector cannot reverse a
nonzero unit separation direction. This is not a collision guarantee.

Environment, threat visibility, radius and reflection follow scenario.py.
Away vectors still sum: opposing predators can cancel, including exact
co-location's zero direction. Proximity still changes social/turn controls
when directional threats cancel. There is no velocity anticipation, learning,
school centre, formation target or response to airborne predators.

Unexposed fish retain their exact original controls, even beside exposed
fish. With no exposed fish step delegates to the original implementation.
An exposed fish can respond when ScenarioConfig.external_cap is zero: the
prototype deliberately replaces that cap outside the repulsion branch.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from .scenario import CueFields, ScenarioConfig, TravellingSchool, external_cues


PROFILE_VERSION = "local_full_escape_v2"


@dataclass(frozen=True)
class ReactiveControls:
    """Detached, step-start arrays in the current stable-ID row order."""

    fields: CueFields
    alignment: np.ndarray
    attraction: np.ndarray
    turning: np.ndarray
    repulsion: np.ndarray
    external_caps: np.ndarray


def reactive_controls(positions, config: ScenarioConfig, threat_positions=None) -> ReactiveControls:
    """Pure local profile; 0 < squared distance <= rr**2 matches native code.

    Only exposed rows are replaced, preserving baseline cue arithmetic for
    all rows with zero proximity weight. Couzin3D.rebuild_connections uses
    get_neighbour_conn_slow's lower-exclusive, upper-inclusive bins in
    src/neighbour_list.hpp. Distinct exactly coincident fish are excluded by
    that native branch, so this mask excludes them too. No separation claim
    applies to coincidence or a cancelling sum of separation directions.
    """
    base = external_cues(positions, config, threat_positions)
    x = np.asarray(positions, dtype=float)
    count = len(x)
    distance_squared = np.sum((x[:, None, :] - x[None, :, :])**2, axis=2)
    repulsion = np.any((distance_squared > 0.) &
                       (distance_squared <= config.repulsion_radius**2), axis=1)
    w = base.threat_strength
    active = w > 0.
    caps = np.full(count, float(config.external_cap))
    caps[active] = 3.
    caps[active & repulsion] = min(float(config.external_cap), .8)
    if np.any(active):
        stronger = external_cues(positions, replace(config, threat_gain=3.), threat_positions)
        threat, raw = base.threat.copy(), base.raw.copy()
        combined, capped = base.combined.copy(), base.capped.copy()
        threat[active], raw[active] = stronger.threat[active], stronger.raw[active]
        magnitude = np.linalg.norm(raw[active], axis=1)
        scale = np.ones(len(magnitude))
        capped[active] = magnitude > caps[active]
        np.divide(caps[active], magnitude, out=scale, where=magnitude > caps[active])
        combined[active] = raw[active] * scale[:, None]
        base = replace(base, threat=threat, raw=raw, combined=combined, capped=capped)
    return ReactiveControls(base, 1.-.75*w, 1.-.5*w, 1.+3.*w, repulsion, caps)


class ReactiveSchool(TravellingSchool):
    """Drop-in school API for an explicitly selected research response variant.

    config remains the baseline ScenarioConfig. last_response describes the
    controls for the latest step, or is None after construction/load_state.
    step returns the usual CueFields. No experiment runner selects this class
    automatically, and no baseline/native source is modified.
    """

    def load_state(self, state):
        super().load_state(state)
        self.last_response = None

    def _build_controls(self, positions, threat_positions=None) -> ReactiveControls:
        """Default-preserving hook for explicitly selected research profiles."""
        return reactive_controls(positions, self.config, threat_positions)

    def step(self, threat_positions=None) -> CueFields:
        controls = self._build_controls(self.positions, threat_positions)
        if not np.any(controls.fields.threat_strength > 0.):
            fields = super().step(threat_positions)
            self.last_response = replace(controls, fields=fields)
            return fields
        fields = controls.fields
        self._school.reset_controls()
        gains = np.linalg.norm(fields.combined, axis=1)
        for i in np.flatnonzero((gains > 0.) | (controls.turning != 1.)):
            self._school.set_agent_control(int(i), float(controls.alignment[i]),
                float(controls.attraction[i]), float(controls.turning[i]),
                fields.combined[i].tolist(), float(gains[i]))
        self._school.move()
        # Same explicit surface fallback as TravellingSchool.step. Reflection
        # may exceed the ordinary turn bound; report stable IDs for path splits.
        x = self.positions
        reflected = x[:, 2] > self.config.surface_z
        self.last_reflected_ids = self._ids[reflected].copy()
        if np.any(reflected):
            h = self.directions
            x[reflected, 2] = 2*self.config.surface_z-x[reflected, 2]
            h[reflected, 2] *= -1
            self._school.load_positions(x.T)
            self._school.load_velocities(h.T)
            self.surface_reflections += int(reflected.sum())
        self.time += self.config.dt
        self.step_index += 1
        self.last_response = controls
        return fields
