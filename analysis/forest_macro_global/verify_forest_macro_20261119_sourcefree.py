#!/usr/bin/env python3
"""Frozen, aggregate-only forest macro evidence arithmetic; NO biological source read.

This is not a meta-analysis, new holdout, replication, causal model, or ecological
effect estimate. Different original endpoint units may not be pooled.
"""
from __future__ import annotations
import argparse
import json
from math import isclose
from pathlib import Path


def eq(x, y, tol=1e-9):
    assert isclose(x, y, rel_tol=0.0, abs_tol=tol), (x, y)


def audit():
    biome = {
        "tropical_moist_broadleaf": (34, 31, 0.1028),
        "temperate_broadleaf_mixed": (5, 5, 0.0361),
    }
    assert sum(n for n, _, _ in biome.values()) == 39
    assert sum(k for _, k, _ in biome.values()) == 36
    rounded_mean = sum(n * value for n, _, value in biome.values()) / 39
    eq(rounded_mean, 0.0942, 0.0001)
    assert len(biome) == 2 and 0 < 0.0638 < 0.1253

    finland_site = 0.00574894 - 0.00556866
    finland_site_pct = 100 * finland_site / 0.00574894
    eq(finland_site_pct, 3.13588, 0.001)
    assert finland_site < 0.00024237  # different source weighting

    chiu = 0.434242622 - 0.414542730
    eq(chiu, 0.019699892)
    eq(2/64, 0.03125)

    slovakia = (-0.0010298147336054403 - 0.001106051007922542) / 2
    eq(slovakia, -0.001067932870763991, 1e-15)
    eq(29386 / 262144, 0.11209869384765625, 1e-15)
    assert -0.0022770806 < 0 < 0.0000944958

    sweden_cti = 0.008523818686 - 0.008726307245
    sweden_rich = 0.0415338578067 - 0.0412326375028
    eq(sweden_cti, -0.000202488559)
    eq(sweden_rich, 0.00030122030388, 1e-11)
    eq(44 / 64, 0.6875)
    eq(50 / 64, 0.78125)
    assert -0.001458379128 < 0 < 0.000927678796
    assert -0.0014672219 < 0 < 0.0020696625

    eq(2 / (2**7), 0.015625)  # BALA seven-island signflip lower bound
    thai_capture_pct = 100 * (899 - 723) / 723
    eq(thai_capture_pct, 24.34301521438451, 1e-10)

    ontology = {
        "predicts": "within_study_reference_relative_simpson",
        "bala": "within_site_temporal_sorensen_excess",
        "thai": "paired_capture_count",
        "burner": "host_tree_label_null_sqrt_jsd",
        "finland": "host_tree_three_guild_hellinger_squared",
        "chiu": "species_mixture_hellinger_squared",
        "slovakia": "weiss_larval_guild_hellinger_squared",
        "sweden_cti": "community_temperature_index_mse",
        "sweden_richness": "source_log_richness_mse",
        "neon": "static_canopy_height_diff_simpson_slope",
    }
    assert len(ontology) == len(set(ontology.values()))
    lineage = {
        "burner": "Burner_three_country",
        "finland": "Burner_three_country",
        "sweden_cti": "Gossmann_six_region",
        "sweden_richness": "Gossmann_six_region",
    }
    assert lineage["burner"] == lineage["finland"]
    assert lineage["sweden_cti"] == lineage["sweden_richness"]

    return {
        "schema": "structural.forest_macro_20261119_sourcefree_arithmetic.v1",
        "status": "PASS_FROZEN_AGGREGATE_ARITHMETIC_AND_NO_POOL_FIREWALL",
        "original_biological_source_rows_opened": 0,
        "new_models_fitted": 0,
        "new_independent_transfer_tests": 0,
        "not_meta_analysis": True,
        "not_universal_resource_mechanism": True,
        "endpoints_are_distinct": ontology,
        "same_original_source_not_independent": lineage,
        "recomputed": {
            "PREDICTS_studies": 39,
            "PREDICTS_positive_studies": 36,
            "PREDICTS_supported_biomes": len(biome),
            "PREDICTS_mean_from_rounded_biome_values": rounded_mean,
            "Finland_site_equal_delta_not_primary": finland_site,
            "Finland_site_equal_percent": finland_site_pct,
            "Finland_primary_grid_equal_delta_DISTINCT": 0.00024237,
            "Chiu_original_six_plot_delta": chiu,
            "Slovakia_forest_type_equal_delta": slovakia,
            "Slovakia_exact_conditional_p": 29386/262144,
            "Sweden_CTI_delta": sweden_cti,
            "Sweden_richness_delta": sweden_rich,
            "BALA_seven_island_exact_signflip_lower_bound": 2/(2**7),
            "Thai_canopy_excess_capture_percent": thai_capture_pct,
        },
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    result = audit()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                            encoding="utf-8")
    print(result["status"])
    print("NO_ORIGINAL_BIOLOGY_REOPENED; NO_NEW_MODEL_OR_CROSS_REGION_REPLICATION")


if __name__ == "__main__":
    main()
