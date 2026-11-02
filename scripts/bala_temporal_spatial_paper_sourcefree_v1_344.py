#!/usr/bin/env python3
"""v1.344: ZERO-original-source island-level temporal/spatial biodiversity audit.

Uses only already published, source-SHA-frozen BALA v1.316 and v1.318
aggregate JSONs. This is retrospective DESCRIPTIVE island-deletion
sensitivity, NOT seven independent tests or a causal claim.
The original 10,379 Event / 63,904 Occurrence source members are NEVER read.
"""
from __future__ import annotations
import argparse,json,math,statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
V316=ROOT/"development/bala_within_campaign_detection_original_result_freeze_v1_316.json"
V318=ROOT/"development/bala_spatial_original_result_freeze_v1_318.json"
CONTRACT=ROOT/"development/bala_temporal_spatial_cross_axis_sourcefree_protocol_v1_344.json"
ISLANDS=("fai","flo","pic","sjg","smg","smr","ter")
GUILDS=("araneae","coleoptera")
SHA316="1a65cb237271560b56484e992eca76ee6bf082048c55a6f3f68eb0f5a2436871"
SHA318="f4e61ddbbd255d3a35a46fb0254273889516984b82479b3949e5edd79853af02"
SOURCE_SHA="4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2"

def mean(v):return statistics.fmean(v)
def near(a,b,label):
    if not math.isclose(a,b,abs_tol=1e-12,rel_tol=0):
        raise ValueError("Original BALA frozen "+label+" numeric evidence differs")

