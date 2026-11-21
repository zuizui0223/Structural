#!/usr/bin/env python3
"""Gloor original Carpathian 116 plot beetle + forest environment ID-only crosswalk.

ONLY first plotid field is parsed from each source row. Species observations and
all original forest numeric/categorical response cells remain entirely opaque.
Read one fixed publisher file per listed role, with exact original MD5/length.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

from carpathian116_original_author_schema_gate import (
    original_record_links, official_get, FROZEN_FILES, SourceStop,
)

PRESPEC = "docs/FOREST_MACRO_CARPATHIAN116_PLOTID_SOURCE_CROSSWALK_PRESPEC_20261118.md"
FILES = (
    ("B_SR_BEETLES.csv", 60, 242, "beetle_B"),
    ("S_SR_BEETLES.csv", 56, 161, "beetle_S"),
    ("Beech.csv", 60, 21, "environment_B"),
    ("Spruce.csv", 56, 21, "environment_S"),
    ("Beech_Spruce.csv", 116, 21, "environment_combined"),
)
PLOT_ID_GRAMMAR=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_ .\-]{0,60}$")
ENV_NAME_GRAMMAR=re.compile(r"^[A-Za-z][A-Za-z0-9_ .%()/\-]{0,75}$")
EXPECT_NAME="plotid"

def source_first_cell_only(raw,name,expected_rows,expected_fields,role):
    # Important: after file source MD5 verification, split on physical LF;
    # decode ONLY the first original CSV field from each raw source line.
    lines=raw.split(b"\n")
    if lines[-1]==b"":
        lines.pop()
    if not lines or len(lines)!=expected_rows+1:
        raise SourceStop("SOURCE_CSV_PHYSICAL_ROW_COUNT_NOT_PUBLISHED_PLOT_GRAIN")
    try:
        header=lines[0].decode("utf-8-sig").rstrip("\r")
        names=next(csv.reader([header],delimiter=",",strict=True))
    except (UnicodeError,csv.Error,StopIteration):
        raise SourceStop("SOURCE_CSV_FIRST_HEADER_NOT_VALID") from None
    if len(names)!=expected_fields or names[0].casefold()!=EXPECT_NAME:
        raise SourceStop("SOURCE_CSV_EXPECTED_FIRST_PLOTID_OR_COLUMNS_DRIFT")
    vals=[]
    for raw_line in lines[1:]:
        if not raw_line or b"," not in raw_line:
            raise SourceStop("SOURCE_CSV_EMPTY_OR_NONCOMMA_ROW_METHOD_STOP")
        first=raw_line.split(b",",1)[0]
        # Never decode or parse any byte of the beetle or environment values
        # following the first original comma. Only source *identity* cell.
        try:
            cell=first.decode("utf-8").strip().strip("\r")
            if cell.startswith('"'):
                cell=next(csv.reader([cell],strict=True))[0]
        except (UnicodeError,csv.Error,StopIteration):
            raise SourceStop("SOURCE_ORIGINAL_PLOTID_FIELD_PARSE_STOP") from None
        cell=cell.strip()
        if not PLOT_ID_GRAMMAR.fullmatch(cell):
            raise SourceStop("SOURCE_ORIGINAL_PLOTID_TOKEN_GRAMMAR_STOP")
        vals.append(cell)
    if len(vals)!=len(set(vals)):
        raise SourceStop("SOURCE_ORIGINAL_PLOTID_NOT_UNIQUE_IN_PHYSICAL_TABLE")
    safe_env=[]
    if role.startswith("environment"):
        for i,n in enumerate(names):
            if ENV_NAME_GRAMMAR.fullmatch(n):
                safe_env.append({"column_index_1based":i+1,"original_environment_field_name_ONLY":n})
    return {
        "name":name,
        "role":role,
        "original_physical_lines_excluding_header":len(vals),
        "original_distinct_original_source_PLOTID":len(set(vals)),
        "original_first_header_field_count":len(names),
        "original_environment_header_names_SAFE_only_if_env_table":safe_env,
        "source_plant_beetle_species_column_labels_NOT_EXPORTED":True,
        "non_PLOTID_beetle_or_wood_rows_VALUES_NEVER_DECODED":True,
        "raw_original_PLOTID_values_NOT_EXPORTED":True,
        "_original_PLOTID_internal_set":set(vals)
    }

def audit(original):
    table={}
    for name,rows,cols,role in FILES:
        n,md5=FROZEN_FILES[name]
        raw=official_get(original[name],"*/*",n+1000)
        if len(raw)!=n or hashlib.md5(raw).hexdigest()!=md5:
            raise SourceStop("SOURCE_ORIGINAL_CSV_PUBLISHER_MD5_BYTES_CHANGED")
        table[role]=source_first_cell_only(raw,name,rows,cols,role)
    keys={role:record.pop("_original_PLOTID_internal_set") for role,record in table.items()}
    a=keys["beetle_B"];b=keys["beetle_S"];c=keys["environment_B"];d=keys["environment_S"];u=keys["environment_combined"]
    summary={
       "original_beech_beetle_vs_beech_environment_exact_plotid":len(a&c),
       "original_beech_beetle_not_in_beech_environment":len(a-c),
       "original_beech_environment_not_in_beetle":len(c-a),
       "original_spruce_beetle_vs_spruce_environment_exact_plotid":len(b&d),
       "original_spruce_beetle_not_in_spruce_environment":len(b-d),
       "original_spruce_environment_not_in_beetle":len(d-b),
       "beech_spruce_original_cross_forest_PLOTID_token_collision_count":len(a&b),
       "beech_plus_spruce_species_source_original_unique_IDs":len(a|b),
       "beech_plus_spruce_env_source_original_unique_IDs":len(c|d),
       "combined_env_source_exact_IDs_matching_union_original_beetles":len(u&(a|b)),
       "combined_env_original_IDs_absent_from_original_beetle_union":len(u-(a|b)),
       "original_beetle_union_IDs_absent_from_combined_env":len((a|b)-u),
       "no_row_order_JOIN_or_id_renaming_performed":True,
       "original_species_catches_environment_measurements_READ":0,
       "original_sample_ID_values_EXPORTED":False,
    }
    eligible=(len(a)==60 and len(b)==56 and len(c)==60 and len(d)==56 and
              len(u)==116 and not (a^c) and not (b^d) and not (a&b) and
              u==(a|b))
    return {
      "schema":"structural.Gloor2026_Carpathian116_plotid_sourceonly.v1",
      "prespec":PRESPEC,
      "source_original_table_schemas":table,
      "original_exact_cross_source_identity_counts":summary,
      "new_effect_estimated":False,
      "source_stand_or_mountain_range_block_NOT_YET_VERIFIED":True,
      "source_authoritative_beetle_feeding_guild_NOT_YET_VERIFIED":True,
      "source_per_trap_effort_zero_denominator_NOT_YET_VERIFIED":True,
      "status":("SOURCE_ORIGINAL_PLOTID_ONE_TO_ONE_CANDIDATE"
                if eligible else
                "SOURCE_ORIGINAL_PLOTID_CROSSWALK_PARTIAL_OR_COLLISION_HOLD")
    }

def synthetic():
    b=("plotid,Beetle1,Beetle2\n"
       "B1,1,3\n"
       "B2,2,0\n").encode()
    t=source_first_cell_only(b,"B_SR_BEETLES.csv",2,3,"beetle_B")
    assert t["original_distinct_original_source_PLOTID"]==2
    assert t["non_PLOTID_beetle_or_wood_rows_VALUES_NEVER_DECODED"]
    assert "Beetle1" not in json.dumps({k:v for k,v in t.items() if k!="_original_PLOTID_internal_set"})
    try:
        source_first_cell_only(b.replace(b"B2,",b"B1,"),"X",2,3,"beetle_B")
        raise AssertionError("duplicate original sample plot ID was accepted")
    except SourceStop:
        pass
    e=("plotid,deadwood_volume,Canopy_cover\n"
       "B1,5.3,43\n"
       "B2,6.5,51\n").encode()
    p=source_first_cell_only(e,"Beech.csv",2,3,"environment_B")
    assert len(p["original_environment_header_names_SAFE_only_if_env_table"])==3
    assert b"5.3" not in json.dumps({k:v for k,v in p.items() if k!="_original_PLOTID_internal_set"}).encode()
    print("SYNTHETIC_CARPATHIAN116_SOURCE_PLOTID_EXACT_UNION_AND_NO_BIOLOGY_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:ap.error("--out needed")
    rep={
        "schema":"structural.Gloor2026_Carpathian116_original_PLOTID_firstfield_only.v1",
        "prespec":PRESPEC,
        "original_record":22142713,
        "old_Finland_Chiu_BELongDead_Piccini_PREDICTS_NEON_BALA_GEB_results_UNCHANGED":True,
        "original_beetle_abundance_or_species_VALUES_READ":False,
        "original_environment_numeric_VALUES_READ":False,
        "eBird_used":False,"TinyFish_used":False
    }
    try:
        rep["source_idonly_qualification"]=audit(original_record_links())
        rep["status"]=rep["source_idonly_qualification"]["status"]
    except SourceStop as ex:
        rep["status"]=str(ex)
        rep["source_only_failure_NOT_ecological_null"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    f=args.out/"Carpathian116_original_beetles_and_forest_PLOTID_only.json"
    f.write_text(json.dumps(rep,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("CARPATHIAN116_ORIGINAL_PLOTID_ONLY",rep["status"])

if __name__=="__main__":
    main()
