#!/usr/bin/env python3
"""v1.296 source-free trail/island/group weighting and sign-consistency audit.

Reads ONLY the committed v1.295 per-trail aggregate (4 trail effects).
No original site, Event, Occurrence, plant taxon, nativeness, S1 or mammal rows
are downloaded, read or scored. A group-count-weighted average is a deliberately
NONINDEPENDENT sensitivity, never a replacement for the original primary.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FROZEN_SOURCE = "development/azores_trail_native_alien_field_aggregate_freeze_v1_295.json"
SCHEMA = "structural.azores_trail_weighting_result.v1_296"
ORIGINAL_ZIP_SHA = "c6c6ad82e268759aade344528c3649459ed323053969c1ef8053f3f518298da7"
ORIGINAL_RESULT_SHA = "7c7953ecdd012a9946006673b79a04bdd83bf5f953c084f19a451b4fa13d5bad"

def _mean(x):
    if not x:
        raise ValueError("Empty group with no independent units")
    return math.fsum(x) / len(x)

def _sign(value):
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "zero"

def calculate(freeze, protocol):
    if (protocol.get("schema") != "structural.azores_trail_aggregation_sensitivity.v1_296"
        or protocol.get("status") != "POSTHOC_SOURCE_FREE_AGGREGATION_ONLY_ORIGINAL_PRIMARY_IMMUTABLE"
        or protocol.get("source") != FROZEN_SOURCE):
        raise ValueError("v1.296 fixed source and aggregate sensitivity protocol required")
    if (freeze.get("schema") != "structural.azores_trail_native_alien_field_aggregate_freeze.v1_295"
        or freeze.get("status") != "ORIGINAL_PUBLISHED_FIELD_SOURCE_DESCRIPTIVE_SCORE_FROZEN"
        or freeze.get("source_original_zip_sha256") != ORIGINAL_ZIP_SHA
        or freeze.get("original_extracted_result_JSON_sha256") != ORIGINAL_RESULT_SHA
        or freeze.get("original_source_run_id") != 40074317603
        or freeze.get("old_v1_292_failure_remains_terminal") is not True
        or freeze.get("GEB_scientific_HOLD") is not True
        or freeze.get("confirmatory_admissions") != 0 or freeze.get("eBird") is not False):
        raise ValueError("Original published aggregate identity/scientific boundary mismatch")

    original = freeze.get("per_trail")
    if not isinstance(original, list) or len(original) != 4:
        raise ValueError("Four original trail aggregates required; cannot select subgroups")
    trails = []
    observed = set()
    for entry in original:
        island = entry.get("island")
        label = entry.get("anonymized_trail")
        identity = (island, label)
        if identity in observed or island not in ("Terceira", "São Miguel") or not label:
            raise ValueError("Unexpected or duplicate original trail label")
        observed.add(identity)
        n = entry.get("matched_area_year_groups")
        if type(n) is not int or n < 1:
            raise ValueError("Nonzero integer matched-area denominator required")
        keys = ("logratio_interior_minus_edge", "native_richness_interior_minus_edge",
                "alien_richness_interior_minus_edge")
        if any(type(entry.get(k)) not in (int, float) or not math.isfinite(entry[k]) for k in keys):
            raise ValueError("Expected finite original three response coordinates")
        log_r = float(entry[keys[0]])
        nat = float(entry[keys[1]])
        alien = float(entry[keys[2]])
        trails.append({
            "island": island,
            "anonymized_trail": label,
            "matched_area_year_groups": n,
            "log_native_alien_interior_minus_edge": log_r,
            "native_taxa_interior_minus_edge": nat,
            "alien_taxa_interior_minus_edge": alien,
            "logratio_direction": _sign(log_r),
            "native_richness_direction": _sign(nat),
            "alien_richness_direction": _sign(alien),
            "relative_native_gain_but_absolute_native_decline": log_r > 0 and nat < 0,
            "relative_native_decline_but_absolute_native_gain": log_r < 0 and nat > 0,
        })
    if set(observed) != {
        ("Terceira", "T1"), ("Terceira", "T2"), ("Terceira", "T3"),
        ("São Miguel", "T1"),
    }:
        raise ValueError("Original original four-trail denominator changed")
    if sum(x["matched_area_year_groups"] for x in trails) != 17:
        raise ValueError("Original 17 matched area-year groups changed")
    if sum(x["matched_area_year_groups"] for x in trails if x["island"] == "Terceira") != 14:
        raise ValueError("Original Terceira repeated area groups changed")
    if sum(x["matched_area_year_groups"] for x in trails if x["island"] == "São Miguel") != 3:
        raise ValueError("Original São Miguel repeated area groups changed")
    old_primary = float(freeze["original_primary_equal_trails_effect"])
    trail_equal = _mean([x["log_native_alien_interior_minus_edge"] for x in trails])
    if not math.isclose(trail_equal, old_primary, rel_tol=0, abs_tol=1e-12):
        raise ValueError("Cannot revise original equal-trail primary")
    if sum(x["logratio_direction"] == "positive" for x in trails) != freeze["original_primary_positive_trail_count"]:
        raise ValueError("Original positive trail count no longer reconciles")
    by_island = {}
    for island in ("Terceira", "São Miguel"):
        selected = [x for x in trails if x["island"] == island]
        expected = freeze["per_island"][island]
        if (len(selected) != expected["trails"]
            or sum(x["matched_area_year_groups"] for x in selected) != expected["matched_area_year_groups"]):
            raise ValueError("Original island and trail group counts no longer reconcile")
        means = _mean([x["log_native_alien_interior_minus_edge"] for x in selected])
        if not math.isclose(means, expected["mean_equal_trails_interior_minus_edge_logratio"],
                            rel_tol=0, abs_tol=1e-12):
            raise ValueError("Original island summary no longer reconciles")
        by_island[island] = {
            "independent_trails": len(selected),
            "repeated_matched_area_year_groups": sum(x["matched_area_year_groups"] for x in selected),
            "equal_trail_mean_relative_logratio": means,
            "trail_effect_range": [
                min(x["log_native_alien_interior_minus_edge"] for x in selected),
                max(x["log_native_alien_interior_minus_edge"] for x in selected),
            ],
            "positive_trails": sum(x["logratio_direction"] == "positive" for x in selected),
            "negative_trails": sum(x["logratio_direction"] == "negative" for x in selected),
        }
    island_equal = _mean([by_island[i]["equal_trail_mean_relative_logratio"]
                          for i in ("Terceira", "São Miguel")])
    groups_weighted = math.fsum(x["log_native_alien_interior_minus_edge"] *
                                x["matched_area_year_groups"] for x in trails) / 17
    methods = {
        "original_equal_independent_trails": trail_equal,
        "descriptive_equal_two_islands": island_equal,
        "nonindependent_repeated_area_group_weight": groups_weighted,
    }
    signs = {key: _sign(val) for key,val in methods.items()}
    return {
        "schema": SCHEMA,
        "status": "SOURCE_FREE_EXACT_AGGREGATION_SENSITIVITY_COMPLETE",
        "data_source": FROZEN_SOURCE,
        "original_fixed_primary_unmodified": old_primary,
        "original_primary_reproduced": trail_equal,
        "three_weighting_estimates": methods,
        "three_weighting_directions": signs,
        "repeated_groups_reverses_original_equal_trail_sign": (
            signs["nonindependent_repeated_area_group_weight"]
            != signs["original_equal_independent_trails"]
        ),
        "equal_islands_reverses_original_equal_trail_sign": (
            signs["descriptive_equal_two_islands"]
            != signs["original_equal_independent_trails"]
        ),
        "independent_trails": 4,
        "independent_islands": 2,
        "source_repeated_area_groups": 17,
        "per_island": by_island,
        "per_trail": trails,
        "whole_trail_effect_min_max": [
            min(x["log_native_alien_interior_minus_edge"] for x in trails),
            max(x["log_native_alien_interior_minus_edge"] for x in trails),
        ],
        "positive_relative_ratio_but_declining_absolute_native_trails": sum(
            x["relative_native_gain_but_absolute_native_decline"] for x in trails),
        "negative_relative_ratio_but_increasing_absolute_native_trails": sum(
            x["relative_native_decline_but_absolute_native_gain"] for x in trails),
        "positive_relative_ratio_not_sufficient_for_native_species_richness_gain": True,
        "summary_is_not_cross_island_statistical_generalization": True,
        "no_p_values_or_confidence_intervals": True,
        "group_weighted_contrast_is_nonindependent_sensitivity_NOT_primary": True,
        "no_original_2017_2019_Event_or_Occurrence_rows_reopened": True,
        "no_old_Pico_GEB_mammal_BioTIME_RLS_S2_S3_S4_responses_reopened": True,
        "not_causal_trail_intervention_or_movement_rescue": True,
        "old_v1_292_failure_terminal_unchanged": True,
        "GEB_scientific_HOLD": True,
        "new_confirmatory_admissions": 0,
        "eBird_used": False,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aggregate", type=Path, default=ROOT/FROZEN_SOURCE)
    parser.add_argument("--protocol", type=Path, default=ROOT/"development/azores_trail_weighting_sensitivity_protocol_v1_296.json")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    freeze = json.loads(args.aggregate.read_text(encoding="utf-8"))
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    result = calculate(freeze, protocol)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "three_estimates": result["three_weighting_estimates"],
        "repeated_groups_sign_reversal": result["repeated_groups_reverses_original_equal_trail_sign"],
        "native_richness_and_logratio_direction_disagreement_count": (
            result["positive_relative_ratio_but_declining_absolute_native_trails"]
            + result["negative_relative_ratio_but_increasing_absolute_native_trails"]
        ),
        "independent_trails": result["independent_trails"],
        "biological_rows_reopened": 0
    }, sort_keys=True))

if __name__ == "__main__":
    main()
