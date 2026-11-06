#!/usr/bin/env python3
"""v1.350 BALA ground vs lower-tree-foliage method comparison: source FREE.

Read ONLY pre-frozen original v1.316/v1.318 aggregates. Original Event,
Occurrence, host-tree identity and taxon labels are NOT accessed. This is a
DESCRIPTIVE contrast of two capture methods, not evidence of height-
stratified vertical niche separation, guild-specific species-level change,
or a new significant ecological treatment effect. Foliage samples were
beaten at ~1.5–2 m, NOT a height-profile of the upper forest canopy.
"""
from __future__ import annotations
import argparse,json,math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/bala_ground_foliage_method_sourcefree_protocol_v1_350.json"
T=ROOT/"development/bala_within_campaign_detection_original_result_freeze_v1_316.json"
S=ROOT/"development/bala_spatial_original_result_freeze_v1_318.json"
BALA_SHA="4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2"
SHA316="1a65cb237271560b56484e992eca76ee6bf082048c55a6f3f68eb0f5a2436871"
SHA318="f4e61ddbbd255d3a35a46fb0254273889516984b82479b3949e5edd79853af02"

def close(a,b,label):
    if a is None or b is None or not math.isclose(a,b,rel_tol=0,abs_tol=1e-12):
        raise ValueError("Frozen original numerical "+label+" changed")

