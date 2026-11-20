#!/usr/bin/env python3
"""Original ONE-SHOT BETA-FOR insect OTU biological scorer launcher.

Original 99-patch / 594-event source and treatment pair are validated before
biological response download. Original raw files stay inside private GitHub
runner TemporaryDirectory only; ALL exported values are aggregate.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import urllib.error
import urllib.request

from betafor11_publisher_metadata_preintake_only import (
    get_official_metadata_only, SourceStop,
)
from betafor11_v2_missingversion_firstheader_sourceonly import (
    validate_publisher_v2,
)
from betafor11_information_firstheader_gate import (
    source_publisher_file_link, official_original_file_bytes, NoRedirect,
)
from betafor11_author_treatment_pairs_sourceonly import (
    read_method_only,
)
from betafor11_otu_original_firstheader_only import (
    published_otutable_link, source_method_label_universe,
)
from betafor11_author_r_four_meta_header_v4_sourceonly import (
    verify_author_roles,
)

PRESPEC = "docs/FOREST_MACRO_BETAFOR11_GEOMETRY_VS_WOOD_BETA_PRIMARY_FREEZE_20261120.md"
ORIGINAL_OTU_MD5 = "81e2c1269bff49fafdf497f03f5922b2"
ORIGINAL_META_MD5 = "873f5d424904d1eed00e079b945dd5dc"
FOREST_CODE = "analysis/forest_macro_global/betafor11_geometry_vs_wood_beta_onepass.R"
MAX_RESPONSE = 80 * 1024 * 1024
NON_NUMERIC = frozenset({
    "status",
    "six_region_mean_D_sorted_anonymous",
    "original_source_6_samples_each_patch",
    "original_source_Simpson_replacement_not_total_Sorensen",
    "biological_response_source_row_values_EXPORTED",
    "original_OTU_species_and_patch_IDs_EXPORTED",
    "all_prior_biological_results_unmodified",
    "not_an_independent_cross_biome_replication",
})


def download_opaque_original_member(source_link, expected_size, md5, destination):
    """Stream verified original bytes into runner-only temp, never artifact."""
    if not 0 < expected_size <= MAX_RESPONSE:
        raise SourceStop("BIOLOGY_SOURCE_ORIGINAL_FILE_SIZE_UNSAFE")
    req = urllib.request.Request(
        source_link,
        headers={"Accept": "*/*",
                 "User-Agent": "Structural-BETAFOR11-ONEPASS-original-source/1.0"},
    )
    seen = 0
    checksum = hashlib.md5()
    first = bytearray()
    first_ended = False
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=90) as resp:
            if resp.status != 200:
                raise SourceStop("BIOLOGY_SOURCE_ORIGINAL_HTTP_NOT200")
            with destination.open("wb") as output:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    seen += len(chunk)
                    if seen > expected_size:
                        raise SourceStop("BIOLOGY_SOURCE_ORIGINAL_RESPONSE_OVERSIZE")
                    checksum.update(chunk)
                    output.write(chunk)
                    if not first_ended:
                        pos = chunk.find(b"\n")
                        if pos >= 0:
                            first.extend(chunk[:pos])
                            first_ended = True
                        else:
                            first.extend(chunk)
                        if len(first) > 2 * 1024 * 1024:
                            raise SourceStop("BIOLOGY_SOURCE_HEADER_UNSAFELY_LONG")
    except urllib.error.HTTPError as ex:
        raise SourceStop("BIOLOGY_SOURCE_HTTP_" + str(ex.code)) from None
    except (urllib.error.URLError, TimeoutError, OSError) as ex:
        raise SourceStop("BIOLOGY_SOURCE_TRANSPORT_" + type(ex).__name__) from None
    if seen != expected_size or checksum.hexdigest() != md5 or not first_ended:
        raise SourceStop("BIOLOGY_SOURCE_ORIGINAL_COMPLETE_FILE_MD5_OR_LENGTH_DRIFT")
    return bytes(first), seen


def read_aggregate_table(filename):
    if not filename.is_file() or filename.stat().st_size > 30000:
        raise SourceStop("BIOLOGY_SCORE_AGGREGATE_OUTPUT_MISSING_OR_UNSAFE")
    with filename.open("r", encoding="utf-8", newline="") as h:
        reader = csv.DictReader(h, delimiter="\t")
        if reader.fieldnames != ["metric", "value"]:
            raise SourceStop("BIOLOGY_SCORE_OUTPUT_TWO_COLUMN_SCHEMA_CHANGED")
        rows = list(reader)
    if not 30 <= len(rows) <= 60:
        raise SourceStop("BIOLOGY_SCORE_OUTPUT_FIELD_COUNT_UNEXPECTED")
    if any(row.get(None) is not None for row in rows):
        raise SourceStop("BIOLOGY_SCORE_OUTPUT_EXTRA_FIELDS")
    payload = {}
    for r in rows:
        key, value = r["metric"], r["value"]
        if not isinstance(key, str) or not key.isidentifier() or key in payload:
            raise SourceStop("BIOLOGY_SCORE_RESULT_DUPLICATE_OR_UNSAFE_KEY")
        if not isinstance(value, str) or len(value) > 1000:
            raise SourceStop("BIOLOGY_SCORE_RESULT_UNEXPECTED_VALUE")
        if key in NON_NUMERIC:
            payload[key] = value
        else:
            try:
                number = float(value)
            except (ValueError, TypeError):
                raise SourceStop("BIOLOGY_SCORE_EXPECTED_NUMERIC_OUTPUT_INVALID") from None
            if not __import__("math").isfinite(number):
                raise SourceStop("BIOLOGY_SCORE_NONFINITE_NUMBER")
            payload[key] = number
    if payload.get("status") not in (
        "EXPLORATORY_REGION_EQUAL_GWD_DIRECTIONALLY_SUPPORTED",
        "EXPLORATORY_REGION_EQUAL_GWD_NOT_SUPPORTED",
    ):
        raise SourceStop("BIOLOGY_SCORE_SOURCE_DIRECTIONAL_STATUS_UNRECOGNIZED")
    if (payload.get("original_sample_columns") != 594 or
        payload.get("original_patches") != 99 or
        payload.get("original_parent_forests") != 11 or
        payload.get("original_geographic_regions") != 6):
        raise SourceStop("BIOLOGY_SCORE_ORIGINAL_INDEPENDENT_DENOMINATOR_DRIFT")
    if payload.get("original_source_6_samples_each_patch") != "true":
        raise SourceStop("BIOLOGY_SCORE_SOURCE_EFFORT_NOT_VERIFIED")
    if (payload.get("biological_response_source_row_values_EXPORTED") != "false" or
        payload.get("original_OTU_species_and_patch_IDs_EXPORTED") != "false" or
        payload.get("not_an_independent_cross_biome_replication") != "true"):
        raise SourceStop("BIOLOGY_SCORE_SOURCE_DATA_PRIVACY_OR_SCOPE_DRIFT")
    if abs(
        payload["primary_region_equal_G_simpson"]
        - payload["primary_region_equal_W_simpson"]
        - payload["primary_region_equal_D_geometry_minus_wood"]
    ) > 1e-9:
        raise SourceStop("BIOLOGY_SCORE_G_MINUS_W_ARITHMETIC_INCONSISTENT")
    if not 0 <= payload["six_region_exact_signed_two_sided_p"] <= 1:
        raise SourceStop("BIOLOGY_SCORE_EXACT_P_OUT_OF_RANGE")
    if not 0 <= payload["within_forest_999_label_permutation_2sided_p"] <= 1:
        raise SourceStop("BIOLOGY_SCORE_PERMUTATION_P_OUT_OF_RANGE")
    if payload["original_author_singleton_corrected_OTU_rows"] > payload["original_counted_OTU_rows"]:
        raise SourceStop("BIOLOGY_SCORE_CORRECTION_COUNTS_INCONSISTENT")
    return payload


def run_source_and_biology():
    # This is ONE original biological response opening, after frozen physical
    # source and treatment gates. Do not rescore after a completed result.
    orig = get_official_metadata_only()
    provenance = validate_publisher_v2(orig)
    if not provenance["original_six_filenames_MD5s_and_sizes_verified"]:
        raise SourceStop("BIOLOGY_SOURCE_ORIGINAL_PUBLISHER_SIX_MD5_HOLD")
    method_link, method_size = source_publisher_file_link(orig)
    method_bytes = official_original_file_bytes(method_link, method_size)
    if hashlib.md5(method_bytes).hexdigest() != ORIGINAL_META_MD5:
        raise SourceStop("BIOLOGY_SOURCE_INFORMATION_MD5_CHANGED")
    method = read_method_only(method_bytes)
    if method["status"] != "SOURCE_TREATMENT_4PAIR_METHOD_READY_CHRONOLOGY_READY_NO_BIOLOGY":
        raise SourceStop("BIOLOGY_SOURCE_ORIGINAL_TREATMENT_PAIR_OR_CHRONOLOGY_NOT_ADMITTED")
    labels, patches, n_unique = source_method_label_universe(method_bytes)
    if len(labels) != 594 or len(patches) != 99 or n_unique != 594:
        raise SourceStop("BIOLOGY_SOURCE_SAMPLE_KEY_UNIVERSE_CHANGED")
    response_link, response_size = published_otutable_link(orig)
    if not Path(FOREST_CODE).is_file():
        raise SourceStop("BIOLOGY_SCORER_SOURCE_NOT_COMMITTED")
    with tempfile.TemporaryDirectory(prefix="structural-betafor-original-onepass-") as d:
        root = Path(d)
        original_method = root / "original_method.csv"
        original_otu = root / "original_otu.csv"
        tab = root / "anonymous_scientific_result.tsv"
        original_method.write_bytes(method_bytes)
        first, full_size = download_opaque_original_member(
            response_link, response_size, ORIGINAL_OTU_MD5, original_otu,
        )
        header = verify_author_roles(first, labels)
        if header["status"] != "BETAFOR11_AUTHOR_R_FOUR_SOURCE_META_HEADER_ROLES_QUALIFIED_ONLY":
            raise SourceStop("BIOLOGY_SOURCE_AUTHOR_R_HEADER_ROLES_NOT_ADMITTED")
        # R code is pure base R, and emits ONLY anonymous scalars and
        # six region means without region identifiers.
        completed = subprocess.run(
            ["Rscript", "--vanilla", FOREST_CODE,
             str(original_method), str(original_otu), str(tab)],
            capture_output=True, text=True, timeout=540, check=False,
        )
        if completed.returncode != 0:
            # Do NOT write R stderr/stdout: source IDs must not leak.
            # A source-effect attempt that opened original rows is not an
            # independent subsequent validation if it needs repair.
            raise SourceStop("BIOLOGY_ORIGINAL_ONEPASS_R_RUN_TERMINAL_NONZERO")
        derived = read_aggregate_table(tab)
        derived["original_response_file_MD5_verified"] = ORIGINAL_OTU_MD5
        derived["original_response_file_full_publisher_bytes_verified"] = full_size
        derived["original_metadata_file_MD5_verified"] = ORIGINAL_META_MD5
        derived["prior_original_treatment_source_gate_passed"] = True
        derived["original_first_four_OTU_header_roles_pinned"] = True
        derived["all_raw_original_data_files_runner_temp_only"] = True
        derived["one_original_outcome_opening_consumed"] = True
        return derived


def synthetic():
    fake = {
        "status": "EXPLORATORY_REGION_EQUAL_GWD_NOT_SUPPORTED",
        "original_sample_columns": 594,
        "original_patches": 99,
        "original_parent_forests": 11,
        "original_geographic_regions": 6,
        "original_source_6_samples_each_patch": "true",
        "biological_response_source_row_values_EXPORTED": "false",
        "original_OTU_species_and_patch_IDs_EXPORTED": "false",
        "not_an_independent_cross_biome_replication": "true",
    }
    # The parser cannot accidentally accept source sample values masquerading
    # as a reported forest-level inference.
    with tempfile.TemporaryDirectory() as d:
        file = Path(d) / "safe.tsv"
        rows = [("metric", "value")] + list(fake.items())
        with file.open("w", encoding="utf-8", newline="") as h:
            w = csv.writer(h, delimiter="\t")
            w.writerows(rows)
        try:
            read_aggregate_table(file)
        except SourceStop:
            pass
        else:
            raise AssertionError("insufficient fake biological model accepted")
    assert PRESPEC.endswith("20261120.md")
    print("SYNTHETIC_BETAFOR11_R_ONEPASS_LAUNCHER_SOURCE_REDACTION_AND_SCHEMA_PASS")


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
    report = {
        "schema": "structural.BETAFOR11_20261120_geometry_vs_wood_original_onepass.v1",
        "prespec": PRESPEC,
        "original_source_2025_paper": "10.1111/1365-2664.70086",
        "original_source_versioned_DOI": "10.5281/zenodo.15371332",
        "original_author_code_DOI": "10.5281/zenodo.15165462",
        "old_forest_and_island_ecological_results_preserved": True,
        "global_cross_biome_replication_claim": False,
        "source_original_11_forests_in_6_regions": True,
        "original_OTU_species_IDs_or_site_coordinate_records_EXPORTED": False,
        "eBird_used": False,
        "TinyFish_used": False,
    }
    try:
        report["derived_anonymous_scientific_result"] = run_source_and_biology()
        report["status"] = report["derived_anonymous_scientific_result"]["status"]
    except SourceStop as ex:
        report["status"] = str(ex)
        report["source_or_model_STOP_not_necessarily_null_biological_effect"] = True
    except subprocess.TimeoutExpired:
        report["status"] = "BIOLOGY_ORIGINAL_ONEPASS_R_TIMEOUT_STOP"
        report["source_or_model_STOP_not_necessarily_null_biological_effect"] = True
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False,
                                  sort_keys=True)+"\n",encoding="utf-8")
    print("BETAFOR11_ORIGINAL_NEW_ECOLOGICAL_ONEPASS", report["status"])
    if "derived_anonymous_scientific_result" in report:
        obj = report["derived_anonymous_scientific_result"]
        for key in (
            "primary_region_equal_G_simpson",
            "primary_region_equal_W_simpson",
            "primary_region_equal_D_geometry_minus_wood",
            "six_region_bootstrap_4000_CI_lower",
            "six_region_bootstrap_4000_CI_upper",
            "six_region_exact_signed_two_sided_p",
            "within_forest_999_label_permutation_2sided_p",
            "region_positive_D_count",
            "region_negative_D_count",
        ):
            print(key, obj[key])
    print("NO_RAW_OTU_ROWS_OR_PHYSICAL_SOURCE_IDS_EXPORTED")


if __name__ == "__main__":
    main()
