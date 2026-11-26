#!/usr/bin/env python3
"""Kortmann 2026 source-only author-R field-role static scan.

Only two hash-pinned R scripts opened; original RData/XLSX remain unopened.
Do not execute original R source code or infer field values / biological effects.
"""
from __future__ import annotations
import argparse
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

PRESPEC="docs/FOREST_MACRO_KORTMANN2026_AUTHOR_R_EXACT_FIELD_CODEBOOK_PREFREEZE_20261121.md"
SCRIPTS={
    "scripts_public/iNEXT3D.R":(825,"96c207052b28db90a280c427151c6b651745ce5dd7fe29d3c08fd6b3acdf9854"),
    "scripts_public/models.R":(16103,"240d1b37150db6cf0b8b0288906dd0ba653fe92661a8a07e86a942f5af797b32"),
}
DATA_MEMBERS={
    "data_public/diversity_satellite.rda":67238,
    "data_public/otu_matrix.rda":1371944,
    "data_public/phylogenetic_tree.rda":418222,
    "data_public/FT_Retz_RV-UniWue-2022-003_COI_w-1-tons_results_AIMIDs.xlsx":73378007,
}
# Exact, predetermined role vocabulary; do not emit arbitrary raw code identifiers.
ROLE_TOKENS={
    "site_key":("site","siteid","site_id","sitecode","location","locationid","plot","plotid","plot_id","patch","patchid","patch_id","triplet","forestsite","forest_id"),
    "forest_type":("foresttype","forest_type","forest","habitat","habitat_type","tree","tree_type","spruce","beech","pine","oak"),
    "disturbance_treatment":("disturbance","disturbed","disturb","treatment","treat","management","manage","cleared","clear","logging","logged","salvage"),
    "time_sampling_effort":("sample","sampleid","sample_id","sampling","year","date","samplingdate","sampling_date","firstday","lastday","meanday","days","duration","period","round","effort","trap","trapdays","samplinglength","sampling_length","samplength","offset"),
    "coverage_and_otu":("coverage","completeness","otu","otus","otu_matrix","iNEXT3D","iNEXT","abundance","read_depth","reads"),
}
FUNCTION_TOKENS=("load","readRDS","read.csv","read.csv2","read.table","read_excel","read_xlsx","merge","left_join","inner_join","full_join","group_by","summarise","summarize","aggregate","offset","gam","iNEXT3D","iNEXT","set.seed")
IDENTIFIER=re.compile(r"(?<![A-Za-z0-9._])[A-Za-z][A-Za-z0-9._]*(?![A-Za-z0-9._])")
DOLLAR_FIELD=re.compile(r"\$\s*([A-Za-z][A-Za-z0-9._]*)")
FAMILY={role:set(s.casefold() for s in names) for role,names in ROLE_TOKENS.items()}
SAFE_ALL=set().union(*FAMILY.values())
assert len(SAFE_ALL)<150

def scan_source_code(text):
    # Scans only predeclared safe token classes. No arbitrary identifier
    # or original author code content ever becomes part of output.
    tokens=[v.casefold() for v in IDENTIFIER.findall(text)]
    field_names=[v.casefold() for v in DOLLAR_FIELD.findall(text)]
    if len(tokens)>200000 or len(field_names)>30000:
        raise SourceStop("SOURCE_AUTHOR_CODE_TOKEN_COUNT_UNSAFE")
    totals={key:sum(t in vocab for t in tokens) for key,vocab in FAMILY.items()}
    fields={key:sorted(t for t in vocab if t in field_names) for key,vocab in FAMILY.items()}
    func_counts={
        name:len(re.findall(r"(?<![A-Za-z0-9._])"+re.escape(name)+r"\s*\(",text,flags=re.I))
        for name in FUNCTION_TOKENS
    }
    # Known named original RData paths only, not arbitrary code path strings.
    member_mentions={name: bool(re.search(re.escape(name),text,re.I))
                     for name in DATA_MEMBERS if name.endswith(".rda")}
    return{
        "source_declared_safe_role_token_counts":totals,
        "source_dollar_field_whitelisted_candidates_ONLY":fields,
        "source_whitelisted_function_call_counts":func_counts,
        "known_original_RData_member_literal_path_mentioned":member_mentions,
        "raw_source_R_code_text_NOT_EXPORTED":True,
        "unknown_code_tokens_or_strings_NOT_EXPORTED":True,
        "candidate_field_names_NOT_VERIFIED_source_data_fields":True,
        "source_original_data_member_opened":False,
        "source_original_code_EXECUTED":False,
    }

