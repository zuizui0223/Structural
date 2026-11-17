#!/usr/bin/env python3
"""Response-sealed BExIS author BELongDead alias/log-name source admission.

Checks only official dataset/metadata + publisher variable-statistics dictionary.
NEVER requests any /api/data rows; never prints variable values, names or descriptions.
Precommitted design: docs/FOREST_BELONGDEAD_AUTHOR_ALIAS_NAMING_SOURCE_GATE_PRESPEC_20261117.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = "https://www.bexis.uni-jena.de"
REGISTRY = (
    (13930, 3, "author_alias_numbers"),
    (16846, 1, "author_log_naming_changes"),
    (16427, 2, "author_subplot_naming"),
    (16390, 1, "author_instrumentation_2009_2010"),
)
MAX_BYTES = 4_000_000
RIGHTS = re.compile(
    r"(?:cc[\s-]*by[\s-]*4(?:\.0)?|creative commons attribution 4(?:\.0)?|"
    r"cc[\s-]*0[\s-]*1(?:\.0)?|public domain)",
    re.IGNORECASE,
)
# Exact families are a TRIAGE of source-author header descriptions, not a join.
FIELD_FAMILIES = {
    "alias_or_renaming": re.compile(
        r"alias|rename|renam|former|previous|old.{0,12}name|new.{0,12}name",
        re.IGNORECASE,
    ),
    "physical_log_or_stem": re.compile(
        r"log|trunk|tree.?id|stem|baum|stamm", re.IGNORECASE
    ),
    "plot_or_subplot": re.compile(
        r"plot|subplot|experimental.?site|fläche|flaeche", re.IGNORECASE
    ),
    "trap_or_instrument": re.compile(
        r"trap|trapping|instrument|flight.?intercept|emergence|eclector",
        re.IGNORECASE,
    ),
    "year_date_period": re.compile(
        r"year|date|period|month|calendar|zeit|jahr", re.IGNORECASE
    ),
    "explicit_effort_or_zero_opportunity": re.compile(
        r"effort|trap.?days?|sampling.?duration|no.?catch|zero.?catch|"
        r"empty.?trap|expos(?:ed|ure)|deployed|installation.?date",
        re.IGNORECASE,
    ),
    "host_or_wood_category": re.compile(
        r"host|wood|holz|tree.?species|totholz", re.IGNORECASE
    ),
}
META_ENDPOINTS = ("dataset", "metadata")
PRESPEC = "docs/FOREST_BELONGDEAD_AUTHOR_ALIAS_NAMING_SOURCE_GATE_PRESPEC_20261117.md"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


class SourceStop(RuntimeError):
    pass


def official_path(dataset_id: int, tag: int, endpoint: str) -> str:
    if (dataset_id, tag) not in {(i, t) for i, t, _ in REGISTRY}:
        raise SourceStop("SOURCE_UNDECLARED_DATASET_OR_TAG")
    if endpoint == "dataset":
        return f"/api/dataset/{dataset_id}"
    if endpoint == "metadata":
        return f"/api/metadata/{dataset_id}?tag={tag}.0"
    if endpoint == "dictionary":
        return f"/api/DataStatistic/{dataset_id}"
    raise SourceStop("SOURCE_UNDECLARED_ENDPOINT")


def read_publisher_json(dataset_id: int, tag: int, endpoint: str):
    path = official_path(dataset_id, tag, endpoint)
    req = urllib.request.Request(ROOT + path, headers={
        "User-Agent": "Structural-response-opaque-BELongDead-author-source-gate/1.0",
        "Accept": "application/json",
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=24) as response:
            raw = response.read(MAX_BYTES + 1)
            http_status = response.status
            ctype = response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        raise SourceStop("SOURCE_HTTP_" + str(exc.code)) from None
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise SourceStop("SOURCE_TRANSPORT_" + type(exc).__name__) from None
    if http_status != 200 or len(raw) > MAX_BYTES or "json" not in ctype.lower():
        raise SourceStop("SOURCE_JSON_RESPONSE_UNAVAILABLE_OR_TOO_LARGE")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError):
        raise SourceStop("SOURCE_JSON_PARSE_STOP") from None
    receipt = {
        "http_status": http_status,
        "original_publisher_response_bytes": len(raw),
        "original_publisher_response_sha256": hashlib.sha256(raw).hexdigest(),
    }
    return document, receipt


def published_open_rights(doc):
    """Scan ONLY license/rights-tagged entries, not arbitrary provenance or values."""
    labels = []
    def recurse(obj, depth=0, rights_context=False):
        if depth > 8 or len(labels) > 100:
            return
        if isinstance(obj, dict):
            for key, val in list(obj.items())[:150]:
                in_rights = rights_context or any(
                    s in str(key).lower()
                    for s in ("license", "licence", "copyright", "accessrights")
                )
                if in_rights:
                    recurse(val, depth + 1, True)
                elif isinstance(val, (dict, list)):
                    recurse(val, depth + 1, False)
        elif isinstance(obj, list):
            for val in obj[:100]:
                recurse(val, depth + 1, rights_context)
        elif rights_context and isinstance(obj, str) and len(obj) <= 1000:
            labels.append(obj)
    recurse(doc)
    return any(RIGHTS.search(x) for x in labels)


def dictionary_family_counts(doc):
    if not isinstance(doc, list) or not 1 <= len(doc) <= 250:
        raise SourceStop("SOURCE_PUBLISHER_DICTIONARY_SHAPE_STOP")
    seen = set()
    family_counts = {key: 0 for key in FIELD_FAMILIES}
    source_fields = 0
    for var in doc:
        if not isinstance(var, dict):
            raise SourceStop("SOURCE_PUBLISHER_DICTIONARY_ENTRY_STOP")
        field = var.get("VariableName", var.get("variableName"))
        if not isinstance(field, str) or not 1 <= len(field) <= 200:
            raise SourceStop("SOURCE_PUBLISHER_DICTIONARY_NAME_STOP")
        if field in seen:
            raise SourceStop("SOURCE_PUBLISHER_DICTIONARY_DUPLICATE_FIELD_STOP")
        seen.add(field)
        source_fields += 1
        description = var.get("VariableDescription", var.get("variableDescription", ""))
        # Description and field name are processed IN MEMORY ONLY.
        # All uniqueValues / min / max / counts / measurements are never accessed.
        if not isinstance(description, str):
            description = ""
        text = field + " " + description[:2000]
        for label, pattern in FIELD_FAMILIES.items():
            if pattern.search(text):
                family_counts[label] += 1
    return {
        "original_publisher_dictionary_field_count": source_fields,
        "publisher_field_name_description_candidate_family_counts_ONLY": family_counts,
        "original_publisher_variable_names_descriptions_NOT_EXPORTED": True,
        "original_publisher_uniqueValues_min_max_counts_NOT_ACCESSED_OR_EXPORTED": True,
        "dictionary_may_reflect_latest_not_published_tag": True,
        "no_source_author_crosswalk_or_effort_proven_by_headers": True,
    }


def audit_one(dataset_id, tag, family):
    entry = {
        "original_public_dataset_id": dataset_id,
        "original_catalogue_tag": tag,
        "author_catalogue_method_family": family,
        "published_catalogue_source": (
            "https://www.biodiversity-exploratories.de/en/projects/"
            "arthropods-i-land-use-above-ground-arthropod-diversity-"
            "and-arthropod-affected-processes/"
        ),
        "original_data_rows_requested": 0,
        "original_beetle_abundance_species_trait_deadwood_values_read": 0,
        "tagged_file_integrity_NOT_YET_AUDITED": True,
        "original_31124_15_TrapID_aliases_NOT_RECONCILED": True,
    }
    rights = False
    for endpoint in META_ENDPOINTS:
        try:
            doc, receipt = read_publisher_json(dataset_id, tag, endpoint)
            entry[endpoint + "_source_metadata_receipt"] = receipt
            rights = rights or published_open_rights(doc)
        except SourceStop as exc:
            entry[endpoint + "_source_metadata_status"] = str(exc)
    entry["publisher_open_rights_in_author_metadata_verified"] = rights
    if not rights:
        entry["status"] = "SOURCE_ACCESS_OR_RIGHTS_STOP"
        return entry
    if not all(endpoint + "_source_metadata_receipt" in entry for endpoint in META_ENDPOINTS):
        entry["status"] = "SOURCE_ACCESS_OR_RIGHTS_STOP"
        return entry
    try:
        doc, receipt = read_publisher_json(dataset_id, tag, "dictionary")
        entry["publisher_dictionary_source_receipt"] = receipt
        entry["publisher_dictionary_source_only"] = dictionary_family_counts(doc)
        counts = entry["publisher_dictionary_source_only"][
            "publisher_field_name_description_candidate_family_counts_ONLY"
        ]
        if counts["alias_or_renaming"] or counts["trap_or_instrument"]:
            entry["status"] = "SOURCE_FIELD_CANDIDATES_ONLY"
        else:
            entry["status"] = "SOURCE_DICTIONARY_ONLY_HOLD"
    except SourceStop as exc:
        entry["publisher_dictionary_source_status"] = str(exc)
        entry["status"] = "SOURCE_DICTIONARY_ONLY_HOLD"
    return entry


def run():
    results = [audit_one(i, tag, label) for i, tag, label in REGISTRY]
    return {
        "schema": "structural.BELongDead_author_alias_logname_metadata_dictionary_gate.v1",
        "precommit": PRESPEC,
        "source_count": len(results),
        "official_author_sources": results,
        "original_full_beetle_31123_log_31124_and_24546_data_read_count": 0,
        "all_original_species_trap_wood_sampling_rows_READ": False,
        "original_15_nonmatching_TrapID_key_problem_RESOLVED": False,
        "field_candidate_only_NEVER_authorizes_any_join": True,
        "independent_multicountry_hostresource_functional_guild_replication_VERIFIED": False,
        "existing_PREDICTS_Finland_Chiu_Piccini_NEON_BALA_GEB_effects_UNCHANGED": True,
        "eBird_used": False,
        "TinyFish_used": False,
        "status": "SOURCE_METHOD_ONLY_NO_BIOLOGICAL_EFFECT",
    }


def synthetic():
    assert len(REGISTRY) == 4
    assert official_path(13930, 3, "metadata").endswith("/13930?tag=3.0")
    try:
        official_path(31123, 1, "dictionary")
        raise AssertionError("old beetle data unexpectedly allowed")
    except SourceStop:
        pass
    try:
        official_path(13930, 1, "metadata")
        raise AssertionError("wrong published tag allowed")
    except SourceStop:
        pass
    fixture = [
        {
            "VariableName": "OldLogName",
            "VariableDescription": "previous naming for a trunk, not a trap event",
            "DataTypeName": "string",
            "uniqueValues": ["SECRET_INDIVIDUAL_SOURCE_LOG_ID"],
            "min": -999,
        },
        {
            "VariableName": "TrapDays",
            "VariableDescription": "sampling effort column, no actual values supplied",
            "uniqueValues": [9876543],
        },
    ]
    checked = dictionary_family_counts(fixture)
    rendered = json.dumps(checked)
    assert checked["original_publisher_dictionary_field_count"] == 2
    assert checked["publisher_field_name_description_candidate_family_counts_ONLY"][
        "alias_or_renaming"
    ] == 1
    assert checked["publisher_field_name_description_candidate_family_counts_ONLY"][
        "explicit_effort_or_zero_opportunity"
    ] == 1
    for forbidden in ("OldLogName", "TrapDays", "SECRET_INDIVIDUAL_SOURCE_LOG_ID", "9876543", "-999"):
        assert forbidden not in rendered
    assert published_open_rights({"license": "CC BY 4.0"})
    assert not published_open_rights({"license": "Access upon request"})
    assert not published_open_rights({"metadata": "CC BY 4.0", "license": "private"})
    print("SYNTHETIC_AUTHOR_NAMING_GATE_NO_ROWS_NO_VALUES_NO_ID_EXPORT_PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    synthetic()
    if args.test:
        return
    if args.out is None:
        parser.error("--out directory required")
    results = run()
    args.out.mkdir(parents=True, exist_ok=True)
    artifact = args.out / "BELongDead_original_author_naming_alias_source_schema_only.json"
    artifact.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # Output only sanitized source statuses to GitHub logs.
    for entry in results["official_author_sources"]:
        print(
            "BEXIS_AUTHOR_NAMING_SOURCE_STATUS",
            entry["original_public_dataset_id"],
            entry["status"],
        )
    print("RESPONSE_SEALED_ORIGINAL_AUTHOR_ALIAS_GATE_DONE_NO_BIOLOGICAL_EFFECT")


if __name__ == "__main__":
    main()
