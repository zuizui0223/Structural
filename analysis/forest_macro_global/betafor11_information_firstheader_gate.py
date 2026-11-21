#!/usr/bin/env python3
"""BETA-FOR11 source method FIRST HEADER ONLY, no original biological rows.

One source-pinned official information CSV, after independently checking the
six-file publisher record. Original file bytes are only checksum-verified,
then the FIRST physical CSV header is decoded. All remaining bytes stay opaque.

Protocol: docs/FOREST_MACRO_BETAFOR11_AUTHOR_INFORMATION_FIRSTHEADER_PREFREEZE_20261119.md
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from betafor11_publisher_metadata_preintake_only import (
    URL, FILES, SourceStop, get_official_metadata_only, parse_publisher_only,
)

FILE_NAME = "BETAFOR_information.csv"
FILE_MD5 = FILES[FILE_NAME]
FILE_CAP = 2 * 1024 * 1024
PRESPEC = (
    "docs/FOREST_MACRO_BETAFOR11_AUTHOR_INFORMATION_FIRSTHEADER_"
    "PREFREEZE_20261119.md"
)
# Names below are deliberately fixed before any first header is opened.
GENERIC_FIELD_NAMES = {
    "site", "siteid", "site_id", "forest", "forestid", "forest_id",
    "forestsite", "forest_site", "region", "regionid", "region_id",
    "patch", "patchid", "patch_id", "plot", "plotid", "plot_id",
    "treatment", "treatmentid", "treatment_id", "treat", "trt",
    "year", "sampleyear", "sample_year", "period", "samplingperiod",
    "sampling_period", "date", "samplingdate", "sampling_date",
    "startdate", "enddate", "start_date", "end_date",
    "duration", "samplinglength", "sampling_length", "days",
    "trapdays", "trap_days", "effort", "sampleid", "sample_id",
    "samplingid", "sampling_id", "trap", "trapid", "trap_id",
}
GROUPS = {
    "forest_region_id": {
        "site", "siteid", "site_id", "forest", "forestid", "forest_id",
        "forestsite", "forest_site", "region", "regionid", "region_id"
    },
    "patch_id": {"patch", "patchid", "patch_id", "plot", "plotid", "plot_id"},
    "treatment": {"treatment", "treatmentid", "treatment_id", "treat", "trt"},
    "time_or_effort": {
        "year", "sampleyear", "sample_year", "period", "samplingperiod",
        "sampling_period", "date", "samplingdate", "sampling_date",
        "startdate", "enddate", "start_date", "end_date", "duration",
        "samplinglength", "sampling_length", "days", "trapdays",
        "trap_days", "effort"
    },
}
assert set().union(*GROUPS.values()).issubset(GENERIC_FIELD_NAMES)
SAFE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,35}$")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def source_publisher_file_link(metadata):
    if not isinstance(metadata, dict):
        raise SourceStop("SOURCE_METADATA_WRONG_JSON_TYPE")
    files = metadata.get("files", ())
    found = [f for f in files if isinstance(f, dict) and f.get("key") == FILE_NAME]
    if len(found) != 1:
        raise SourceStop("SOURCE_INFORMATION_FILE_ROLE_MISSING_OR_DUPLICATE")
    f = found[0]
    if f.get("checksum") != "md5:" + FILE_MD5:
        raise SourceStop("SOURCE_INFORMATION_PUBLISHER_MD5_DRIFT")
    size = f.get("size")
    if type(size) is not int or not 0 < size <= FILE_CAP:
        raise SourceStop("SOURCE_INFORMATION_FILE_SIZE_UNSAFE")
    links = f.get("links", {})
    if not isinstance(links, dict):
        raise SourceStop("SOURCE_INFORMATION_PUBLISHER_LINK_MISSING")
    link = links.get("content") or links.get("self")
    if not isinstance(link, str):
        raise SourceStop("SOURCE_INFORMATION_PUBLISHER_LINK_MISSING")
    p = urllib.parse.urlparse(link)
    if (p.scheme != "https" or p.hostname != "zenodo.org"
        or p.username or p.password or p.port
        or p.query or p.fragment):
        raise SourceStop("SOURCE_INFORMATION_NONORIGINAL_PUBLISHER_LINK")
    # Never invent file URLs. Only accept the original file's official link.
    expected_a = "/api/records/15371332/files/" + FILE_NAME + "/content"
    expected_b = r"/api/files/[0-9a-fA-F\-]{36}/" + re.escape(FILE_NAME)
    if p.path != expected_a and not re.fullmatch(expected_b, p.path):
        raise SourceStop("SOURCE_INFORMATION_UNKNOWN_PUBLISHER_FILE_PATH")
    return link, size


def official_original_file_bytes(link, size):
    req = urllib.request.Request(
        link, headers={"Accept": "*/*",
                       "User-Agent": "Structural-BETAFOR11-original-header-only/1.0"}
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=45) as h:
            if h.status != 200:
                raise SourceStop("SOURCE_INFORMATION_HTTP_NOT200")
            raw = h.read(size + 1)
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_INFORMATION_HTTP_" + str(e.code)) from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise SourceStop("SOURCE_INFORMATION_TRANSPORT_" + type(e).__name__) from None
    if len(raw) != size or hashlib.md5(raw).hexdigest() != FILE_MD5:
        raise SourceStop("SOURCE_INFORMATION_ORIGINAL_FILE_BYTES_MD5_SIZE_MISMATCH")
    return raw


def parse_first_header_only(raw):
    # DO NOT split/decode/parse any original data row or original taxon values.
    first_line = raw.partition(b"\n")[0]
    if len(first_line) > 65536 or not first_line:
        raise SourceStop("SOURCE_INFORMATION_HEADER_EMPTY_OR_UNSAFE")
    try:
        line = first_line.decode("utf-8-sig").rstrip("\r")
    except UnicodeError:
        raise SourceStop("SOURCE_INFORMATION_HEADER_ENCODING_STOP") from None
    if "\x00" in line:
        raise SourceStop("SOURCE_INFORMATION_HEADER_BINARY_STOP")
    delimiter = max((",", ";", "\t"), key=line.count)
    try:
        fields = next(csv.reader([line], delimiter=delimiter, strict=True))
    except (StopIteration, csv.Error):
        raise SourceStop("SOURCE_INFORMATION_HEADER_CSV_PARSE_STOP") from None
    if not 2 <= len(fields) <= 300:
        raise SourceStop("SOURCE_INFORMATION_HEADER_FIELD_COUNT_STOP")
    safe_fields = []
    for idx, item in enumerate(fields, start=1):
        name = item.strip()
        if name.casefold() in GENERIC_FIELD_NAMES and SAFE_NAME.fullmatch(name):
            safe_fields.append({"original_index_1based": idx,
                                "predeclared_generic_nonresponse_field": name})
    recognized = {x["predeclared_generic_nonresponse_field"].casefold()
                  for x in safe_fields}
    groups = {group: bool(members & recognized)
              for group, members in GROUPS.items()}
    return {
        "first_header_column_count": len(fields),
        "first_header_delimiter": (
            "comma" if delimiter == "," else
            "semicolon" if delimiter == ";" else "tab"
        ),
        "allowed_generic_field_names_ONLY": safe_fields,
        "generic_roles_detected": groups,
        "unknown_headers_and_all_values_NOT_EXPORTED": True,
        "source_data_rows_parsed": 0,
        "original_source_sample_labels_exposed": 0,
        "status": (
            "SOURCE_INFORMATION_GENERIC_HEADER_CANDIDATES_ONLY_NO_ROW_ADMISSION"
            if all(groups.values()) else
            "SOURCE_METHOD_HEADER_HOLD_INCOMPLETE_GENERIC_ROLE_SUPPORT"
        )
    }


def synthetic():
    record = {
        "files": [
            {"key": FILE_NAME, "checksum": "md5:" + FILE_MD5,
             "size": 112, "links": {
                 "content": "https://zenodo.org/api/records/15371332/files/"
                            "BETAFOR_information.csv/content"
             }}
        ]
    }
    link, size = source_publisher_file_link(record)
    assert size == 112 and link.startswith("https://zenodo.org/")
    for bad in (
        "https://example.com/data.csv",
        "https://zenodo.org/api/records/15371332/files/com_singletons.csv/content",
        "https://zenodo.org/api/records/15371332/files/BETAFOR_information.csv/content?token=fake",
    ):
        obj = json.loads(json.dumps(record))
        obj["files"][0]["links"]["content"] = bad
        try:
            source_publisher_file_link(obj)
            raise AssertionError("Unapproved original-source file link accepted")
        except SourceStop:
            pass
    src = (
        b"Forest,Patch,Treatment,Year,SamplingPeriod,TrapDays,Species_Test\n"
        b"F1,P1,GAP,2022,1,14,RAWTAXON_DATA_FORBIDDEN\n"
    )
    out = parse_first_header_only(src)
    assert out["first_header_column_count"] == 7
    assert all(out["generic_roles_detected"].values())
    assert out["source_data_rows_parsed"] == 0
    assert "Species_Test" not in json.dumps(out)
    assert "RAWTAXON_DATA_FORBIDDEN" not in json.dumps(out)
    print("SYNTHETIC_BETAFOR11_SOURCE_INFORMATION_HEADER_ONLY_FIREWALL_PASS")


def run():
    original = get_official_metadata_only()
    published = parse_publisher_only(original)  # checks six source MD5s/version/license
    if published["status"] != "ORIGINAL_PUBLISHER_SIX_FILE_METADATA_ONLY_PASS":
        raise SourceStop("SOURCE_PUBLISHER_PREINTAKE_NOT_ADMITTED")
    link, published_size = source_publisher_file_link(original)
    raw = official_original_file_bytes(link, published_size)
    detail = parse_first_header_only(raw)
    return {
        "publisher_registry_all_six_files_verified": True,
        "original_publisher_information_md5_verified": FILE_MD5,
        "original_information_file_publisher_size": published_size,
        "header_only": detail,
        "response_and_information_DATA_ROWS_PARSED": 0,
        "published_99_patches_594_samples_NOT_reverified_by_source_rows": True,
        "original_OTU_and_sequencing_tables_NOT_DOWNLOADED": True,
        "original_species_effects_scored": 0,
        "status": detail["status"],
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    synthetic()
    if args.test:
        return
    if args.out is None:
        p.error("--out required")
    result = {
        "schema": "structural.BETAFOR11_original_information_header_only.v1",
        "prespec": PRESPEC,
        "original_organism_response_rows_read": 0,
        "new_biodiversity_effect_estimations": 0,
        "original_other_five_source_members_requested": 0,
        "prior_outcome_freezes_unchanged": True,
    }
    try:
        result["source"] = run()
        result["status"] = result["source"]["status"]
    except SourceStop as e:
        result["status"] = "SOURCE_METHOD_STOP_" + str(e)
        result["no_ecological_null_inferred_from_source_stop"] = True
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print("BETAFOR11_ORIGINAL_FIRSTHEADER_ONLY", result["status"])
    print("NO_ORIGINAL_DATA_ROWS_OR_BIOLOGICAL_EFFECT_SCORED")


if __name__ == "__main__":
    main()