def analyze(v316,v318,p):
    if (p.get("schema")!="structural.bala_temporal_spatial_cross_axis_manuscript_audit.v1_344"
        or p.get("status")!="SOURCE_FREE_POST_HOC_ISLAND_DELETION_SENSITIVITY_AND_MANUSCRIPT_POSITIONING"
        or p["evidence_sources"]["v316_original_response_inner_SHA256"]!=SHA316
        or p["evidence_sources"]["v318_original_response_inner_SHA256"]!=SHA318
        or p["evidence_sources"]["original_DwCA_SHA256"]!=SOURCE_SHA
        or p["evidence_sources"]["seven_islands"]!=list(ISLANDS)
        or v316.get("schema")!="structural.bala_between_within_original_aggregate_freeze.v1_316"
        or v318.get("schema")!="structural.bala_original_spatial_beta_numeric_freeze.v1_318"
        or v316["original"]["v316_original_inner_JSON_SHA256"]!=SHA316
        or v318["original_evidence"]["original_result_JSON_SHA256"]!=SHA318
        or v316["original"]["source_original_zip_sha256"]!=SOURCE_SHA
        or v318["original_evidence"]["original_2024_DwCA_SHA256"]!=SOURCE_SHA
        or v316["original"]["source_Event_selected"]!=4620
        or v318["original_evidence"]["source_equal_Event_coreid_count"]!=4620
        or v316["original"]["source_transects"]!=29
        or v318["original_evidence"]["original_repeated_transects"]!=29):
        raise ValueError("Frozen source field data identity/physical site denominators mismatch")
    if (v316["limits"].get("old_original_v314_taxon_workflow")!="SEALED"
        or v316["limits"].get("v316_original_taxon_workflow")!="SEALED_AFTER_SUCCESS"
        or not v316["limits"].get("GEB_scientific_HOLD")
        or not v318["limitations"].get("GEB_scientific_HOLD")
        or not v318["limitations"].get("original_v318_scorer_sealed_after_success")
        or v316["limits"].get("new_confirmatory_systems")!=0
        or v318["limitations"].get("new_confirmatory_systems")!=0):
        raise ValueError("Biological source one-shot original scorer seal/GEB HOLD changed")
    out={}
    for guild in GUILDS:
        temporal=v316["pitfall"][guild]
        spatial=v318["main_pitfall"][guild]
        if set(temporal["per_island"])!=set(ISLANDS) or set(spatial["per_island"])!=set(ISLANDS):
            raise ValueError("Original seven island cohort is incomplete")
        initial=[temporal["per_island"][i]["excess_sorensen"] for i in ISLANDS]
        temporal_mean=mean(initial)
        near(temporal_mean,temporal["island_equal_excess_sorensen"],guild+" temporal")
        orig=[spatial["per_island"][i]["delta_spatial_simpson"] for i in ISLANDS]
        total_sor=[spatial["per_island"][i]["delta_spatial_sorensen"] for i in ISLANDS]
        near(mean(orig),spatial["island_equal_delta_spatial_simpson"],guild+" Simpson")
        near(mean(total_sor),spatial["island_equal_delta_spatial_sorensen"],guild+" Sorensen")
        sites=sum(spatial["per_island"][i]["matched_physical_sites"] for i in ISLANDS)
        pairs=sum(spatial["per_island"][i]["dependent_pairs"] for i in ISLANDS)
        if sites!=spatial["source_physical_sites"] or pairs!=spatial["dependent_site_pairs"]:
            raise ValueError("Original spatial site and dependent-pair denominators drifted")
        if sites!=(29 if guild=="araneae" else 28) or pairs!=(56 if guild=="araneae" else 49):
            raise ValueError("Original physical site/pair source count not frozen")
        leave_one={
            island:mean([spatial["per_island"][j]["delta_spatial_simpson"]
                         for j in ISLANDS if j!=island])
            for island in ISLANDS
        }
        source_directions={
            island:"homogenization" if spatial["per_island"][island]["delta_spatial_simpson"]<0
                   else "differentiation" if spatial["per_island"][island]["delta_spatial_simpson"]>0
                   else "unchanged" for island in ISLANDS
        }
        rise_and_homogenize=[
            island for island in ISLANDS
            if spatial["per_island"][island]["delta_spatial_simpson"]<0 and
            spatial["per_island"][island]["mean_B3_site_richness"]>
            spatial["per_island"][island]["mean_B1_site_richness"]
        ]
        sensitivity={
            "original_9_salts_times_2_complementary_halves":18,
            "same_spatial_simpson_direction_half_count":spatial["source_half_simpson_same_sign"],
            "same_spatial_sorensen_direction_half_count":spatial["source_half_sorensen_same_sign"],
            "original_18_half_samples_not_biologically_independent":True
        }
        out[guild]={
            "original_spatial_independent_plot_n":sites,
            "original_spatial_dependent_pair_n":pairs,
            "same_camp_half_sample_temporal_excess_positive_islands":sum(x>0 for x in initial),
            "island_equal_excess_temporal_sorensen":temporal_mean,
            "island_equal_spatial_simpson_B3_minus_B1":mean(orig),
            "island_equal_spatial_sorensen_B3_minus_B1":mean(total_sor),
            "source_spatial_Simpson_direction_by_island":source_directions,
            "source_each_island_spatial_delta_simpson":dict(zip(ISLANDS,orig)),
            "source_each_island_temporal_excess_sorensen":dict(zip(ISLANDS,initial)),
            "source_one_island_delete_spatial_simpson_mean":leave_one,
            "source_one_island_delete_spatial_simpson_min_max":[min(leave_one.values()),max(leave_one.values())],
            "source_one_island_delete_negative_count":sum(x<0 for x in leave_one.values()),
            "source_one_island_delete_positive_count":sum(x>0 for x in leave_one.values()),
            "source_islands_homogenizing_despite_mean_local_richness_gain":rise_and_homogenize,
            "recorded_source_half_effort_sensitivity":sensitivity
        }
    b=out["coleoptera"];s=out["araneae"]
    if (b["same_camp_half_sample_temporal_excess_positive_islands"]!=7
        or s["same_camp_half_sample_temporal_excess_positive_islands"]!=7
        or b["source_one_island_delete_negative_count"]!=7
        or b["recorded_source_half_effort_sensitivity"]["same_spatial_simpson_direction_half_count"]!=18
        or s["recorded_source_half_effort_sensitivity"]["same_spatial_simpson_direction_half_count"]!=13):
        raise ValueError("Original source corroborating BALA site/season diagnostic changed")
    return {
       "schema":"structural.bala_temporal_spatial_sourcefree_paper_basis.v1_344",
       "status":"BALA_SEVEN_ISLAND_BEETLE_HOMOGENIZATION_LOO_SOURCEFREE_VALIDATED",
       "original_DwCA_archive_SHA256":SOURCE_SHA,
       "original_316_numeric_response_SHA256":SHA316,
       "original_318_numeric_response_SHA256":SHA318,
       "original_island_context_n":len(ISLANDS),
       "original_29_physical_transects":29,
       "source_pitfall_guilds":out,
       "beetle_homogenization_direction_persists_under_each_one_island_deletion":True,
       "spider_positive_spatial_direction_not_stable_under_every_one_island_deletion":s["source_one_island_delete_negative_count"]>0,
       "LOO_and_half_splits_not_independent_ecological_replications":True,
       "original_arthropod_Event_or_Occurrence_rows_reopened":0,
       "prior_v314_v316_v318_one_shot_source_scorers_SEALED":True,
       "ecological_identification_limitation":"Temporal species replacement and spatial beta are detection-based; no observed species immigrations, causes or recipient population persistence.",
       "published_BALA_overall_richness_stability_is_prior_art":True,
       "GEB_scientific_HOLD":True,
       "new_confirmatory_systems":0,
       "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--316",dest="p316",type=Path,default=V316)
    p.add_argument("--318",dest="p318",type=Path,default=V318)
    p.add_argument("--contract",type=Path,default=CONTRACT)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8"))
    result=analyze(read(a.p316),read(a.p318),read(a.contract))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps({
        "status":result["status"],
        "beetle_original_delta":result["source_pitfall_guilds"]["coleoptera"]["island_equal_spatial_simpson_B3_minus_B1"],
        "beetle_all_seven_LOO_negative":result["source_pitfall_guilds"]["coleoptera"]["source_one_island_delete_negative_count"],
        "beetle_LOO_range":result["source_pitfall_guilds"]["coleoptera"]["source_one_island_delete_spatial_simpson_min_max"],
        "spider_delta":result["source_pitfall_guilds"]["araneae"]["island_equal_spatial_simpson_B3_minus_B1"],
        "spider_LOO_negative":result["source_pitfall_guilds"]["araneae"]["source_one_island_delete_negative_count"],
        "original_species_rows_reopened":0
    },sort_keys=True))
if __name__=="__main__":main()
