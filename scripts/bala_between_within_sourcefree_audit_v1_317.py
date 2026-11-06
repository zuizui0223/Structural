#!/usr/bin/env python3
"""v1.317 original-BALA source-free excess temporal replacement audit.

Only the already scored, SHA-locked, seven-island aggregate is read. Original
2024 Event/Occurrence rows, all site/taxon labels and detection models are
NOT reopened, refit, resampled or inferred. The 9 partitions are NOT 9
independent biological replicates. No inferential P-values.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"development/bala_within_campaign_detection_original_result_freeze_v1_316.json"
CONTRACT=ROOT/"development/bala_within_period_excess_sourcefree_protocol_v1_317.json"
SOURCE_SHA="1a65cb237271560b56484e992eca76ee6bf082048c55a6f3f68eb0f5a2436871"
ISLANDS=("fai","flo","pic","sjg","smg","smr","ter")
GUILDS=("araneae","coleoptera")

def check_close(a,b,label):
    if not math.isclose(a,b,rel_tol=0,abs_tol=1e-12):
        raise ValueError(f"Original aggregate {label} disagrees with seven-island arithmetic")

def audit(source,contract):
    if (contract.get("schema")!="structural.bala_within_phase_excess_sourcefree_audit.v1_317"
        or contract.get("status")!="EXACT_POSTHOC_AUDIT_ONLY_NO_BIOLOGICAL_REOPEN"
        or contract.get("original_v316_source_result_JSON_SHA256")!=SOURCE_SHA
        or contract.get("original_v316_source_run")!=40636604430
        or source.get("schema")!="structural.bala_between_within_original_aggregate_freeze.v1_316"
        or source.get("status")!="ORIGINAL_SEVEN_ISLAND_BALA_WITHIN_CAMPAIGN_DETECTION_CONTROL_COMPLETE"
        or source["original"].get("v316_original_inner_JSON_SHA256")!=SOURCE_SHA
        or source["original"].get("source_original_zip_sha256")!="4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2"
        or source["original"].get("source_transects")!=29
        or source["original"].get("islands")!=7
        or source["original"].get("source_Event_selected")!=4620):
        raise ValueError("Original source identity / source-free audit contract mismatch")
    guard=source["limits"]
    if (guard.get("old_original_v314_taxon_workflow")!="SEALED"
        or guard.get("v316_original_taxon_workflow")!="SEALED_AFTER_SUCCESS"
        or not guard.get("GEB_scientific_HOLD")
        or guard.get("new_confirmatory_systems")!=0
        or guard.get("eBird")):
        raise ValueError("Original scientific HOLD or one-shot source seal not preserved")
    primary=source["pitfall"]
    if set(primary)!=set(GUILDS):
        raise ValueError("Original guild identity changed")
    byguild={}
    for guild in GUILDS:
        g=primary[guild]
        sites=sum(x["n"] for x in g["per_island"].values())
        positive=sum(x["positive"] for x in g["per_island"].values())
        if (set(g["per_island"])!=set(ISLANDS) or sites!=g["eligible_original_sites"]
            or positive!=g["sites_with_positive_excess_sorensen"]
            or g["islands_with_eligible_source_site"]!=7):
            raise ValueError(f"Original guild site supports changed: {guild}")
        if guild=="araneae" and (sites!=29 or positive!=26 or g["valid_split_counts_histogram"]!={"9":29}):
            raise ValueError("Original Spider site and nine-split supports inconsistent")
        if guild=="coleoptera" and (sites!=26 or positive!=25 or
            g["valid_split_counts_histogram"]!={"0":2,"2":1,"7":2,"8":1,"9":23}):
            raise ValueError("Original Beetle site and nine-split supports inconsistent")
        for within,between,delta in (("island_equal_within_sorensen",
                "island_equal_across_sorensen","island_equal_excess_sorensen"),
            ("island_equal_within_simpson","island_equal_across_simpson",
                "island_equal_excess_simpson")):
            check_close(g[between]-g[within],g[delta],f"{guild}:{delta}")
        for name,kind in (("excess_sorensen","sorensen"),("excess_simpson","simpson")):
            value=statistics.fmean(x[name] for x in g["per_island"].values())
            check_close(value,g["island_equal_excess_"+kind],f"{guild}:{kind} island average")
        if any(not (0<=v["positive"]<=v["n"]) for v in g["per_island"].values()):
            raise ValueError("Original source site sign cannot exceed eligible physical plot count")
        within=g["island_equal_within_sorensen"]
        across=g["island_equal_across_sorensen"]
        if across<=0:
            raise ValueError("Zero original across-period denominator")
        byguild[guild]={
            "physical_eligible_transects":sites,
            "physical_sites_positive_across_minus_within_sorensen":positive,
            "fraction_physical_sites_positive_excess_sorensen":positive/sites,
            "islands_positive_excess_sorensen":sum(
                v["excess_sorensen"]>0 for v in g["per_island"].values()),
            "islands_positive_excess_simpson":sum(
                v["excess_simpson"]>0 for v in g["per_island"].values()),
            "island_equal_within_period_sorensen":within,
            "island_equal_between_period_sorensen":across,
            "island_equal_excess_sorensen":g["island_equal_excess_sorensen"],
            "island_equal_within_period_simpson_replacement":g["island_equal_within_simpson"],
            "island_equal_between_period_simpson_replacement":g["island_equal_across_simpson"],
            "island_equal_excess_simpson_replacement":g["island_equal_excess_simpson"],
            "ratio_within_period_to_between_period_sorensen":within/across,
            "ratio_is_not_detection_explained_fraction":True,
            "original_source_island_deltas":{
                island:{
                    "source_transects":g["per_island"][island]["n"],
                    "positive_transects":g["per_island"][island]["positive"],
                    "delta_sorensen":g["per_island"][island]["excess_sorensen"],
                    "delta_simpson":g["per_island"][island]["excess_simpson"]
                } for island in ISLANDS
            }
        }
        if byguild[guild]["islands_positive_excess_sorensen"]!=7 or byguild[guild]["islands_positive_excess_simpson"]!=7:
            raise ValueError("Original all-seven-islands positive excess no longer supported")
    secondary=source["secondary_beating"]
    if secondary["coleoptera"].get("status")!="STOP_INSUFFICIENT_HALF_SAMPLE_GUILD_DETECTION_SUPPORT" or secondary["coleoptera"]["eligible_sites"]!=13 or secondary["coleoptera"]["excess_sorensen"] is not None:
        raise ValueError("Original Canopy-Beetle fixed secondary STOP was changed")
    beetle_greater=sum(
        byguild["coleoptera"]["original_source_island_deltas"][island]["delta_sorensen"]>
        byguild["araneae"]["original_source_island_deltas"][island]["delta_sorensen"]
        for island in ISLANDS
    )
    return {
        "schema":"structural.bala_original_seven_island_sourcefree_excess_turnover_audit.v1_317",
        "status":"ORIGINAL_SOURCE_FREE_SEVEN_ISLAND_TEMPORAL_EXCESS_VALIDATED",
        "source_original_v316_readonly_inner_JSON_SHA256":SOURCE_SHA,
        "source_original_v316_run_id":40636604430,
        "source_original_independent_transects":29,
        "source_original_island_contexts":7,
        "source_original_9_partitions_pseudoreplicates_not_independent":True,
        "main_pitfall":byguild,
        "islands_beetle_excess_sorensen_greater_than_spider_excess":beetle_greater,
        "secondary_canopy_spider_excess_sorensen":secondary["araneae"]["excess_sorensen"],
        "secondary_canopy_beetle_scientifically_stopped":True,
        "original_source_has_not_been_reopened_by_this_audit":True,
        "within_sample_split_is_not_species_detection_probability_model":True,
        "biogeographic_immigration_or_extinction_not_observed":True,
        "no_causal_drivers_or_invasion_inferred":True,
        "v1_314_original_biological_workflow_SEALED":True,
        "v1_316_original_biological_workflow_SEALED":True,
        "original_mammal_BioTIME_RLS_S2S3S4_heldouts_unopened":True,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
        "eBird_used":False
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input",type=Path,default=SOURCE)
    ap.add_argument("--contract",type=Path,default=CONTRACT)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    result=audit(json.loads(args.input.read_text(encoding="utf-8")),
                 json.loads(args.contract.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "spider_delta_sorensen":result["main_pitfall"]["araneae"]["island_equal_excess_sorensen"],
        "beetle_delta_sorensen":result["main_pitfall"]["coleoptera"]["island_equal_excess_sorensen"],
        "spider_site_signs":result["main_pitfall"]["araneae"]["physical_sites_positive_across_minus_within_sorensen"],
        "beetle_site_signs":result["main_pitfall"]["coleoptera"]["physical_sites_positive_across_minus_within_sorensen"],
        "positive_islands_each":[result["main_pitfall"][g]["islands_positive_excess_sorensen"] for g in GUILDS],
        "original_biological_rows_opened":0
    },sort_keys=True))
if __name__=="__main__":
    main()
