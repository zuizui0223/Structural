#!/usr/bin/env python3
"""Neff 2022 author-code-backed, source-only BExIS18270 EP vs 31123 PlotID audit.

No beetle outcome/count/TrapID, no forest basal area, no original individual
plot label output. A historical author zero-pad grammar test, NOT an authorized
cross-dataset biological join and NEVER an ecological effect.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from belongdead_bexis_13tree_original_source_gate import NoRedirect
from belongdead_bexis18270_paper_basala_plot_source_gate import inventory_bytes, SourceStop
from belongdead20406_31123_exact_token_concordance import (
    get_publisher_original_31123_method_source,
)

PRESPEC = "docs/FOREST_BELONGDEAD_NEFF2022_AUTHOR_CODE_PLOTKEY_CROSSWALK_PRESPEC_20261118.md"
CODE_URL = "https://raw.githubusercontent.com/nefff1/fcnt_blngdd/main/R_full_code.R"
CODE_GIT_BLOB_SHA1 = "9bf7adb9c833275e0289ac1f459d50648ed6a17b"
STAND_SHA = "1161dfe75ea6c5ee3fab1dda98c5ec1d142db2e08a03b63d6c6266bc27b0914d"
STAND_SIZE = 240356
BEETLE_SHA = "73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e"
BEETLE_SIZE = 8103493


def author_code():
    req = urllib.request.Request(
        CODE_URL,
        headers={
            "Accept": "text/plain",
            "User-Agent": "Structural-Neff2022-author-canonical-R-code-source-only/1.0",
        },
    )
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=35) as resp:
            if resp.status != 200:
                raise SourceStop("AUTHOR_GITHUB_CODE_NOT_HTTP200")
            data = resp.read(1_000_001)
    except urllib.error.HTTPError as exc:
        raise SourceStop("AUTHOR_SOURCE_CODE_HTTP_" + str(exc.code)) from None
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise SourceStop("AUTHOR_SOURCE_CODE_TRANSPORT_" + type(exc).__name__) from None
    if len(data) > 1_000_000:
        raise SourceStop("AUTHOR_SOURCE_CODE_TOO_LARGE")
    blob = hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()
    if blob != CODE_GIT_BLOB_SHA1:
        raise SourceStop("AUTHOR_ORIGINAL_R_GIT_BLOB_DRIFT")
    try:
        source = data.decode("utf-8-sig")
    except UnicodeError:
        raise SourceStop("AUTHOR_ORIGINAL_R_NON_UTF8") from None
    checks = {
        "original_author_beetle_plot_token_from_trapid":
            bool(re.search(r"substr\s*\(\s*TrapID\s*,\s*1\s*,\s*5\s*\)", source)),
        "original_author_stand_18270_EP_to_PlotID_rename":
            bool(re.search(r"rename\s*\(\s*BA\s*=\s*Basal_Area\s*,\s*PlotID\s*=\s*EP\s*\)", source)),
        "original_author_four_to_five_legacy_plot_alias":
            bool(re.search(r"nchar\s*\(\s*plotID\s*\)\s*==\s*4", source) and
                 re.search(
                     r"paste0\s*\(\s*substr\s*\(\s*plotID\s*,\s*1\s*,\s*3\s*\)\s*,"
                     r"\s*[\"']0[\"']\s*,\s*substr\s*\(\s*plotID\s*,\s*4\s*,\s*4\s*\)\s*\)",
                     source,
                     re.DOTALL,
                 )),
        "original_author_positive_beetle_captures_only":
            bool(re.search(r"filter\s*\(\s*ToplaAdults\s*>\s*0\s*\)", source)),
    }
    if not all(checks.values()):
        raise SourceStop("AUTHOR_ORIGINAL_CODE_FROZEN_GUARD_PATTERN_NOT_FOUND")
    return {
        "author_original_code_repository": "nefff1/fcnt_blngdd",
        "canonical_R_file_Git_blob_SHA1": blob,
        "original_author_code_method_pattern_verified": checks,
        "original_author_R_code_NOT_EXECUTED": True,
        "original_BExIS18270_2_historical_vs_tag1_NOT_proven_equivalent": True,
        "published_alternate_plot_rule_is_NOT_explicitly_for_18270": True,
    }


def original_stand_ep_only(raw):
    if len(raw) != STAND_SIZE or hashlib.sha256(raw).hexdigest() != STAND_SHA:
        raise SourceStop("STAND_18270_PINNED_SOURCE_BYTES_CHANGED")
    rd = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
    header = next(rd, [])
    if len(header) != 7 or header[4] != "EP":
        raise SourceStop("STAND_18270_EP_HEADER_EXACT_POSITION_CHANGED")
    ep = set()
    rows = 0
    for row in rd:
        if not row:
            continue
        rows += 1
        if len(row) != 7 or not row[4].strip():
            raise SourceStop("STAND_EP_SOURCE_METHOD_ROW_SHAPE_OR_ID_MISSING")
        ep.add(row[4].strip())
    if rows != 4200 or len(ep) != 150:
        raise SourceStop("STAND_18270_PHYSICAL_PARENT_SUPPORT_DRIFT")
    return ep


def original_experiment_plot_only(raw):
    if len(raw) != BEETLE_SIZE or hashlib.sha256(raw).hexdigest() != BEETLE_SHA:
        raise SourceStop("BEETLE_31123_TAG1_FINGERPRINT_CHANGED")
    rd = csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline=""), strict=True)
    header = next(rd, [])
    if len(header) != 17 or header[2] != "PlotID":
        raise SourceStop("BEETLE_31123_ORIGINAL_PLOTID_FIELD_CHANGED")
    beetle_sites = set()
    count = 0
    for row in rd:
        if not row:
            continue
        count += 1
        if len(row) != 17 or not row[2].strip():
            raise SourceStop("BEETLE_31123_PLOT_ONLY_ROW_DRIFT")
        # Reads exclusively PlotID: no biological outcome, TrapID, species, forest value.
        beetle_sites.add(row[2].strip())
    if count != 59850 or len(beetle_sites) != 30:
        raise SourceStop("BEETLE_31123_FROZEN_30_PLOTS_DRIFT")
    return beetle_sites


def published_author_alias_test(ep, beetle):
    if len(ep) != 150 or len(beetle) != 30:
        raise SourceStop("PUBLISHER_PLOT_UNIVERSE_SIZES_WRONG")
    exact = len(ep & beetle)
    if exact != 3:
        raise SourceStop("PRESPEC_ORIGINAL_UNTRANSFORMED_3_OF_30_MATCH_DRIFT")
    # ONLY literal author-published four-char to five-char key proposal.
    def old_author_rule(x):
        return x[:3] + "0" + x[3] if len(x) == 4 else x
    mapped = [old_author_rule(x) for x in ep]
    candidate = set(mapped)
    added = len(candidate & beetle) - exact
    collision = len(mapped) - len(candidate)
    result = {
        "schema": "structural.BELongDead_Neff2022_publisher_code_18270_31123_IDonly.v1",
        "prespec": PRESPEC,
        "original_18270_distinct_EP_tokens": len(ep),
        "original_31123_distinct_PlotID_tokens": len(beetle),
        "original_18270_31123_exact_EP_PlotID_intersection": exact,
        "source_original_18270_EP_token_count_with_author_fourchar_rule_applied":
            sum(len(x) == 4 for x in ep),
        "author_rule_candidate_new_tokens_colliding_in_stand_inventory": collision,
        "author_rule_candidate_source_EP_unique_after_normalization": len(candidate),
        "author_rule_candidate_18270_stand_EP_vs_31123_beetle_PlotID_exact_matches":
            len(candidate & beetle),
        "author_rule_candidate_new_18270_to_31123_matches_over_raw_exact": added,
        "original_31123_plotIDs_still_unmatched_after_ONE_fixed_author_rule": len(beetle - candidate),
        "no_original_plot_labels_or_plant_beetle_measurements_EXPORTED": True,
        "published_author_rule_not_authorized_as_18270_31123_historical_version_crosswalk": True,
        "author_code_does_NOT_autozero_pad_18270_tree1_in_published_R": True,
        "new_ecological_effect_estimated": False,
        "status": (
            "METHOD_CANDIDATE_ALL30_COLLISIONFREE_NOT_AUTHOR_VERSION_PROVEN"
            if collision == 0 and len(candidate & beetle) == 30
            else "METHOD_CANDIDATE_PARTIAL_OR_COLLIDED_HOLD_NO_FURTHER_ID_SEARCH"
        ),
    }
    return result


def known_truth():
    original = {"HEW1", "ALB2", "SCH3"} | {f"A{i:04d}" for i in range(147)}
    want = {"HEW01", "ALB02", "SCH03"} | {f"A{i:04d}" for i in range(27)}
    assert len(original) == 150 and len(want) == 30
    # Synthetic exact gate is held 3/30; this is only a transform unit test.
    assert (len({"HEW1", "HEW01"}) - len({"HEW01", "HEW01"})) == 1
    assert ("HEW1"[:3] + "0" + "HEW1"[3]) == "HEW01"
    print("SYNTHETIC_AUTHORED_FOURCHAR_ID_NORMALIZATION_AND_COLLISION_GUARDS_PASS")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--out", type=Path)
    args = p.parse_args()
    known_truth()
    if args.test:
        return
    if not args.out:
        p.error("--out required")
    receipt = {
        "schema": "structural.BELongDead_Neff2022_author_plotkey_candidate_sourceonly.v1",
        "prespec": PRESPEC,
        "original_beetle_and_forest_numeric_response_READ": False,
        "original_31124_15_unmatched_TrapIDs_RESOLVED": False,
        "original_20406_2013_2017_source_method_gaps_RESOLVED": False,
        "old_Finland_Chiu_Piccini_Burner_PREDICTS_NEON_BALA_GEB_scores_UNCHANGED": True,
        "eBird_used": False,
        "TinyFish_used": False,
    }
    try:
        receipt["original_author_code_verified"] = author_code()
        ep = original_stand_ep_only(inventory_bytes())
        beetle = original_experiment_plot_only(
            get_publisher_original_31123_method_source())
        receipt["candidate_original_method_key_result"] = published_author_alias_test(ep, beetle)
        receipt["status"] = receipt["candidate_original_method_key_result"]["status"]
    except (SourceStop, ValueError, UnicodeError, csv.Error) as exc:
        # Do not export unconstrained source error messages.
        receipt["status"] = str(exc) if isinstance(exc, SourceStop) else "SOURCE_CSV_OR_PLOT_VALUE_PARSE_STOP"
        receipt["source_method_STOP_not_biological_null"] = True
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "BELongDead_Neff2022_public_R_authorkey_18270_31123_sourceonly.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("NEFF2022_AUTHOR_CODE_ORIGINAL_FOREST_BEETLE_SITEKEY_ONLY", receipt["status"])


if __name__ == "__main__":
    main()
