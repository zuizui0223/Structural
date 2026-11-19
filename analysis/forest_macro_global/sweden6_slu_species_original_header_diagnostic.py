#!/usr/bin/env python3
"""Response-opaque diagnosis of one SLU species CSV FIRST physical header.

Never parses original 3460 beetle records, temperature, log or taxon values.
Preserves prior six-column frozen STOP as a separate historical result.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

from sweden6_slu_original_three_file_header_gate import official_get, SourceStop

PRESPEC="docs/FOREST_SWEDEN6_ORIGINAL_SPECIES_FIRST_HEADER_DIAGNOSTIC_PRESPEC_20261119.md"
SOURCE="https://earchive.slu.se/bitstreams/4394f565-ede9-457b-a1b1-c4e5d042cb88/download"
DELIMITERS=((",","comma"),(";","semicolon"),("\t","tab"))
MAX_HEADER_BYTES=65536

def original_firstline_diag(raw):
    line=raw.split(b"\n",1)[0].rstrip(b"\r")
    if not line or len(line)>MAX_HEADER_BYTES or b"\x00" in line:
        raise SourceStop("SLU_SPECIES_ORIGINAL_FIRST_LINE_BINARY_OR_TOO_LONG")
    try:
        txt=line.decode("utf-8-sig")
    except UnicodeError:
        raise SourceStop("SLU_SPECIES_ORIGINAL_HEADER_NOT_UTF8") from None
    parsed={}
    for delimiter,label in DELIMITERS:
        try:
            names=next(csv.reader([txt],delimiter=delimiter,strict=True))
        except (csv.Error,StopIteration):
            parsed[label]={"grammar_valid":False}
            continue
        safe=(
            len(names)<=40 and len(names)>=1 and
            all(0<len(v.strip())<=120 and
                not re.search(r"[\r\n\x00-\x1f]",v) for v in names)
        )
        parsed[label]={
            "grammar_valid":True,
            "field_count":len(names),
            "unique_headers":len(names)==len(set(names)),
            "no_empty_field_labels":all(bool(x.strip()) for x in names),
            "header_labels_lexically_SAFE":safe,
        }
        if label in ("comma","semicolon","tab") and len(names)>1 and safe:
            parsed[label]["source_original_first_header_names_ONLY"]=names
    candidates=[k for k,v in parsed.items() if v.get("grammar_valid") and
                v.get("field_count",0)>1 and
                v.get("unique_headers") and v.get("no_empty_field_labels") and
                v.get("header_labels_lexically_SAFE")]
    return {
       "source_original_species_file_bytes":len(raw),
       "source_original_species_file_sha256":hashlib.sha256(raw).hexdigest(),
       "source_original_first_line_bytes":len(line),
       "source_original_first_line_sha256":hashlib.sha256(line).hexdigest(),
       "source_first_header_parse_by_literal_delimiter":parsed,
       "source_delimiter_candidates_with_gt1_column":candidates,
       "source_candidate_unambiguous":len(candidates)==1,
       "source_original_species_rows_SEMANTICALLY_READ":0,
       "original_first_header_only_source_diagnosis":True,
       "original_species_names_abundances_log_IDs_or_readcounts_EXPORTED":False,
       "source_previous_expected_six_columns_STOP_PRESERVED":True,
       "status":("SOURCE_SWEDEN6_SPECIES_CSV_ORIGINAL_FIRST_HEADER_DIAGNOSIS_ONLY"
                 if len(candidates)==1 else
                 "SOURCE_SWEDEN6_SPECIES_FIRST_HEADER_AMBIGUOUS_STOP"),
    }

def synthetic_test():
    raw=b'Block;Plot;Log;Sampling_date;Species;Number;STI\nSECRET_SPECIES_VALUE;999\n'
    r=original_firstline_diag(raw)
    assert r["source_candidate_unambiguous"]
    assert r["source_delimiter_candidates_with_gt1_column"]==["semicolon"]
    assert r["source_first_header_parse_by_literal_delimiter"]["semicolon"]["field_count"]==7
    assert r["source_previous_expected_six_columns_STOP_PRESERVED"]
    assert "SECRET_SPECIES_VALUE" not in json.dumps(r)
    assert r["source_original_species_rows_SEMANTICALLY_READ"]==0
    print("SYNTHETIC_SLU_SPECIES_ORIGINAL_FIRSTHEADER_7SEMICOLON_NO_BIOLOGY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic_test()
    if a.test:return
    if a.out is None:p.error("--out required")
    result={
      "schema":"structural.SLU_sweden6_species_original_firstline_diagnostic.v1",
      "precommit":PRESPEC,
      "original_verified_SLUpublisher_DOI":"10.5878/dhmc-bq15",
      "prior_6_column_script_STOP_NOT_REVISED":True,
      "original_climate_wood_beetle_response_ROWS_READ":0,
      "all_previous_Structural_forest_biology_outcomes_UNCHANGED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        raw=official_get(SOURCE)
        result["original_source_single_file_FIRST_HEADER_DIAGNOSIS"]=original_firstline_diag(raw)
        result["status"]=result["original_source_single_file_FIRST_HEADER_DIAGNOSIS"]["status"]
    except SourceStop as exc:
        result["status"]=str(exc)
        result["source_or_format_STOP_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Sweden6_SLU_original_species_first_header_diagnostic.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("SLU_SWEDEN6_SPECIES_ORIGINAL_HEADER_DIAG",result["status"])
    print("NO_ORIGINAL_3460_BIOLOGICAL_SPECIES_ROWS_OPENED")
if __name__=="__main__":
    main()
