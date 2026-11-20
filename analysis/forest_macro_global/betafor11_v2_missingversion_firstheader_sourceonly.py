#!/usr/bin/env python3
"""BETA-FOR v2 original source metadata.version-null admission + first header only.

Historical v1 publisher version STOP remains unchanged. No biology or data rows.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from betafor11_publisher_metadata_preintake_only import (
    FILES, RECORD, DOI, get_official_metadata_only, SourceStop,
)
from betafor11_publisher_version_sourceonly_diag import audit as original_six_md5_audit
from betafor11_information_firstheader_gate import (
    FILE_NAME, source_publisher_file_link, official_original_file_bytes,
    parse_first_header_only,
)

PRESPEC = "docs/FOREST_MACRO_BETAFOR11_V2_MISSING_VERSION_SOURCE_GATE_PREFREEZE_20261120.md"
EXPECTED_FILES = 6

def validate_publisher_v2(doc):
    # Separate, established v1-independent diagnostic verifies exact original
    # versioned DOI, ID, published status, CC-BY-SA and SIX frozen names+MD5.
    receipt = original_six_md5_audit(doc)
    md = doc["metadata"]
    if md.get("version") is not None:
        # This is the SPECIFIC missing-version compatibility fix, not a general
        # relaxation of v1 or auto-follow to other publisher versions.
        raise SourceStop("V2_REQUIRED_MISSING_OR_NULL_METADATA_VERSION")
    if receipt["six_fixed_source_filename_checksum_matches"] != EXPECTED_FILES:
        raise SourceStop("V2_PUBLISHER_SIX_SOURCE_FILES_NOT_VERIFIED")
    if (receipt["publisher_record"] != RECORD or
        receipt["published_versioned_doi"] != DOI):
        raise SourceStop("V2_FROZEN_ORIGINAL_RECORD_DOI_MISMATCH")
    return {
        "original_six_filenames_MD5s_and_sizes_verified": True,
        "metadata_version_absent_or_null": True,
        "metadata_version_field_present_but_null": bool(receipt["metadata_version_FIELD_PRESENT"]),
        "publisher_versioned_DOI_pinned": DOI,
        "publisher_record_id": RECORD,
        "previous_v1_version_STOP_preserved": True,
        "six_original_file_members_untouched": True,
    }


def run():
    doc = get_official_metadata_only()
    provenance = validate_publisher_v2(doc)
    link, byte_size = source_publisher_file_link(doc)
    raw = official_original_file_bytes(link, byte_size)
    header = parse_first_header_only(raw)
    return {
        "status": header["status"],
        "source_provenance": provenance,
        "exact_one_original_file": FILE_NAME,
        "original_file_MD5_from_v1_unchanged": FILES[FILE_NAME],
        "publisher_reported_original_file_bytes": byte_size,
        "original_header_only": header,
        "original_source_information_rows_opened": 0,
        "original_other_five_member_GET": 0,
        "original_organism_rows_opened": 0,
        "new_ecological_effects_scored": 0,
        "no_sample_IDs_or_unknown_header_or_biology_exported": True,
    }


def synthetic():
    fake = {
        "id": RECORD, "doi": DOI, "status": "published",
        "metadata": {"license": {"id": "cc-by-sa-4.0"}},
        "files": [{"key": k, "checksum": "md5:" + digest, "size": 120,
                   "links": {
                       "content": ("https://zenodo.org/api/records/15371332/files/"
                                   + k + "/content")}}
                  for k, digest in FILES.items()],
    }
    q = validate_publisher_v2(fake)
    assert q["metadata_version_absent_or_null"] is True
    fake["metadata"]["version"] = None
    assert validate_publisher_v2(fake)["metadata_version_field_present_but_null"]
    for forbidden in ("v1", "v2", "1", "latest"):
        fake["metadata"]["version"] = forbidden
        try:
            validate_publisher_v2(fake)
        except SourceStop:
            pass
        else:
            raise AssertionError("unexpected version admitted: " + forbidden)
    fake["metadata"]["version"] = None
    fake["files"][0]["checksum"] = "md5:" + "0"*32
    try:
        validate_publisher_v2(fake)
    except SourceStop:
        pass
    else:
        raise AssertionError("publisher original MD5 drift accepted")
    before = (
        b"Forest,Patch,Treatment,Year,SamplingPeriod,TrapDays,UnknownTaxon\n"
        b"F1,P1,GAP,2022,1,14,SENSITIVE_UNDERLYING_ROW\n"
    )
    h = parse_first_header_only(before)
    assert h["source_data_rows_parsed"] == 0
    assert h["status"] == "SOURCE_INFORMATION_GENERIC_HEADER_CANDIDATES_ONLY_NO_ROW_ADMISSION"
    assert "UnknownTaxon" not in json.dumps(h)
    assert "SENSITIVE_UNDERLYING_ROW" not in json.dumps(h)
    print("SYNTHETIC_BETAFOR11_V2_VERSION_AND_HEADER_NO_BIOLOGY_PASS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    synthetic()
    if a.test:
        return
    if a.out is None:
        p.error("--out required")
    report = {
        "schema": "structural.BETAFOR11_v2_missingversion_original_information_firstheader.v1",
        "prespec": PRESPEC,
        "scientific_status": "SOURCE_ONLY_NO_BIOLOGICAL_ENDPOINT",
        "previous_v1_version_STOP_preserved": True,
        "old_ecology_results_unchanged": True,
        "eBird_used": False,
        "TinyFish_used": False,
        "original_organism_response_rows_opened": 0,
        "new_biological_effect_estimations": 0,
    }
    try:
        data = run()
        report["source"] = data
        report["status"] = data["status"]
    except SourceStop as ex:
        report["status"] = "SOURCE_V2_STOP_" + str(ex)
        report["source_stop_is_not_ecological_null"] = True
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, ensure_ascii=False, indent=2,
                                sort_keys=True) + "\n", encoding="utf-8")
    print("BETAFOR11_V2_MISSINGVERSION_FIRSTHEADER", report["status"])
    print("BIOLOGICAL_ROWS=0; MODEL_FITS=0; PREVIOUS_V1_STOP_PRESERVED")


if __name__ == "__main__":
    main()
