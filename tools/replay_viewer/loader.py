"""Load declared, sealed saved encounters using NumPy; never import a simulator."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import numpy as np
from .display import _display, _metrics, normalize_events
from .metrics import case_summary, compare_runs, partner_references
ROOT = Path(__file__).resolve().parents[2]
ALLOWED_STUDIES = ("pilot_regime_sweep_2026-11-09_v2", "high_count_regime_extension_2026-11-09")


def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def event_rows(path):
    with gzip.open(path, "rt") as stream:
        return [json.loads(line) for line in stream if line.strip()]

def validate_source(directory):
    """Check the exact consumed files against the source's completion seal."""
    directory = Path(directory)
    completion, audit, summary, config = (read(directory / name) for name in
        ("completion.json", "audit.json", "summary.json", "config.json"))
    if completion["status"] != "complete" or audit["status"] != "passed" or summary["status"] != "complete":
        raise ValueError("Only complete, audited current runs are admitted: " + directory.name)
    if config["study"] not in ALLOWED_STUDIES:
        raise ValueError("Source belongs to an undeclared experiment")
    if config["geometry"] != "point" or config["capture_probability"] != .7:
        raise ValueError("Current point-contact/p=.7 model identity differs")
    files = ("config.json", "horizons.json", "summary.json", "trajectories.npz",
             "events.jsonl.gz", "school_metrics.json", "initial_shared.json")
    checked = {}
    for name in files:
        actual = sha(directory / name)
        if actual != completion["files"][name]:
            raise ValueError("Consumed saved artifact differs from its seal: " + name)
        checked[name] = actual
    return config, summary, checked

def metadata(directory, *, signature):
    directory = Path(directory)
    config, recorded, consumed = validate_source(directory)
    summary = case_summary(config, read(directory / "horizons.json"), 36.,
                           case_id=directory.name, source_signature=signature)
    h, g, d = config["herding_minimum_T"], config["gannets"], config["dolphins"]
    label = (f"H{h:g}T · {g} gannets · dolphins + gannets" if d and g else
             f"H{h:g}T · dolphins only" if d else f"{g} gannets only")
    return dict(id=directory.name, label=label, study=config["study"], school_seed=config["school_seed"],
        herd_duration_T=h if d else None, gannet_count=g, dolphin_count=d,
        presence=config["presence"], condition=config["presence"],
        policy="herd_strike", status="complete", duration=36., cadence=.1,
        dt=config["dt"], capture_seed=config["capture_seed"],
        data_file=f"data/{directory.name}.js", summary=summary,
        variables=summary["variables"], source=str(directory),
        consumed_source_sha256=consumed)

