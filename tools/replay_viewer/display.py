"""Existing replay normalization and school diagnostics, isolated from simulator imports."""
from __future__ import annotations
import numpy as np

def _display(value):
    """Convert arrays/numpy scalars to finite, compact JSON values."""
    if isinstance(value, np.ndarray):
        return _display(value.tolist())
    if isinstance(value, (list, tuple)):
        return [_display(item) for item in value]
    if isinstance(value, dict):
        return {str(key): float(item) if key == "time" and isinstance(item, (float, np.floating))
                else _display(item) for key, item in value.items()}
    if isinstance(value, (float, np.floating)):
        return round(float(value), 5) if np.isfinite(value) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value

def _first_frame(times, clock):
    return min(int(np.searchsorted(times, clock - 1e-9, side="left")), len(times) - 1)

def normalize_events(rows, times, start_clock, actor_ids, prey_ids, alive, *, relative=False):
    """Normalize both event formats and reconcile capture IDs with saved frames."""
    contacts, events = [], []
    prey_columns = {int(identity): i for i, identity in enumerate(prey_ids)}
    for sequence, row in enumerate(rows):
        kind = row.get("kind")
        if kind in ("oral", "contact"):
            proposal = row.get("proposal", row)
            geometry = proposal.get("contact", proposal.get("geometry", {}))
            absolute_clock = float(geometry["time"])
            clock = float(row["time"]) if relative else absolute_clock - start_clock
            frame = _first_frame(times, clock)
            status = row.get("status")
            identity = int(proposal["prey_id"])
            if status == "captured":
                if identity not in prey_columns:
                    raise ValueError(f"Capture references unknown prey ID {identity}")
                disappeared = np.flatnonzero(~alive[:, prey_columns[identity]])
                if not len(disappeared):
                    raise ValueError(f"Captured prey {identity} remains alive in final replay")
                frame = int(disappeared[0])
                # A capture should be shown in the first retained post-contact
                # frame, within one native-sampling interval of its event.
                if times[frame] + 1e-8 < clock:
                    raise ValueError(f"Prey {identity} disappears before its contact")
            contacts.append(dict(time=float(clock), actor_id=str(proposal["actor_id"]),
                prey_id=identity, status=status, position=geometry.get("prey_position"),
                body_position=geometry.get("body_position"),
                frame_index=frame, display_time=float(times[frame]),
                sequence=int(row.get("sequence", sequence)), bout_id=proposal.get("bout_id")))
            events.append(dict(time=float(clock),
                kind="capture" if status == "captured" else "contact_failed" if status == "contact_failed" else "contact",
                actor_id=str(proposal["actor_id"]), prey_id=identity, target_id=identity,
                before=None, after=None, reason=status, status=status,
                position=geometry.get("prey_position"), frame_index=frame,
                sequence=int(row.get("sequence", sequence)), bout_id=proposal.get("bout_id")))
        elif kind in ("transition", "choice", "phase"):
            clock = float(row["time"]) - (0. if relative else start_clock)
            events.append(dict(time=clock, kind=kind, actor_id=str(row["actor_id"]),
                before=row.get("before"), after=row.get("after"), reason=row.get("reason"),
                target_id=row.get("target_id"), bout_id=row.get("bout_id"),
                sequence=int(row.get("sequence", sequence)),
                frame_index=_first_frame(times, clock)))
    contacts.sort(key=lambda event: (event["time"], event["sequence"]))
    events.sort(key=lambda event: (event["time"], event["sequence"]))
    captures = [event for event in contacts if event["status"] == "captured"]
    captured = [event["prey_id"] for event in captures]
    if len(set(captured)) != len(captured):
        raise ValueError("A stable prey ID was captured more than once")
    if any(event["actor_id"] not in actor_ids for event in contacts):
        raise ValueError("Contact attributed to an unknown predator")
    initial_ids = {int(prey_ids[i]) for i in np.flatnonzero(alive[0])}
    final_ids = {int(prey_ids[i]) for i in np.flatnonzero(alive[-1])}
    if initial_ids - final_ids != set(captured):
        raise ValueError("Final prey removals differ from the capture log")
    for frame in range(len(times)):
        known = {event["prey_id"] for event in captures if event["frame_index"] <= frame}
        displayed = {int(prey_ids[i]) for i in np.flatnonzero(alive[frame])}
        if displayed != initial_ids - known:
            raise ValueError(f"Frame {frame}: prey disappearance/capture count mismatch")
    return captures, contacts, events

def _metrics(positions, times, records=None, series=None):
    result = []
    keep = ("n_live", "survival_fraction", "largest_component_fraction", "r90", "rg",
            "outward_fraction", "outward_p90", "mean_depth", "centroid", "polarization", "contained")
    for i, (clock, frame) in enumerate(zip(times, positions)):
        live = np.isfinite(frame).all(axis=1)
        centre = frame[live].mean(axis=0) if live.any() else np.zeros(3)
        radii = np.linalg.norm(frame[live] - centre, axis=1)
        metric = dict(time=float(clock), n_live=int(live.sum()), centroid=centre,
            r90=float(np.quantile(radii, .9)) if len(radii) else None,
            rg=float(np.sqrt(np.mean(radii**2))) if len(radii) else None,
            mean_depth=float(-centre[2]) if live.any() else None)
        if records:
            record = records[i]
            metric.update({key: record[key] for key in keep if key in record})
        if series:
            metric.update({key: series[key][i] for key in keep if key in series})
        result.append(metric)
    return result
