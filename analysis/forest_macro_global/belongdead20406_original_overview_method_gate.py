#!/usr/bin/env python3
"""BELongDead original BExIS 20406/tag2 study log overview: schema-only gate.

Does not access 31123/31124, species, capture, forest wood measurements, IDs,
site rows or zero counts. CSV bytes beyond the FIRST header are SHA-streamed
without decoding/parsing. DataStatistic uniqueValues/min/max are not inspected.

Protocol: docs/FOREST_BELONGDEAD_20406_AUTHOR_STUDY_OVERVIEW_ORIGINAL_GATE_PRESPEC_20261118.md
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

ORIGINAL_ID = 20406
ORIGINAL_TAG = 2
ROOT = "https://www.bexis.uni-jena.de"
PRESPEC = "docs/FOREST_BELONGDEAD_20406_AUTHOR_STUDY_OVERVIEW_ORIGINAL_GATE_PRESPEC_20261118.md"
PATHS = {
    "dataset": "/api/dataset/20406",
    "tag_metadata": "/api/metadata/20406?tag=2.0",
    "variable_dictionary": "/api/DataStatistic/20406",
    "original_tagged_file": "/api/data/20406/tag/2",
}
DOC_LIMIT = 16 * 1024 * 1024
FILE_LIMIT = 20 * 1024 * 1024
HEADER_LIMIT = 65536
from belongdead_author_alias_naming_source_gate import (
    NoRedirect, published_open_rights, FIELD_FAMILIES,
)


class SourceStop(RuntimeError):
    pass


def open_get(category, accept):
    if category not in PATHS:
        raise SourceStop("SOURCE_UNDECLARED_PUBLISHER_ENDPOINT")
    url = ROOT + PATHS[category]
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Structural-forest-BELongDead-20406-original-author-source/1.0",
            "Accept": accept,
        },
    )
    try:
        return urllib.request.build_opener(NoRedirect).open(req, timeout=55)
    except urllib.error.HTTPError as exc:
        raise SourceStop(f"SOURCE_ORIGINAL_{category}_HTTP_{exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SourceStop(f"SOURCE_ORIGINAL_{category}_TRANSPORT_{type(exc).__name__}") from None


def json_doc(category):
    try:
        with open_get(category, "application/json") as resp:
            if resp.status != 200:
                raise SourceStop("SOURCE_ORIGINAL_PUBLISHER_HTTP_NOT200")
            mime = resp.headers.get("Content-Type", "")
            raw = resp.read(DOC_LIMIT + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SourceStop("SOURCE_ORIGINAL_DOC_READ_" + type(exc).__name__) from None
    if "json" not in mime.casefold() or not raw or len(raw) > DOC_LIMIT:
        raise SourceStop("SOURCE_ORIGINAL_DOC_NOT_PUBLIC_JSON_OR_TOO_LARGE")
    try:
        obj = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise SourceStop("SOURCE_ORIGINAL_DOC_JSON_PARSE_STOP") from None
    return obj, {
        "original_publisher_http_status": 200,
        "original_publisher_response_bytes": len(raw),
        "original_publisher_response_sha256": hashlib.sha256(raw).hexdigest(),
    }


def method_family_counts(fields):
    result = {name: 0 for name in FIELD_FAMILIES}
    for field in fields:
        for label, regex in FIELD_FAMILIES.items():
            if regex.search(field):
                result[label] += 1
    return result


def original_variable_dictionary(doc):
    if not isinstance(doc, list) or not 1 <= len(doc) <= 300:
        raise SourceStop("SOURCE_PUBLISHER_ORIGINAL_DICTIONARY_SHAPE_STOP")
    seen = set()
    fields = []
    for item in doc:
        if not isinstance(item, dict):
            raise SourceStop("SOURCE_PUBLISHER_DICTIONARY_RECORD_SHAPE_STOP")
        key = item.get("VariableName", item.get("variableName"))
        if not isinstance(key, str) or not 1 <= len(key) <= 200:
            raise SourceStop("SOURCE_PUBLISHER_DICTIONARY_FIELD_STOP")
        if key in seen:
            raise SourceStop("SOURCE_PUBLISHER_DICTIONARY_DUPLICATE_FIELD_STOP")
        seen.add(key)
        desc = item.get("VariableDescription", item.get("variableDescription", ""))
        if not isinstance(desc, str):
            desc = ""
        # Author field name / description ONLY; never visit stats uniqueValues.
        fields.append(key + " " + desc[:2000])
    return {
        "original_publisher_dictionary_variable_count": len(fields),
        "lexical_method_family_count_name_AND_description": method_family_counts(fields),
        "variable_names_description_tokens_NOT_EXPORTED": True,
        "uniqueValues_min_max_counts_NEVER_ACCESSED_OR_EXPORTED": True,
        "dictionary_may_be_latest_not_tagged_original": True,
    }


def parse_one_source_header_line(line):
    if not line or len(line) > HEADER_LIMIT or not line.endswith((b"\r", b"\n")):
        raise SourceStop("SOURCE_TAGGED_CSV_HEADER_UNTERMINATED_OR_TOO_LARGE")
    try:
        decoded = line.decode("utf-8-sig").rstrip("\r\n")
    except UnicodeError:
        raise SourceStop("SOURCE_TAGGED_CSV_HEADER_ENCODING_STOP") from None
    if re.match(r"\s*<(?:html|!doctype|head|body)", decoded, re.I):
        raise SourceStop("SOURCE_TAGGED_CSV_HTML_STOP")
    try:
        fields = next(csv.reader([decoded], delimiter=",", quotechar='"', strict=True))
    except (csv.Error, StopIteration):
        raise SourceStop("SOURCE_TAGGED_CSV_HEADER_PARSE_STOP") from None
    if not 1 <= len(fields) <= 300 or len(set(fields)) != len(fields):
        raise SourceStop("SOURCE_TAGGED_CSV_HEADER_COLUMN_COUNT_OR_DUPLICATE_STOP")
    if any(not f.strip() or len(f) > 200 for f in fields):
        raise SourceStop("SOURCE_TAGGED_CSV_HEADER_FIELD_SHAPE_STOP")
    return {
        "first_original_CSV_header_column_count": len(fields),
        "first_original_CSV_header_lexical_method_family_counts": method_family_counts(fields),
        "original_exact_field_tokens_NOT_EXPORTED": True,
        "no_subsequent_original_CSV_row_PARSED": True,
    }


def source_header_and_sha():
    try:
        with open_get("original_tagged_file", "text/csv,application/octet-stream;q=0.8") as resp:
            if resp.status != 200:
                raise SourceStop("SOURCE_TAGGED_FILE_HTTP_NOT200")
            first = resp.readline(HEADER_LIMIT + 1)
            result = parse_one_source_header_line(first)
            digest = hashlib.sha256()
            digest.update(first)
            n = len(first)
            while True:
                if n >= FILE_LIMIT:
                    # Avoid one-byte read after exactly FILE_LIMIT; the file bound
                    # is inclusive and the next single-byte proves oversize.
                    chunk = resp.read(1)
                else:
                    chunk = resp.read(min(65536, FILE_LIMIT + 1 - n))
                if not chunk:
                    break
                n += len(chunk)
                if n > FILE_LIMIT:
                    raise SourceStop("SOURCE_TAGGED_CSV_TOO_LARGE")
                digest.update(chunk)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SourceStop("SOURCE_TAGGED_CSV_READ_" + type(exc).__name__) from None
    result.update({
        "source_original_tag": ORIGINAL_TAG,
        "source_original_file_byte_count": n,
        "source_original_tagged_file_sha256": digest.hexdigest(),
        "body_beyond_header_bytes_HASHED_NOT_PARSED": True,
        "method_data_rows_parsed": 0,
        "beetle_wood_counts_or_observations_read": 0,
    })
    return result


def audit():
    out = {
        "schema": "structural.BELongDead20406_original_log_overview_source_schema_only.v1",
        "prespec": PRESPEC,
        "publisher_original_dataset_id": ORIGINAL_ID,
        "publisher_original_tag": ORIGINAL_TAG,
        "published_original_is_NOT_new_independent_forest_cohort": True,
        "original_BExIS31123_31124_24546_rows_requested": 0,
        "original_31124_fifteen_TrapID_aliases_RESOLVED": False,
        "source_original_beetle_species_abundance_trait_values_READ": 0,
        "prior_Finland_Germany_PREDICTS_NEON_BALA_GEB_scoring_UNCHANGED": True,
        "eBird_used": False,
        "TinyFish_used": False,
    }
    try:
        pub_docs = []
        for category in ("dataset", "tag_metadata"):
            doc, receipt = json_doc(category)
            pub_docs.append(doc)
            out["original_" + category + "_metadata_receipt"] = receipt
        if not any(published_open_rights(doc) for doc in pub_docs):
            raise SourceStop("SOURCE_ACCESS_RIGHTS_STOP")
        out["recognizable_original_open_license_verified"] = True
        # a variable dictionary may fail independently; do not infer latest/tag equivalence.
        try:
            variables, receipt = json_doc("variable_dictionary")
            out["variable_dictionary_receipt"] = receipt
            out["variable_dictionary_source_only"] = original_variable_dictionary(variables)
        except SourceStop as exc:
            out["variable_dictionary_source_only_STOP"] = str(exc)
        out["tagged_original_CSV_first_header_only"] = source_header_and_sha()
        dic = out.get("variable_dictionary_source_only")
        if dic is None:
            out["status"] = "SOURCE_DICTIONARY_OR_ORIGINAL_TAG_STOP"
        elif (
            dic["original_publisher_dictionary_variable_count"]
            != out["tagged_original_CSV_first_header_only"]["first_original_CSV_header_column_count"]
        ):
            out["status"] = "SOURCE_TAGGED_HEADER_DICTIONARY_MISMATCH"
        else:
            combined = (
                dic["lexical_method_family_count_name_AND_description"],
                out["tagged_original_CSV_first_header_only"]["first_original_CSV_header_lexical_method_family_counts"],
            )
            if any(
                v.get("trap_or_instrument", 0)
                or v.get("explicit_effort_or_zero_opportunity", 0)
                or (v.get("physical_log_or_stem", 0) and v.get("plot_or_subplot", 0))
                for v in combined
            ):
                out["status"] = "SOURCE_AUTHOR_METHOD_SCHEMA_CANDIDATE_ONLY"
            else:
                out["status"] = "SOURCE_NO_EXPLICIT_METHOD_CANDIDATE"
    except SourceStop as exc:
        out["status"] = str(exc)
        out["source_or_schema_STOP_not_ecological_null"] = True
    out["no_biological_response_estimated"] = True
    out["author_trap_deployment_effort_NOT_PROVEN"] = True
    out["source_author_method_ID_crosswalk_NOT_PROVEN"] = True
    return out


def synthetic():
    assert list(PATHS) == ["dataset", "tag_metadata", "variable_dictionary", "original_tagged_file"]
    assert "/api/data/31123" not in " ".join(PATHS.values())
    assert "20406/tag/2" in PATHS["original_tagged_file"]
    assert published_open_rights({"license": "CC BY 4.0"})
    fixture = [
        {"VariableName": "LogID", "VariableDescription": "old and new log aliases",
         "uniqueValues": ["PRIVATE_WOOD_LOG_ID"], "min": -1234},
        {"VariableName": "TrapDays", "VariableDescription": "sampling effort"},
    ]
    got = original_variable_dictionary(fixture)
    h = parse_one_source_header_line(b"LogID,TrapDays\n")
    assert got["original_publisher_dictionary_variable_count"] == 2
    assert h["first_original_CSV_header_column_count"] == 2
    assert got["lexical_method_family_count_name_AND_description"]["alias_or_renaming"] == 1
    for forbidden in ("PRIVATE_WOOD_LOG_ID", "LogID", "TrapDays", "-1234"):
        assert forbidden not in json.dumps(got) + json.dumps(h)
    for invalid in (b"<html>Access denied\n", b"duplicate,duplicate\n", b""):
        try:
            parse_one_source_header_line(invalid)
            raise AssertionError("bad source header unexpectedly accepted")
        except SourceStop:
            pass
    print("SYNTHETIC_BELONGDEAD_20406_SOURCE_ONLY_HEADER_HASH_AND_DICTIONARY_REDACTION_PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    synthetic()
    if args.test:
        return
    if not args.out:
        parser.error("--out required")
    result = audit()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "BELongDead20406_original_author_log_overview_schema_only.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "BEXIS_20406_ORIGINAL_PUBLISHED_TAG_SOURCE_GATE", result["status"],
        "NO_SPECIES_OR_SAMPLING_ROWS_PARSED"
    )


if __name__ == "__main__":
    main()
