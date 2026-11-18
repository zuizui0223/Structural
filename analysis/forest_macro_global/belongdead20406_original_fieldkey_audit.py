#!/usr/bin/env python3
"""Published author 20406/tag2 safe field NAME audit: schema only, never rows.

The 14 original CSV field names are explicitly approved for output as
methodological schema, no source sample or insect observation values.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from belongdead_author_alias_naming_source_gate import NoRedirect, FIELD_FAMILIES

URL = "https://www.bexis.uni-jena.de/api/data/20406/tag/2"
PINNED_SHA = "9bf68312668065a5d533fbbe65b22e9aef45b32f0d146921ab45e5133354b13f"
PINNED_SIZE = 2717980
EXPECTED_COLUMNS = 14
PRESPEC = "docs/FOREST_BELONGDEAD_20406_AUTHOR_FIELDKEY_ALLOWLIST_PRESPEC_20261118.md"
VOCAB = {
    "exact_plot_column": {"plotid", "plot", "site", "siteid", "ep", "vip"},
    "exact_log_column": {"treeid", "tree", "logid", "log", "stemid", "stem", "trunkid", "trunk"},
    "exact_exploratory_column": {"exploratory", "exploratoryid", "exp", "region"},
    "exact_temporal_column": {
        "collectionyear", "samplingyear", "year",
        "collectiondate", "samplingdate", "date"
    },
    "exact_trap_or_effort_column": {
        "trapid", "trap", "traptype", "samplingeffort",
        "effort", "trapdays", "exposure"
    },
}


class SourceStop(RuntimeError):
    pass


def read_and_expose_safe_header():
    request = urllib.request.Request(URL, headers={
        "Accept": "text/csv,application/octet-stream;q=0.8",
        "User-Agent": "Structural-BELongDead-20406-original-author-fieldname-only/1.0",
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=55) as response:
            if response.status != 200:
                raise SourceStop("SOURCE_AUTHOR_TAG2_NOT_HTTP200")
            first = response.readline(65537)
            if len(first) > 65536 or not first.endswith((b"\n", b"\r")):
                raise SourceStop("SOURCE_FIRST_HEADER_TERMINATION_STOP")
            digest = hashlib.sha256(first)
            size = len(first)
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                size += len(chunk)
                if size > PINNED_SIZE:
                    raise SourceStop("SOURCE_ORIGINAL_SIZE_CHANGED_STOP")
                digest.update(chunk)
    except urllib.error.HTTPError as ex:
        raise SourceStop(f"SOURCE_ORIGINAL_AUTHOR_CSV_HTTP_{ex.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as ex:
        raise SourceStop("SOURCE_ORIGINAL_TRANSPORT_" + type(ex).__name__) from None
    if size != PINNED_SIZE or digest.hexdigest() != PINNED_SHA:
        raise SourceStop("SOURCE_ORIGINAL_20406_TAG2_SHA_AND_LENGTH_DRIFT_STOP")
    try:
        header = next(csv.reader([first.decode("utf-8-sig").rstrip("\r\n")],
                                 delimiter=",", strict=True))
    except (UnicodeError, csv.Error, StopIteration):
        raise SourceStop("SOURCE_AUTHOR_HEADER_NOT_UTF8_CSV") from None
    if len(header) != EXPECTED_COLUMNS or len(set(header)) != EXPECTED_COLUMNS:
        raise SourceStop("SOURCE_AUTHOR_HEADER_14_SCHEMA_DRIFT_STOP")
    return safe_field_table(header)


def safe_field_table(header):
    if len(header) != 14:
        raise SourceStop("SOURCE_AUTHOR_EXPECTED_14_FIELDS_MISSING")
    result = []
    for i, field in enumerate(header):
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 _.\-]{0,63}", field):
            raise SourceStop("SOURCE_PUBLIC_AUTHOR_FIELD_NAME_GRAMMAR_STOP")
        exact = [
            group for group, words in VOCAB.items()
            if field.casefold() in words
        ]
        lexical = [
            group for group, regex in FIELD_FAMILIES.items()
            if regex.search(field)
        ]
        result.append({
            "one_based_original_author_header_position": i + 1,
            "published_original_variable_name_ONLY": field,
            "strict_case_only_generic_key_families": exact,
            "predeclared_original_field_lexical_families": lexical,
        })
    return {
        "original_public_field_names_are_NOT_original_sample_values": True,
        "original_author_tagged_20406_file_sha256_verified": PINNED_SHA,
        "original_author_tagged_20406_file_bytes_verified": PINNED_SIZE,
        "original_public_field_names": result,
        "predeclared_EXACT_source_key_candidate_counts": {
            group: sum(group in item["strict_case_only_generic_key_families"]
                       for item in result)
            for group in VOCAB
        },
        "identical_31123_three_part_parent_key_schema_observed": all(
            any(item["published_original_variable_name_ONLY"].casefold() == field.casefold()
                for item in result)
            for field in ("Exploratory", "PlotID", "TreeID")
        ),
        "no_original_20406_content_rows_PARSED": True,
        "no_original_31123_31124_species_or_method_rows_REQUESTED": True,
        "no_original_catch_log_site_IDs_exposed": True,
    }


def known_truth():
    fields = [
        "UID", "Exploratory", "PlotID", "TreeID", "CollectionYear",
        "log_alias", "site_state", "position", "device", "status",
        "management", "notes", "forest", "source"
    ]
    t = safe_field_table(fields)
    assert t["identical_31123_three_part_parent_key_schema_observed"]
    assert t["predeclared_EXACT_source_key_candidate_counts"]["exact_log_column"] == 1
    assert t["predeclared_EXACT_source_key_candidate_counts"]["exact_trap_or_effort_column"] == 0
    assert "TrapID" not in json.dumps(t)
    try:
        safe_field_table(["bad/name"] + fields[1:])
        raise AssertionError("unsanitized original author field allowed")
    except SourceStop:
        pass
    print("SYNTHETIC_20406_TAG2_AUTHOR_FIELD_KEYS_CASE_ONLY_NO_ROW_PARSE_PASS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    known_truth()
    if a.test:
        return
    if not a.out:
        p.error("--out required")
    report = {
        "schema": "structural.BELongDead20406_original_public_author_field_names_only.v1",
        "prespec": PRESPEC,
        "dataset_id": 20406, "published_tag": 2,
        "original_beetle_species_or_capture_values_read": 0,
        "original_31124_15_TrapIDs_explained": False,
        "no_new_guild_or_community_effect_estimated": True,
        "eBird_used": False, "TinyFish_used": False,
    }
    try:
        report["source_header_only"] = read_and_expose_safe_header()
        report["status"] = (
            "EXACT_31123_PLOT_LOG_EXPLORATORY_PARENT_KEY_SCHEMA_CANDIDATE_ONLY"
            if report["source_header_only"]["identical_31123_three_part_parent_key_schema_observed"]
            else "SOURCE_AUTHOR_20406_31123_PARENT_FIELD_SCHEMAS_NOT_EXACTLY_IDENTICAL"
        )
    except SourceStop as ex:
        report["status"] = str(ex)
        report["source_stop_not_ecological_null"] = True
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "BELongDead20406_original_tag2_safe_public_author_field_names_only.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("ORIGINAL_20406_PUBLIC_SOURCE_FIELD_NAMES_AUDIT", report["status"])


if __name__ == "__main__":
    main()
