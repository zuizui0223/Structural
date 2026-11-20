#!/usr/bin/env python3
"""Kortmann2026 original two small R scripts + ZIP role names ONLY.

This reads original source code as METHOD metadata, never executes it, and
does not open any original .rda, .xlsx, OTU, capture or ecology data member.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path

from kortmann2026_17775805_original_zip_directory_only import (
    SourceStop, original_file_metadata, official_get_one_zip,
    inspect_central_directory_only,
)

PRESPEC = "docs/FOREST_MACRO_KORTMANN2026_17775805_ORIGINAL_AUTHOR_CODE_ROLE_GATE_PREFREEZE_20261120.md"
SCRIPTS = {
    "scripts_public/iNEXT3D.R": 825,
    "scripts_public/models.R": 16103,
}
EXPECTED_RDA_COUNT = 3
EXPECTED_XLSX = {
    "data_public/FT_Retz_RV-UniWue-2022-003_COI_w-1-tons_results_AIMIDs.xlsx": 73378007,
}
LEXICON = {
    "physical_site_patch_triplet": re.compile(r"(?i)\b(?:sites?|plots?|patch(?:es)?|triplets?)\b"),
    "forest_tree_type": re.compile(r"(?i)\b(?:forest(?:s)?|trees?|spruce|beech|oak|pine)\b"),
    "disturbance_management": re.compile(r"(?i)\b(?:disturb(?:ed|ance)?|cleared?|logging|managed|unmanaged)\b"),
    "effort_time_sampling": re.compile(r"(?i)\b(?:sampling|samples?|traps?|effort|dates?|periods?|days?)\b"),
    "otu_or_sequence": re.compile(r"(?i)\b(?:OTUs?|sequences?|metabarcod(?:ing|e))\b"),
    "coverage_model": re.compile(r"(?i)\b(?:coverage|iNEXT(?:3D)?|completeness)\b"),
    "source_data_reader": re.compile(r"(?i)\b(?:load|readRDS|read\.csv|read_excel|read\.xlsx|read_xlsx|import)\b"),
    "species_replacement": re.compile(r"(?i)\b(?:beta|turnover|simpson|sorensen|dissimilarity)\b"),
}


def read_only_two_original_scripts_from_zip(raw):
    directory=inspect_central_directory_only(raw)
    if directory["status"]!="SOURCE_ZIP_CENTRAL_DIRECTORY_READY_METADATA_ONLY":
        raise SourceStop("SOURCE_ORIGINAL_DIRECTORY_NOT_AUTHENTICATED")
    with zipfile.ZipFile(io.BytesIO(raw),"r") as z:
        table={info.filename:info for info in z.infolist() if not info.is_dir()}
        if len(table)!=6:
            raise SourceStop("SOURCE_ORIGINAL_MEMBER_DENOMINATOR_CHANGED")
        seen_rda={
            n:info.file_size for n,info in table.items()
            if Path(n).suffix.lower() in {".rda",".rdata",".rds"}
        }
        if len(seen_rda)!=EXPECTED_RDA_COUNT:
            raise SourceStop("SOURCE_ORIGINAL_RDA_FILE_COUNT_DRIFT")
        seen_xlsx={n:info.file_size for n,info in table.items()
                   if Path(n).suffix.lower()==".xlsx"}
        if seen_xlsx!=EXPECTED_XLSX:
            raise SourceStop("SOURCE_ORIGINAL_XLSX_ID_OR_LENGTH_DRIFT")
        script_infos={n:info for n,info in table.items() if Path(n).suffix.lower()==".r"}
        if set(script_infos)!=set(SCRIPTS):
            raise SourceStop("SOURCE_ORIGINAL_R_SCRIPT_NAME_DRIFT")
        reports={}
        for name,nbyte in SCRIPTS.items():
            if table[name].file_size!=nbyte:
                raise SourceStop("SOURCE_ORIGINAL_R_SCRIPT_LENGTH_DRIFT")
            try:
                source_bytes=z.read(name)  # ONLY two author .R code members; no data
            except (zipfile.BadZipFile,KeyError,OSError,ValueError):
                raise SourceStop("SOURCE_AUTHOR_R_SCRIPT_MEMBER_READ_STOP") from None
            if len(source_bytes)!=nbyte:
                raise SourceStop("SOURCE_AUTHOR_R_SCRIPT_ACTUAL_BYTES_LENGTH_STOP")
            try:
                source_text=source_bytes.decode("utf-8-sig")
            except UnicodeError:
                raise SourceStop("SOURCE_AUTHOR_R_SCRIPT_ENCODING_STOP") from None
            reports[name]={
                "author_original_script_bytes_verified":nbyte,
                "original_R_script_SHA256":hashlib.sha256(source_bytes).hexdigest(),
                "lexical_role_counts_ONLY":{
                    label:len(rx.findall(source_text))
                    for label,rx in LEXICON.items()
                },
                "code_NOT_EXECUTED":True,
                "code_original_text_NOT_EXPORTED":True,
            }
        if not any(v for record in reports.values()
                   for v in record["lexical_role_counts_ONLY"].values()):
            raise SourceStop("SOURCE_CODE_NO_RECOGNIZABLE_METHOD_ROLE_WORDS")
        return {
            "status":"SOURCE_ORIGINAL_AUTHOR_CODE_ROLE_HINTS_ONLY_NO_BIOLOGY",
            "original_ZIP_bytes_authentic_and_directory_unchanged":True,
            "exact_two_code_members_opened_only":sorted(SCRIPTS),
            "original_R_scripts_fingerprint_and_method_word_counts_ONLY":reports,
            "three_original_RData_member_names_DIRECTORY_ONLY":[
                {"original_safe_source_role_name":n,
                 "advertised_bytes_NOT_OPENED":size}
                for n,size in sorted(seen_rda.items())
            ],
            "original_XLSX_member":list(EXPECTED_XLSX),
            "all_original_RData_and_XLSX_member_CONTENT_UNOPENED":True,
            "biological_OTU_or_site_values_accessed":False,
            "original_R_code_NOT_EXECUTED":True,
            "new_biological_model_fits":0,
        }


def synthetic():
    data=io.BytesIO()
    with zipfile.ZipFile(data,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("scripts_public/iNEXT3D.R",
                   ("plot sample coverage iNEXT " + " "*(825-27)).encode()[:825])
        z.writestr("scripts_public/models.R",
                   ("forest plot sample management " + " "*(16103-30)).encode()[:16103])
        for n in range(3):
            z.writestr(f"data_public/synthetic{n}.rda",b"NEVER_OPEN")
        z.writestr(list(EXPECTED_XLSX)[0],b"\0"*73378007)
    # This synthetic uses 73 MB in a highly compressed ZIP to test that the
    # original XLSX *member* is NOT opened. No real source values are involved.
    result=read_only_two_original_scripts_from_zip(data.getvalue())
    assert result["all_original_RData_and_XLSX_member_CONTENT_UNOPENED"] is True
    assert result["new_biological_model_fits"]==0
    print("SYNTHETIC_KORTMANN_AUTHOR_CODE_ONLY_RDA_XLSX_SEALED_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out required")
    report={
        "schema":"structural.Kortmann2026_original_two_code_members_role_only.v1",
        "prespec":PRESPEC,
        "previous_Zenodo_concept_HTTP302_STOP_unchanged":True,
        "original_BETAFOR99_beta_onepass_SEALED":True,
        "original_organism_or_site_data_rows_read":0,
        "new_ecological_effects":0,
        "eBird_used":False,
        "TinyFish_used":False,
    }
    try:
        link=original_file_metadata()
        source_zip=official_get_one_zip(link)
        report["source_role_audit"]=read_only_two_original_scripts_from_zip(source_zip)
        report["status"]=report["source_role_audit"]["status"]
    except SourceStop as e:
        report["status"]="SOURCE_AUTHOR_CODE_ONLY_STOP_"+str(e)
        report["no_biology_null_inferred_from_source_STOP"]=True
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("KORTMANN_AUTHOR_CODE_ROLE_SOURCE",report["status"])
    print("ORIGINAL_RDA_XLSX_BIOLOGICAL_MEMBERS_UNOPENED")


if __name__=="__main__":main()
