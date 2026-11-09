"""Pure summaries/comparisons for saved current-regime runs; no simulator imports.

The selected H and bird count are treatment variables, not matching failures.
Percent gains use captures per predator per nominal model time. An absent
species or a zero reference has no percentage gain, including zero versus zero.
"""
from __future__ import annotations

from copy import deepcopy
import json
import math


SPECIES = ("D", "G")
REQUIRED_CONTEXT = ("study", "school_seed", "capture_seed", "checkpoint_sha256",
                    "native_sha256", "dt", "capture_probability", "geometry",
                    "contact_model", "units", "initial_fish")
SHARED_CONFIG = ("study", "school_seed", "capture_seed", "checkpoint_sha256",
    "native_sha256", "dt", "capture_probability", "geometry", "contact_model",
    "units", "preparation_manifest_sha256", "original_declaration_sha256",
    "dolphin_policy_version", "dolphin_target_policy", "shared_gannet_policy",
    "coupling_scheduler", "cycle_rule", "target_selection",
    "exposure_neighbour_radius", "bird_observation", "bird_targeting",
    "bird_roster", "stochastic_initialization", "remove_prey", "predator_cues")


def _number(value, *, name, nonnegative=True):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(name + " must be finite numeric data")
    if nonnegative and value < 0:
        raise ValueError(name + " must be nonnegative")
    return value


def _int(value, name):
    value = _number(value, name=name)
    if int(value) != value:
        raise ValueError(name + " must be an integer")
    return int(value)


def percent_change(current, reference):
    """A percent is undefined at zero baseline; never return inf/NaN."""
    if current is None or reference is None:
        return dict(value=None, reason="metric_unavailable")
    _number(current, name="current", nonnegative=False)
    _number(reference, name="reference", nonnegative=False)
    if reference == 0:
        return dict(value=None, reason="baseline_zero")
    return dict(value=100. * (current-reference)/reference, reason=None)


def _actor_physics(config):
    values = {species: [] for species in SPECIES}
    for actor in config.get("actors", []):
        species = actor.get("state", {}).get("species", actor.get("config", {}).get("species"))
        if species not in values:
            continue
        value = dict(config=actor.get("config"), mouth=actor.get("mouth"),
                     capture_probability=actor.get("capture_probability"))
        canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        if canonical not in values[species]:
            values[species].append(canonical)
    return {key: sorted(value) for key, value in values.items()}