def load_case(directory, meta=None):
    directory = Path(directory)
    config, recorded, _ = validate_source(directory)
    with np.load(directory / "trajectories.npz", allow_pickle=False) as data:
        arrays = {key: data[key].copy() for key in data.files}
    times = arrays["time"].astype(float)
    x = arrays["positions"].astype(float)
    directions = arrays["directions"].astype(float)
    alive = arrays["alive"].astype(bool)
    if x.shape != directions.shape or x.shape[:2] != alive.shape:
        raise ValueError("Trajectory/heading/alive shapes differ")
    if len(times) != 361 or abs(times[0]) > 1e-9 or abs(times[-1]-36.) > 1e-7 or np.any(np.diff(times) <= 0):
        raise ValueError("Expected 361 elapsed frames over the full 36T encounter")
    if not alive[0].all() or np.any(alive[1:] & ~alive[:-1]):
        raise ValueError("Prey resurrect or initial school is incomplete")
    # This recorder keeps finite coordinates after consumption. The explicit
    # alive mask, not NaN detection, defines displayed prey and all counters.
    x[~alive] = np.nan
    directions[~alive] = np.nan
    actor_ids = arrays["actor_ids"].astype(str).tolist()
    prey_ids = arrays["prey_ids"].astype(int).tolist()
    initial = read(directory / "initial_shared.json")
    origin = float(initial["actors"][0]["time"])
    raw_events = event_rows(directory / "events.jsonl.gz")
    for event in raw_events:
        clock = event.get("contact", {}).get("time", event["time"] if "time" in event else None)
        if clock is not None and "elapsed" in event and abs(clock-origin-event["elapsed"]) > 1e-8:
            raise ValueError("Event absolute/elapsed clocks disagree")
    captures, contacts, events = normalize_events(raw_events, times, origin, actor_ids, prey_ids, alive)
    for event in events:
        event["display_time"] = float(times[event["frame_index"]])
    oral = {(r["actor_id"], r["bout_id"], r["prey_id"], r["contact"]["time"]-origin): r
            for r in raw_events if r["kind"] == "oral"}
    for contact in contacts:
        row = oral[(contact["actor_id"], contact["bout_id"], contact["prey_id"], contact["time"])]
        contact.update(mouth_position=row["contact"]["mouth_position"],
                       heading=row["contact"]["heading"], draw=row.get("draw"))
    counts = {actor: sum(c["actor_id"] == actor for c in captures) for actor in actor_ids}
    for actor in actor_ids:
        if counts[actor] != recorded["per_actor"][actor]["captures"]:
            raise ValueError("Per-predator food differs from exact capture events")
    if len(captures) != int(alive[0].sum()-alive[-1].sum()):
        raise ValueError("Saved survivors do not conserve consumption")
    records = read(directory / "school_metrics.json")
    if len(records) != len(times):
        raise ValueError("School diagnostic and trajectory cadences differ")
    for i, record in enumerate(records):
        if abs(record["elapsed"]-times[i]) > 1e-8 or record["n_live"] != int(alive[i].sum()):
            raise ValueError("School diagnostic clocks or surviving counts differ")
    targets = arrays["target_ids"].astype(object)
    targets[arrays["target_ids"] < 0] = None
    phases = arrays["dolphin_phases"].astype(object)
    phases[np.isin(arrays["dolphin_phases"], ("not_dolphin", "", "none", "None"))] = None
    info = dict(meta or {}, id=directory.name, source=str(directory),
        label=meta["label"] if meta else directory.name, school_seed=config["school_seed"],
        condition=config["presence"], policy="herd_strike", duration=36., dt=config["dt"],
        cadence=.1, prey_ids=prey_ids, actor_ids=actor_ids,
        actor_species=[a[0] for a in actor_ids], times=times,
        positions=x, directions=directions, predators=arrays["predator_positions"],
        modes=arrays["predator_modes"], targets=targets, phases=phases,
        intents=[[None]*len(actor_ids) for _ in times],
        metrics=_metrics(x, times, records=records),
        captures=captures, contacts=contacts, events=events, final_counts=counts,
        initial_count=int(alive[0].sum()), final_count=int(alive[-1].sum()),
        body_radii=None, state_method="Actual 0.1T positions, headings, alive masks, physical modes, targets and controller phases",
        note="Point-contact model; continuous local proximity for H then one exposed-prey strike. No coupling scheduler.")
    # Coordinates are a five-decimal visual copy. Exact event clocks and
    # contact observations remain full precision, separate from sampled paths.
    payload = _display(info)
    payload["captures"], payload["contacts"], payload["events"] = captures, contacts, events
    # Only visual coordinates/headings are rounded. Do not double-round saved
    # final rates or comparison metadata when a lazy asset replaces its stub.
    if meta:
        for key in ("summary", "variables", "matched_controls", "partners"):
            if key in meta:
                payload[key] = meta[key]
    return payload


