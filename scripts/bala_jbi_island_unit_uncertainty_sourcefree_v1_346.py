#!/usr/bin/env python3
"""BALA v1.346: original-source-free seven-island uncertainty report.

This is a retrospective, exploratory ISLAND-UNIT uncertainty audit.
Uses ONLY SHA-frozen original 2024 BALA v1.316/v1.318 island numerical
summaries and v1.344 existing field-identity validation. No taxon/plot
source reopening, no 49/56 dependent pair bootstrap, no 18 salt replicate
or synthetic "independent archipelago" test.

Mean+Student-t intervals are DESCRIPTIVE conditional on seven islands
and a seven-island symmetric sign-flip exercise is NOT confirmatory or
adjusted for multiple comparisons. Report even when zero is included.
"""
from __future__ import annotations
import argparse,itertools,json,math,statistics
from pathlib import Path

from bala_temporal_spatial_paper_sourcefree_v1_344 import (
    analyze, V316, V318, CONTRACT, ISLANDS, SHA316, SHA318, SOURCE_SHA
)

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL=ROOT/"development/bala_jbi_island_unit_uncertainty_protocol_v1_346.json"
T6_975=2.4469118511449692

def verify_science_sources(v316,v318,v344,contract):
    if (contract.get("schema")!="structural.bala_jbi_island_unit_uncertainty_audit.v1_346"
        or contract.get("status")!="FROZEN_SOURCE_FREE_EXPLORATORY_ISLAND_LEVEL_UNCERTAINTY_AFTER_V1_345_DRAFT"
        or contract["source"]["source_DwCA_sha256"]!=SOURCE_SHA
        or contract["source"]["source_v316_response_sha256"]!=SHA316
        or contract["source"]["source_v318_response_sha256"]!=SHA318
        or contract["source"]["original_independent_islands"]!=7
        or tuple(contract["source"]["island_code_order"])!=tuple(ISLANDS)
        or contract["source"]["physical_transects_in_unique_original_source"]!=29
        or contract["source"]["original_source_selected_event_ids"]!=4620):
        raise ValueError("Original BALA island-units scientific uncertainty protocol not frozen")
    old=analyze(v316,v318,v344)
    if (old["status"]!="BALA_SEVEN_ISLAND_BEETLE_HOMOGENIZATION_LOO_SOURCEFREE_VALIDATED"
        or old["original_arthropod_Event_or_Occurrence_rows_reopened"]!=0
        or not old["prior_v314_v316_v318_one_shot_source_scorers_SEALED"]
        or not old["GEB_scientific_HOLD"]
        or old["new_confirmatory_systems"]!=0 or old["eBird_used"]):
        raise ValueError("BALA original source SHA or one-shot scientific HOLD did not pass")
    return old

def island_unit_summary(values):
    if len(values)!=7 or any(not math.isfinite(v) for v in values):
        raise ValueError("Only seven finite source island values are permitted")
    mean=statistics.fmean(values)
    sd=statistics.stdev(values)
    se=sd/math.sqrt(7)
    effects=[statistics.fmean(v*direction for v,direction in zip(values,signs))
             for signs in itertools.product((-1.,1.),repeat=7)]
    assert len(effects)==128
    tail=sum(abs(v)>=abs(mean)-1e-12 for v in effects)
    return {
       "original_independent_island_contexts":7,
       "original_island_effects_in_locked_order":list(values),
       "source_islands_positive":sum(x>0 for x in values),
       "source_islands_negative":sum(x<0 for x in values),
       "source_islands_zero":sum(x==0 for x in values),
       "island_equal_mean":mean,
       "sample_standard_deviation_across_seven_islands":sd,
       "island_mean_standard_error_conditional_on_independence":se,
       "descriptive_t95_interval_conditional_on_seven_islands":[mean-T6_975*se,mean+T6_975*se],
       "t95_interval_includes_zero":mean-T6_975*se<=0<=mean+T6_975*se,
       "symmetric_sign_flip_null_permutations":128,
       "symmetric_sign_flip_two_sided_tail_count":tail,
       "symmetric_sign_flip_two_sided_p_exploratory":tail/128,
       "not_corrected_for_multiple_metrics_or_archipelago_dependence":True,
       "not_detections_corrected_occupancy":True,
    }