def assess(p,t,s):
    if (p.get("schema")!="structural.bala_observation_method_ground_foliage_sourcefree.v1_350"
        or p.get("status")!="FROZEN_EXISTING_AGGREGATE_ONLY_METHOD_CONTEXT_NOT_NEW_ORIGINAL_RESPONSE"
        or p["source_archives"]["published_original_DwCA_SHA256"]!=BALA_SHA
        or p["source_archives"]["original_v316_numeric_sha256"]!=SHA316
        or p["source_archives"]["original_v318_numeric_sha256"]!=SHA318
        or t["original"]["source_original_zip_sha256"]!=BALA_SHA
        or t["original"]["v316_original_inner_JSON_SHA256"]!=SHA316
        or s["original_evidence"]["original_result_JSON_SHA256"]!=SHA318
        or t["original"]["source_transects"]!=29
        or t["original"]["source_Event_selected"]!=4620
        or s["original_evidence"]["original_repeated_transects"]!=29):
        raise ValueError("Original source or scientific cohort SHA changed")
    old=p["fixed_previously_observed_data"]
    ground=t["pitfall"]["araneae"]
    foliage=t["secondary_beating"]["araneae"]
    ground_sp=s["main_pitfall"]["araneae"]
    leaf_sp=s["secondary_canopy"]["araneae"]
    close(ground["island_equal_excess_sorensen"],old["spider_ground_temporal"]["excess_sorensen"],"Spider pitfall temporal")
    close(foliage["excess_sorensen"],old["spider_foliage_temporal"]["excess_sorensen"],"Spider foliage temporal")
    close(ground_sp["island_equal_delta_spatial_simpson"],old["spider_ground_spatial"]["delta_simpson"],"Spider pitfall spatial")
    close(leaf_sp["island_equal_delta_spatial_simpson"],old["spider_foliage_spatial"]["delta_simpson"],"Spider foliage spatial")
    for method,d in (("ground",ground),("foliage",foliage)):
        within=d["island_equal_within_sorensen"] if method=="ground" else d["within_sorensen"]
        across=d["island_equal_across_sorensen"] if method=="ground" else d["across_sorensen"]
        excess=d["island_equal_excess_sorensen"] if method=="ground" else d["excess_sorensen"]
        close(across-within,excess,method+" temporal subtraction")
    assert ground["eligible_original_sites"]==29 and foliage["eligible_sites"]==29
    assert ground_sp["source_physical_sites"]==29 and leaf_sp["physical_sites"]==29
    # Source-frozen stop receipts must NOT be converted into zero effects.
    b_temporal=t["secondary_beating"]["coleoptera"]
    b_spatial=s["secondary_canopy"]["coleoptera"]
    if (b_temporal["status"]!="STOP_INSUFFICIENT_HALF_SAMPLE_GUILD_DETECTION_SUPPORT"
        or b_temporal["eligible_sites"]!=13 or b_temporal["excess_sorensen"] is not None
        or b_spatial["status"]!="STOP_FROZEN_GUILD_SPATIAL_PAIR_ESTIMABILITY"
        or b_spatial["eligible_sites"]!=22 or b_spatial["spatial_beta_delta"] is not None):
        raise ValueError("Original foliage Beetle hard scientific STOP modified")
    close(t["pitfall"]["coleoptera"]["island_equal_excess_sorensen"],
          old["beetle_ground_temporal"]["excess_sorensen"],"Beetle ground temporal")
    close(s["main_pitfall"]["coleoptera"]["island_equal_delta_spatial_simpson"],
          old["beetle_ground_spatial"]["delta_simpson"],"Beetle ground spatial")
    if (not t["limits"]["GEB_scientific_HOLD"]
        or not s["limitations"]["GEB_scientific_HOLD"]
        or not p["firewall"]["prior_v314_v316_v318_original_scorers_SEALED"]
        or p["firewall"]["new_confirmatory_systems"]!=0
        or p["firewall"]["eBird"]):
        raise ValueError("Original biological holdout or original source seal violated")
    temporal_difference=ground["island_equal_excess_sorensen"]-foliage["excess_sorensen"]
    spatial_difference=(ground_sp["island_equal_delta_spatial_simpson"]-
                        leaf_sp["island_equal_delta_spatial_simpson"])
    return {
        "schema":"structural.bala_sourcefree_ground_foliage_method_receipt.v1_350",
        "status":"SOURCE_FREE_BALA_METHOD_SPECIFIC_SPIDER_DESCRIPTIVE_CONTRAST_BEETLE_STOP",
        "source_original_field_DwCA_SHA256":BALA_SHA,
        "source_v316_original_aggregate_SHA256":SHA316,
        "source_v318_original_aggregate_SHA256":SHA318,
        "original_physical_transects":29,
        "field_beating_height_metres_approx":[1.5,2.0],
        "source_sampling_method":"Branch foliage beating on native woody plants, five strikes at ~1.5–2 m, within 5 m of pitfall transect; NOT upper canopy measurement",
        "source_original_equal_per_campaign_sampling_Events":{
             "ground_pitfall":781, "foliage_beating":759
        },
        "spider":{
          "ground_pitfall":{
            "eligible_original_temporal_sites":ground["eligible_original_sites"],
            "temporal_within_campaign_sorensen":ground["island_equal_within_sorensen"],
            "temporal_across_campaign_sorensen":ground["island_equal_across_sorensen"],
            "temporal_sorensen_excess":ground["island_equal_excess_sorensen"],
            "temporal_simpson_excess":ground["island_equal_excess_simpson"],
            "eligible_original_spatial_sites":ground_sp["source_physical_sites"],
            "spatial_simpson_beta_B3_minus_B1":ground_sp["island_equal_delta_spatial_simpson"]
          },
          "foliage_beating":{
            "eligible_original_temporal_sites":foliage["eligible_sites"],
            "temporal_within_campaign_sorensen":foliage["within_sorensen"],
            "temporal_across_campaign_sorensen":foliage["across_sorensen"],
            "temporal_sorensen_excess":foliage["excess_sorensen"],
            "temporal_simpson_excess":foliage["excess_simpson"],
            "eligible_original_spatial_sites":leaf_sp["physical_sites"],
            "spatial_simpson_beta_B3_minus_B1":leaf_sp["island_equal_delta_spatial_simpson"]
          },
          "observed_temporal_excess_ground_minus_foliage":temporal_difference,
          "observed_spatial_Simpson_beta_ground_minus_foliage":spatial_difference,
          "not_an_island_paired_significance_test":True,
          "folio_source_original_per_island_spatial_values_not_available_in_frozen_aggregate":True
        },
        "beetle":{
          "ground_temporal_sorensen_excess":t["pitfall"]["coleoptera"]["island_equal_excess_sorensen"],
          "ground_spatial_simpson_beta_B3_minus_B1":s["main_pitfall"]["coleoptera"]["island_equal_delta_spatial_simpson"],
          "foliage_temporal":{"status":"SCIENTIFIC_STOP","eligible_sites":13,"effect":None},
          "foliage_spatial":{"status":"SCIENTIFIC_STOP","eligible_sites":22,"effect":None}
        },
        "upper_tree_canopy_height_stratification_not_measured":True,
        "sampling_method_and_microhabitat_completely_confound_the_comparison":True,
        "host_tree_species_effect_not_tested":True,
        "foliage_per_island_uncertainty_and_method_interaction_not_estimable":True,
        "no_original_BALA_Event_Occurrence_or_taxon_rows_reopened":True,
        "old_v314_v316_v318_biological_scorers_SEALED":True,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
        "eBird_used":False
    }

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("--protocol",type=Path,default=P)
    a.add_argument("--316",dest="p316",type=Path,default=T)
    a.add_argument("--318",dest="p318",type=Path,default=S)
    a.add_argument("--out",type=Path,required=True)
    args=a.parse_args()
    read=lambda p:json.loads(p.read_text(encoding="utf-8"))
    result=assess(read(args.protocol),read(args.p316),read(args.p318))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],
      "spider_temporal_ground":result["spider"]["ground_pitfall"]["temporal_sorensen_excess"],
      "spider_temporal_foliage":result["spider"]["foliage_beating"]["temporal_sorensen_excess"],
      "spider_spatial_ground":result["spider"]["ground_pitfall"]["spatial_simpson_beta_B3_minus_B1"],
      "spider_spatial_foliage":result["spider"]["foliage_beating"]["spatial_simpson_beta_B3_minus_B1"],
      "beetle_foliage_temporal":result["beetle"]["foliage_temporal"]["status"],
      "beetle_foliage_spatial":result["beetle"]["foliage_spatial"]["status"],
      "original_species_rows_opened":0},sort_keys=True))
if __name__=="__main__":main()
