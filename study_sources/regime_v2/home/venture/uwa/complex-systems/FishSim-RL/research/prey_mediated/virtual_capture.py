"""Geometric availability locks for the no-removal formation diagnostic.

After a successful virtual capture, retain the resolver's captured ID as a lock
and impose the predator's ordinary handling. At each NEXT step boundary, call
release_virtual_locks with all current prey and predator poses before proposing
contacts. A lock persists while the prey overlaps any underwater oral sphere,
including the mouth of a recovering or otherwise inactive predator. Facing and
bite eligibility do not release a lock. Misses close a bout but create no lock.

This does not model food, remove prey, move bodies, change timers or draw RNGs.
Closed bout identities are preserved permanently. Real captures continue using
contacts.OwnershipState without this adapter.

Release is deliberately conservative at sampled step boundaries. It can miss a
brief exit and re-entry within a step, and can delay release by up to one step
after a lasting separation. There is no arbitrary cooldown. Integration must
log virtual lock durations and test timestep sensitivity. Use actual corrected
post-contact poses, including bodies holding during the remainder of a step;
the uncorrected full-step movement proposal is not an actual mouth position.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real

from .contacts import MouthGeometry, OwnershipState


def _vector(value, name):
    try:
        coordinates = tuple(value)
    except TypeError as error:
        raise ValueError(f"{name} must be a finite 3-vector") from error
    if len(coordinates) != 3 or any(
        isinstance(x, bool) or not isinstance(x, Real) or not math.isfinite(x)
        for x in coordinates
    ):
        raise ValueError(f"{name} must be a finite 3-vector")
    return tuple(float(x) for x in coordinates)


def _prey_id(value):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
        raise ValueError("prey IDs must be nonnegative integers")
    return int(value)


@dataclass(frozen=True)
class MouthPose:
    """One actual body/heading pose, with no readiness or facing filter."""

    actor_id: str
    body_position: tuple[float, float, float]
    heading: tuple[float, float, float]
    mouth: MouthGeometry

    def __post_init__(self):
        if not isinstance(self.actor_id, str) or not self.actor_id:
            raise ValueError("actor_id must be a nonempty stable identifier")
        if not isinstance(self.mouth, MouthGeometry):
            raise TypeError("mouth must be MouthGeometry")
        body = _vector(self.body_position, "body_position")
        heading = _vector(self.heading, "heading")
        if abs(math.hypot(*heading)-1.) > 1e-8:
            raise ValueError("actual heading must be unit length")
        centre = tuple(x+self.mouth.forward_offset*h for x, h in zip(body, heading))
        if not all(math.isfinite(x) for x in centre):
            raise ValueError("mouth geometry overflow; rescale coordinates")
        object.__setattr__(self, "body_position", body)
        object.__setattr__(self, "heading", heading)

    @property
    def mouth_position(self):
        return tuple(x+self.mouth.forward_offset*h
                     for x, h in zip(self.body_position, self.heading))


def release_virtual_locks(ownership, *, prey_ids, prey_positions, mouths):
    """Return a new ledger after strict all-mouth clearance at the same clock.

    Supply EVERY predator currently present, even when handling, recovering,
    airborne or not allowed to bite. Missing actors cannot be inferred here.
    IDs may be in any order. All supplied IDs must be known, unique and matched
    to finite position rows; every locked ID must still be physically present.
    A subset of other known prey is permitted because it cannot affect release.

    Underwater eligibility follows contacts.py: body, mouth centre and prey
    centre must each be at or below that mouth's surface. An exactly touching
    sphere retains the lock. No direction/hemisphere test is applied.
    """
    if not isinstance(ownership, OwnershipState):
        raise TypeError("ownership must be OwnershipState")
    ids = tuple(_prey_id(value) for value in prey_ids)
    positions = tuple(_vector(value, "prey position") for value in prey_positions)
    if len(ids) != len(positions) or len(set(ids)) != len(ids):
        raise ValueError("prey IDs and position rows must match uniquely")
    known = frozenset(ownership.prey_ids)
    if not set(ids) <= known:
        raise ValueError("unknown prey ID")
    if not ownership.captured_ids <= set(ids):
        raise ValueError("every virtually locked prey ID must remain physically present")
    mouths = tuple(mouths)
    if any(not isinstance(pose, MouthPose) for pose in mouths):
        raise TypeError("mouths must contain MouthPose values")
    if len({pose.actor_id for pose in mouths}) != len(mouths):
        raise ValueError("one actual mouth pose per actor is required")

    by_id = dict(zip(ids, positions))
    retained = set()
    for prey_id in ownership.captured_ids:
        prey = by_id[prey_id]
        for pose in mouths:
            centre = pose.mouth_position
            surface = pose.mouth.surface_z
            if (pose.body_position[2] > surface or centre[2] > surface
                or prey[2] > surface):
                continue
            distance = math.dist(prey, centre)
            if not math.isfinite(distance):
                raise ValueError("mouth/prey geometry overflow; rescale coordinates")
            if distance <= pose.mouth.radius:
                retained.add(prey_id)
                break
    return OwnershipState(ownership.prey_ids, frozenset(retained),
                          ownership.closed_bouts, ownership.time)
