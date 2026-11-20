#!/usr/bin/env python3
"""Source-only exact Zenodo 302 Location diagnostic; no GET of target or data.

Does not replace historical 17775804 source-index HTTP302 STOP.
"""
from __future__ import annotations
import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

URL = "https://zenodo.org/api/records/17775804"
RECORD_ID = 17775804
PRESPEC = ("docs/FOREST_MACRO_KORTMANN2026_CONCEPT_REDIRECT_"
           "SOURCEONLY_DIAG_PREFREEZE_20261120.md")
PATH_RULE = re.compile(r"^/api/records/([1-9][0-9]*)$")


class SourceStop(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def parse_302_target(location):
    if not isinstance(location, str) or len(location) > 2048:
        raise SourceStop("SOURCE_REDIRECT_LOCATION_MISSING_OR_UNSAFE")
    p = urllib.parse.urlsplit(location)
    if p.query or p.fragment or p.username or p.password:
        raise SourceStop("SOURCE_REDIRECT_HAS_FORBIDDEN_COMPONENT")
    if p.scheme or p.netloc:
        if p.scheme != "https" or p.netloc != "zenodo.org":
            raise SourceStop("SOURCE_REDIRECT_NOT_EXACT_PUBLISHER")
    elif not location.startswith("/"):
        raise SourceStop("SOURCE_REDIRECT_RELATIVE_NOT_ROOTED")
    match = PATH_RULE.fullmatch(p.path)
    if match is None:
        raise SourceStop("SOURCE_REDIRECT_NOT_CANONICAL_RECORD_PATH")
    target = int(match.group(1))
    if target == RECORD_ID:
        raise SourceStop("SOURCE_REDIRECT_LOOPS_TO_SOURCE_RECORD")
    return {
        "target_record_id": target,
        "same_original_zenodo_publisher": True,
        "destination_url_NOT_REQUESTED": True,
        "target_version_and_file_roster_NOT_AUTHENTICATED": True,
        "candidate_only_NOT_ADMITTED_FOR_DATA": True,
    }


def inspect_original_http_302_only():
    req = urllib.request.Request(
        URL,
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": "Structural-Kortmann17775804-ExactRedirectMetadataOnly/1.0",
        },
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=45) as response:
            # A direct HTTP 200 would be a change in original route; this
            # diagnostic NEVER consumes a source response body.
            raise SourceStop("SOURCE_ORIGINAL_RETURNED_" + str(response.status) +
                             "_NOT_HTTP302")
    except urllib.error.HTTPError as exc:
        if exc.code != 302:
            raise SourceStop("SOURCE_ORIGINAL_HTTP_" + str(exc.code) +
                             "_NOT_PREDECLARED_302") from None
        location = exc.headers.get("Location")
        # no read() on the HTTPError response
        return parse_302_target(location)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise SourceStop("SOURCE_ORIGINAL_TRANSPORT_" + type(exc).__name__) from None


def synthetic_tests():
    for valid, target in [
        ("/api/records/18888888", 18888888),
        ("https://zenodo.org/api/records/16660000", 16660000),
    ]:
        assert parse_302_target(valid)["target_record_id"] == target
    for bad in [
        "https://evil.example/api/records/123",
        "//evil.example/api/records/123",
        "https://zenodo.org@evil.example/api/records/123",
        "/api/records/17775804",
        "/api/records/0",
        "/api/records/123/files",
        "/api/records/123?download=true",
        "https://zenodo.org/api/records/123#info",
        "http://zenodo.org/api/records/123",
        "api/records/123",
        "/api/records/123/",
    ]:
        try:
            parse_302_target(bad)
        except SourceStop:
            pass
        else:
            raise AssertionError("invalid Location accepted")
    print("SYNTHETIC_KORTMANN_302_EXACT_PUBLISHER_AND_NO_TARGET_GET_PASS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    synthetic_tests()
    if args.test:
        return
    if args.out is None:
        p.error("--out required")
    result = {
        "schema": "structural.Kortmann17775804_original_HTTP302_location_only_v1",
        "prespec": PRESPEC,
        "original_source_url": URL,
        "source_record_ID": RECORD_ID,
        "historical_HTTP302_STOP_UNCHANGED": True,
        "target_get_requests": 0,
        "original_file_member_requests": 0,
        "original_plot_method_or_OTU_rows_READ": 0,
        "original_biodiversity_effects_fitted": 0,
        "not_independent_biome_replication": True,
        "eBird_used": False,
        "TinyFish_used": False,
    }
    try:
        result["redirect"] = inspect_original_http_302_only()
        result["status"] = "SOURCE_ONLY_CANONICAL_TARGET_ID_IDENTIFIED_NOT_ADMITTED"
    except SourceStop as exc:
        result["status"] = "SOURCE_ONLY_REDIRECT_DIAGNOSTIC_STOP_" + str(exc)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("KORTMANN2026_302_SOURCE_DIAG", result["status"])
    if "redirect" in result:
        print("CANONICAL_TARGET_CANDIDATE_ID",
              result["redirect"]["target_record_id"])
    print("NO_TARGET_GET; NO_ORIGINAL_FILES; NO_ORGANISM_SOURCE_ROWS")


if __name__ == "__main__":
    main()
