"""Read-only independent checks of sealed exposed-replication case artifacts.

This review helper imports no simulator implementation and never advances a model.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def read(path):
    return json.loads(Path(path).read_text())


def records(path):
    with gzip.open(path, "rt") as handle:
        return [json.loads(line) for line in handle]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def generator(state):
    rng = np.random.default_rng(0)
    rng.bit_generator.state = deepcopy(state)
    return rng


def dolphin_projection(receipt):
    return dict(
        actors=[a for a in receipt["actors"] if a["species"] == "D"],
        actor_policy={k: v for k, v in receipt["actor_policy"].items() if k.startswith("D")},
        capture_rng={k: v for k, v in receipt["capture_rng"].items() if k.startswith("D")},
        controllers={k: v for k, v in receipt["controllers"].items() if k.startswith("D")},
        tie_rng=receipt["tie_rng"],
        ownership=receipt["ownership"],
    )


def audit_case(directory, expected_duration=36.):
    d = Path(directory).resolve()
    study = d.parents[3]
    prior = study.parent / "simple_herd_strike_pilot_2026-11-08"
    seal, summary, config = (read(d / name) for name in
                             ("completion.json", "summary.json", "config.json"))
    assert seal["status"] == summary["status"] == "complete"
    for name, digest in seal["files"].items():
        assert sha(d / name) == digest, ("file_hash", d.name, name)
    for path, digest in read(d / "source_manifest.json").items():
        assert sha(path) == digest, ("source_hash", path)
    assert (study / "gannet.py").read_bytes() == (prior / "gannet.py").read_bytes()
    assert (study / "controllers.py").read_bytes() == (prior / "controllers.py").read_bytes()
    old_manifest = read(prior / "results/full_36T_v1/cases/s39061001_exposed_DG/source_manifest.json")
    for name in ("gannet.py", "controllers.py"):
        assert sha(study / name) == old_manifest[str(prior / name)]
    prep = read(config["preparation_manifest_path"])
    assert prep["status"] == "complete" and prep["preparation_gate_passed"]
    assert sha(config["preparation_manifest_path"]) == config["preparation_manifest_sha256"]
    checkpoint = prep["checkpoints"][str(summary["school_seed"])]
    assert checkpoint["screen_status"] == "passed"
    assert sha(checkpoint["path"]) == checkpoint["sha256"] == config["checkpoint_sha256"]
    assert sha(prep["native"]["path"]) == prep["native"]["sha256"] == config["native_sha256"]
    with np.load(checkpoint["path"]) as prepared, np.load(d / "initial_school.npz") as loaded:
        assert np.array_equal(prepared["positions"], loaded["positions"])
        assert np.allclose(prepared["directions"], loaded["directions"], rtol=0, atol=1e-10)
        assert np.array_equal(prepared["prey_ids"], loaded["prey_ids"])
        assert int(loaded["step_index"]) == int(prepared["step_index"]) == 16000
        assert float(loaded["time"]) == float(prepared["time"]) and abs(float(loaded["time"])-20) < 1e-8
    assert summary["planned_duration"] == expected_duration
    assert abs(summary["actual_duration"] - expected_duration) < 1e-8
    assert summary["native_steps"] == round(expected_duration / summary["dt"])
    assert summary["dt"] == .00125 and summary["capture_probability"] == .7
    initial, final = read(d / "initial_engine.json"), read(d / "final_engine.json")
    events, cycles = records(d / "events.jsonl.gz"), records(d / "opportunities.jsonl.gz")
    oral = [e for e in events if e["kind"] == "oral"]
    physics = {}
    removed = []
    for who, policy in initial["actor_policy"].items():
        cfg, mouth = policy["config"], policy["mouth"]
        assert policy["capture_probability"] == .7
        actor_events = [e for e in events if e["kind"] == "transition" and e["actor_id"] == who]
        launches = [e for e in actor_events if e["reason"] == "launch"]
        launch_times = {e["bout_id"]: e["time"] for e in launches}
        assert len(launch_times) == len(launches)
        actor_oral = [e for e in oral if e["actor_id"] == who]
        row = summary["per_actor"][who]
        assert row["launches"] == len(launches)
        assert abs(sum(row["physical_mode_time"].values()) - expected_duration) < 1e-8
        assert abs(sum(row["time"].values()) - expected_duration) < 1e-8
        assert abs(row["exposure_time"]["water"] + row["exposure_time"]["air"] - expected_duration) < 1e-8
        rng = generator(initial["capture_rng"][who])
        closes, captures = set(), 0
        for event in actor_oral:
            c = event["contact"]
            assert c["segment_start"] - 1e-10 <= c["time"] <= c["segment_end"] + 1e-10
            assert abs(c["time"] - (c["segment_start"] + c["fraction"] *
                                   (c["segment_end"] - c["segment_start"]))) < 1e-9
            body, prey = np.asarray(c["body_position"]), np.asarray(c["prey_position"])
            mouth_position, heading = np.asarray(c["mouth_position"]), np.asarray(c["heading"])
            assert np.linalg.norm(mouth_position - prey) <= mouth["radius"] + 1e-8
            # The inherited oral model uses an endpoint mouth chord while its
            # facing direction normalizes the interpolated heading.
            chord_bound = mouth["forward_offset"] * (1 - math.cos(
                cfg["turn_rate"] * (c["segment_end"] - c["segment_start"]) / 2))
            assert np.linalg.norm(mouth_position - body - mouth["forward_offset"] * heading) <= chord_bound + 1e-9
            assert abs(np.linalg.norm(heading) - 1) < 1e-8
            assert np.dot(prey - body, heading) >= -1e-8
            assert mouth_position[2] <= cfg["surface_z"] + 1e-8 and body[2] <= cfg["surface_z"] + 1e-8
            assert launch_times[event["bout_id"]] - 1e-9 <= c["time"] <= launch_times[event["bout_id"]] + cfg["bout_duration"] + 1e-9
            if event["draw"] is None:
                assert not event["closes_bout"]
            else:
                assert event["closes_bout"] and rng.random() == event["draw"]
                assert (event["status"] == "captured") == (event["draw"] < .7)
                assert event["bout_id"] not in closes
                closes.add(event["bout_id"])
                if event["status"] == "captured":
                    captures += 1
                    removed.append(event["prey_id"])
        assert rng.bit_generator.state == final["capture_rng"][who]
        assert row["contacts"] == len(closes) and row["captures"] == captures
        initial_actor = next(a for a in initial["actors"] if a["actor_id"] == who)
        ready = initial_actor["ready_at"]
        for event in actor_events:
            if event["reason"] == "launch":
                assert event["time"] >= ready - 1e-8, ("recovery", who, event)
            elif event["reason"] == "capture":
                ready = event["time"] + cfg["handling_duration"]
            elif event["reason"] in ("contact_miss", "timeout", "target_not_visible",
                                     "ascent_depth_margin", "uncommitted_water_entry"):
                ready = event["time"] + cfg["miss_recovery_duration"]
        physics[who] = dict(launches=len(launches), contacts=len(closes), captures=captures,
                            contact_geometry="passed", recovery_readiness="passed",
                            capture_rng_replay="passed")
    assert len(removed) == len(set(removed)) == summary["initial_count"] - summary["final_count"]
    assert set(removed) == set(final["ownership"]["captured_ids"])
    with np.load(d / "initial_school.npz") as a, np.load(d / "final_school.npz") as b:
        assert set(map(int, a["prey_ids"])) - set(map(int, b["prey_ids"])) == set(removed)
        assert abs(float(b["time"]) - float(a["time"]) - expected_duration) < 1e-8
    tie, tie_records = generator(initial["tie_rng"]), read(d / "tie_stream_calls.json")
    for event in tie_records:
        assert tie.permutation(event["n"]).tolist() == event["result"]
    assert tie.bit_generator.state == final["tie_rng"]

    dolphin_launches = [e for e in events if e["kind"] == "transition" and
                       e["reason"] == "launch" and e["actor_id"].startswith("D")]
    cycle_launches = [e for e in cycles if e["kind"] == "cycle_launch"]
    key = lambda e: (e["actor_id"], e["bout_id"], e["target_id"], e["time"])
    assert len(dolphin_launches) == len(cycle_launches)
    assert {key(e) for e in dolphin_launches} == {key(e) for e in cycle_launches}
    active, counts = {}, Counter()
    for event in cycles:
        who, kind = event["actor_id"], event["kind"]
        counts[kind] += 1
        assert event["policy"] == summary["policy"]
        assert event["attempt_started"] is None and event["attempt_deadline"] is None
        if kind == "cycle_pressure_start":
            assert who not in active and event["nearest_visible_prey"] < 4.5
            assert event["pressure_started"] == event["time"]
            active[who] = event["time"]
        elif kind == "cycle_pressure_reset":
            assert active.pop(who) == event["pressure_started"]
        elif kind == "cycle_launch":
            assert active.pop(who) == event["pressure_started"]
            assert event["pressure_elapsed"] >= 2 - 1e-10
            assert abs(event["time"] - event["pressure_started"] - event["pressure_elapsed"]) < 1e-9
            assert event["feasible_count"] > 0
            if summary["policy"] == "exposed":
                assert event["selected_neighbor_count"] == event["feasible_min_neighbor_count"]
        else:
            raise AssertionError(("unknown_cycle_event", kind))
    sampled_pressure = 0
    for row in records(d / "monitor.jsonl.gz"):
        if row["cycle_pressure_started"] is not None:
            assert row["diagnostics"]["actual_proximity"]
            assert row["diagnostics"]["nearest_visible_prey"] < 4.5
            sampled_pressure += 1
    for event in records(d / "bird_events.jsonl.gz"):
        if event["kind"] == "dive_detection":
            assert event["controller_input"] is False

    birds = {}
    prior_start = read(prior / "results/full_36T_v1/cases" /
                       "s39061001_exposed_DG/initial_engine.json")
    for who in (k for k in initial["controllers"] if k.startswith("G")):
        assert initial["actor_policy"][who] == prior_start["actor_policy"][who]
        target_seed = int(np.random.SeedSequence([int(summary["school_seed"]),
            int(summary["capture_seed"]), 8111, *map(ord, who)]).generate_state(1)[0])
        assert initial["controllers"][who]["target_rng_state"] == np.random.default_rng(target_seed).bit_generator.state
        rng = generator(initial["controllers"][who]["target_rng_state"])
        weighted = fallback = 0
        for event in events:
            if event.get("reason") != "gannet_global_dense_target_selected" or event["actor_id"] != who:
                continue
            detail = event["targeting_diagnostics"]
            assert detail["selected"] and detail["target_id"] == event["target_id"]
            assert detail["target_id"] in detail["patch_ids"]
            p = detail["selection_probabilities"]
            if p:
                weights = np.asarray(detail["eligible_patch_accessible_counts"], float)
                assert np.allclose(weights / weights.sum(), p, rtol=0, atol=1e-15)
                assert int(rng.choice(len(p), p=p)) == detail["selected_patch"]
                weighted += 1
            else:
                assert detail["reason"] == "fallback_densest_accessible_neighbourhood"
                assert detail["selected_patch"] is None
                fallback += 1
        assert rng.bit_generator.state == final["controllers"][who]["target_rng_state"]
        assert final["controllers"][who]["pending"] is None
        birds[who] = dict(weighted_draws=weighted, sparse_fallbacks=fallback,
                          exact_target_rng_replay="passed", prior_capabilities_and_declared_initial_rng="passed")
    opposite = "D" if summary["presence"] == "DG" else "DG"
    counterpart = d.parent / f"s{summary['school_seed']}_{summary['policy']}_{opposite}_c{summary['capture_seed']}"
    paired = "pending_other_presence_initial_state"
    if (counterpart / "initial_engine.json").exists():
        other = read(counterpart / "initial_engine.json")
        assert dolphin_projection(initial) == dolphin_projection(other)
        with np.load(d / "initial_school.npz") as a, np.load(counterpart / "initial_school.npz") as b:
            assert a.files == b.files and all(np.array_equal(a[k], b[k]) for k in a.files)
        paired = "passed"
    return dict(case=d.name, status="passed", duration=summary["actual_duration"],
                native_steps=summary["native_steps"], species=summary["species"],
                source_and_file_hashes="passed", gannet_source_exact_copy="passed", dolphin_source_exact_copy="passed",
                preparation_provenance_and_checkpoint_loading="passed",
                matched_presence_initial_state=paired, actors=physics,
                unique_removals=len(removed), tie_rng_replay="passed", tie_calls=len(tie_records),
                cycle_counts=dict(counts), minimum_prelaunch_pressure_T=min(
                    [e["pressure_elapsed"] for e in cycle_launches], default=None),
                maximum_prelaunch_pressure_T=max(
                    [e["pressure_elapsed"] for e in cycle_launches], default=None),
                exposed_launches_at_positive_neighbor_count=sum(
                    e["selected_neighbor_count"] > 0 for e in cycle_launches)
                    if summary["policy"] == "exposed" else None,
                sampled_pressure_checks=sampled_pressure, gannets=birds,
                completion_sha256=sha(d / "completion.json"))
