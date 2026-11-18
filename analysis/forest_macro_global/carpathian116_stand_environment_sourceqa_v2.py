#!/usr/bin/env python3
"""Response-sealed Carpathian116 stand/environment source v2 after partition proof.

Does NOT relax v1 original source-stop retrospectively. New precommitted method
eligibility uses original Beech/Spruce stand labels, not alias remapping.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from carpathian116_original_author_schema_gate import (
    original_record_links, official_get, FROZEN_FILES, SourceStop,
)
from carpathian116_stand_environment_sourceqa import (
    only_whitelist, summary_values,
)
from carpathian116_stand_label_conflict_diagnostic import partition

PRESPEC="docs/FOREST_MACRO_CARPATHIAN116_STAND_ENVIRONMENT_QA_V2_PRESPEC_20261118.md"
FILES=(("Beech.csv",60,"B"),("Spruce.csv",56,"S"),("Beech_Spruce.csv",116,"combined"))

def run():
    published=original_record_links()
    table={}
    for filename,n,role in FILES:
        size,md5=FROZEN_FILES[filename]
        binary=official_get(published[filename],"*/*",size+1024)
        if len(binary)!=size or hashlib.md5(binary).hexdigest()!=md5:
            raise SourceStop("SOURCE_ORIGINAL_FOREST_COVARIATE_PUBLISHER_HASH_DRIFT")
        table[role]=only_whitelist(binary,n,filename)
    b,s,c=table["B"],table["S"],table["combined"]
    if set(b)&set(s) or (set(b)|set(s))!=set(c):
        raise SourceStop("SOURCE_BEETLE_FOREST_ORIGINAL_PLOT_UNIVERSE_CHANGED")
    standpart={
      "B":partition({plot:row["standshort"] for plot,row in b.items()})
         ==partition({plot:c[plot]["standshort"] for plot in b}),
      "S":partition({plot:row["standshort"] for plot,row in s.items()})
         ==partition({plot:c[plot]["standshort"] for plot in s}),
    }
    if not all(standpart.values()):
        raise SourceStop("SOURCE_ORIGINAL_STAND_GROUP_MEMBERSHIP_V2_NOT_IDENTICAL")
    summaries={role:summary_values(table[role],role) for role in ("B","S","combined")}
    complete={
      role:(q["source_original_standshort_distinct_ID_count"]>=5 and
            q["original_8_predictor_complete_physical_plots"]==q["original_physical_plot_rows"])
      for role,q in summaries.items() if role in ("B","S")
    }
    return {
      "schema":"structural.Carpathian116_stand_environment_v2_original_sourceonly.v1",
      "author_original_stand_partition_identical_within_each_forest":standpart,
      "source_environment_only_by_original_forest":summaries,
      "precommitted_all_five_stand_eight_finite_variables_pass":complete,
      "original_standshort_is_NOT_source_verified_mountain_range":True,
      "source_original_plot_and_stand_values_NEVER_EXPORTED":True,
      "no_original_beetle_or_richness_response_SOURCE_ACCESSED":True,
      "original_feeding_guild_and_trap_zeros_UNVERIFIED":True,
      "new_biological_effect_estimated":False,
      "status":("ORIGINAL_FOREST_SPECIFIC_STAND_ENVIRONMENT_READINESS_PASS_ONLY"
                 if all(complete.values()) else
                 "SOURCE_FOREST_STAND_OR_EIGHT_PREDICTOR_GATE_NOT_QUALIFIED")
    }

def synthetic():
    from carpathian116_stand_label_conflict_diagnostic import partition
    assert partition({"p1":"s1","p2":"s1","p3":"s2"}) == partition(
        {"p1":"A","p2":"A","p3":"B"})
    assert partition({"p1":"s1","p2":"s1","p3":"s2"}) != partition(
        {"p1":"A","p2":"B","p3":"B"})
    print("SYNTHETIC_CARPATHIAN_STAND_ENV_V2_PARTITION_PROOF_REUSE_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:ap.error("--out needed")
    result={
       "schema":"structural.Carpathian116_stand_environment_sourceonly_v2.v1",
       "prespec":PRESPEC,
       "old_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_results_UNCHANGED":True,
       "new_species_guild_or_community_response_NOT_OPENED":True,
       "no_forest_to_country_generalization_claim":True,
       "eBird_used":False,"TinyFish_used":False
    }
    try:
        result["source_v2"]=run()
        result["status"]=result["source_v2"]["status"]
    except SourceStop as ex:
        result["status"]=str(ex)
        result["source_ONLY_HOLD_not_ecological_non_support"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Carpathian116_stand_environment_v2_sourceonly.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("CARPATHIAN116_STAND_ENVIRONMENT_V2_SOURCE",result["status"])

if __name__=="__main__":
    main()
