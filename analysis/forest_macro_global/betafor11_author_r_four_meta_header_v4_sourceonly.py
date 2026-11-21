#!/usr/bin/env python3
"""Source-only v4 BETA-FOR OTU matrix nullable X + OTUNr/Family/Order header.

Original authors' v1 R code independently identifies the first four metadata
columns; never read any original OTU data ROW or taxon/source values here.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path

from betafor11_publisher_metadata_preintake_only import (
    get_official_metadata_only, SourceStop,
)
from betafor11_v2_missingversion_firstheader_sourceonly import validate_publisher_v2
from betafor11_information_firstheader_gate import source_publisher_file_link, official_original_file_bytes
from betafor11_otu_original_firstheader_only import (
    published_otutable_link, original_otu_header_streamed,
    source_method_label_universe,
)

PRESPEC="docs/FOREST_MACRO_BETAFOR11_AUTHOR_R_HEADER4_NULL_FIRST_SOURCE_PREFREEZE_20261120.md"
HEADER_SHA="9fc427a6ed338de1f0bd3903668049b9814e0569a2ac9d1defd72d505a4d12af"
AUTHOR_EXPLICIT=frozenset({"OTUNr","Family","Order"})


def verify_author_roles(first_header,sample_labels,*, expected_header_cols=598,expected_sample_cols=594):
    if expected_header_cols==598 and hashlib.sha256(first_header).hexdigest()!=HEADER_SHA:
        raise SourceStop("AUTHOR_R_FIRST_HEADER_SOURCE_SHA_CHANGED")
    try:
        fields=next(csv.reader([first_header.decode("utf-8-sig").rstrip("\r")],
                               delimiter=";",strict=True))
    except (StopIteration,csv.Error,UnicodeError):
        raise SourceStop("AUTHOR_R_ORIGINAL_FIRST_HEADER_CSV_STOP") from None
    if len(fields)!=expected_header_cols or len(sample_labels)!=expected_sample_cols:
        raise SourceStop("AUTHOR_R_ORIGINAL_HEADER_OR_SAMPLE_DIMENSION_DRIFT")
    matched=[(i+1,v.strip()) for i,v in enumerate(fields)
             if v.strip() in sample_labels]
    others=[(i+1,v.strip()) for i,v in enumerate(fields)
            if v.strip() not in sample_labels]
    if len(matched)!=expected_sample_cols or len(others)!=4:
        raise SourceStop("AUTHOR_R_FOUR_META_AND_SAMPLE_LABEL_COUNTS_CHANGED")
    if [i for i,_ in others]!=[1,2,3,4]:
        raise SourceStop("AUTHOR_R_FOUR_META_NOT_FIRST_FOUR_PHYSICAL_FIELDS")
    names=[v for _,v in others]
    if names[0] not in ("","X") or set(names[1:])!=AUTHOR_EXPLICIT or len(set(names[1:]))!=3:
        raise SourceStop("AUTHOR_R_ORIGINAL_FOUR_META_NOT_X_OTUNR_FAMILY_ORDER")
    return {
        "status":"BETAFOR11_AUTHOR_R_FOUR_SOURCE_META_HEADER_ROLES_QUALIFIED_ONLY",
        "original_first_header_sha256_verified":expected_header_cols==598,
        "original_594_author_sample_columns_exact_match":expected_sample_cols==594,
        "original_first_four_meta_indices":[1,2,3,4],
        "original_first_col_unnamed_R_imports_as_X": names[0]=="",
        "original_first_col_literal_X": names[0]=="X",
        "original_OTUNr_column_source_header_position":others[1+names[1:].index("OTUNr")][0],
        "original_Family_column_source_header_position":others[1+names[1:].index("Family")][0],
        "original_Order_column_source_header_position":others[1+names[1:].index("Order")][0],
        "author_singleton_estimator_original_script_pinned": "01_Singleton_Filter.R",
        "author_98pct_Hill_coverage_script_pinned":"06_iNEXT_3D.R",
        "biology_response_source_rows_PARSED":0,
        "original_OTU_species_or_abundance_values_EXPORTED":False,
        "new_organism_effects_scored":0,
        "further_taxon_and_capture_eligibility_REQUIRED":True,
    }


def run():
    publisher=get_official_metadata_only()
    frozen=validate_publisher_v2(publisher)
    if not frozen["original_six_filenames_MD5s_and_sizes_verified"]:
        raise SourceStop("AUTHOR_R_ORIGINAL_SIX_FILE_MD5_DRIFT")
    info_url,info_size=source_publisher_file_link(publisher)
    info=official_original_file_bytes(info_url,info_size)
    sample_set,patch_set,n=source_method_label_universe(info)
    if n!=594 or len(patch_set)!=99:
        raise SourceStop("AUTHOR_R_ORIGINAL_PHYSICAL_SAMPLE_SUPPORT_DRIFT")
    otu_url,otu_size=published_otutable_link(publisher)
    first,received=original_otu_header_streamed(otu_url,otu_size)
    result=verify_author_roles(first,sample_set)
    result["original_full_response_file_byte_size_md5_verified"]=received
    return result


def synthetic():
    h=b";OTUNr;Family;Order;S1;S2"
    x=verify_author_roles(h,{"S1","S2"},expected_header_cols=6,expected_sample_cols=2)
    assert x["original_first_col_unnamed_R_imports_as_X"]
    assert x["original_OTUNr_column_source_header_position"]==2
    bad=b";OTUNr;Order;Unexpected;S1;S2"
    try:verify_author_roles(bad,{"S1","S2"},expected_header_cols=6,expected_sample_cols=2)
    except SourceStop:pass
    else:raise AssertionError("Unexpected original meta field admitted")
    print("SYNTHETIC_BETAFOR11_AUTHOR_R_FOUR_META_FIRST_HEADER_SOURCEONLY_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out needed")
    result={
        "schema":"structural.BETAFOR11_original_2025_author_R_four_meta_firstheader.v1",
        "prespec":PRESPEC,
        "all_previous_version_schema_technical_STOPs_preserved":True,
        "original_source_response_rows_semantically_parsed":0,
        "new_biodiversity_estimations":0,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        result["author_method_header"]=run()
        result["status"]=result["author_method_header"]["status"]
    except SourceStop as ex:
        result["status"]="AUTHOR_R_FOUR_META_SOURCE_STOP_"+str(ex)
        result["not_a_biological_null"]=True
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("BETAFOR11_ORIGINAL_AUTHOR_FOUR_META_HEADER",result["status"])
    print("SOURCE_ORGANISM_NUMERIC_ROWS_PARSED=0; NO_NEW_MODEL_FITS")


if __name__=="__main__":
    main()
