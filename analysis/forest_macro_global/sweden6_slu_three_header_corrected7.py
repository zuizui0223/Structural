#!/usr/bin/env python3
"""New response-sealed SLU full three-file source with DIAGNOSED 7-field species CSV.

Prior six-field immutable STOP remains; original biology data rows never read.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from sweden6_slu_original_three_file_header_gate import (
    ORIGINAL_URLS, official_get, first_header_only, readme_source_only, SourceStop
)

PRESPEC="docs/FOREST_SWEDEN6_SEMICOLON7_SOURCE_HEADER_CORRECTION_PRESPEC_20261119.md"
SPECIES_SIZE=157911
SPECIES_SHA="a67a905ee05e3994f3e85bc29f8b68fbb314677d6e5a6cc4cd479b2b9d87ec9a"
SPECIES_HEADER=[
    "Block","Plot","Log","Sampling_date","Species","Number","STI"
]
EXPECTED_SOURCES=("boreal_forest_climate_data.csv","specieslist_xylo.csv","readme.txt")

def corrected_onepass(get=official_get):
    files={}
    for name in EXPECTED_SOURCES:
        url,_=ORIGINAL_URLS[name]
        raw=get(url)
        obj={
           "original_source_name":name,
           "official_publisher_download_length":len(raw),
           "official_publisher_source_SHA256":hashlib.sha256(raw).hexdigest(),
           "source_original_biological_rows_READ":0,
        }
        if name=="specieslist_xylo.csv":
            if len(raw)!=SPECIES_SIZE or obj["official_publisher_source_SHA256"]!=SPECIES_SHA:
                raise SourceStop("SLU_SPECIES_DIAGNOSED_157911BYTE_SHA_CHANGED")
            h=first_header_only(raw,7)
            if h["original_HEADER_exact_author_field_names"]!=SPECIES_HEADER or h["original_CSV_header_delimiter"]!="semicolon":
                raise SourceStop("SLU_ORIGINAL_7_FIELD_SPECIES_HEADER_NOT_SAME_AS_DIAGNOSIS")
            obj["source_original_first_header_only"]=h
        elif name=="boreal_forest_climate_data.csv":
            obj["source_original_first_header_only"]=first_header_only(raw,12)
        else:
            obj["source_author_README_method_only"]=readme_source_only(raw)
            if not all(obj["source_author_README_method_only"]["source_author_README_protocol_families_present"].values()):
                raise SourceStop("SLU_AUTHOR_README_STUDY_DESIGN_TOKENS_CHANGED")
        files[name]=obj
    return {
      "source_dataset_doi":"10.5878/dhmc-bq15",
      "source_original_3_file_source_receipts":files,
      "source_6_regions_30_plots_3shade_435_logs_AUTHOR_DESIGN_NOT_RECOUNTED":True,
      "original_species_and_climate_CSV_DATA_ROWS_READ":0,
      "source_prior_6_field_HEADER_FAILURE_REMAINS_STOP":True,
      "original_species_file_HARDPIN_DIAGNOSTIC7":True,
      "source_microclimate2020_beetles2021_temporal_mismatch":True,
      "new_BIOLOGICAL_effect_scored":False,
      "status":"SOURCE_SWEDEN6_SLU_ORIGINAL_THREE_HEADERS_CORRECTED7_PASS",
    }

def test():
    def mock(url):
        if "cac76f42" in url:
            return ("Block;Plot;Shade;Mikrotemp;Makrotemp;CTI;Bark;Diameter;"
                    "Regional_climate;Aspect;Species_richness;Totalab\n"
                    "DONT_OPEN_CLIMATE\n").encode()
        if "4394f565" in url:
            return ("Block;Plot;Log;Sampling_date;Species;Number;STI\n"
                    "DONT_OPEN_SPECIES\n").encode()
        return ("The data set contains 88 rows and 3460 rows. Block: six different study sites "
                "Plot: five study plots. Shade: three different shade level. "
                "Mikro- and makrotemp: measured. Bark: yes. Diameter: yes. "
                "Number: Number of each species.").encode()
    # Check only format with no dependency on hardpin for synthetic.
    c=first_header_only(mock(ORIGINAL_URLS["boreal_forest_climate_data.csv"][0]),12)
    s=first_header_only(mock(ORIGINAL_URLS["specieslist_xylo.csv"][0]),7)
    assert c["original_CSV_header_delimiter"]=="semicolon"
    assert s["original_CSV_header_delimiter"]=="semicolon"
    assert s["original_HEADER_exact_author_field_names"]==SPECIES_HEADER
    assert s["original_data_rows_OPENED"]==0
    assert len(SPECIES_SHA)==64
    print("SYNTHETIC_SLU_CORRECTED_12_AND_7_ORIGINAL_HEADERS_NO_BIOLOGY_PASS")

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    test()
    if a.test:return
    if a.out is None:p.error("--out required")
    result={
      "schema":"structural.SLU_Sweden6_corrected_original_12plus7_headers.v1",
      "precommit":PRESPEC,
      "original_SLU_DOI":"10.5878/dhmc-bq15",
      "prior_six_column_original_STOP_PRESERVED":True,
      "original_beetle_species_3460_RECORD_ROWS_READ":0,
      "old_Finland_Carpathian_England_PREDICTS_NEON_BALA_GEB_biology_NOT_REOPENED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        a1=corrected_onepass()
        result["original_corrected_source_headers_ONLY"]=a1
        result["status"]=a1["status"]
    except SourceStop as exc:
        result["status"]=str(exc)
        result["source_syntax_or_public_access_STOP_NOT_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Sweden6_slu_corrected12plus7_original_headers_only.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("SLU_CORRECTED_12PLUS7_SOURCE_HEADER_GATE",result["status"])
    print("NO_ORIGINAL_BIOLOGICAL_ROWS_READ")
if __name__=="__main__":
    main()
