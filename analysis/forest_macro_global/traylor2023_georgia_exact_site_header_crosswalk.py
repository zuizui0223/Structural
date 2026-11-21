#!/usr/bin/env python3
"""Original Traylor 2023 Georgia 40 forest sites to beetle matrix HEADERS only.

Reads one original site field per forest-environment record and only the
first species-file header. All raw IDs remain runner-private. No beetle
species/guild/count values or forest environment numerics selected.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import urllib.parse
from pathlib import Path

from traylor2023_georgia_original_source_only import (
    FILES, HOST, LIMIT, RECORD, SourceStop, get, official_manifest,
    normalized
)

HEADERS_GUILD={"group","functional","functionalgroup","functional_groups",
               "feedingguild","feedinggroup","saproxylicgroup",
               "trophicgroup","guild","sapgroup","functionaltype"}
HEADERS_TAXON={"species","speciesname","speciesid","genus","taxon","taxonid"}
HEADERS_ABUND={"count","abundance","individuals","abund","number"}
HEADERS_TIME={"period","year","date","samplingperiod","collectionperiod"}
HEADERS_SITE={"site","siteid","site_id","location","locationid"}
EXPECTED_FOREST_COLUMNS=96
EXPECTED_BEETLE_COLUMNS=58

def read_published_one(name,sizes):
    url=HOST+"/records/"+str(RECORD)+"/files/"+urllib.parse.quote(name,safe="")+"?download=1"
    raw=get(url,LIMIT)
    if len(raw)!=sizes[name] or hashlib.md5(raw).hexdigest()!=FILES[name]:
        raise SourceStop("SOURCE_STOP_ORIGINAL_CSV_FILE_MD5_OR_SIZE_DRIFT")
    return raw

def parse_header_csv(raw):
    try: reader=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),
                          delimiter=",",strict=True)
    except UnicodeError as e:raise SourceStop("SOURCE_STOP_SOURCE_NON_UTF8") from e
    try:header=next(reader)
    except (StopIteration,csv.Error) as e:raise SourceStop("SOURCE_STOP_CSV_HEADER_UNAVAILABLE") from e
    return reader,header

def inspect_forest_site_values(raw,expected_rows=40,expected_width=EXPECTED_FOREST_COLUMNS):
    reader,header=parse_header_csv(raw)
    if len(header)!=expected_width:
        raise SourceStop("SOURCE_STOP_FOREST_ENV_COLUMNS_DRIFT")
    pos=[i for i,h in enumerate(header) if normalized(h)=="site"]
    if len(pos)!=1:raise SourceStop("SOURCE_STOP_FOREST_AUTHOR_SITE_FIELD_NOT_UNIQUE")
    site_ids=[]
    for row in reader:
        if len(row)!=len(header):
            raise SourceStop("SOURCE_STOP_FOREST_AUTHOR_ROW_WIDTH")
        # Source environmental values remain untouched; only site ID.
        label=row[pos[0]].strip()
        if not label:raise SourceStop("SOURCE_STOP_ORIGINAL_FOREST_SITE_EMPTY")
        site_ids.append(label)
        if len(site_ids)>1000:raise SourceStop("SOURCE_STOP_FOREST_SITE_ROW_LIMIT")
    if len(site_ids)!=expected_rows or len(set(site_ids))!=expected_rows:
        raise SourceStop("SOURCE_STOP_AUTHOR_40_UNIQUE_FOREST_SITE_IDS_NOT_REPRODUCED")
    return set(site_ids),{"source_original_forest_environment_rows":len(site_ids),
                          "source_original_unique_site_ID_count":len(set(site_ids)),
                          "raw_source_site_names_NOT_EXPORTED":True,
                          "original_environmental_numeric_variables_UNTOUCHED":True}

def inspect_species_header_only(raw,sites,expected_width=EXPECTED_BEETLE_COLUMNS):
    # Safely access FIRST line; not one biological record parsed.
    try:
        b=io.BytesIO(raw).readline(32000)
        if not b.endswith((b"\n",b"\r")):
            raise SourceStop("SOURCE_STOP_BEETLE_FIRST_HEADER_TOO_LONG")
        header=next(csv.reader([b.decode("utf-8-sig").rstrip("\r\n")],
                               delimiter=",",strict=True))
    except (UnicodeError,csv.Error,StopIteration) as e:
        raise SourceStop("SOURCE_STOP_BEETLE_HEADER_PARSER") from e
    if len(header)!=expected_width:
        raise SourceStop("SOURCE_STOP_ORIGINAL_BEETLE_TABLE_HEADER_WIDTH_DRIFT")
    h=[s.strip() for s in header]
    norm=[normalized(s) for s in h]
    if len(set(h))!=len(h):
        raise SourceStop("SOURCE_STOP_BEETLE_DUPLICATE_ORIGINAL_HEADER")
    exact=[name for name in h if name in sites]
    casefold_sites={s.casefold() for s in sites}
    casefold=[name for name in h if name.casefold() in casefold_sites]
    s2=[s for s in sites if s not in h]
    groups={k:sorted(set(n for n in norm if n in {
        normalized(x) for x in v})) for k,v in {
           "guild_or_functional_group":HEADERS_GUILD,
           "taxon":HEADERS_TAXON,
           "abundance":HEADERS_ABUND,
           "time":HEADERS_TIME,
           "author_site_header":HEADERS_SITE}.items()}
    # Don't report individual original 40 site IDs, nor non-generic column labels.
    return {"source_original_beetle_file_header_columns":len(h),
        "source_forest_site_IDs_in_original_beetle_COLUMN_headers_EXACT":len(set(exact)),
        "source_forest_site_IDs_in_beetle_header_CASEFOLD_DIAGNOSTIC_ONLY":len(set(casefold)),
        "forest_site_IDs_NOT_EXACTLY_MATCHED_TO_beetle_column_header":len(s2),
        "source_other_columns_not_exact_site_identifiers":len(h)-len(exact),
        "source_generic_header_category_matches_SAFE_ONLY":{
            key:value for key,value in groups.items() if value},
        "original_site_header_values_NOT_EXPORTED":True,
        "original_beetle_species_guild_abundance_rows_READ":0,
        "no_guess_or_index_based_site_ID_join":True}

def source_gate():
    out={"status":"ORIGINAL_UNQUALIFIED",
         "original_beetle_species_guild_abundance_values_UNREAD":True,
         "old_original_Structural_scorers_SEALED":True}
    try:
        original,sizes=official_manifest()
        out["publisher_record_id"]=original["record"]
        env=read_published_one("site_forest_variables.csv",sizes)
        beetles=read_published_one("species_list_abundance_per_site_functional_group.csv",sizes)
        sites,field=inspect_forest_site_values(env)
        report=inspect_species_header_only(beetles,sites)
        out["forest_site_grain"]=field
        out["beetle_header_site_crosswalk"]=report
        if report["source_forest_site_IDs_in_original_beetle_COLUMN_headers_EXACT"]==40:
            out["status"]="EXACT_SITE_COLUMN_HEADER_CROSSWALK_40_REPRODUCED_BIOLOGY_UNREAD"
        elif report["source_generic_header_category_matches_SAFE_ONLY"].get("author_site_header"):
            out["status"]="ORIGINAL_BEETLE_LONG_SITE_HEADER_POSSIBLE_NEEDS_SEPARATE_METHOD_AUDIT"
        else:
            out["status"]="ORIGINAL_SITE_MATRIX_LINK_NOT_ESTABLISHED_NO_SPECIES_SCORING"
    except SourceStop as e:
        out["status"]=str(e)
        out["SOURCE_STOP_NOT_ECOLOGICAL_NULL"]=True
    return out

def known_truth():
    sites={"S"+str(i) for i in range(40)}
    h=["Species","Functional Group","Abundance"]+sorted(sites)+[
       "meta"+str(i) for i in range(15)]
    assert len(h)==58
    report=inspect_species_header_only((",".join(h)+"\n").encode(),sites)
    assert report["source_forest_site_IDs_in_original_beetle_COLUMN_headers_EXACT"]==40
    assert report["source_forest_site_IDs_in_beetle_header_CASEFOLD_DIAGNOSTIC_ONLY"]==40
    assert report["source_other_columns_not_exact_site_identifiers"]==18
    assert report["source_generic_header_category_matches_SAFE_ONLY"][
        "guild_or_functional_group"]==["functionalgroup"]
    env_header=["site"]+["v"+str(i) for i in range(95)]
    env_rows=[["S"+str(i)]+["0"]*95 for i in range(40)]
    env_data="\n".join([",".join(env_header)]+[",".join(r) for r in env_rows])+"\n"
    ids,s=inspect_forest_site_values(env_data.encode())
    assert len(ids)==40 and s["source_original_forest_environment_rows"]==40
    assert "S0" not in json.dumps(report)
    print("SYNTHETIC_40SITE_SOURCE_FIELD_VS_BEETLE_HEADER_MATCH_AND_PRIVACY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    out={"schema":"structural.Traylor2023_Georgia40_exact_site_matrix_header_crosswalk.v1",
      "precommit":"docs/FOREST_BEETLE_TRAYLOR_US40_SITE_MATRIX_CROSSWALK_PRESPEC_20261117.md",
      "original":source_gate(),
      "no_new_biological_effect_scored":True,
      "old_2026_Piccini_Kriegel_Finland_Thai_PREDICTS_NEON_BALA_GEB_sealed":True,
      "eBird_used":False,"TinyFish_used":False}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Traylor2023_Georgia40_author_site_header_crosswalk.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
