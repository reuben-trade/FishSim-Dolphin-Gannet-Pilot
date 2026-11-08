"""Travelling-school scenario using the existing, unchanged native Couzin model.

All quantities are model units. Environmental preferences depend on each fish's
position and a fixed route, never on a school centre. The TOTAL external vector
is capped after combining route, depth, surface and local underwater threats;
thus saturation changes their effective weights. Native Couzin adds this vector
even in its repulsion branch: a cap below one cannot reverse a unit repulsion
component, but neither that bound nor bounded turning prevents close approaches.

Noise is fixed to zero because the native global RNG state is not serializable.
Two new schools loaded from the same checkpoint replay exactly. Loading native
headings normalizes them, so a restarted run can differ from an uninterrupted
one by roundoff; ordinary stepping does not reload or renormalize native state.
Surface reflection is an explicit fallback outside the turning bound. A later
feeding integrator must account for reflected path segments when resolving a
contact in such an interval, rather than assume the endpoint chord is the path.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

import numpy as np


@dataclass(frozen=True)
class ScenarioConfig:
    n: int = 160
    dt: float = .005
    speed: float = 3.
    repulsion_radius: float = 1.
    alignment_radius: float = 3.
    attraction_radius: float = 14.
    perception_angle: float = float(3 * np.pi / 4)
    turn_rate: float = float(np.pi / 2)
    native_noise: float = 0.
    initial_shape: str = "elongated"
    elongated_semiaxes: tuple[float, float, float] = (12., 4., 3.)
    initial_centre_xy: tuple[float, float] = (0., 0.)
    initial_centre_depth: float = 6.
    initial_min_distance: float = 1.
    initial_heading_spread: float = .1
    initial_max_draws: int = 200_000
    route_direction: tuple[float, float, float] = (1., 0., 0.)
    migration_gain: float = .2
    preferred_depth: float = 5.
    depth_gain: float = .1
    depth_scale: float = 2.
    depth_deadband: float = 0.
    surface_z: float = 0.
    surface_layer: float = 3.
    surface_gain: float = .8
    external_cap: float = .8
    threat_radius: float = 4.5
    threat_gain: float = .8
    threat_turn_multiplier: float = 1.

    def __post_init__(self):
        if (isinstance(self.depth_deadband, (bool, np.bool_))
            or not isinstance(self.depth_deadband, (int, float, np.integer, np.floating))
            or not np.isfinite(self.depth_deadband) or self.depth_deadband < 0):
            raise ValueError("depth_deadband must be finite and nonnegative")
        for name in ("n", "initial_max_draws"):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("dt", "speed", "repulsion_radius", "alignment_radius", "attraction_radius",
                     "perception_angle", "turn_rate", "initial_centre_depth", "initial_min_distance",
                     "preferred_depth", "depth_scale", "surface_layer", "threat_radius"):
            value = getattr(self, name)
            if not np.isscalar(value) or not np.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        for name in ("native_noise", "initial_heading_spread", "migration_gain", "depth_gain",
                     "surface_gain", "external_cap", "threat_gain", "surface_z", "threat_turn_multiplier"):
            value = getattr(self, name)
            if not np.isscalar(value) or not np.isfinite(value):
                raise ValueError(f"{name} must be finite")
            if name != "surface_z" and value < 0:
                raise ValueError(f"{name} must be nonnegative")
        if self.native_noise != 0:
            raise ValueError("native_noise must be zero for independent replayable schools")
        if not self.repulsion_radius <= self.alignment_radius <= self.attraction_radius:
            raise ValueError("require repulsion_radius <= alignment_radius <= attraction_radius")
        if self.perception_angle > np.pi or self.initial_heading_spread > np.pi:
            raise ValueError("angles must not exceed pi")
        if self.threat_turn_multiplier < 1:
            raise ValueError("threat_turn_multiplier must be at least one")
        if self.initial_min_distance < self.repulsion_radius:
            raise ValueError("initial_min_distance must be at least repulsion_radius")
        if self.initial_shape not in ("elongated", "compact"):
            raise ValueError("initial_shape must be elongated or compact")
        axes = _vector(self.elongated_semiaxes, 3, "elongated_semiaxes")
        if np.any(axes <= 0):
            raise ValueError("elongated_semiaxes must be positive")
        centre = _vector(self.initial_centre_xy, 2, "initial_centre_xy")
        route = _vector(self.route_direction, 3, "route_direction")
        route_norm = np.linalg.norm(route)
        if route[2] != 0 or not np.isfinite(route_norm) or route_norm == 0:
            raise ValueError("route_direction must be nonzero and horizontal")
        object.__setattr__(self, "elongated_semiaxes", tuple(float(x) for x in axes))
        object.__setattr__(self, "initial_centre_xy", tuple(float(x) for x in centre))
        object.__setattr__(self, "route_direction", tuple(float(x) for x in route / route_norm))
        if self.initial_centre_depth <= self.initial_axes[2]:
            raise ValueError("initial ellipsoid must lie strictly below the surface")

    @property
    def initial_axes(self):
        """Equal volumes across compact/elongated starts; no surface clipping."""
        axes = np.asarray(self.elongated_semiaxes)
        return np.full(3, float(np.prod(axes) ** (1 / 3))) if self.initial_shape == "compact" else axes.copy()


def _vector(value, length, name):
    array = np.asarray(value, dtype=float)
    if array.shape != (length,) or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a finite vector of length {length}")
    return array


def _points(value, name):
    array = np.array(value, dtype=float, copy=True)
    if array.ndim != 2 or array.shape[1] != 3 or not np.isfinite(array).all():
        raise ValueError(f"{name} must have finite shape (N, 3)")
    return array


def _ids(value, length=None):
    array = np.asarray(value)
    if array.shape == (0,):
        array = array.astype(np.int64)
    if array.ndim != 1 or array.dtype.kind not in "iu" or np.any(array < 0):
        raise ValueError("prey IDs must be a vector of nonnegative integers")
    if len(np.unique(array)) != len(array) or (length is not None and len(array) != length):
        raise ValueError("prey IDs must be unique and match the fish count")
    if np.any(array > np.iinfo(np.int64).max):
        raise ValueError("prey IDs must fit int64")
    return np.array(array, dtype=np.int64, copy=True)


@dataclass(frozen=True)
class SchoolState:
    """Detached checkpoint, with unit heading directions rather than velocities.

    Time is retained explicitly so the same checkpoint can initialize a finer
    timestep. step_index is a diagnostic counter, not the definition of time.
    Arrays are copied and read-only; state() returns another detached copy.
    """
    positions: np.ndarray
    directions: np.ndarray
    prey_ids: np.ndarray
    time: float = 0.
    step_index: int = 0
    surface_reflections: int = 0

    def __post_init__(self):
        x = _points(self.positions, "positions")
        h = _points(self.directions, "directions")
        if h.shape != x.shape or not np.allclose(np.linalg.norm(h, axis=1), 1., rtol=0, atol=1e-8):
            raise ValueError("directions must match positions and be unit vectors")
        ids = _ids(self.prey_ids, len(x))
        if not np.isscalar(self.time) or not np.isfinite(self.time) or self.time < 0:
            raise ValueError("time must be finite and nonnegative")
        for name in ("step_index", "surface_reflections"):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        for name, array in (("positions", x), ("directions", h), ("prey_ids", ids)):
            array.flags.writeable = False
            object.__setattr__(self, name, array)


def make_initial_state(seed: int, config: ScenarioConfig) -> SchoolState:
    """Uniform-volume rejection sampling with a finite, declared attempt cap.

    Positions and headings have separate seed streams. A crowded/invalid setup
    raises openly; it never substitutes a different seed or relaxes separation.
    Compact starts use the same volume and centre depth as elongated starts.
    """
    if isinstance(seed, (bool, np.bool_)) or not isinstance(seed, (int, np.integer)) or seed < 0:
        raise ValueError("seed must be a nonnegative integer")
    rng = np.random.default_rng(np.random.SeedSequence([int(seed), 1900]))
    heading_rng = np.random.default_rng(np.random.SeedSequence([int(seed), 1901]))
    route = np.asarray(config.route_direction)
    side = np.array([-route[1], route[0], 0.])
    up = np.array([0., 0., 1.])
    basis = np.column_stack((route, side, up))
    centre = np.array([*config.initial_centre_xy, config.surface_z - config.initial_centre_depth])
    positions = np.empty((config.n, 3))
    count = 0
    for _ in range(config.initial_max_draws):
        # Cube rejection avoids a zero-vector normalization special case.
        unit_ball = rng.uniform(-1., 1., 3)
        if np.dot(unit_ball, unit_ball) > 1:
            continue
        candidate = centre + basis @ (unit_ball * config.initial_axes)
        if count and np.any(np.linalg.norm(positions[:count] - candidate, axis=1) < config.initial_min_distance):
            continue
        positions[count] = candidate
        count += 1
        if count == config.n:
            break
    if count != config.n:
        raise RuntimeError(f"initial placement failed for seed {seed}: placed {count}/{config.n} "
                           f"after {config.initial_max_draws} draws; configuration/seed not replaced")
    cosine = heading_rng.uniform(np.cos(config.initial_heading_spread), 1., config.n)
    azimuth = heading_rng.uniform(0., 2 * np.pi, config.n)
    sine = np.sqrt(np.maximum(0., 1. - cosine * cosine))
    directions = (cosine[:, None] * route + (sine * np.cos(azimuth))[:, None] * side
                  + (sine * np.sin(azimuth))[:, None] * up)
    return SchoolState(positions, directions, np.arange(config.n, dtype=np.int64))


@dataclass(frozen=True)
class CueFields:
    route: np.ndarray
    depth: np.ndarray
    surface: np.ndarray
    threat: np.ndarray
    raw: np.ndarray
    combined: np.ndarray
    capped: np.ndarray
    threat_strength: np.ndarray


def external_cues(positions, config: ScenarioConfig, threat_positions=None) -> CueFields:
    """Pure per-fish cues; only underwater threats inside threat_radius count.

    Threats are summed distance-tapered unit escape vectors. Exact co-location
    supplies zero directional escape rather than an arbitrary global direction.
    Removing threat inputs disables both their direction and turning response.
    external_cap=0 disables all external directions, not native social motion.
    A positive depth_deadband removes depth restoration inside the fixed habitat
    band preferred_depth +/- depth_deadband. Outside it, restoration increases
    continuously with distance from the nearest band edge. It is a preference,
    not a wall; the separate local surface cue is unchanged. The zero-band path
    retains the original point-depth arithmetic exactly.
    """
    x = _points(positions, "positions")
    if threat_positions is None or np.asarray(threat_positions).shape == (0,):
        p = np.empty((0, 3))
    else:
        p = _points(threat_positions, "threat_positions")
    p = p[p[:, 2] < config.surface_z]
    route = np.broadcast_to(np.asarray(config.route_direction) * config.migration_gain, x.shape).copy()
    depth = np.zeros_like(x)
    if config.depth_deadband == 0:
        depth[:, 2] = config.depth_gain * np.tanh(
            (config.surface_z - config.preferred_depth - x[:, 2]) / config.depth_scale)
    else:
        delta = config.surface_z - config.preferred_depth - x[:, 2]
        outside = np.abs(delta) > config.depth_deadband
        depth[outside, 2] = np.sign(delta[outside]) * config.depth_gain * np.tanh(
            (np.abs(delta[outside]) - config.depth_deadband) / config.depth_scale)
    surface = np.zeros_like(x)
    surface[:, 2] = -config.surface_gain * np.clip(
        1. - (config.surface_z - x[:, 2]) / config.surface_layer, 0., 1.)
    threat = np.zeros_like(x)
    strength = np.zeros(len(x))
    if len(p):
        delta = x[:, None, :] - p[None, :, :]
        distance = np.linalg.norm(delta, axis=2)
        weight = np.clip(1. - distance / config.threat_radius, 0., 1.)
        unit = np.divide(delta, distance[:, :, None], out=np.zeros_like(delta), where=distance[:, :, None] > 0)
        threat = config.threat_gain * np.sum(unit * weight[:, :, None], axis=1)
        strength = weight.max(axis=1)
    raw = route + depth + surface + threat
    magnitude = np.linalg.norm(raw, axis=1)
    capped = magnitude > config.external_cap
    scale = np.ones(len(x))
    np.divide(config.external_cap, magnitude, out=scale, where=capped)
    combined = raw * scale[:, None]
    return CueFields(route, depth, surface, threat, raw, combined, capped, strength)


def _native_school(count, config):
    # Import the installed repository extension; never compile or seed its
    # process-global generator. Constructor positions are immediately replaced.
    lib = str(Path(__file__).resolve().parents[2] / "lib")
    if lib not in sys.path:
        sys.path.insert(0, lib)
    from fish_sim import cmodel
    return cmodel.Couzin3D(n=int(count), rr=config.repulsion_radius, ro=config.alignment_radius,
        ra=config.attraction_radius, perception=config.perception_angle, noise=config.native_noise,
        speed=config.speed, turn_rate=config.turn_rate, dt=config.dt)


class TravellingSchool:
    """Native school plus explicit environment, stable IDs and detached state.

    step() returns the start-of-interval CueFields for telemetry. Arrays exposed
    by properties/state() are copies; callers cannot mutate the live simulation.
    load_state() accepts complete or depleted checkpoints, retaining their clock.
    """
    def __init__(self, config: ScenarioConfig, state: SchoolState | None = None, *, seed: int = 0):
        self.config = config
        self._school = None
        self.load_state(make_initial_state(seed, config) if state is None else state)

    def load_state(self, state: SchoolState):
        if not isinstance(state, SchoolState):
            raise TypeError("state must be a SchoolState")
        # Revalidate before touching native state: even read-only NumPy arrays
        # can deliberately be made writable by their owner.
        state = SchoolState(state.positions, state.directions, state.prey_ids,
                            state.time, state.step_index, state.surface_reflections)
        if len(state.positions) > self.config.n or np.any(state.prey_ids >= self.config.n):
            raise ValueError("checkpoint IDs/count exceed the configured initial population")
        if np.any(state.positions[:, 2] > self.config.surface_z):
            raise ValueError("checkpoint fish must be at or below the surface")
        if self._school is None or self._school.n != len(state.positions):
            self._school = _native_school(len(state.positions), self.config)
        self._school.load_positions(state.positions.T)
        self._school.load_velocities(state.directions.T)
        self._school.reset_controls()
        self._ids = state.prey_ids.copy()
        self.time = float(state.time)
        self.step_index = int(state.step_index)
        self.surface_reflections = int(state.surface_reflections)
        self.last_reflected_ids = np.empty(0, dtype=np.int64)

    @property
    def positions(self):
        return np.asarray(self._school.positions).T.copy()

    @property
    def directions(self):
        return np.asarray(self._school.velocities).T.copy()

    @property
    def velocities(self):
        return self.directions * self.config.speed

    @property
    def prey_ids(self):
        return self._ids.copy()

    @property
    def n(self):
        return len(self._ids)

    def state(self) -> SchoolState:
        return SchoolState(self.positions, self.directions, self._ids, self.time,
                           self.step_index, self.surface_reflections)

    def step(self, threat_positions=None) -> CueFields:
        fields = external_cues(self.positions, self.config, threat_positions)
        self._school.reset_controls()
        gains = np.linalg.norm(fields.combined, axis=1)
        turning = 1. + (self.config.threat_turn_multiplier - 1.) * fields.threat_strength
        for i in np.flatnonzero((gains > 0) | (turning != 1)):
            self._school.set_agent_control(int(i), 1., 1., float(turning[i]),
                                           fields.combined[i].tolist(), float(gains[i]))
        self._school.move()
        x = self.positions
        reflected = x[:, 2] > self.config.surface_z
        self.last_reflected_ids = self._ids[reflected].copy()
        if np.any(reflected):
            h = self.directions
            x[reflected, 2] = 2 * self.config.surface_z - x[reflected, 2]
            h[reflected, 2] *= -1
            self._school.load_positions(x.T)
            self._school.load_velocities(h.T)
            self.surface_reflections += int(reflected.sum())
        self.time += self.config.dt
        self.step_index += 1
        return fields

    def remove_ids(self, prey_ids):
        """Remove unique captured IDs once; reject unknown/repeated IDs openly."""
        ids = _ids(prey_ids)
        if np.any(~np.isin(ids, self._ids)):
            raise ValueError("cannot remove an absent prey ID")
        rows = np.flatnonzero(np.isin(self._ids, ids))
        survivors = np.asarray(self._school.remove_agents(rows.tolist()), dtype=np.int64)
        self._ids = self._ids[survivors]
