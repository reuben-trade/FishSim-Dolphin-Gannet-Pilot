"""Read-only diagnostics of saved gannet attack cessation and accessibility.

No simulator, native module, controller, target-selection RNG, or model stepping
is imported. Eligibility is reconstructed from saved live-fish/actor positions
using the frozen current controller's *new-target* depth/travel criteria. A
committed attack can retain a target that no longer passes these criteria.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np


REPO = Path(__file__).resolve().parents[2]
DEFAULT_BANK = REPO / "research/pilot_regime_sweep_2026-11-09_v2/results/full_36T_v1"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "outputs"
ACTIVE_BOUT_MODES = {"plunge", "pursuit"}
READ_FILES = ("config.json", "summary.json", "trajectories.npz", "events.jsonl.gz")
DEFINITIONS = {
    "units": "Uncalibrated model time T and model length units; not seconds/metres",
    "last_gannet_launch_T": "Last realised transition with reason launch, including aerial plunges that never enter water",
    "last_gannet_water_entry_T": "Last committed plunge-to-pursuit transition with reason water_entry; uncommitted water entry is excluded",
    "last_gannet_capture_T": "Last oral event with status captured, counted once rather than also counting its transition",
    "last_gannet_bout_end_T": "Last transition from plunge/pursuit to a non-attack mode; an unfinished final attack has no invented end",
    "no_launch_final_6T": "No realised gannet launch in the final 6T; descriptive gap, not evidence of permanent cessation",
    "no_launch_final_10T": "No realised gannet launch in the final 10T; descriptive gap, not evidence of permanent cessation",
    "accessibility": "New-target gate only: underwater live fish within sense radius and detection depth, depth <= max_dive_depth - speed/turn_rate - ascent_margin, and (horizontal distance + positive air height)/air_speed + depth/speed <= bout_duration",
    "depth_blackouts": "Sampled intervals with living fish but zero within the operative depth cap/detection depth, independent of bird distance; saved 0.1T frames held left-constant, interval boundaries uncertain by one sample",
    "all_birds_final_search": "All birds are in physical search mode in the final saved frame; does not mean deleted or intentionally abandoning prey",
    "final_shallow_but_out_of_reach": "Live fish pass the operative depth cap, but all birds have zero new-target eligibility after distance/travel checks; independent of physical bird modes",
    "terminal_evidence": "Description at the 36T observation boundary, not a prediction of what would happen in a longer simulation",
    "temporary_launch_gaps_6T": "Consecutive aggregate gannet launch times separated by >=6T, followed by a realised launch; excludes the unfinished terminal gap",
    "replication": "48 G-bearing cells: 36 mixed and 12 G-only over four previously observed schools; cells share school/control data and are not 48 independent replicates",
    "individual_scope": "160 saved bird trajectories (120 mixed, 40 G-only), not 160 independent experimental units; per-bird endpoint search differs from an entire flock losing access",
}


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(part)
    return digest.hexdigest()


def sampled_intervals(times, mask):
    """Left-constant sampled intervals; never append time beyond the horizon."""
    times = np.asarray(times, dtype=float)
    mask = np.asarray(mask, dtype=bool)
    if times.ndim != 1 or mask.shape != times.shape or len(times) < 2:
        raise ValueError("Times and mask require matching one-dimensional samples")
    if np.any(np.diff(times) <= 0):
        raise ValueError("Sample times must increase")
    result = []
    start = None
    for i in range(len(times) - 1):
        if mask[i] and start is None:
            start = float(times[i])
        if start is not None and (not mask[i] or i == len(times) - 2):
            end = float(times[i] if not mask[i] else times[i + 1])
            result.append(dict(start_T=start, end_T=end, duration_T=end - start,
                               reaches_horizon=bool(end == times[-1] and mask[-1])))
            start = None
    return result


def new_target_eligibility(fish, bird, config):
    """Reproduce deterministic geometry checks, without selecting a target."""
    fish = np.asarray(fish, dtype=float).reshape(-1, 3)
    bird = np.asarray(bird, dtype=float)
    depth = config["surface_z"] - fish[:, 2]
    depth_cap = config["max_dive_depth"] - config["speed"] / config["turn_rate"] - config["ascent_margin"]
    visible = ((depth >= 0) & (depth <= config["detection_depth"])
               & (np.linalg.norm(fish - bird, axis=1) <= config["sense_radius"]))
    shallow = visible & (depth <= depth_cap)
    horizontal = np.linalg.norm(fish[:, :2] - bird[:2], axis=1)
    travel = ((horizontal + max(0., bird[2] - config["surface_z"])) / config["air_speed"]
              + depth / config["speed"])
    eligible = shallow & (travel <= config["bout_duration"])
    return dict(visible=visible, shallow=shallow, eligible=eligible, depth=depth,
                horizontal=horizontal, travel=travel, depth_cap=depth_cap)


def event_times(events, event_type):
    if event_type == "launch":
        selected = [e for e in events if e.get("kind") == "transition" and e.get("reason") == "launch"]
    elif event_type == "water_entry":
        selected = [e for e in events if e.get("kind") == "transition" and e.get("reason") == "water_entry"
                    and e.get("before") == "plunge" and e.get("after") == "pursuit"]
    elif event_type == "capture":
        selected = [e for e in events if e.get("kind") == "oral" and e.get("status") == "captured"]
    elif event_type == "bout_end":
        selected = [e for e in events if e.get("kind") == "transition" and e.get("before") in ACTIVE_BOUT_MODES
                    and e.get("after") not in ACTIVE_BOUT_MODES]
    else:
        raise ValueError(event_type)
    return sorted(float(e["elapsed"]) for e in selected)


def last(values):
    return max(values) if len(values) else None


def analyze_case(case_dir):
    case_dir = Path(case_dir)
    config = json.loads((case_dir / "config.json").read_text())
    if not config["gannets"]:
        return None
    completion = json.loads((case_dir / "completion.json").read_text())
    summary = json.loads((case_dir / "summary.json").read_text())
    if completion["status"] != "complete" or summary["status"] != "complete":
        raise ValueError(f"Incomplete case: {case_dir.name}")
    signatures = {}
    for name in READ_FILES:
        signatures[name] = sha256(case_dir / name)
        if completion["files"].get(name) != signatures[name]:
            raise ValueError(f"Sealed output changed: {case_dir.name}/{name}")
    if config["study"] != "pilot_regime_sweep_2026-11-09_v2" or config["contact_model"] != "point" or config["capture_probability"] != .7:
        raise ValueError("Unexpected model generation")
    with gzip.open(case_dir / "events.jsonl.gz", "rt") as stream:
        events = [json.loads(line) for line in stream]
    events = [e for e in events if e.get("actor_id", "").startswith("G")]
    actor_config = {a["state"]["actor_id"]: a["config"] for a in config["actors"] if a["state"]["species"] == "G"}
    with np.load(case_dir / "trajectories.npz", allow_pickle=False) as raw:
        data = {key: raw[key] for key in raw.files}
    times = np.asarray(data["time"], dtype=float)
    horizon = float(config["duration_T"])
    if abs(times[-1] - horizon) > 1e-7 or np.any(np.diff(times) <= 0):
        raise ValueError("Incomplete or unordered saved frames")
    bird_columns = [(i, str(actor)) for i, actor in enumerate(data["actor_ids"]) if str(actor) in actor_config]
    if len(bird_columns) != config["gannets"]:
        raise ValueError("Bird roster mismatch")
    timeline = []
    for frame, time in enumerate(times):
        fish = data["positions"][frame][data["alive"][frame].astype(bool)]
        rows = []
        for column, actor in bird_columns:
            bird = data["predator_positions"][frame, column]
            check = new_target_eligibility(fish, bird, actor_config[actor])
            rows.append(dict(actor_id=actor, mode=str(data["predator_modes"][frame, column]),
                target_id=int(data["target_ids"][frame, column]),
                visible_count=int(check["visible"].sum()), depth_eligible_count=int(check["shallow"].sum()),
                accessible_count=int(check["eligible"].sum()),
                nearest_fish_horizontal_distance=float(check["horizontal"].min()) if len(fish) else None,
                centroid_distance=float(np.linalg.norm(bird - fish.mean(axis=0))) if len(fish) else None))
        first = actor_config[bird_columns[0][1]]
        depth = first["surface_z"] - fish[:, 2]
        cap = first["max_dive_depth"] - first["speed"] / first["turn_rate"] - first["ascent_margin"]
        # Independent of bird position/sense radius, unlike per-bird visibility.
        underwater = depth >= 0
        depth_eligible = underwater & (depth <= first["detection_depth"]) & (depth <= cap)
        timeline.append(dict(time_T=float(time), live_fish_count=len(fish),
            minimum_depth=float(depth.min()) if len(fish) else None,
            median_depth=float(np.median(depth)) if len(fish) else None,
            mean_depth=float(depth.mean()) if len(fish) else None,
            detection_depth_fish_count=int((underwater & (depth <= first["detection_depth"])).sum()),
            depth_eligible_fish_count=int(depth_eligible.sum()),
            any_bird_accessible=any(r["accessible_count"] > 0 for r in rows),
            all_birds_search=all(r["mode"] == "search" for r in rows), birds=rows))
    birds = []
    for index, (_, actor) in enumerate(bird_columns):
        ae = [e for e in events if e.get("actor_id") == actor]
        ending = timeline[-1]["birds"][index]
        transitions = [e for e in ae if e.get("kind") == "transition" and e.get("after") == "search" and e.get("before") != "search"]
        birds.append(dict(actor_id=actor, final_mode=ending["mode"],
            final_search_since_T=last([e["elapsed"] for e in transitions]) if ending["mode"] == "search" else None,
            last_launch_T=last(event_times(ae, "launch")), last_water_entry_T=last(event_times(ae, "water_entry")),
            last_capture_T=last(event_times(ae, "capture")), last_bout_end_T=last(event_times(ae, "bout_end")),
            captures=len(event_times(ae, "capture")), launches=len(event_times(ae, "launch")),
            no_launch_final_6T=not any(t >= horizon-6.-1e-8 for t in event_times(ae, "launch")),
            no_launch_final_10T=not any(t >= horizon-10.-1e-8 for t in event_times(ae, "launch")),
            final_visible_count=ending["visible_count"], final_depth_eligible_count=ending["depth_eligible_count"],
            final_accessible_count=ending["accessible_count"], final_centroid_distance=ending["centroid_distance"],
            final_search_no_accessible_target=ending["mode"] == "search" and ending["accessible_count"] == 0,
            final_search_shallow_but_out_of_reach=ending["mode"] == "search" and ending["accessible_count"] == 0 and ending["depth_eligible_count"] > 0,
            final_nearest_fish_horizontal_distance=ending["nearest_fish_horizontal_distance"]))
    launch = event_times(events, "launch")
    capture = event_times(events, "capture")
    if len(launch) != sum(summary["per_actor"][b["actor_id"]]["launches"] for b in birds):
        raise ValueError("Event/summary launch mismatch")
    if len(capture) != sum(summary["per_actor"][b["actor_id"]]["captures"] for b in birds):
        raise ValueError("Event/summary capture mismatch")
    all_search = all(b["final_mode"] == "search" for b in birds)
    all_no_target = all(b["final_accessible_count"] == 0 for b in birds)
    end = timeline[-1]
    shallow_far = end["depth_eligible_fish_count"] > 0 and all_no_target
    if not end["live_fish_count"]:
        evidence = "no_live_prey_at_horizon"
    elif all_search and all_no_target:
        evidence = "all_search_shallow_fish_beyond_travel_gate" if shallow_far else "all_search_fish_beyond_depth_cap"
    elif all_search:
        evidence = "all_search_some_new_targets_eligible"
    elif any(b["final_mode"] in ACTIVE_BOUT_MODES for b in birds):
        evidence = "attack_in_progress_at_horizon"
    elif any(b["final_mode"] == "orient" for b in birds):
        evidence = "orienting_at_horizon"
    else:
        evidence = "returning_or_recovering_at_horizon"
    blackouts = sampled_intervals(times, [v["live_fish_count"] > 0 and not v["depth_eligible_fish_count"] for v in timeline])
    inaccessible = sampled_intervals(times, [v["live_fish_count"] > 0 and not v["any_bird_accessible"] for v in timeline])
    final_inaccessible_since = next((v["start_T"] for v in inaccessible if v["reaches_horizon"]), None)
    temporary = [dict(previous_launch_T=a, resumed_launch_T=b, gap_T=b-a)
                 for a, b in zip(launch[:-1], launch[1:]) if b-a >= 6.-1e-8]
    result = dict(id=case_dir.name, presence=config["presence"], H_T=config["herding_minimum_T"],
        gannets=config["gannets"], dolphins=config["dolphins"], school_seed=config["school_seed"],
        capture_seed=config["capture_seed"], horizon_T=horizon, gannet_launches=len(launch), gannet_captures=len(capture),
        last_gannet_launch_T=last(launch), last_gannet_water_entry_T=last(event_times(events, "water_entry")),
        last_gannet_capture_T=last(capture), last_gannet_bout_end_T=last(event_times(events, "bout_end")),
        no_launch_final_6T=not any(t >= horizon-6.-1e-8 for t in launch),
        no_launch_final_10T=not any(t >= horizon-10.-1e-8 for t in launch),
        terminal_launch_gap_T=horizon-last(launch) if launch else horizon,
        all_birds_final_search=all_search, all_birds_final_no_accessible_targets=all_no_target,
        all_birds_final_search_since_T=max(b["final_search_since_T"] for b in birds) if all_search and all(b["final_search_since_T"] is not None for b in birds) else None,
        final_inaccessible_since_T=final_inaccessible_since,
        final_shallow_but_out_of_reach=shallow_far, terminal_evidence=evidence,
        final_live_fish_count=end["live_fish_count"], final_depth_eligible_fish_count=end["depth_eligible_fish_count"],
        final_detection_depth_fish_count=end["detection_depth_fish_count"],
        final_median_fish_depth=end["median_depth"], effective_target_depth_cap=cap,
        detection_depth=first["detection_depth"], sense_radius=first["sense_radius"],
        depth_blackouts=blackouts, depth_blackout_total_sampled_T=sum(v["duration_T"] for v in blackouts),
        depth_blackout_longest_sampled_T=max([v["duration_T"] for v in blackouts], default=0.),
        no_accessible_target_intervals=inaccessible, temporary_launch_gaps_6T=temporary,
        birds=birds, timeline=timeline, launch_times_T=launch,
        committed_water_entry_times_T=event_times(events, "water_entry"), capture_times_T=capture,
        source=dict(case_path=str(case_dir.resolve()), completion_sha256=sha256(case_dir / "completion.json"), files=signatures))
    return result


def cohort_summary(label, cases):
    flags = ("no_launch_final_6T", "no_launch_final_10T", "all_birds_final_search",
             "all_birds_final_no_accessible_targets", "final_shallow_but_out_of_reach")
    birds = [dict(case_id=case["id"], **bird) for case in cases for bird in case["birds"]]
    individual_flags = ("no_launch_final_6T", "no_launch_final_10T", "final_search_no_accessible_target",
                        "final_search_shallow_but_out_of_reach")
    return dict(label=label, count=len(cases),
        **{flag: dict(count=sum(c[flag] for c in cases), denominator=len(cases),
                       cases=[c["id"] for c in cases if c[flag]]) for flag in flags},
        terminal_evidence={key: dict(count=sum(c["terminal_evidence"] == key for c in cases), denominator=len(cases),
                                    cases=[c["id"] for c in cases if c["terminal_evidence"] == key])
                           for key in sorted({c["terminal_evidence"] for c in cases})},
        cases_with_temporary_gap_6T=[c["id"] for c in cases if c["temporary_launch_gaps_6T"]],
        individual_birds=dict(count=len(birds), final_mode_counts={mode: sum(b["final_mode"] == mode for b in birds)
                             for mode in sorted({b["final_mode"] for b in birds})},
            **{flag: dict(count=sum(b[flag] for b in birds), denominator=len(birds),
                          bird_ids=[dict(case_id=b["case_id"], actor_id=b["actor_id"]) for b in birds if b[flag]])
               for flag in individual_flags}))


def analyze_bank(bank_root=DEFAULT_BANK):
    bank_root = Path(bank_root)
    case_dirs = sorted((bank_root / "cases").glob("s*"))
    cases = [result for path in case_dirs if (result := analyze_case(path)) is not None]
    inventory = dict(total_saved_cases=len(case_dirs), gannet_cases=len(cases),
        mixed_cases=sum(c["presence"] == "DG" for c in cases), gannet_only_cases=sum(c["presence"] == "G" for c in cases),
        school_seeds=sorted({c["school_seed"] for c in cases}))
    if inventory != dict(total_saved_cases=60, gannet_cases=48, mixed_cases=36, gannet_only_cases=12,
                         school_seeds=[39061001, 39061002, 39063501, 39063502]):
        raise ValueError(f"Unexpected current bank inventory: {inventory}")
    cohorts = [cohort_summary("all_G_bearing", cases)]
    for presence in ("DG", "G"):
        selected = [c for c in cases if c["presence"] == presence]
        cohorts.append(cohort_summary(presence, selected))
        for count in (1, 3, 6):
            cohorts.append(cohort_summary(f"{presence}_G{count}", [c for c in selected if c["gannets"] == count]))
    for h in (1, 2, 3):
        selected = [c for c in cases if c["presence"] == "DG" and c["H_T"] == h]
        cohorts.append(cohort_summary(f"DG_H{h}", selected))
        for count in (1, 3, 6):
            cohorts.append(cohort_summary(f"DG_H{h}_G{count}", [c for c in selected if c["gannets"] == count]))
    return dict(schema_version=1, analysis="saved_current_regime_gannet_cessation_diagnostic",
                bank_path=str(bank_root.resolve()), definitions=DEFINITIONS, inventory=inventory,
                cohorts=cohorts, cases=cases)


def write_outputs(result, output=DEFAULT_OUTPUT):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    # Compact rich per-frame JSON; human-readable per-case/bird tables are CSV.
    (output / "cessation_summary.json").write_text(json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n")
    fields = [key for key, value in result["cases"][0].items() if not isinstance(value, (list, dict))]
    with (output / "cessation_summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in fields} for row in result["cases"])
    bird_fields = ["case_id", *result["cases"][0]["birds"][0]]
    with (output / "bird_details.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=bird_fields)
        writer.writeheader()
        writer.writerows(dict(case_id=case["id"], **bird) for case in result["cases"] for bird in case["birds"])
    sample_fields = ["case_id", *[key for key in result["cases"][0]["timeline"][0] if key != "birds"]]
    with (output / "sampled_accessibility.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=sample_fields)
        writer.writeheader()
        writer.writerows(dict(case_id=case["id"], **{key: value for key, value in row.items() if key != "birds"})
                         for case in result["cases"] for row in case["timeline"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = analyze_bank(args.bank)
    write_outputs(result, args.output)
    print(json.dumps(dict(inventory=result["inventory"], cohorts=[{key: value for key, value in c.items()
        if key in ("label", "count", "no_launch_final_6T", "no_launch_final_10T", "terminal_evidence")} for c in result["cohorts"][:3]]), indent=2))