def analyze_uncertainty(v316,v318,v344,contract):
    old=verify_science_sources(v316,v318,v344,contract)
    data={}
    for guild in ("araneae","coleoptera"):
        r=old["source_pitfall_guilds"][guild]
        temporal=[r["source_each_island_temporal_excess_sorensen"][i] for i in ISLANDS]
        spatial=[r["source_each_island_spatial_delta_simpson"][i] for i in ISLANDS]
        temporal_diag=island_unit_summary(temporal)
        spatial_diag=island_unit_summary(spatial)
        if not math.isclose(temporal_diag["island_equal_mean"],
                            r["island_equal_excess_temporal_sorensen"],rel_tol=0,abs_tol=1e-12):
            raise ValueError("Source seven island temporal effect inconsistent")
        if not math.isclose(spatial_diag["island_equal_mean"],
                            r["island_equal_spatial_simpson_B3_minus_B1"],rel_tol=0,abs_tol=1e-12):
            raise ValueError("Source seven island spatial effect inconsistent")
        data[guild]={
          "temporal_species_identity_excess_sorensen":temporal_diag,
          "within_island_spatial_simpson_B3_minus_B1":spatial_diag,
          "island_leave_one_out_negative_count":
              r["source_one_island_delete_negative_count"],
          "original_half_event_sensitivity_same_direction_count":
              r["recorded_source_half_effort_sensitivity"]["same_spatial_simpson_direction_half_count"]
        }
    paired=[
        old["source_pitfall_guilds"]["coleoptera"]["source_each_island_spatial_delta_simpson"][i]-
        old["source_pitfall_guilds"]["araneae"]["source_each_island_spatial_delta_simpson"][i]
        for i in ISLANDS
    ]
    paired_diag=island_unit_summary(paired)
    if not math.isclose(paired_diag["island_equal_mean"],
        data["coleoptera"]["within_island_spatial_simpson_B3_minus_B1"]["island_equal_mean"]-
        data["araneae"]["within_island_spatial_simpson_B3_minus_B1"]["island_equal_mean"],
        rel_tol=0,abs_tol=1e-12):
        raise ValueError("Cross-guild paired island source spatial contrast inconsistent")
    return {
      "schema":"structural.bala_jbi_seven_island_uncertainty_sourcefree.v1_346",
      "status":"SOURCE_FREE_ISLAND_UNIT_UNCERTAINTY_RECONCILED_NOT_CONFIRMATORY",
      "source_original_DwCA_SHA256":SOURCE_SHA,
      "source_316_original_field_result_SHA256":SHA316,
      "source_318_original_field_result_SHA256":SHA318,
      "original_island_codes_in_frozen_order":list(ISLANDS),
      "island_sample_n":7,
      "island_mean_t95_critical_df6":T6_975,
      "guilds":data,
      "paired_beetle_minus_spider_spatial_simpson_delta":paired_diag,
      "beetle_original_mean_still_negative_under_all_seven_LOO":
        data["coleoptera"]["island_leave_one_out_negative_count"]==7,
      "beetle_original_18_half_salts_still_negative":
        data["coleoptera"]["original_half_event_sensitivity_same_direction_count"]==18,
      "beetle_island_level_spatial_interval_includes_zero":
        data["coleoptera"]["within_island_spatial_simpson_B3_minus_B1"]["t95_interval_includes_zero"],
      "paired_guild_island_level_interval_includes_zero":
        paired_diag["t95_interval_includes_zero"],
      "no_independent_taxon_guild_interaction_demonstrated":True,
      "no_new_original_event_occurrence_or_species_rows_opened":True,
      "original_v314_v316_v318_scorers_SEALED":True,
      "n7_islands_from_one_archipelago_only":True,
      "retrospective_exploratory_sign_flip_not_a_prespecified_significance_test":True,
      "source_field_species_colonization_or_extinction_not_measured":True,
      "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--316",dest="path316",type=Path,default=V316)
    parser.add_argument("--318",dest="path318",type=Path,default=V318)
    parser.add_argument("--344",dest="path344",type=Path,default=CONTRACT)
    parser.add_argument("--contract",type=Path,default=PROTOCOL)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    read=lambda f:json.loads(f.read_text(encoding="utf-8"))
    result=analyze_uncertainty(read(args.path316),read(args.path318),
                               read(args.path344),read(args.contract))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "beetle_spatial_interval":
          result["guilds"]["coleoptera"]["within_island_spatial_simpson_B3_minus_B1"]["descriptive_t95_interval_conditional_on_seven_islands"],
        "beetle_spatial_exact_two_sided_p":
          result["guilds"]["coleoptera"]["within_island_spatial_simpson_B3_minus_B1"]["symmetric_sign_flip_two_sided_p_exploratory"],
        "temporal_spider_p":
          result["guilds"]["araneae"]["temporal_species_identity_excess_sorensen"]["symmetric_sign_flip_two_sided_p_exploratory"],
        "temporal_beetle_p":
          result["guilds"]["coleoptera"]["temporal_species_identity_excess_sorensen"]["symmetric_sign_flip_two_sided_p_exploratory"],
        "original_species_rows_reopened":0
    },sort_keys=True))
if __name__=="__main__":main()
