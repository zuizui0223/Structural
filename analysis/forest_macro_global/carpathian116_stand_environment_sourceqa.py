#!/usr/bin/env python3
"""Carpathian 116 source environmental predictors and stand blocks, NO beetle outcomes.

Publisher-original environment tables have response richness columns. This
runner NEVER decodes anything outside a 10-column frozen nonresponse whitelist.
Outputs only anonymous environment aggregate counts and method feasibility.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path

from carpathian116_original_author_schema_gate import (
    original_record_links, official_get, FROZEN_FILES, SourceStop
)

PRESPEC="docs/FOREST_MACRO_CARPATHIAN116_STAND_AND_ENVIRONMENT_QA_PRESPEC_20261118.md"
FILES=(("Beech.csv",60,"B"),("Spruce.csv",56,"S"),("Beech_Spruce.csv",116,"combined"))
FIELDS=(
    "plotid","standshort",
    "ForestUse_pland_1000_Primary",
    "Disturbance_pland_1000_clearcut",
    "LandCover_shdi_1000",
    "age_max",
    "volume_dead_tree_lying",
    "dbh_div_dead_100",
    "openness_mean",
    "altitude_m"
)
PREDICTORS=FIELDS[2:]
UNKNOWN={"","na","nan","null","missing","none","-999"}
EXPECTED_COLUMNS=21

def clean_cell(raw):
    try:
        s=raw.decode("utf-8").strip().rstrip("\r")
    except UnicodeError:
        raise SourceStop("SOURCE_ORIGINAL_ALLOWED_FIELD_NON_UTF8") from None
    if s.startswith('"') and s.endswith('"') and len(s)>=2:
        s=s[1:-1].replace('""','"')
    return s.strip()

def only_whitelist(data,expected_rows,filename):
    rows=data.split(b"\n")
    if rows[-1]==b"":rows.pop()
    if len(rows)!=expected_rows+1:
        raise SourceStop("SOURCE_ENVIRONMENT_PHYSICAL_ROW_COUNT_STOP")
    try:
        h=rows[0].decode("utf-8-sig").rstrip("\r").split(",")
    except UnicodeError:
        raise SourceStop("SOURCE_ENVIRONMENT_HEADER_NOT_UTF8") from None
    if len(h)!=EXPECTED_COLUMNS or h[0]!="plotid" or not all(name in h for name in FIELDS):
        raise SourceStop("SOURCE_PUBLISHED_ENVIRONMENT_FIELD_ALLOWLIST_ABSENT")
    indices={name:h.index(name) for name in FIELDS}
    if len(set(indices.values()))!=len(FIELDS):
        raise SourceStop("SOURCE_ENVIRONMENT_DUPLICATE_FIELDS_STOP")
    allowed={}
    for line in rows[1:]:
        # All 21 column fields are split in byte-space, not decoded.
        # Only ten already-public/nonresponse columns are decoded by clean_cell.
        parts=line.rstrip(b"\r").split(b",")
        if len(parts)!=EXPECTED_COLUMNS:
            raise SourceStop("SOURCE_ENVIRONMENT_CSV_ROW_QUOTED_MULTILINE_OR_SHAPE_STOP")
        v={name:clean_cell(parts[idx]) for name,idx in indices.items()}
        ident=v.pop("plotid")
        if not ident or len(ident)>80 or not v["standshort"] or len(v["standshort"])>80:
            raise SourceStop("SOURCE_ENVIRONMENT_MISSING_OR_BAD_PLOT_STAND_KEY")
        if ident in allowed:
            raise SourceStop("SOURCE_ENVIRONMENT_DUPLICATE_AUTHOR_PLOT_ID")
        allowed[ident]=v
    if len(allowed)!=expected_rows:
        raise SourceStop("SOURCE_ENVIRONMENT_UNEXPECTED_PLOT_COUNT")
    return allowed

def summary_values(rows,role):
    block=Counter(v["standshort"] for v in rows.values())
    sizes=sorted(block.values())
    numeric={}
    complete=0
    for field in PREDICTORS:
        finite=[];missing=0;invalid=0
        for row in rows.values():
            z=row[field]
            if z.casefold() in UNKNOWN:missing+=1;continue
            try:x=float(z)
            except ValueError:invalid+=1;continue
            if not math.isfinite(x):invalid+=1;continue
            finite.append(x)
        numeric[field]={
            "original_finite_numeric_plot_count":len(finite),
            "original_missing_value_plot_count":missing,
            "original_nonfinite_or_non_numeric_plot_count":invalid,
            "original_nonresponse_min":min(finite) if finite else None,
            "original_nonresponse_max":max(finite) if finite else None,
            "original_nonresponse_population_variance":(
                statistics.pvariance(finite) if len(finite)>1 else None),
            "individual_plot_values_NOT_EXPORTED":True,
        }
    for v in rows.values():
        if all(
            z.casefold() not in UNKNOWN and
            # converted once only for environment QA
            is_finite_numeric(z)
            for name,z in v.items() if name in PREDICTORS
        ):complete+=1
    return {
        "source_original_forest_stratum":role,
        "original_physical_plot_rows":len(rows),
        "source_original_standshort_distinct_ID_count":len(block),
        "original_standshort_plots_min":min(sizes),
        "original_standshort_plots_median":statistics.median(sizes),
        "original_standshort_plots_max":max(sizes),
        "original_standshort_with_at_least_two_plots":sum(n>=2 for n in sizes),
        "original_8_predictor_complete_physical_plots":complete,
        "fixed_eight_original_nonresponse_environment_predictors":numeric,
        "stand_short_code_NOT_PROVEN_mountain_range":True,
        "forest_resource_unit_not_inferred_from_header":True,
        "source_site_stand_ids_NOT_EXPORTED":True,
        "beetle_or_other_biodiversity_response_values_NOT_ACCESSED":True
    }

def is_finite_numeric(s):
    try:return math.isfinite(float(s))
    except (ValueError,TypeError):return False

def audit():
    source=original_record_links()
    tab={}
    for fname,n,role in FILES:
        length,md5=FROZEN_FILES[fname]
        body=official_get(source[fname],"*/*",length+1024)
        if len(body)!=length or hashlib.md5(body).hexdigest()!=md5:
            raise SourceStop("SOURCE_ENVIRONMENT_PUBLISHER_FILE_MD5_OR_BYTES_DRIFT")
        tab[role]=only_whitelist(body,n,fname)
    b,s,c=tab["B"],tab["S"],tab["combined"]
    if set(b)&set(s):
        raise SourceStop("SOURCE_ENVIRONMENT_FOREST_PLOTID_COLLISION_STOP")
    if set(b)|set(s)!=set(c):
        raise SourceStop("SOURCE_ENVIRONMENT_COMBINED_ORIGINAL_PLOTID_UNIVERSE_STOP")
    mismatch=sum(v["standshort"]!=c[pid]["standshort"] for pid,v in (b|s).items())
    if mismatch:
        raise SourceStop("SOURCE_ORIGINAL_STANDSHORT_ANNOTATION_BETWEEN_TABLES_CONFLICT")
    outputs={key:summary_values(value,key) for key,value in tab.items()}
    sample=len(b)+len(s)
    eligible=(
       all(outputs[x]["source_original_standshort_distinct_ID_count"]>=5
           and outputs[x]["original_8_predictor_complete_physical_plots"]==
           outputs[x]["original_physical_plot_rows"]
           for x in ("B","S"))
       and sample==116 and not mismatch
    )
    return {
      "schema":"structural.Carpathian116_original_stand_environment_QA_v1",
      "source_original_116_plot_environment_QA":outputs,
      "source_beech_spruce_116_combined_stand_assignment_conflicts":mismatch,
      "future_predeclared_min_five_stands_each_forest_and_full_eight_predictor_eligibility":eligible,
      "standshort_NOT_independently_validated_as_mountain_range_or_independent_unit":True,
      "feeding_guild_source_NOT_VERIFIED":True,
      "true_trap_effort_zero_record_NOT_VERIFIED":True,
      "original_species_or_richness_data_rows_OPENED":False,
      "new_ecological_score_or_effect_ESTIMATED":False,
      "status":("SOURCE_STAND_ENVIRONMENT_FEASIBLE_SEPARATE_GUILD_QUALITY_HOLD"
                if eligible else
                "SOURCE_STAND_OR_ENVIRONMENT_NONESTIMABLE_UNDER_FROZEN_GATE")
    }

def synthetic():
    header=[
        "plotid","standshort","species","lng","lat",
        "B_SR_BIRD","B_SR_BEETLE","B_RL_BEETLE","B_SR_FUNGI","B_RL_FUNGI",
        "B_SR_LICHEN","B_RL_LICHEN","B_PROP",
        "ForestUse_pland_1000_Primary","Disturbance_pland_1000_clearcut",
        "LandCover_shdi_1000","age_max","volume_dead_tree_lying","dbh_div_dead_100",
        "openness_mean","altitude_m"
    ]
    assert len(header)==21
    row=["p1","block1","S","10","11","PRIVATE","PRIVATE","PRIVATE","PRIVATE",
         "PRIVATE","PRIVATE","PRIVATE","PRIVATE","0.3","0.2","0.1","232",
         "42.0","9","15","1300"]
    fake=(",".join(header)+"\n"+",".join(row)+"\n").encode()
    parsed=only_whitelist(fake,1,"Beech.csv")
    assert parsed["p1"]["standshort"]=="block1"
    assert parsed["p1"]["volume_dead_tree_lying"]=="42.0"
    assert "PRIVATE" not in json.dumps(parsed)
    x=summary_values(parsed,"B")
    assert x["original_8_predictor_complete_physical_plots"]==1
    assert x["source_original_standshort_distinct_ID_count"]==1
    print("SYNTHETIC_CARPATHIAN_STAND_BLOCK_ENV_FENCE_NO_RESPONSE_PASS")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--test",action="store_true")
    a.add_argument("--out",type=Path)
    args=a.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:a.error("--out directory required")
    out={
       "schema":"structural.Carpathian116_original_environment_source_only_v1",
       "prespec":PRESPEC,
       "original_beetle_matrix_files_NEVER_DOWNLOADED":True,
       "old_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_results_UNCHANGED":True,
       "eBird_used":False,"TinyFish_used":False
    }
    try:
        out["source_environment_only"]=audit()
        out["status"]=out["source_environment_only"]["status"]
    except SourceStop as e:
        out["status"]=str(e)
        out["source_only_STOP_not_beetle_non_support"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Carpathian116_original_environment_stand_only.json").write_text(
       json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("CARPATHIAN116_ORIGINAL_ENVIRONMENT_STAND_QA",out["status"])

if __name__=="__main__":
    main()
