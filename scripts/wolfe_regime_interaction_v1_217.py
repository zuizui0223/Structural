#!/usr/bin/env python3
"""Post-outcome Wolfe 2022 movement-regime audit; no mechanism inference."""
import argparse
import json
from pathlib import Path
from run_wolfe_ambiguous_row_bounds_v1_212 import load_source, LEVELS

EXPECTED_SOURCE = "e78003d425b646b390ae02e36c007892c1c70926"
CATEGORIES = ("none", "low", "high")

def cell(groups, patches, matrix, corridor):
    """Sharp finite missing binary-outcome bounds for a fixed four-vs-four arm."""
    het = groups[(patches, "heterogeneous", matrix, corridor)]
    hom = groups[(patches, "homogeneous", matrix, corridor)]
    if not (3 <= len(het) <= 4 and 3 <= len(hom) <= 4):
        raise ValueError("Incorrect replicate count")
    h = sum(x[2] for x in het)
    o = sum(x[2] for x in hom)
    if any(x[2] not in (0, 1) for x in het + hom):
        raise ValueError("Joint response must be binary")
    return {
        "heterogeneous_positive_over_observed": [h, len(het)],
        "homogeneous_positive_over_observed": [o, len(hom)],
        "observed_only_difference": h / len(het) - o / len(hom),
        "missing_lower": (h - o - (4 - len(hom))) / 4,
        "missing_upper": (h + (4 - len(het)) - o) / 4,
        "unobserved_or_unassigned_units": 8 - len(het) - len(hom),
    }

def corridor_summary(cells, patches, corridor):
    rows = [cells[(patches, mat, corridor)] for mat in CATEGORIES]
    return {
        "matrix_regimes": 3,
        "observed_only_difference": sum(r["observed_only_difference"] for r in rows) / 3,
        "missing_lower": sum(r["missing_lower"] for r in rows) / 3,
        "missing_upper": sum(r["missing_upper"] for r in rows) / 3,
        "unobserved_or_unassigned_units": sum(r["unobserved_or_unassigned_units"] for r in rows),
    }

def compute(groups):
    cells = {(n, m, c): cell(groups, n, m, c)
             for n in (4, 6) for m in CATEGORIES for c in CATEGORIES}
    summaries = {
        str(n): {c: corridor_summary(cells, n, c) for c in CATEGORIES}
        for n in (4, 6)
    }
    low = summaries["6"]["low"]
    high = summaries["6"]["high"]
    # Sharp bounds: the low/high corridor groups use disjoint microcosms.
    interaction = {
        "observed_only": low["observed_only_difference"] - high["observed_only_difference"],
        "missing_lower": low["missing_lower"] - high["missing_upper"],
        "missing_upper": low["missing_upper"] - high["missing_lower"],
    }
    overall = {}
    for n in (4, 6):
        rr = list(summaries[str(n)].values())
        overall[str(n)] = {
            "observed_only": sum(x["observed_only_difference"] for x in rr) / 3,
            "missing_lower": sum(x["missing_lower"] for x in rr) / 3,
            "missing_upper": sum(x["missing_upper"] for x in rr) / 3
        }
    if sum(c["unobserved_or_unassigned_units"] for c in cells.values()) != 5:
        raise ValueError("Frozen original five focal missing units differ")
    return {
        "schema": "structural.wolfe_movement_regime_posthoc.v1_217",
        "status": "EXPLORATORY_EXPOSED_SOURCE_ONLY_NOT_PREDECLARED",
        "original_source_blob_sha1": EXPECTED_SOURCE,
        "experiment": "Wolfe 2022 day21 Stentor AND (Didinium OR Dileptus) across independent microcosms",
        "sample_units": "microcosms, not patches or source populations",
        "stratum": "patch count x matrix transfer x corridor transfer",
        "design": "four intended replicates per cell; original ambiguous 6HoLM1 excluded",
        "regime_contrasts": summaries,
        "six_patch_local_low_minus_high_heterogeneity_interaction": interaction,
        "all_regime_contrast_reproduces_v1_212": overall,
        "cell_details": [
            {"patches": n, "matrix": m, "corridor": c, **cells[(n,m,c)]}
            for n in (4, 6) for m in CATEGORIES for c in CATEGORIES
        ],
        "all_ranges_are_missingness_bounds_not_confidence_intervals": True,
        "dispersal_effect_causal_identification_claimed": False,
        "within_patch_process_or_rescue_identified": False,
        "tested_hypothesis_preregistered": False,
        "original_mammal_heldout_or_graph_scores_opened": False,
        "eBird_used": False,
        "GEB_submission_authorized": False
    }

def run(raw):
    return compute(load_source(raw))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_csv", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    answer = run(args.source_csv.read_bytes())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(answer, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(answer, sort_keys=True))

if __name__ == "__main__":
    main()