def build_catalog(root=ROOT):
    """Use the declared 108-case bank, not every archived folder on disk."""
    root = Path(root).resolve()
    manifest_path = root / "DATASET_2026-11-09_high_counts.json"
    manifest = read(manifest_path)
    selected = [row for row in manifest["cases"] if row["study"] in ALLOWED_STUDIES]
    counts = Counter(row["study"] for row in selected)
    if counts != {ALLOWED_STUDIES[0]: 60, ALLOWED_STUDIES[1]: 48}:
        raise ValueError("Expected the declared 60-case regime bank plus 48 higher-count cases")
    if len({row["case"] for row in selected}) != 108:
        raise ValueError("Declared case identifiers are not unique")
    signatures = {}
    for study in ALLOWED_STUDIES:
        signatures[study] = sha(root / "data/research" / study / "frozen_sources.json")
    scenarios = []
    for row in sorted(selected, key=lambda item: item["case"]):
        directory = (root / row["relative_path"]).resolve()
        expected = root / "data/research" / row["study"] / "results/full_36T_v1/cases" / row["case"]
        if directory != expected.resolve() or not directory.is_relative_to(root / "data"):
            raise ValueError("Declared saved-run path is outside its expected bank")
        # This is the packaged completion seal; rebased JSON is not compared
        # with an original-machine JSON hash from another repository.
        if sha(directory / "completion.json") != row["completion_sha256"]:
            raise ValueError("Packaged completion differs from the dataset declaration: " + row["case"])
        meta = metadata(directory, signature=signatures[row["study"]])
        if meta["study"] != row["study"]:
            raise ValueError("Case configuration and declared study differ")
        meta["variables"]["study"] = row["study"]
        scenarios.append(meta)
    summaries = [scenario["summary"] for scenario in scenarios]
    for scenario in scenarios:
        scenario["matched_controls"] = partner_references(scenario["summary"], summaries)
        scenario["partners"] = scenario["matched_controls"]
    comparisons = {
        a["id"] + "|" + b["id"]: compare_runs(a["summary"], b["summary"])
        for a in scenarios for b in scenarios if a["school_seed"] == b["school_seed"]
    }
    return dict(
        schema="fishsim_saved_run_viewer_v1", generated_date="2026-11-09",
        generated_at=datetime.now(timezone.utc).isoformat(),
        title="Saved 36T regime bank · H × gannet count", scenarios=scenarios,
        default_ids=["s39063501_H2_G6_DG_c61001", "s39063501_H2_G0_D_c61001"],
        default_time=0., horizon_T=36., pair_comparisons=comparisons,
        status="108 complete saved encounters; four previously observed schools",
        current_study="Declared 60-case regime bank and 48-case higher-count extension",
        pending=[], units="model units; T is not seconds",
        data_loading="On-demand local HTTP; two-run server cache and four-run browser cache",
        notes=[
            "108 declared, completed 36T encounters from four previously observed discovery schools: 60 original regime cases and 48 higher-count extension cases.",
            "H = 1, 2 or 3T. Gannet counts = 0, 1, 3, 6, 9, 12 or 18; twelve dolphins when present; 160 initial fish.",
            "Point geometry, contact probability 0.7, continuous local proximity for H followed by one exposed-prey strike; no phase-coupling scheduler.",
            "The higher-count extension is a separate declared study. Cross-study percentages remain NA in this viewer; original-bank dolphin-only controls are not silently pooled into it.",
            "Within-study mixed runs use the same-school/H dolphin-only reference where available and the same-school/count gannet-only reference. Zero reference percentages are NA.",
            "Final outcomes cover the full 36T encounter. Playback counters follow actual prey removals at the selected retained frame.",
            "The first-school higher-count pilot is already included in the declared extension and is not duplicated. Older archived pilot and held-out data are outside this viewer's scope."
        ],
        validation=[
            "All declared packaged completion seals and seven consumed-file hashes are checked before the library is served.",
            "Each loaded replay reconciles explicit alive masks with captured stable prey IDs at every retained frame, and checks per-predator totals.",
            "No simulator or native module is imported. No model run or saved data is changed.",
            "Gains use fish captured per predator per full 36T, including waiting and recovery; different-school or incompatible comparisons are disabled."
        ],
        source=dict(manifest=str(manifest_path), manifest_sha256=sha(manifest_path),
                    studies={study: dict(frozen_sources_sha256=signature) for study, signature in signatures.items()}))
