#!/usr/bin/env python3
"""Source-free complete equal-plot-effort sensitivity for published MOVECLIM aggregates.

Reads only the committed v1.278 four-island counts (plots, taxa, plot-taxon cells),
never source observations or new species/site IDs. This is retrospective
robustness of the pre-existing v1.279 m=10 primary, not a new confirmatory test.
"""
from __future__ import annotations
import argparse
import json
from fractions import Fraction
from pathlib import Path

from azores_MOVECLIM_2013_rarefaction_bounds_v1_279 import (
    ISLANDS, bounds, report_from_freeze,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "development/azores_MOVECLIM_2013_native_plot_field_result_freeze_v1_278.json"


def _ratio(x: Fraction) -> dict:
    return {"exact": str(x), "float": float(x)}


def curve_from_freeze(data: dict) -> dict:
    # Recheck frozen source identity, plot/incidence totals, earlier m=8/m=10
    # before extending source-free sensitivity to the full common range.
    prior = report_from_freeze(data)
    by_island = data["by_island"]
    assert prior["protected_biological_rows_opened_this_run"] == 0
    m_max = min(by_island[s]["plots"] for s in ISLANDS)
    if m_max != 10:
        raise ValueError("Frozen smallest island plot denominator changed")

    curve = []
    for m in range(1, m_max+1):
        estimates = {}
        for island in ISLANDS:
            r = by_island[island]
            n = r["plots"]
            t = r["S1_affected_native_taxa"]
            p = r["S1_affected_plot_taxon_positives"]
            other_t = r["reference_native_taxa"]
            other_p = r["total_native_plot_taxon_positives"]-p
            focal_lo, focal_hi = bounds(n,t,p,m)
            other_lo, other_hi = bounds(n,other_t,other_p,m)
            ratio_lo = focal_lo/(focal_lo+other_hi)
            ratio_hi = focal_hi/(focal_hi+other_lo)
            estimates[island] = {
                "focal_richness_lower": _ratio(focal_lo),
                "focal_richness_upper": _ratio(focal_hi),
                "focal_fraction_of_expected_total_native_lower": _ratio(ratio_lo),
                "focal_fraction_of_expected_total_native_upper": _ratio(ratio_hi),
            }
        pico = estimates["Pico"]
        others = [estimates[s] for s in ISLANDS if s != "Pico"]
        other_rich_max = max(Fraction(x["focal_richness_upper"]["exact"]) for x in others)
        other_ratio_max = max(Fraction(x["focal_fraction_of_expected_total_native_upper"]["exact"]) for x in others)
        pico_rich_min = Fraction(pico["focal_richness_lower"]["exact"])
        pico_ratio_min = Fraction(pico["focal_fraction_of_expected_total_native_lower"]["exact"])
        curve.append({
            "equal_plots_m": m,
            "pico_min_focal_richness": _ratio(pico_rich_min),
            "largest_other_max_focal_richness": _ratio(other_rich_max),
            "pico_min_focal_fraction": _ratio(pico_ratio_min),
            "largest_other_max_focal_fraction": _ratio(other_ratio_max),
            "pico_richness_dominance_certified": pico_rich_min > other_rich_max,
            "pico_fraction_dominance_certified": pico_ratio_min > other_ratio_max,
        })

    # The published-source v1.279 primary and sensitivity stay immutable.
    if curve[9]["pico_min_focal_richness"]["exact"] != "8/3":
        raise AssertionError("m10 primary changed")
    if curve[7]["pico_min_focal_richness"]["exact"] != "7/3":
        raise AssertionError("m8 sensitivity changed")
    if not curve[9]["pico_fraction_dominance_certified"]:
        raise AssertionError("m10 proportional ordering changed")

    return {
        "schema": "structural.azores_MOVECLIM_complete_effort_curve.v1_280",
        "status": "RETROSPECTIVE_SOURCE_FREE_FULL_M_SENSITIVITY",
        "input": "development/azores_MOVECLIM_2013_native_plot_field_result_freeze_v1_278.json",
        "population": "58 original nonrandom native-vegetation plots across four Azorean islands",
        "m_scope": "every common integer plot subsample size from 1 to 10",
        "richness_dominance_m": [x["equal_plots_m"] for x in curve if x["pico_richness_dominance_certified"]],
        "fraction_dominance_m": [x["equal_plots_m"] for x in curve if x["pico_fraction_dominance_certified"]],
        "fraction_not_certified_m": [x["equal_plots_m"] for x in curve if not x["pico_fraction_dominance_certified"]],
        "curve": curve,
        "interpretation": "Conditional expected species-richness bounds, NOT p-values, observed subsample results, extinction risk or biological dispersal",
        "no_raw_plant_or_event_rows_reopened": True,
        "no_original_mammal_BioTIME_RLS_or_S2_S3_S4_values_reopened": True,
        "confirmatory_systems_admitted": 0,
        "GEB_scientific_HOLD": True,
        "eBird_used": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = curve_from_freeze(json.loads(args.source.read_text(encoding="utf-8")))
    content = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(content,encoding="utf-8")
    else:
        print(content, end="")


if __name__ == "__main__":
    main()