def run():
    links=original_file_metadata()              # exact canonical publisher / MD5
    archive=official_get_one_zip(links)          # exact original source ZIP
    directory=inspect_central_directory_only(archive)
    if directory["status"]!="SOURCE_ZIP_CENTRAL_DIRECTORY_READY_METADATA_ONLY":
        raise SourceStop("SOURCE_ZIP_DIRECTORY_NOT_VERIFIED")
    summary={}
    with zipfile.ZipFile(io.BytesIO(archive),"r") as z:
        files={n.filename:n for n in z.infolist() if not n.is_dir()}
        if set(files)!=set(SCRIPTS)|set(DATA_MEMBERS):
            raise SourceStop("SOURCE_ZIP_UNEXPECTED_MEMBER_ROSTER")
        for n,size in DATA_MEMBERS.items():
            if files[n].file_size!=size:
                raise SourceStop("SOURCE_DATA_MEMBER_DIRECTORY_SIZE_DRIFT")
        for name,(size,sha) in SCRIPTS.items():
            if files[name].file_size!=size:
                raise SourceStop("SOURCE_AUTHOR_SCRIPT_DIRECTORY_SIZE_DRIFT")
            try:
                script=z.read(name)
            except (zipfile.BadZipFile,KeyError,OSError,ValueError):
                raise SourceStop("SOURCE_AUTHOR_SCRIPT_READ_STOP") from None
            if len(script)!=size or hashlib.sha256(script).hexdigest()!=sha:
                raise SourceStop("SOURCE_AUTHOR_SCRIPT_SHA_OR_SIZE_DRIFT")
            try:
                txt=script.decode("utf-8-sig")
            except UnicodeError:
                raise SourceStop("SOURCE_AUTHOR_SCRIPT_UNEXPECTED_ENCODING") from None
            summary[name]={
                "publisher_original_SHA256_verified":sha,
                "original_author_script_bytes":size,
                "static_method_cues_ONLY":scan_source_code(txt),
            }
    site=summary["scripts_public/models.R"]["static_method_cues_ONLY"]
    roles=site["source_declared_safe_role_token_counts"]
    # Only a reportable method clue; nothing below licenses RData opening.
    return{
        "schema":"structural.Kortmann2026_author_R_exact_method_roles_no_biology.v1",
        "status":("SOURCE_AUTHOR_R_ROLE_CANDIDATES_ONLY_NO_FIELD_FRAME_ADMISSION"
                  if roles["site_key"]>0 and roles["disturbance_treatment"]>0
                  else "SOURCE_METHOD_KEY_ROLE_UNRESOLVED_NO_BIOLOGY"),
        "original_exact_ZIP_MD5_verified":True,
        "exact_original_two_author_R_members_only_opened":summary,
        "original_data_members_content_UNOPENED":True,
        "source_plot_triplet_and_sample_ID_rows_read":0,
        "source_OTU_richness_coverage_or_abundance_rows_read":0,
        "source_R_scripts_executed":False,
        "new_ecological_models_fitted":0,
        "not_independent_geographic_replication":True,
    }

def synthetic():
    test='''obj$Site <- x$plot_ID
    obj$ForestType <- y$stand
    d$Management <- z$Treatment
    m$SamplingLength <- 14
    d$OTU <- 123
    load("data_public/otu_matrix.rda")
    strange_person_name$SECRET_VALUE <- "DO_NOT_EXPORT"
    '''
    r=scan_source_code(test)
    assert "site" in r["source_dollar_field_whitelisted_candidates_ONLY"]["site_key"]
    assert "management" in r["source_dollar_field_whitelisted_candidates_ONLY"]["disturbance_treatment"]
    assert r["known_original_RData_member_literal_path_mentioned"]["data_public/otu_matrix.rda"]
    assert r["source_whitelisted_function_call_counts"]["load"]==1
    s=json.dumps(r)
    assert "SECRET_VALUE" not in s and "DO_NOT_EXPORT" not in s
    assert "123" not in s and "14" not in s
    assert r["source_original_data_member_opened"] is False
    print("SYNTHETIC_KORTMANN_AUTHOR_R_STATIC_FIELD_ROLE_NO_RDATA_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out required")
    result={
        "schema":"structural.Kortmann2026_source_R_role_scan_receipt.v1",
        "prespec":PRESPEC,
        "historical_concept_HTTP302_STOP_unchanged":True,
        "BETAFOR99_original_biological_onepass_SEALED":True,
        "all_previous_biological_endpoints_unchanged":True,
        "no_source_data_RData_or_XLSX_member_GET":True,
        "source_original_biology_rows_read":0,
        "new_organismal_effects":0,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        result["source"]=run()
        result["status"]=result["source"]["status"]
    except SourceStop as e:
        result["status"]="SOURCE_AUTHOR_R_ROLE_STOP_"+str(e)
        result["not_biological_null"]=True
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("KORTMANN_AUTHOR_R_EXACT_FIELD_CODEBOOK",result["status"])
    print("ALL_SOURCE_ORIGINAL_RDATA_AND_XLSX_MEMBERS_STILL_SEALED")

if __name__=="__main__":
    main()
