#!/usr/bin/env python3
"""BETA-FOR original eight information CSV COLUMN NAMES only; no source rows.

New v3 method diagnostic after frozen v2 source syntax HOLD; does not relax v2.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from betafor11_publisher_metadata_preintake_only import (
    get_official_metadata_only, SourceStop,
)
from betafor11_v2_missingversion_firstheader_sourceonly import (
    validate_publisher_v2,
)
from betafor11_information_firstheader_gate import (
    source_publisher_file_link, official_original_file_bytes,
)

PRESPEC = "docs/FOREST_MACRO_BETAFOR11_AUTHOR_EIGHT_HEADER_CODEBOOK_PREFREEZE_20261120.md"
SAFE_HEADER = re.compile(r"^[A-Za-z][A-Za-z0-9_ .-]{0,44}$")
SENSITIVE_VALUE = re.compile(r"(?i)(?:^=|https?://|@|\\|\x00)")
ROLE = {
    "geography_or_forest_label": ("region", "site", "forest", "location"),
    "experimental_patch_label": ("patch", "plot", "treatmentplot"),
    "treatment_label": ("treatment", "trt", "manipulat", "mortality", "deadwood", "canopy"),
    "sample_time_label": ("year", "period", "date", "time", "season", "week"),
    "effort_label": ("trap", "duration", "effort", "days"),
    "sample_label": ("sample", "sampleid", "barcode"),
}
EXPECTED_COLUMNS = 8
EXPECTED_DELIM = ";"


def parse_information_header_only(raw):
    # First physical header ONLY. No code may split or decode the body.
    first_line = raw.partition(b"\n")[0]
    if not first_line or len(first_line) > 4096:
        raise SourceStop("ORIGINAL_INFO_FIRST_HEADER_EMPTY_OR_OVERSIZED")
    try:
        text = first_line.decode("utf-8-sig").rstrip("\r")
        fields = next(csv.reader([text], delimiter=EXPECTED_DELIM, strict=True))
    except (UnicodeError, csv.Error, StopIteration):
        raise SourceStop("ORIGINAL_INFO_HEADER_NOT_SEMICOLON_UTF8_CSV") from None
    if len(fields) != EXPECTED_COLUMNS:
        raise SourceStop("ORIGINAL_INFO_HEADER_NOT_EIGHT_COLUMNS")
    names = [x.strip() for x in fields]
    if (any(not SAFE_HEADER.fullmatch(x) or SENSITIVE_VALUE.search(x)
            for x in names) or len(set(x.casefold() for x in names)) != EXPECTED_COLUMNS):
        raise SourceStop("ORIGINAL_INFO_HEADER_NOT_SAFE_COLUMN_NAMES")
    hints = {}
    for role, words in ROLE.items():
        hints[role] = [i+1 for i,n in enumerate(names)
                       if any(w in n.casefold().replace("_", "") for w in words)]
    return {
        "first_header_column_count": len(names),
        "first_header_delimiter": "semicolon",
        "original_column_names_source_method_ONLY": [
            {"column_index_1based": i+1, "original_safe_header_field": name}
            for i, name in enumerate(names)
        ],
        "role_hint_indices_ONLY_not_author_codebook": hints,
        "all_eight_names_in_a_frozen_source_header": True,
        "original_author_field_semantics_not_yet_proved": True,
        "information_source_data_rows_parsed": 0,
        "original_OTU_or_taxon_headers_or_data_rows_read": 0,
        "original_forest_patch_treatment_year_values_exported": False,
        "new_biodiversity_effects": 0,
        "status": "ORIGINAL_BETAFOR11_EIGHT_INFORMATION_HEADER_NAMES_METHOD_DIAGNOSTIC_ONLY",
    }


def run():
    official = get_official_metadata_only()
    meta = validate_publisher_v2(official)
    link, size = source_publisher_file_link(official)
    raw = official_original_file_bytes(link,size)
    columns = parse_information_header_only(raw)
    return {
        "publisher_missing_version_six_file_MD5_verified": meta["original_six_filenames_MD5s_and_sizes_verified"],
        "original_information_file_MD5_and_size_verified": True,
        "original_information_published_byte_size": size,
        "source_only_field_header_diagnostic": columns,
        "all_original_nonheader_source_rows_opaque": True,
        "all_original_OTU_files_unopened": True,
        "no_original_biological_response_scored": True,
        "status": columns["status"],
    }


def synthetic():
    src = (
        b"patch;forest;region;treatment;Year;sample;trapdays;sampling period\n"
        b"P2;F3;Bavaria;G;2023;S1;14;1\n"
        b"SENSITIVE_ROW_NOT_TO_EXPORT\n"
    )
    result = parse_information_header_only(src)
    assert result["first_header_column_count"] == 8
    assert result["information_source_data_rows_parsed"] == 0
    assert result["role_hint_indices_ONLY_not_author_codebook"]["treatment_label"] == [4]
    assert "SENSITIVE_ROW" not in json.dumps(result)
    bad = src.replace(b"patch;",b"patch;patch;",1)
    try:
        parse_information_header_only(bad)
    except SourceStop:
        pass
    else:
        raise AssertionError("Non-8-column source accepted")
    formula = src.replace(b"patch;",b"=A1;",1)
    try:
        parse_information_header_only(formula)
    except SourceStop:
        pass
    else:
        raise AssertionError("Formula field accepted")
    print("SYNTHETIC_BETAFOR11_V3_ORIGINAL_EIGHT_METHOD_HEADER_ONLY_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:
        return
    if a.out is None:
        p.error("--out needed")
    rep={
        "schema":"structural.BETA_FOR_v3_original_eight_info_header_names_only.v1",
        "prespec": PRESPEC,
        "original_v1_VERSION_STOP_preserved": True,
        "original_v2_ROLE_HOLD_preserved": True,
        "original_source_biological_rows_opened": 0,
        "original_source_information_data_rows_opened": 0,
        "new_organism_effects_fitted": 0,
        "eBird_used":False,
        "TinyFish_used":False,
    }
    try:
        rep["diagnostic"]=run()
        rep["status"]=rep["diagnostic"]["status"]
    except SourceStop as ex:
        rep["status"]="ORIGINAL_EIGHT_HEADER_METHOD_DIAGNOSTIC_STOP_"+str(ex)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(rep,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("BETAFOR11_EIGHT_HEADER_CODEBOOK_DIAG",rep["status"])
    print("INFORMATION_DATA_ROWS=0; OTU_FILES=0; BIOLOGICAL_MODELS=0")


if __name__=="__main__":
    main()
