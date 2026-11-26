#!/usr/bin/env python3
"""Carpathian116 original standshort literal-label vs physical site partition QA.

Only the first TWO original method fields per row are decoded. Beetle species,
richness and forest environment numeric values remain opaque and unread.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import statistics
from collections import Counter,defaultdict
from itertools import combinations
from pathlib import Path

from carpathian116_original_author_schema_gate import (
    original_record_links, official_get, FROZEN_FILES, SourceStop
)

PRESPEC="docs/FOREST_MACRO_CARPATHIAN116_STAND_LABEL_CONFLICT_DIAGNOSTIC_PRESPEC_20261118.md"
SRC=(("Beech.csv",60,"B"),("Spruce.csv",56,"S"),("Beech_Spruce.csv",116,"combined"))
CODE="Rscript.R"

def decode_one(b):
    try:
        x=b.decode("utf-8").strip().rstrip("\r")
    except UnicodeError:
        raise SourceStop("SOURCE_STAND_OR_PLOT_FIELD_UTF8_STOP") from None
    if x.startswith('"') and x.endswith('"'):
        x=x[1:-1].replace('""','"')
    return x.strip()

def method_two_columns(raw,expected):
    rows=raw.split(b"\n")
    if rows[-1]==b"":rows.pop()
    if len(rows)!=expected+1 or rows[0].decode("utf-8-sig").split(",")[:2]!=["plotid","standshort"]:
        raise SourceStop("SOURCE_STAND_OR_PLOT_HEADER_GRAIN_STOP")
    out={}
    for line in rows[1:]:
        p=line.rstrip(b"\r").split(b",",2)
        if len(p)!=3:
            raise SourceStop("SOURCE_STAND_OR_PLOT_FIRST_TWO_COLUMNS_NOT_AVAILABLE")
        key,stand=decode_one(p[0]),decode_one(p[1])
        if not key or not stand or len(key)>80 or len(stand)>80:
            raise SourceStop("SOURCE_PLOT_OR_STAND_FIELD_MISSING_OR_TOO_LONG")
        if key in out:
            raise SourceStop("SOURCE_DUPLICATE_AUTHOR_PLOT_ID")
        out[key]=stand
    return out

def partition(groups):
    d=defaultdict(set)
    for site,stand in groups.items():d[stand].add(site)
    return frozenset(frozenset(sites) for sites in d.values())

def pair_partition(a,b):
    if set(a)!=set(b):raise SourceStop("SOURCE_PLOT_ID_UNIVERSES_DIFFER")
    n=0; in_both=0;different=0;sum_a=0;sum_b=0
    for x,y in combinations(sorted(a),2):
        one=a[x]==a[y]
        two=b[x]==b[y]
        n+=1
        sum_a+=int(one);sum_b+=int(two)
        in_both+=int(one and two)
        different+=int(one!=two)
    sizes=sorted(Counter(a.values()).values())
    return {
        "physical_plot_count":len(a),
        "original_table_standshort_groups_count":len(sizes),
        "original_table_stand_block_size_min":min(sizes),
        "original_table_stand_block_size_median":statistics.median(sizes),
        "original_table_stand_block_size_max":max(sizes),
        "source_original_name_label_mismatch_same_plot_count":sum(a[x]!=b[x] for x in a),
        "original_source_within_forest_partitions_IDENTICAL":partition(a)==partition(b),
        "within_forest_plot_pair_total":n,
        "original_source_A_pairs_same_stand":sum_a,
        "original_source_combined_pairs_same_stand":sum_b,
        "within_forest_plot_pairs_with_different_group_membership":different,
        "source_original_stand_id_literal_values_NOT_EXPORTED":True,
    }

def author_code_only(raw):
    try:
        text=raw.decode("utf-8-sig")
    except UnicodeError:
        raise SourceStop("SOURCE_AUTHOR_R_CODE_NON_UTF8") from None
    patterns={
        "standshort_literal":r"\bstandshort\b",
        "combined_source_file_literal":r"Beech_Spruce\.csv",
        "mutate_call":r"\bmutate\s*\(",
        "rename_call":r"\brename\s*\(",
        "factor_call":r"\bfactor\s*\(",
        "recode_or_case_when_call":r"\b(?:recode|case_when)\s*\(",
        "binding_by_position_call":r"\b(?:cbind|bind_cols)\s*\(",
    }
    return {
      "published_original_author_R_code_METHOD_TEXT_only":True,
      "original_author_code_lexical_method_call_counts_ONLY":{
          name:len(re.findall(pattern,text,flags=re.IGNORECASE))
          for name,pattern in patterns.items()
      },
      "source_original_R_code_not_executed_or_exported":True,
    }

def run():
    links=original_record_links()
    tables={}
    for name,n,role in SRC:
        size,md5=FROZEN_FILES[name]
        raw=official_get(links[name],"*/*",size+1024)
        if len(raw)!=size or hashlib.md5(raw).hexdigest()!=md5:
            raise SourceStop("SOURCE_ORIGINAL_ENVIRONMENT_MD5_OR_SIZE_CHANGED")
        tables[role]=method_two_columns(raw,n)
    b,s,u=tables["B"],tables["S"],tables["combined"]
    if set(b)&set(s) or set(b)|set(s)!=set(u):
        raise SourceStop("SOURCE_ORIGINAL_116_SITE_ID_UNIVERSE_DRIFT")
    out={"beech":pair_partition(b,{x:u[x] for x in b}),
         "spruce":pair_partition(s,{x:u[x] for x in s})}
    if sum(x["source_original_name_label_mismatch_same_plot_count"] for x in out.values())==0:
        raise SourceStop("SOURCE_PREVIOUS_STAND_LABEL_MISMATCH_NOT_REPRODUCED")
    size,md5=FROZEN_FILES[CODE]
    raw=official_get(links[CODE],"*/*",size+1024)
    if len(raw)!=size or hashlib.md5(raw).hexdigest()!=md5:
        raise SourceStop("SOURCE_ORIGINAL_AUTHOR_R_CODE_MD5_DRIFT")
    methods=author_code_only(raw)
    partsame=all(x["original_source_within_forest_partitions_IDENTICAL"] for x in out.values())
    return {
      "schema":"structural.Carpathian116_standshort_label_partition_diagnostic_v1",
      "source_original_stand_label_vs_partition_anonymous":out,
      "publisher_original_R_method_grammar_ONLY":methods,
      "source_author_original_plot_and_stand_ID_values_EXPORTED":False,
      "source_raw_species_or_guild_data_files_OPENED":False,
      "source_original_environment_numeric_columns_OPENED":False,
      "source_original_richness_or_RL_columns_OPENED":False,
      "author_standshort_mountain_range_identity_NOT_PROVEN":True,
      "original_feeding_guild_source_and_trap_zeros_NOT_VERIFIED":True,
      "new_ecological_effect_estimated":False,
      "status":("SOURCE_STAND_LABEL_RECODE_PARTITION_IDENTICAL_METHOD_ONLY"
                if partsame else "SOURCE_STAND_GROUP_PARTITION_CONFLICT_HOLD")
    }

def synthetic():
    a={"p1":"x","p2":"x","p3":"y","p4":"z"}
    rename={"p1":"r","p2":"r","p3":"s","p4":"t"}
    altered={"p1":"r","p2":"s","p3":"s","p4":"t"}
    p=pair_partition(a,rename)
    assert p["source_original_name_label_mismatch_same_plot_count"]==4
    assert p["original_source_within_forest_partitions_IDENTICAL"]
    assert p["within_forest_plot_pairs_with_different_group_membership"]==0
    q=pair_partition(a,altered)
    assert not q["original_source_within_forest_partitions_IDENTICAL"]
    print("SYNTHETIC_CARPATHIAN_STAND_PARTITION_VS_LABEL_AND_NO_RESPONSE_PASS")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--test",action="store_true")
    a.add_argument("--out",type=Path)
    args=a.parse_args()
    synthetic()
    if args.test:return
    if not args.out:a.error("--out needed")
    res={
      "schema":"structural.Carpathian116_original_standshort_conflict_sourceonly.v1",
      "prespec":PRESPEC,
      "old_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_results_UNCHANGED":True,
      "no_biodiversity_target_or_model_fitted":True,
      "eBird_used":False,"TinyFish_used":False
    }
    try:
        res["source_stand_method_diagnostic"]=run()
        res["status"]=res["source_stand_method_diagnostic"]["status"]
    except SourceStop as ex:
        res["status"]=str(ex)
        res["source_METHOD_STOP_not_ecological_null"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Carpathian116_original_stand_label_partition_method_only.json").write_text(
        json.dumps(res,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("CARPATHIAN116_STAND_LABEL_PARTITION_METHOD_ONLY",res["status"])

if __name__=="__main__":
    main()
