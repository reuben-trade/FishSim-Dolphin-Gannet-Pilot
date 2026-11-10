"""Policy-independent oral contact and chronological, single-prey ownership.

Geometry is deterministic and has no simulator imports. It adapts the stable
line/sphere and water-clipping pattern from the archived shark prototype, adding
an explicit front-of-body halfspace using BOTH actual heading endpoints.

The body and prey follow declared linear segments. The offset mouth follows the
chord between its two endpoint positions; its curved path during a turn is an
approximation. Facing uses normalized linear interpolation of actual headings,
not a desired heading or the displacement direction. Split reflection/bounce
paths and antipodal turns into valid pieces BEFORE calling this module. Endpoint
data alone cannot reveal an undisclosed bounce. Refining a turning segment can
change the mouth-chord approximation; this needs timestep sensitivity checks.

All physical windows and segments are closed, including exact boundary contact.
Supply every actor's proposals at an equal physical time in ONE resolver call.
For adjacent calls a contact may reappear at the shared endpoint: immutable
closed-bout/captured-prey state prevents another attempt or duplicate capture.
Do not introduce an actor's previously omitted boundary proposal in a later call
and expect a retrospective tie lottery. Contacts at a deadline precede timeout.

First contact with a still-available fish ends that bout, success OR miss, with
one private capture draw. A consumed fish is skipped without a draw and does not
end the bout: another candidate can still be reached. Handling/recovery, movement
after contact, timeout, native deletion and virtual-capture policy are callers'
responsibility. A returned captured ID must be removed once by the integrator.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Integral, Real
from typing import Mapping


def _real(value, name):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite and real")
    return float(value)


def _integer(value, name):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer")
    return int(value)


def _vector(value, name):
    if len(value) != 3:
        raise ValueError(f"{name} must have three coordinates")
    return tuple(_real(x, name) for x in value)


def _actor(value):
    if not isinstance(value, str) or not value:
        raise ValueError("actor_id must be a nonempty stable identifier")
    return value


def _key(value):
    if len(value) != 2:
        raise ValueError("bout key must be (actor_id, bout_id)")
    return _actor(value[0]), _integer(value[1], "bout_id")


def _dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b))


def _sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def _lerp(a, b, u):
    return tuple(x + u * (y - x) for x, y in zip(a, b))


def _unit_heading(value):
    h = _vector(value, "actual heading")
    norm = math.hypot(*h)
    if abs(norm - 1.) > 1e-8:
        raise ValueError("actual headings must be unit vectors")
    return tuple(x / norm for x in h)


@dataclass(frozen=True)
class TimeWindow:
    open: float
    close: float

    def __post_init__(self):
        opening, closing = _real(self.open, "window open"), _real(self.close, "window close")
        if opening < 0 or closing < opening:
            raise ValueError("require 0 <= window open <= close")
        object.__setattr__(self, "open", opening)
        object.__setattr__(self, "close", closing)


@dataclass(frozen=True)
class LinearSegment:
    start: float
    end: float
    before: tuple[float, float, float]
    after: tuple[float, float, float]
    contains_reflection: bool = False

    def __post_init__(self):
        start, end = _real(self.start, "start"), _real(self.end, "end")
        if start < 0 or end <= start:
            raise ValueError("require 0 <= start < end")
        if self.contains_reflection is not False:
            raise ValueError("split a reflected/nonlinear path into linear pieces first")
        object.__setattr__(self, "start", start)
        object.__setattr__(self, "end", end)
        object.__setattr__(self, "before", _vector(self.before, "before"))
        object.__setattr__(self, "after", _vector(self.after, "after"))


@dataclass(frozen=True)
class MouthGeometry:
    radius: float
    forward_offset: float
    surface_z: float

    def __post_init__(self):
        for name in ("radius", "forward_offset", "surface_z"):
            object.__setattr__(self, name, _real(getattr(self, name), name))
        if self.radius <= 0 or self.forward_offset < 0:
            raise ValueError("mouth radius must be positive and offset nonnegative")


@dataclass(frozen=True)
class Contact:
    time: float
    fraction: float  # Relative to THIS linear piece, not an enclosing integrator step.
    segment_start: float
    segment_end: float
    body_position: tuple[float, float, float]
    mouth_position: tuple[float, float, float]
    prey_position: tuple[float, float, float]
    heading: tuple[float, float, float]

    def __post_init__(self):
        for name in ("time", "fraction", "segment_start", "segment_end"):
            object.__setattr__(self, name, _real(getattr(self, name), name))
        if not 0 <= self.segment_start < self.segment_end or not 0 <= self.fraction <= 1:
            raise ValueError("invalid contact segment/fraction")
        if not self.segment_start <= self.time <= self.segment_end:
            raise ValueError("contact time lies outside its segment")
        recomposed = self.segment_start + self.fraction * (self.segment_end - self.segment_start)
        if abs(recomposed - self.time) > 8 * math.ulp(max(1., abs(self.time), abs(recomposed))):
            raise ValueError("contact fraction and physical time disagree")
        for name in ("body_position", "mouth_position", "prey_position", "heading"):
            object.__setattr__(self, name, _vector(getattr(self, name), name))
        _unit_heading(self.heading)


def _nonnegative_intervals(a, b, c, lo, hi):
    """Closed intervals where a*u²+b*u+c >= 0, with stable quadratic roots."""
    if not all(math.isfinite(x) for x in (a, b, c)):
        raise ValueError("geometry overflow; rescale coordinates")
    if a == 0:
        if b == 0:
            return [(lo, hi)] if c >= 0 else []
        root = -c / b
        pair = (max(lo, root), hi) if b > 0 else (lo, min(hi, root))
        return [pair] if pair[0] <= pair[1] else []
    disc = b * b - 4 * a * c
    if not math.isfinite(disc):
        raise ValueError("geometry overflow; rescale coordinates")
    if disc < 0:
        return [(lo, hi)] if a > 0 else []
    q = -.5 * (b + math.copysign(math.sqrt(disc), b))
    roots = (q / a, c / q) if q else (-b / (2 * a),) * 2
    first, last = sorted(roots)
    candidates = [(lo, min(hi, first)), (max(lo, last), hi)] if a > 0 else [(max(lo, first), min(hi, last))]
    return [(left, right) for left, right in candidates if left <= right]


def swept_contact(*, body: LinearSegment, prey: LinearSegment,
                  heading_before, heading_after, mouth: MouthGeometry,
                  bite_window: TimeWindow, water_window: TimeWindow):
    """Earliest oral overlap with prey in front of the interpolated body heading.

    Front means dot(prey-body, heading) >= 0: a forward hemisphere, not a fitted
    cone. Body, mouth centre AND prey centre must be at/below surface_z, also
    inside the explicit water window. Time bounds do not receive tolerances.
    """
    if not isinstance(body, LinearSegment) or not isinstance(prey, LinearSegment):
        raise TypeError("body and prey must be LinearSegment values")
    if (body.start, body.end) != (prey.start, prey.end):
        raise ValueError("split motions onto a common time segment")
    if not isinstance(mouth, MouthGeometry) or not isinstance(bite_window, TimeWindow) or not isinstance(water_window, TimeWindow):
        raise TypeError("explicit MouthGeometry and bite/water TimeWindows required")
    h0, h1 = _unit_heading(heading_before), _unit_heading(heading_after)
    if math.hypot(*(x + y for x, y in zip(h0, h1))) < 1e-8:
        raise ValueError("split an antipodal turn into smaller actual-heading segments")
    m0 = tuple(x + mouth.forward_offset * h for x, h in zip(body.before, h0))
    m1 = tuple(x + mouth.forward_offset * h for x, h in zip(body.after, h1))
    opening = max(body.start, bite_window.open, water_window.open)
    closing = min(body.end, bite_window.close, water_window.close)
    if opening > closing:
        return None
    duration = body.end - body.start
    lo, hi = (opening - body.start) / duration, (closing - body.start) / duration
    intervals = [(lo, hi)]
    relative = _sub(prey.before, m0)
    relative_delta = _sub(_sub(prey.after, m1), relative)
    facing = _sub(prey.before, body.before)
    facing_delta = _sub(_sub(prey.after, body.after), facing)
    heading_delta = _sub(h1, h0)
    conditions = [(-_dot(relative_delta, relative_delta), -2 * _dot(relative, relative_delta),
                   mouth.radius ** 2 - _dot(relative, relative)),
                  (_dot(facing_delta, heading_delta),
                   _dot(facing, heading_delta) + _dot(facing_delta, h0), _dot(facing, h0))]
    for before, after in ((body.before, body.after), (m0, m1), (prey.before, prey.after)):
        conditions.append((0., before[2] - after[2], mouth.surface_z - before[2]))
    for a, b, c in conditions:
        intervals = [piece for left, right in intervals
                     for piece in _nonnegative_intervals(a, b, c, left, right)]
        if not intervals:
            return None
    fraction = min(left for left, _ in intervals)
    when = body.start + duration * fraction
    # Preserve literal window/segment endpoint clocks for exact-boundary ties.
    for boundary in (body.start, body.end, opening, closing):
        if fraction == (boundary - body.start) / duration:
            when = boundary
            break
    when = min(closing, max(opening, when))  # Recomposition roundoff only.
    h = _lerp(h0, h1, fraction)
    norm = math.hypot(*h)
    return Contact(when, fraction, body.start, body.end,
        _lerp(body.before, body.after, fraction), _lerp(m0, m1, fraction),
        _lerp(prey.before, prey.after, fraction), tuple(x / norm for x in h))


@dataclass(frozen=True)
class ContactProposal:
    actor_id: str
    bout_id: int
    prey_id: int
    contact: Contact

    def __post_init__(self):
        _actor(self.actor_id)
        object.__setattr__(self, "bout_id", _integer(self.bout_id, "bout_id"))
        object.__setattr__(self, "prey_id", _integer(self.prey_id, "prey_id"))
        if not isinstance(self.contact, Contact):
            raise TypeError("proposal requires Contact geometry")

    @property
    def key(self):
        return self.actor_id, self.bout_id


def propose_contacts(*, actor_id, bout_id, prey_segments: Mapping[int, LinearSegment], **geometry):
    """Read-only proposals for ALL supplied stable prey IDs, with no RNG draws.

    Candidate availability/sensing is a caller decision. Supplying only one
    target prevents fallback when another actor consumes it earlier this step.
    """
    _actor(actor_id); _integer(bout_id, "bout_id")
    result = []
    for prey_id, segment in prey_segments.items():
        prey_id = _integer(prey_id, "prey_id")
        contact = swept_contact(prey=segment, **geometry)
        if contact is not None:
            result.append(ContactProposal(actor_id, bout_id, prey_id, contact))
    return tuple(sorted(result, key=lambda p: (p.contact.time, p.prey_id)))


@dataclass(frozen=True)
class Bout:
    actor_id: str
    bout_id: int
    window: TimeWindow
    capture_probability: float

    def __post_init__(self):
        _actor(self.actor_id)
        object.__setattr__(self, "bout_id", _integer(self.bout_id, "bout_id"))
        probability = _real(self.capture_probability, "capture_probability")
        if not isinstance(self.window, TimeWindow) or not 0 <= probability <= 1:
            raise ValueError("bout requires an explicit window and probability in [0,1]")
        object.__setattr__(self, "capture_probability", probability)

    @property
    def key(self):
        return self.actor_id, self.bout_id


@dataclass(frozen=True)
class OwnershipState:
    prey_ids: tuple[int, ...]
    captured_ids: frozenset[int] = frozenset()
    closed_bouts: frozenset[tuple[str, int]] = frozenset()
    time: float = 0.

    def __post_init__(self):
        ids = tuple(_integer(i, "prey_id") for i in self.prey_ids)
        captured = frozenset(_integer(i, "captured_id") for i in self.captured_ids)
        closed = frozenset(_key(key) for key in self.closed_bouts)
        when = _real(self.time, "state time")
        if len(set(ids)) != len(ids) or not captured <= set(ids) or when < 0:
            raise ValueError("state requires unique known IDs, captured subset and nonnegative time")
        object.__setattr__(self, "prey_ids", ids)
        object.__setattr__(self, "captured_ids", captured)
        object.__setattr__(self, "closed_bouts", closed)
        object.__setattr__(self, "time", when)

    @property
    def live_ids(self):
        return tuple(i for i in self.prey_ids if i not in self.captured_ids)


@dataclass(frozen=True)
class ContactOutcome:
    proposal: ContactProposal
    status: str  # captured, contact_failed, prey_unavailable, bout_closed
    draw: float | None
    closes_bout: bool


@dataclass(frozen=True)
class Resolution:
    state: OwnershipState
    outcomes: tuple[ContactOutcome, ...]
    captured_ids: tuple[int, ...]  # NEW captures, in physical resolution order.


def resolve_contacts(proposals, bouts, state: OwnershipState, *, end,
                     capture_rngs: Mapping[str, object], tie_rng):
    """Return new immutable ownership; only the explicit RNG streams mutate.

    Resolve [state.time,end] jointly. Input state/bouts/proposals are unchanged.
    Exact equal-time groups use a uniform ACTOR permutation, so an actor with
    more candidate fish gains no extra lottery tickets. Within one actor's exact
    tie use stable prey-ID order. Near times are kept chronological, not fuzzed.
    All inputs are validated before draws. A failing RNG must abort the run:
    do not retry against partially advanced streams without restoring them.
    """
    if not isinstance(state, OwnershipState):
        raise TypeError("state must be OwnershipState")
    end = _real(end, "resolution end")
    if end <= state.time:
        raise ValueError("resolution end must advance the state clock")
    proposals, bouts = tuple(proposals), tuple(bouts)
    lookup = {}
    active_actors = set()
    for bout in bouts:
        if not isinstance(bout, Bout) or bout.key in lookup:
            raise ValueError("unique Bout values required")
        lookup[bout.key] = bout
        if bout.key not in state.closed_bouts:
            if bout.actor_id in active_actors:
                raise ValueError("one unfinished bout per actor")
            active_actors.add(bout.actor_id)
    streams = []
    for actor in {b.actor_id for b in bouts}:
        if actor not in capture_rngs or not callable(getattr(capture_rngs[actor], "random", None)):
            raise ValueError(f"missing private capture RNG for {actor}")
        streams.append(capture_rngs[actor])
    if not callable(getattr(tie_rng, "permutation", None)):
        raise ValueError("tie_rng must supply permutation(n)")
    identities = [id(getattr(rng, "bit_generator", rng)) for rng in streams + [tie_rng]]
    if len(set(identities)) != len(identities):
        raise ValueError("actor capture streams and tie stream must be distinct")
    known = frozenset(state.prey_ids)
    for proposal in proposals:
        if not isinstance(proposal, ContactProposal) or proposal.key not in lookup or proposal.prey_id not in known:
            raise ValueError("proposal has unknown actor/bout/prey identity")
        when = proposal.contact.time
        window = lookup[proposal.key].window
        if not state.time <= when <= end or not window.open <= when <= window.close:
            raise ValueError("proposal lies outside resolution or bout window")
    ordered = sorted(proposals, key=lambda p: (p.contact.time, p.actor_id, p.bout_id, p.prey_id))
    captured, closed = set(state.captured_ids), set(state.closed_bouts)
    outcomes, new_ids = [], []
    index = 0
    while index < len(ordered):
        finish = index + 1
        while finish < len(ordered) and ordered[finish].contact.time == ordered[index].contact.time:
            finish += 1
        group = ordered[index:finish]
        actors = sorted({p.actor_id for p in group if p.key not in closed and p.prey_id not in captured})
        if len(actors) > 1:
            permutation = list(tie_rng.permutation(len(actors)))
            if any(isinstance(i, bool) or not isinstance(i, Integral) for i in permutation) or sorted(permutation) != list(range(len(actors))):
                raise ValueError("tie RNG returned an invalid permutation")
            actors = [actors[i] for i in permutation]
        # Inactive/unavailable-only actors have no ticket and consume no RNG.
        actors += sorted({p.actor_id for p in group} - set(actors))
        for actor in actors:
            for proposal in (p for p in group if p.actor_id == actor):
                if proposal.key in closed:
                    outcomes.append(ContactOutcome(proposal, "bout_closed", None, False))
                elif proposal.prey_id in captured:
                    outcomes.append(ContactOutcome(proposal, "prey_unavailable", None, False))
                else:
                    draw = _real(capture_rngs[actor].random(), "capture draw")
                    if not 0 <= draw < 1:
                        raise ValueError("capture RNG must return a value in [0,1)")
                    success = draw < lookup[proposal.key].capture_probability
                    closed.add(proposal.key)
                    if success:
                        captured.add(proposal.prey_id); new_ids.append(proposal.prey_id)
                    outcomes.append(ContactOutcome(proposal, "captured" if success else "contact_failed", draw, True))
        index = finish
    updated = OwnershipState(state.prey_ids, frozenset(captured), frozenset(closed), end)
    return Resolution(updated, tuple(outcomes), tuple(new_ids))
