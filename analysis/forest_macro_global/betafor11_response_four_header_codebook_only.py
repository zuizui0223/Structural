#!/usr/bin/env python3
"""Original BETA-FOR OTU file: four non-sample first-header field names ONLY.

Never parse any original taxon/abundance data row; source full MD5 check first.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from pathlib import Path

from betafor11_publisher_metadata_preintake_only import (
    get_official_metadata_only, SourceStop,
)
from betafor11_v2_missingversion_firstheader_sourceonly import validate_publisher_v2
from betafor11_information_firstheader_gate import (
    source_publisher_file_link, official_original_file_bytes,
)
from betafor11_otu_original_firstheader_only import (
    published_otutable_link, original_otu_header_streamed,
    source_method_label_universe,
)

PRESPEC="docs/FOREST_MACRO_BETAFOR11_RESPONSE_FOUR_HEADER_CODEBOOK_PREFREEZE_20261120.md"
ORIGINAL_HEADER_SHA="9fc427a6ed338de1f0bd3903668049b9814e0569a2ac9d1defd72d505a4d12af"
SAFE_FIELD=re.compile(r"^[A-Za-z][A-Za-z0-9_ .-]{0,50}$")


def audit_four_header_fields(first_header, sample_literals):
    if hashlib.sha256(first_header).hexdigest()!=ORIGINAL_HEADER_SHA:
        raise SourceStop("ORIGINAL_OTU_HEADER_SHA_CHANGED")
    try:
        text=first_header.decode("utf-8-sig").rstrip("\r")
        cols=next(csv.reader([text],delimiter=";",strict=True))
    except (UnicodeError,csv.Error,StopIteration):
        raise SourceStop("ORIGINAL_OTU_HEADER_PARSE_FAILED") from None
    if len(cols)!=598 or len(sample_literals)!=594:
        raise SourceStop("ORIGINAL_OTU_OR_SAMPLE_DENOMINATOR_CHANGED")
    matches=[i+1 for i,v in enumerate(cols) if v.strip() in sample_literals]
    remaining=[(i+1,v.strip()) for i,v in enumerate(cols) if v.strip() not in sample_literals]
    if len(matches)!=594 or len(set(matches))!=594 or len(remaining)!=4:
        raise SourceStop("ORIGINAL_OTU_SAMPLE_HEADER_PAIRING_DRIFT")
    if (any(not SAFE_FIELD.fullmatch(name) for _,name in remaining)
        or len({name.casefold() for _,name in remaining})!=4):
        raise SourceStop("ORIGINAL_UNMATCHED_FOUR_HEADER_FIELDS_UNSAFE_OR_DUPLICATE")
    return {
        "status":"BETAFOR11_ORIGINAL_FOUR_NON_SAMPLE_HEADER_NAMES_PROVEN_SOURCE_ONLY",
        "original_header_sha256_matches_previous_independent_source":True,
        "full_publisher_original_file_MD5_verified_by_stream":True,
        "original_header_field_count":598,
        "original_sample_fields_exactly_matched":594,
        "source_author_four_non_sample_header_fields": [
            {"original_index_1based":i,"safe_non_sample_column_name_ONLY":n}
            for i,n in remaining
        ],
        "source_original_OTU_data_rows_and_numeric_cells_parsed":0,
        "source_original_taxon_identifiers_or_sample_ID_values_exported":False,
        "author_codebook_ontology_not_yet_verified":True,
        "new_biodiversity_effects":0,
    }


def run():
    original=get_official_metadata_only()
    v2=validate_publisher_v2(original)
    if not v2["original_six_filenames_MD5s_and_sizes_verified"]:
        raise SourceStop("ORIGINAL_PUBLISHER_SIX_FILES_CHANGED")
    info_link,info_size=source_publisher_file_link(original)
    info=official_original_file_bytes(info_link,info_size)
    sample_literals,patches,nunique=source_method_label_universe(info)
    if nunique!=594 or len(patches)!=99:
        raise SourceStop("ORIGINAL_SOURCE_METHOD_LABEL_UNIVERSE_CHANGED")
    response_link,response_bytes=published_otutable_link(original)
    header,full_size=original_otu_header_streamed(response_link,response_bytes)
    data=audit_four_header_fields(header,sample_literals)
    data["original_complete_source_member_bytes_MD5_verified"]=full_size
    data["original_information_source_member_verified"]=True
    return data


def synthetic():
    fake=b"OTU;Family;Order;Sequence;S1;S2\nsecret,1,2,3,4,5\n"
    h=fake.partition(b"\n")[0]
    # Test the exact field-name whitelist without binding a fake fixture to
    # the real previously published original header fingerprint.
    fields=next(csv.reader([h.decode()],delimiter=";",strict=True))
    other=[(i+1,v) for i,v in enumerate(fields) if v not in {"S1","S2"}]
    assert len(other)==4
    assert all(SAFE_FIELD.fullmatch(v) for _,v in other)
    assert b"secret" not in h
    assert not SAFE_FIELD.fullmatch("http://malicious/path")
    print("SYNTHETIC_BETAFOR11_FOUR_ORIGINAL_HEADER_NAME_ONLY_FIREWALL_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out needed")
    out={
        "schema":"structural.BETAFOR11_first_four_original_OTU_header_fields.v1",
        "prespec":PRESPEC,
        "original_organism_OTU_rows_parsed":0,
        "original_biodiversity_effects_fitted":0,
        "previous_original_source_and_ecology_receipts_unchanged":True,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        out["codebook"]=run()
        out["status"]=out["codebook"]["status"]
    except SourceStop as e:
        out["status"]="SOURCE_OTU_FOUR_HEADER_FIELDS_STOP_"+str(e)
        out["scientific_null_not_inferred"]=True
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("BETAFOR11_ORIGINAL_FOUR_HEADER_FIELDS",out["status"])
    print("BIOLOGICAL_ORIGINAL_OTU_ROWS_PARSED=0; NO_MODELS")


if __name__=="__main__":
    main()
