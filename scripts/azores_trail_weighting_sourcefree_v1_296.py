#!/usr/bin/env python3
"""Source-free posthoc aggregation and community composition sensitivity.

Reads exclusively frozen, anonymized four trail-level v1.295 effect estimates.
Never reopens Event/Occurrence or any biological response values.
"""
from __future__ import annotations
import argparse,json,statistics
from pathlib import Path

def analyze(d,p):
    if d.get("schema")!="structural.azores_trail_native_alien_field_aggregate_freeze.v1_295" or (
       d.get("status")!="ORIGINAL_PUBLISHED_FIELD_SOURCE_DESCRIPTIVE_SCORE_FROZEN"
       or p.get("schema")!="structural.azores_trail_aggregation_sensitivity.v1_296"
       or p.get("status")!="POSTHOC_SOURCE_FREE_AGGREGATION_ONLY_ORIGINAL_PRIMARY_IMMUTABLE"):
        raise ValueError("Original v1.295 frozen response-free aggregation required")
    r=d["per_trail"]
    if len(r)!=4 or sum(x["matched_area_year_groups"] for x in r)!=17:
        raise ValueError("Original 4 trails and 17 matched source groups changed")
    island_counts={i:len([x for x in r if x["island"]==i]) for i in ("Terceira","São Miguel")}
    if island_counts!={"Terceira":3,"São Miguel":1}:
        raise ValueError("Original 3+1 island/trail support changed")
    v=[float(x["logratio_interior_minus_edge"]) for x in r]
    primary=sum(v)/len(v)
    if abs(primary-d["original_primary_equal_trails_effect"])>1e-12:
        raise ValueError("Original frozen primary effect altered")
    islandmeans={i:statistics.mean(x["logratio_interior_minus_edge"] for x in r if x["island"]==i)
      for i in ("Terceira","São Miguel")}
    for i,calc in islandmeans.items():
        if abs(calc-d["per_island"][i]["mean_equal_trails_interior_minus_edge_logratio"])>1e-12:
            raise ValueError("Frozen island trail summaries do not reconcile")
    equal_island=statistics.mean(islandmeans.values())
    grouped=sum(x["matched_area_year_groups"]*x["logratio_interior_minus_edge"] for x in r)/17
    positive=sum(x>0 for x in v)
    if positive!=d["original_primary_positive_trail_count"]:
        raise ValueError("Primary original sign count altered")
    trails=[{
        "island":x["island"],
        "anonymized_trail":x["anonymized_trail"],
        "matched_area_year_groups":x["matched_area_year_groups"],
        "log_ratio_effect":x["logratio_interior_minus_edge"],
        "native_richness_difference":x["native_richness_interior_minus_edge"],
        "alien_richness_difference":x["alien_richness_interior_minus_edge"],
        "relative_and_native_absolute_sign_agree":
            ((x["logratio_interior_minus_edge"]>0)==(x["native_richness_interior_minus_edge"]>0))
    } for x in r]
    output={
        "schema":"structural.azores_trail_source_free_weighting_synthesis.v1_296",
        "status":"SOURCE_FREE_AGGREGATION_COMPLETE_NONINDEPENDENT_SENSITIVITY",
        "original_v1_295_primary_equal_trail_mean":primary,
        "primary_frozen_without_adjustment":True,
        "equal_island_descriptive_mean":equal_island,
        "matched_area_group_weighted_nonindependent_mean":grouped,
        "island_mean_over_trails":islandmeans,
        "original_source_4_trail_min":min(v),
        "original_source_4_trail_max":max(v),
        "original_positive_trail_count":positive,
        "original_negative_trail_count":len(v)-positive,
        "direction_by_weighting":{
            "equal_trails":"positive" if primary>0 else "negative" if primary<0 else "zero",
            "equal_islands":"positive" if equal_island>0 else "negative" if equal_island<0 else "zero",
            "group_weighted_nonindependent":"positive" if grouped>0 else "negative" if grouped<0 else "zero"
        },
        "pooled_sign_reversal_vs_frozen_primary":(primary<0<grouped) or (grouped<0<primary),
        "relative_composition_sign_differs_from_native_absolute_richness_in_trails":[
            {"island":z["island"],"anonymized_trail":z["anonymized_trail"]}
            for z in trails if not z["relative_and_native_absolute_sign_agree"]],
        "per_trail_source_aggregate":trails,
        "no_p_value_or_bootstrap":True,
        "group_count_weighting_invalid_as_independent_replication":True,
        "island_pair_not_archipelago_replication":True,
        "not_invasive_causation_nor_natal_rescue":True,
        "original_source_biological_rows_reopened":0,
        "original_v1_292_terminal_unchanged":True,
        "original_GEB_scientific_HOLD":True,
        "new_confirmatory_admissions":0,"eBird_used":False
    }
    return output

def main():
    x=argparse.ArgumentParser(description=__doc__)
    x.add_argument("--source",required=True,type=Path)
    x.add_argument("--contract",required=True,type=Path)
    x.add_argument("--out",required=True,type=Path)
    a=x.parse_args()
    result=analyze(json.loads(a.source.read_text(encoding="utf-8")),
                   json.loads(a.contract.read_text(encoding="utf-8")))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in (
        "status","original_v1_295_primary_equal_trail_mean","equal_island_descriptive_mean",
        "matched_area_group_weighted_nonindependent_mean","pooled_sign_reversal_vs_frozen_primary",
        "relative_composition_sign_differs_from_native_absolute_richness_in_trails",
        "original_source_biological_rows_reopened"
    )},sort_keys=True))
if __name__=="__main__":main()