def case_summary(config, horizons, horizon_T=36., case_id=None, *, source_signature=None):
    """Summarize exactly one saved completed horizon, never a nearest prefix.

    source_signature is an optional caller-verified frozen-source fingerprint.
    Callers should supply it when cataloguing more than one source generation.
    """
    _number(horizon_T, name="horizon_T")
    if horizon_T <= 0:
        raise ValueError("horizon_T must be positive")
    candidates = [v for v in horizons.values()
                  if float(v.get("nominal_horizon_T", -1.)) == float(horizon_T)]
    if len(candidates) != 1:
        raise ValueError("Exactly one recorded horizon is required")
    horizon = candidates[0]
    if horizon.get("status") != "complete":
        raise ValueError("An incomplete horizon cannot supply final gain/loss")
    if horizon.get("physical_accounting_audit", {}).get("status") not in (None, "passed"):
        raise ValueError("Failed physical accounting audit")
    initial = _int(horizon["initial_count"], "initial_count")
    final = _int(horizon["final_count"], "final_count")
    species = {}
    for key in SPECIES:
        raw = horizon.get("species", {}).get(key, {})
        count = _int(raw.get("count", 0), "species count")
        captures = _int(raw.get("captures", 0), "captures")
        launches = _int(raw.get("launches", 0), "launches")
        contacts = _int(raw.get("contacts", 0), "contacts")
        if not count and any((captures, launches, contacts)):
            raise ValueError("An absent species has recorded activity")
        if config.get("counts", {}).get(key, count) != count:
            raise ValueError("Configured and recorded species counts differ")
        if captures > contacts or contacts > launches:
            raise ValueError("Capture/contact/launch counters are inconsistent")
        species[key] = dict(count=count, present=count > 0, captures=captures,
            launches=launches, contacts=contacts,
            captures_per_actor_per_T=captures/count/horizon_T if count else None,
            captures_per_actor=captures/count if count else None,
            capture_success_pct=100.*captures/launches if launches else None,
            contact_success_pct=100.*captures/contacts if contacts else None)
    if initial-final != sum(value["captures"] for value in species.values()):
        raise ValueError("Prey removals do not equal species captures")

    params = deepcopy(config.get("dolphin_policy_parameters") or {})
    params.pop("pressure_minimum", None)  # H is the declared treatment variable.
    context = {key: deepcopy(config.get(key)) for key in SHARED_CONFIG}
    d_fields = ("dolphin_policy_version", "dolphin_target_policy", "cycle_rule", "target_selection", "exposure_neighbour_radius")
    g_fields = ("shared_gannet_policy", "bird_observation", "bird_targeting", "bird_roster")
    species_context = {"D": {key: context.pop(key) for key in d_fields},
                       "G": {key: context.pop(key) for key in g_fields}}
    species_context["D"]["dolphin_parameters_except_H"] = params
    context.update(initial_fish=initial, horizon_T=float(horizon_T), source_signature=source_signature)
    missing = [key for key in REQUIRED_CONTEXT if context.get(key) is None]
    h = config.get("herding_minimum_T", config.get("minimum_herding_duration"))
    d_actor = next((a for a in config.get("actors", []) if a.get("state", {}).get("species") == "D"), None)
    g_actor = next((a for a in config.get("actors", []) if a.get("state", {}).get("species") == "G"), None)
    d_cfg, g_cfg = (a.get("config", {}) if a else {} for a in (d_actor, g_actor))
    variables = dict(H_T=h if species["D"]["present"] else None,
        dolphins=species["D"]["count"], gannets=species["G"]["count"],
        fish=initial, horizon_T=float(horizon_T), capture_probability=config.get("capture_probability"),
        dt_T=config.get("dt"), geometry=config.get("geometry"), contact_model=config.get("contact_model"),
        dolphin_policy=config.get("dolphin_policy_version") if species["D"]["present"] else None,
        dolphin_targeting=config.get("target_selection") if species["D"]["present"] else None,
        gannet_policy=config.get("shared_gannet_policy") if species["G"]["present"] else None,
        gannet_targeting=config.get("bird_targeting") if species["G"]["present"] else None,
        bird_observation=config.get("bird_observation") if species["G"]["present"] else None,
        bird_layout=config.get("bird_roster") if species["G"]["present"] else None,
        bird_count_scope=config.get("bird_count_scope") if species["G"]["present"] else None,
        coupling=config.get("coupling_scheduler"),
        dolphin_speed=d_cfg.get("speed"), dolphin_sensing_radius=d_cfg.get("sense_radius"),
        gannet_airspeed=g_cfg.get("air_speed"), gannet_waterspeed=g_cfg.get("speed"),
        gannet_detection_depth=g_cfg.get("detection_depth"),
        gannet_max_dive_depth=g_cfg.get("max_dive_depth"),
        exposure_neighbour_radius=config.get("exposure_neighbour_radius"),
        school_seed=config.get("school_seed"), capture_seed=config.get("capture_seed"),
        native_sha256=config.get("native_sha256"), checkpoint_sha256=config.get("checkpoint_sha256"),
        units=config.get("units"))
    return dict(id=case_id or config.get("case_name"), school_seed=config.get("school_seed"),
        capture_seed=config.get("capture_seed"), presence=config.get("presence"),
        policy=config.get("policy"), horizon_T=float(horizon_T), status="complete",
        final_count=final, initial_count=initial, total_captures=initial-final,
        observed_native_duration_T=horizon.get("observed_native_duration_T"),
        absorbing_continuation=bool(horizon.get("absorbing_no_food_continuation")),
        variables=variables, match_context=context, species_context=species_context, match_context_missing=missing,
        actor_physics=_actor_physics(config), species=species,
        primary_metric="captures_per_actor_per_T",
        uncertainty="Single saved encounter; descriptive gain/loss, not an independent replicate estimate")


