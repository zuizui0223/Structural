#!/usr/bin/env python3
"""BELongDead author naming/instrumentation PUBLISHED TAGGED CSV HEADER only.

Source bytes after first header line: streamed directly to SHA256, never parsed.
NEVER parse any original beetle / forest-wood / source-method data rows.
Prespec: docs/FOREST_BELONGDEAD_AUTHOR_TAGGED_HEADER_SOURCE_GATE_PRESPEC_20261117.md
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

from belongdead_author_alias_naming_source_gate import (
    ROOT, NoRedirect, SourceStop, FIELD_FAMILIES,
    read_publisher_json, published_open_rights,
)

PRESPEC = "docs/FOREST_BELONGDEAD_AUTHOR_TAGGED_HEADER_SOURCE_GATE_PRESPEC_20261117.md"
# These two original publisher metadata fingerprints were verified in the
# prior source-only workflow #44102672012, not copied from study outcome.
FROZEN = (
    {
        "dataset": 16846, "tag": 1, "fields": 12,
        "name": "original_author_log_naming",
        "dataset_sha": "a1c12dae34f6ba7470ca57caa56ca0f0546d1d40054873f9c41adbd432d01cd0",
        "metadata_sha": "6c7f49b2c7f7c229fe5d09e4bfbed2c5bf59a5a5ccf87cba3b9487c30e0c2a37",
    },
    {
        "dataset": 16390, "tag": 1, "fields": 13,
        "name": "original_author_instrumentation_2009_2010",
        "dataset_sha": "62e4ed9f671f375eaad79986491d0af38ffd4426ba7ba309a6de617afd63e3ad",
        "metadata_sha": "1c96a8218a4f41ff6caa1057fbe83b2f0ec97c5ee069733c15893eef35a8e476",
    },
)
MAX_SIZE = 10 * 1024 * 1024
MAX_HEADER = 65536
SOURCE_ALLOWLIST = {(x["dataset"], x["tag"]) for x in FROZEN}


def original_tag_url(dataset_id, tag):
    if (dataset_id, tag) not in SOURCE_ALLOWLIST:
        raise SourceStop("SOURCE_UNFROZEN_DATASET_TAG_STOP")
    return ROOT + f"/api/data/{dataset_id}/tag/{tag}"


def source_header_fields(first_line, required_count):
    if len(first_line) > MAX_HEADER or not first_line.endswith((b"\n", b"\r")):
        raise SourceStop("SOURCE_HEADER_TOO_LONG_OR_UNTERMINATED")
    try:
        head_text = first_line.decode("utf-8-sig").rstrip("\r\n")
    except UnicodeError:
        raise SourceStop("SOURCE_HEADER_NOT_UTF8") from None
    if re.match(r"\s*<(?:!DOCTYPE|html|head|body)", head_text, re.IGNORECASE):
        raise SourceStop("SOURCE_HTML_NOT_ORIGINAL_CSV")
    try:
        columns = next(csv.reader([head_text], delimiter=",", quotechar='"', strict=True))
    except (csv.Error, StopIteration):
        raise SourceStop("SOURCE_HEADER_CSV_PARSE_STOP") from None
    if len(columns) != required_count or len(set(columns)) != required_count:
        raise SourceStop("SOURCE_TAGGED_HEADER_COUNT_OR_DUPLICATE_STOP")
    if any(not f or len(f) > 200 for f in columns):
        raise SourceStop("SOURCE_TAGGED_HEADER_EMPTY_OR_OVERSIZE_FIELD_STOP")
    family_count = {
        family: sum(bool(pattern.search(field)) for field in columns)
        for family, pattern in FIELD_FAMILIES.items()
    }
    return {
        "tagged_original_first_header_column_count": len(columns),
        "source_first_header_only_lexical_candidate_family_counts": family_count,
        "original_header_field_names_NOT_EXPORTED": True,
        "original_source_row_keys_and_values_NOT_PARSED_OR_EXPORTED": True,
    }


def read_tagged_original_header_and_fingerprint(dataset_id, tag, n_columns):
    req = urllib.request.Request(original_tag_url(dataset_id, tag), headers={
        "User-Agent": "Structural-BELongDead-tagged-original-method-header-gate/1.0",
        "Accept": "text/csv,application/octet-stream;q=0.5",
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=45) as response:
            if response.status != 200:
                raise SourceStop("SOURCE_ORIGINAL_CSV_HTTP_NOT200")
            header = response.readline(MAX_HEADER + 1)
            parsed = source_header_fields(header, n_columns)
            digest = hashlib.sha256()
            digest.update(header)
            count = len(header)
            while True:
                buf = response.read(min(65536, MAX_SIZE + 1 - count))
                if not buf:
                    break
                digest.update(buf)
                count += len(buf)
                if count > MAX_SIZE:
                    raise SourceStop("SOURCE_TAGGED_CSV_TOO_LARGE")
    except urllib.error.HTTPError as exc:
        raise SourceStop("SOURCE_TAGGED_CSV_HTTP_" + str(exc.code)) from None
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise SourceStop("SOURCE_TAGGED_CSV_TRANSPORT_" + type(exc).__name__) from None
    parsed.update({
        "original_tagged_csv_byte_length": count,
        "original_tagged_csv_sha256": digest.hexdigest(),
        "original_beyond_first_header_bytes_STREAMED_FOR_HASH_ONLY": True,
        "original_species_capture_trap_site_wood_numeric_rows_PARSED": 0,
    })
    return parsed


def check_one(frozen):
    dataset_id, tag = frozen["dataset"], frozen["tag"]
    record = {
        "source_original_dataset_id": dataset_id,
        "source_original_published_tag": tag,
        "author_method_title_family": frozen["name"],
        "original_source_schema_expected_field_count": frozen["fields"],
        "source_original_31123_31124_specimen_rows_READ": 0,
        "original_alias_or_trap_opportunity_join_PROVED": False,
    }
    try:
        docs = []
        for category in ("dataset", "metadata"):
            doc, receipt = read_publisher_json(dataset_id, tag, category)
            required_sha = frozen[category + "_sha"]
            if receipt["original_publisher_response_sha256"] != required_sha:
                raise SourceStop("SOURCE_METADATA_PRIOR_RECEIPT_SHA_DRIFT")
            docs.append(doc)
            record["source_" + category + "_SHA256_verification"] = True
        if not any(published_open_rights(doc) for doc in docs):
            raise SourceStop("SOURCE_PUBLISHER_OPEN_LICENSE_NOT_VERIFIED")
        record["original_source_public_rights_verification"] = True
        record["original_tagged_CSV_header_fingerprint_only"] = (
            read_tagged_original_header_and_fingerprint(
                dataset_id, tag, frozen["fields"])
        )
        record["status"] = "TAGGED_ORIGINAL_HEADER_VALIDATED_NO_TRAP_CROSSWALK"
    except SourceStop as exc:
        record["status"] = str(exc)
        record["source_failure_not_ecological_null"] = True
    return record


def actual_run():
    records = [check_one(source) for source in FROZEN]
    return {
        "schema": "structural.BELongDead_author_published_tagged_header_only.v1",
        "precommit": PRESPEC,
        "published_author_original_sources": records,
        "author_method_original_source_count": len(records),
        "original_author_source_rows_semantically_opened": 0,
        "original_beetle_or_deadwood_observation_rows_opened": 0,
        "original_31124_15_TrapID_not_reconciled": True,
        "original_31123_31124_24546_not_requested": True,
        "no_new_ecological_effect_calculated": True,
        "old_Finland_Chiu_Piccini_PREDICTS_NEON_BALA_GEB_sealed": True,
        "eBird_used": False,
        "TinyFish_used": False,
        "status": "ORIGINAL_TAGGED_METHOD_HEADER_GATE_ONLY",
    }


def synthetic():
    assert original_tag_url(16846, 1).endswith("/api/data/16846/tag/1")
    try:
        original_tag_url(31123, 1)
        raise AssertionError("old beetle data endpoint allowed")
    except SourceStop:
        pass
    fake = ("PlotID,LogID,TrapID,Year," +
            ",".join("blank_" + str(i) for i in range(8)) + "\n").encode()
    r = source_header_fields(fake, 12)
    assert r["tagged_original_first_header_column_count"] == 12
    assert r["source_first_header_only_lexical_candidate_family_counts"][
        "trap_or_instrument"] == 1
    assert "TrapID" not in json.dumps(r)
    for source in (b"<html>not original CSV\n", b"one,too,few\n"):
        try:
            source_header_fields(source, 12)
            raise AssertionError("malformed original source header passed")
        except SourceStop:
            pass
    print("SYNTHETIC_TAGGED_ORIGINAL_AUTHOR_HEADER_ONLY_NO_ROWS_NO_ALIAS_MATCH_PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    synthetic()
    if args.test:
        return
    if args.out is None:
        parser.error("--out needed")
    result = actual_run()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "BELongDead_original_tagged_author_method_first_header_only.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for one in result["published_author_original_sources"]:
        print("TAGGED_AUTHOR_METHOD_SOURCE", one["source_original_dataset_id"],
              one["status"])
    print("METHOD_ONLY_NO_ECOLOGY_NO_RECODE_NO_TRAP_ALIAS_PROVEN")


if __name__ == "__main__":
    main()
