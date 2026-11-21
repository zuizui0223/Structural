#!/usr/bin/env python3
"""Versioned, separately frozen 7-column source-header re-admission (NO biology).

Original 6-column method-only STOP retained. Exactly official 3 SLU bitstreams;
CSV bodies are kept opaque, FIRST physical header line only is decoded.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

from sweden6_slu_original_three_file_header_gate import (
    ORIGINAL_URLS, official_get, first_header_only, readme_source_only, SourceStop,
)

PRESPEC="docs/FOREST_SWEDEN6_SEMICOLON7_SOURCE_HEADER_CORRECTION_PRESPEC_20261119.md"
SPECIES_SIZE=157911
SPECIES_SHA256="a67a905ee05e3994f3e85bc29f8b68fbb314677d6e5a6cc4cd479b2b9d87ec9a"
SPECIES_HEADER_SHA256="6afd0dd229cf48e6e473d1fef419260ec8748ae81ec35a4b1e0087e6582cc443"
SPECIES_HEADERS=["Block","Plot","Log","Sampling_date","Species","Number","STI"]
CLIMATE_SOURCE="boreal_forest_climate_data.csv"
SPECIES_SOURCE="specieslist_xylo.csv"
README_SOURCE="readme.txt"
README_CRITICAL=("original_SIX_geographic_blocks",
                 "original_30_plot_hierarchy",
                 "original_THREE_shade_levels",
                 "original_2020_micro_macro_temperature",
                 "original_substrate_bark_and_diameter",
                 "original_2021_beetle_abundance_fields")

def first_line_bytes(blob):
    return blob.split(b"\n",1)[0].rstrip(b"\r")

def source_only_once(fetch=official_get):
    out={}
    for name in (CLIMATE_SOURCE,SPECIES_SOURCE,README_SOURCE):
        url,old_declared=ORIGINAL_URLS[name]
        blob=fetch(url)
        current={
            "original_SLUpublisher_file_name":name,
            "original_original_bytes":len(blob),
            "original_SHA256":hashlib.sha256(blob).hexdigest(),
            "original_source_exact_official_download_ONLY":True,
        }
        if name==SPECIES_SOURCE:
            if len(blob)!=SPECIES_SIZE or current["original_SHA256"]!=SPECIES_SHA256:
                raise SourceStop("SLU_2025_SPECIES_PUBLISHED_ORIGINAL_SHA256_DRIFT")
            if hashlib.sha256(first_line_bytes(blob)).hexdigest()!=SPECIES_HEADER_SHA256:
                raise SourceStop("SLU_2025_SPECIES_ORIGINAL_FIRST_LINE_SHA256_DRIFT")
            current.update(first_header_only(blob,7))
            if (current["original_CSV_header_delimiter"]!="semicolon" or
                current["original_HEADER_exact_author_field_names"]!=SPECIES_HEADERS):
                raise SourceStop("SLU_2025_SPECIES_CORRECTED_SEVEN_AUTHOR_FIELDS_DRIFT")
        elif name==CLIMATE_SOURCE:
            current.update(first_header_only(blob,12))
            # Do not infer source numeric content from matching header names.
            if current["original_HEADER_exact_author_field_names"][:3]!=["Block","Plot","Shade"]:
                raise SourceStop("SLU_2025_CLIMATE_AUTHOR_ID_SHADE_HEADER_DRIFT")
        else:
            current.update(readme_source_only(blob))
            flags=current["source_author_README_protocol_families_present"]
            if not all(flags.get(k,False) for k in README_CRITICAL):
                raise SourceStop("SLU_2025_AUTHOR_README_CORE_METHOD_FIELDS_NOT_VERIFIED")
        out[name]=current
    return {
       "status":"SOURCE_SWEDEN6_SLU_ORIGINAL_THREE_HEADERS_CORRECTED7_PASS",
       "source_original_author_DOI":"10.5878/dhmc-bq15",
       "original_file_sha_and_header_receipts_ONLY":out,
       "original_6_col_previous_original_gate_STOP_RETAINED":True,
       "climate_original_CSV_value_rows_OPENED":0,
       "beetle_original_CSV_value_rows_OPENED":0,
       "source_original_30plots_3shade_6region_AUTHOR_DESIGN_NOT_YET_RECOUNTED":True,
       "source_2020_microclimate_vs_2021_beetle_sample_lag":True,
       "source_no_same_trap_method_vertical_stratum_comparison":True,
       "new_biological_or_macro_response_result_COMPUTED":False,
    }

def synthetic():
    orig_species=("Block;Plot;Log;Sampling_date;Species;Number;STI\n"+
                  "HIDDEN_BIOLOGICAL_RESPONSE;01;12;2021-05-01;Rare_species;3;15\n").encode()
    climate=("Block,Plot,Shade,Tmicro,Tmacro,Bark,Diameter,CTI,Richness,Abundance,Climate,Aspect\n"+
             "HIDDEN_CLIMATE_VALUES,01,1,11,12,13,14,15,16,17,18,19\n").encode()
    from sweden6_slu_original_three_file_header_gate import README_KEYWORDS
    assert first_header_only(orig_species,7)["original_HEADER_exact_author_field_names"]==SPECIES_HEADERS
    assert first_header_only(climate,12)["original_HEADER_exact_author_field_names"][:3]==["Block","Plot","Shade"]
    assert hashlib.sha256(first_line_bytes(orig_species)).hexdigest()==SPECIES_HEADER_SHA256  # synthetic intentionally uses the exact frozen original header
    assert README_CRITICAL
    out=json.dumps(first_header_only(orig_species,7))
    assert "HIDDEN_BIOLOGICAL_RESPONSE" not in out
    assert "Rare_species" not in out
    print("SYNTHETIC_SLU_CORRECTED7_CSV_HEADERS_AND_OUTCOME_SEAL_PASS")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--test",action="store_true")
    a.add_argument("--out",type=Path)
    x=a.parse_args()
    synthetic()
    if x.test:return
    if x.out is None:a.error("--out required")
    report={
        "schema":"structural.SLU_sweden6_2025_original_corrected7_source_headers_only.v1",
        "precommit":PRESPEC,
        "source_original_species_SHA256_previously_verified":SPECIES_SHA256,
        "source_original_species_firstline_SHA256_previously_verified":SPECIES_HEADER_SHA256,
        "previous_original_six_column_SOURCE_STOP_UNCHANGED":True,
        "original_2020_temperature_and_2021_beetle_original_rows_READ":0,
        "all_earlier_England_Carpathian_Finland_PREDICTS_Thai_NEON_BALA_GEB_scores_UNCHANGED":True,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        data=source_only_once()
        report["original_source_first_header_only_receipts"]=data
        report["status"]=data["status"]
    except SourceStop as e:
        report["status"]=str(e)
        report["source_transport_or_original_method_STOP_not_ecological_null"]=True
    x.out.mkdir(parents=True,exist_ok=True)
    (x.out/"SLU_sweden6_corrected7_original_source_header_receipt.json").write_text(
         json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("SLU_SWEDEN6_CORRECTED7_SOURCE_ONLY",report["status"])
    print("ZERO_ORIGINAL_CSV_DATA_ROWS_OPENED_AND_PREVIOUS_STOP_RETAINED")

if __name__=="__main__":
    main()