def compare_runs(current, reference):
    """Current relative to reference; mismatched context is explicit, never pooled."""
    reasons = []
    if current.get("match_context_missing") or reference.get("match_context_missing"):
        reasons.append("missing_matching_metadata")
    current_context, reference_context = current["match_context"], reference["match_context"]
    for key in sorted(set(current_context) | set(reference_context)):
        if current_context.get(key) != reference_context.get(key):
            reasons.append(key)
    for species in SPECIES:
        if current["species"][species]["present"] and reference["species"][species]["present"]:
            if current.get("actor_physics", {}).get(species) != reference.get("actor_physics", {}).get(species):
                reasons.append(species + "_actor_physics")
            if current.get("species_context", {}).get(species) != reference.get("species_context", {}).get(species):
                reasons.append(species + "_policy_parameters")
    matched = not reasons
    effects = {}
    for key in SPECIES:
        a, b = current["species"][key], reference["species"][key]
        available = matched and a["present"] and b["present"]
        reason = None if available else ("mismatched_context" if not matched else "species_absent")
        pct = percent_change(a["captures_per_actor_per_T"], b["captures_per_actor_per_T"]) if available else dict(value=None, reason=reason)
        success_a, success_b = a["capture_success_pct"], b["capture_success_pct"]
        effects[key] = dict(available=available, reason=reason,
            current_rate=a["captures_per_actor_per_T"], reference_rate=b["captures_per_actor_per_T"],
            current_captures=a["captures"] if a["present"] else None,
            reference_captures=b["captures"] if b["present"] else None,
            rate_difference=a["captures_per_actor_per_T"]-b["captures_per_actor_per_T"] if available else None,
            rate_percent_change=pct["value"], rate_percent_reason=pct["reason"],
            capture_difference=a["captures"]-b["captures"] if available else None,
            attack_success_pp_difference=success_a-success_b if available and success_a is not None and success_b is not None else None)
    changed = [key for key in sorted(set(current["variables"]) | set(reference["variables"]))
               if current["variables"].get(key) != reference["variables"].get(key)]
    return dict(current_id=current["id"], reference_id=reference["id"], matched=matched,
        mismatch_reasons=reasons, changed_variables=changed,
        primary_metric="captures_per_actor_per_T", species=effects,
        interpretation="Descriptive same-school treatment contrast" if matched else "Side-by-side viewing only; no matched percentage comparison")


def partner_references(current, all_summaries):
    """Same H D-only / same bird-count G-only, with complete matching metadata."""
    result = {}
    for species in SPECIES:
        candidates = []
        if current["presence"] == "DG" and current["species"][species]["present"]:
            for candidate in all_summaries:
                if candidate["presence"] != species:
                    continue
                if species == "D" and candidate["variables"]["H_T"] != current["variables"]["H_T"]:
                    continue
                if candidate["species"][species]["count"] != current["species"][species]["count"]:
                    continue
                comparison = compare_runs(current, candidate)
                if comparison["matched"]:
                    candidates.append((candidate, comparison))
        if len(candidates) == 1:
            candidate, comparison = candidates[0]
            result[species] = dict(comparison["species"][species], reference_id=candidate["id"],
                comparison=comparison)
        else:
            result[species] = dict(available=False, reference_id=None,
                reason="not_a_mixed_run" if current["presence"] != "DG" else
                       "species_absent" if not current["species"][species]["present"] else
                       "ambiguous_matching_controls" if candidates else "no_matching_control",
                rate_percent_change=None, rate_difference=None)
    return result
