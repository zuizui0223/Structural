#!/usr/bin/env python3
"""Kortmann 2026 original OTU RData FIRST schema + sample-key identity, NO scores.

Response-bearing OTU object IS deserialized in isolated R memory; its numeric
values are never accessed/summarized. Source sample/OTU labels never exported.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path

from kortmann2026_17775805_original_zip_directory_only import (
    SourceStop, original_file_metadata, official_get_one_zip,
    inspect_central_directory_only,
)
PRESPEC = "docs/FOREST_MACRO_KORTMANN39_OTU_SAMPLE_IDENTITY_PREOPEN_20261121.md"
SCRIPT = Path(__file__).with_name("kortmann2026_otu_sample_identity_schema.R")
SOURCES = {
    "data_public/diversity_satellite.rda": {
        "size": 67238,
        "sha": "8b3f47258b4d9c8f6fa0f7fac0d820ecccb860adadaa9c3c311f21fa28e3da3a",
    },
    "data_public/otu_matrix.rda": {"size": 1371944},
}
METRICS = {
    "method_id_eligible_fields",
    "method_candidate_distinct_vectors",
    "exact_702_named_axis_matches",
    "max_unique_source_sample_label_overlap",
    "matched_39_retained_sample_keys",
    "matched_12_excluded_sample_keys",
}
OBJECT_TYPES = {"matrix", "data.frame", "array", "list", "other"}
READY = "SOURCE_OTU_702_KEY_MATCH_690_RETAINED_READY_NO_COUNTS"
HOLD = "SOURCE_OTU_SAMPLE_LINK_HOLD"
MARKERS = {
    "ORIGINAL_OTU_NUMERIC_CELLS_ACCESSED\t0",
    "ORIGINAL_TAXON_OR_SAMPLE_ID_EXPORTED\t0",
    "BIOLOGICAL_EFFECTS_FITTED\t0",
    "OTU_RESPONSE_OBJECT_DESERIALIZED_SCHEMA_ONLY\t1",
}

def parse_r_output(stdout):
    lines = stdout.strip().splitlines()
    if not lines or lines[0] != "KORTMANN_OTU_ID_SCHEMA_V1":
        raise SourceStop("SOURCE_OTU_R_OUTPUT_MAGIC_DRIFT")
    metrics = {}
    objs = []
    flags = set()
    status = None
    for row in lines[1:]:
        cells = row.split("\t")
        if len(cells) == 7 and cells[0] == "OBJECT":
            try:
                i, nr, nc, rn, cn = (int(cells[k]) for k in (1, 3, 4, 5, 6))
            except ValueError:
                raise SourceStop("SOURCE_OTU_OBJECT_DIMS_UNPARSABLE") from None
            if (i != len(objs) + 1 or cells[2] not in OBJECT_TYPES
                or not (0 <= nr <= 150000 and 0 <= nc <= 150000)
                or nr * nc > 50000000 or rn < 0 or cn < 0
                or rn > nr or cn > nc):
                raise SourceStop("SOURCE_OTU_OBJECT_SHAPE_OR_TYPE_DRIFT")
            objs.append({
                "anonymous_object_index": i,
                "container_type": cells[2],
                "n_rows_NOT_taxon_count_certification": nr,
                "n_columns_NOT_sample_count_certification": nc,
                "n_row_labels_NOT_EXPORTED": rn,
                "n_column_labels_NOT_EXPORTED": cn,
            })
        elif len(cells) == 3 and cells[0] == "METRIC":
            key = cells[1]
            if key not in METRICS or key in metrics or not cells[2].isdigit():
                raise SourceStop("SOURCE_OTU_UNKNOWN_METRIC_OR_NONINTEGER")
            metrics[key] = int(cells[2])
        elif len(cells) == 2 and cells[0] == "STATUS" and cells[1] in (READY, HOLD):
            if status is not None:
                raise SourceStop("SOURCE_OTU_DUPLICATE_STATUS")
            status = cells[1]
        elif row in MARKERS:
            flags.add(row)
        else:
            raise SourceStop("SOURCE_OTU_UNEXPECTED_RAW_SOURCE_OR_LOG_OUTPUT")
    if (not (1 <= len(objs) <= 12) or set(metrics) != METRICS
        or flags != MARKERS or status is None
        or len(lines) != 1 + len(objs) + len(METRICS) + 1 + len(MARKERS)):
        raise SourceStop("SOURCE_OTU_INCOMPLETE_ANONYMOUS_REPORT")
    if status == READY:
        if (metrics["exact_702_named_axis_matches"] != 1
            or metrics["matched_39_retained_sample_keys"] != 690
            or metrics["matched_12_excluded_sample_keys"] != 12
            or metrics["max_unique_source_sample_label_overlap"] != 702):
            raise SourceStop("SOURCE_OTU_REPORT_FAVOURABLE_CONTRADICTION")
    return {
        "status": status,
        "anonymous_original_OTU_RData_object_shapes": objs,
        "source_method_to_OTU_sample_ID_overlap_COUNTS_ONLY": metrics,
        "response_bearing_OTU_RData_DESERIALIZED": True,
        "no_original_otu_numeric_values_accessed_or_summary_computed": True,
        "no_original_OTU_names_or_sample_IDs_output": True,
        "no_species_beta_or_alpha_model_fitted": True,
        "the_original_40_triplet_strict_gate_still_failed": True,
        "the_independently_frozen_secondary_39_population_unchanged": True,
        "season_and_detection_coverage_NOT_VERIFIED": True,
    }

def run_r(args, synthetic=False):
    try:
        p = subprocess.run(
            ["Rscript", "--vanilla", str(SCRIPT)] + args,
            capture_output=True, text=True, timeout=90, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        raise SourceStop("SOURCE_OTU_RSCRIPT_NOT_AVAILABLE") from None
    if p.returncode != 0:
        # R stderr could contain sensitive original object names. Never export.
        raise SourceStop("SOURCE_OTU_R_SCHEMA_OR_METHOD_GUARD_STOP")
    if synthetic:
        if p.stdout.strip() != "SYNTHETIC_KORTMANN_OTU_SAMPLE_ID_ONLY_NO_COUNTS_PASS":
            raise SourceStop("SOURCE_OTU_SYNTHETIC_KNOWN_TRUTH_FAILED")
        return None
    return parse_r_output(p.stdout)

def synthetic():
    run_r(["--synthetic"], synthetic=True)
    try:
        parse_r_output(
            "KORTMANN_OTU_ID_SCHEMA_V1\nOBJECT\t1\tmatrix\t21\t702\t21\t702\n"
            "METRIC\tSECRET_OTU_ID\t52\n")
    except SourceStop:
        pass
    else:
        raise AssertionError("sensitive field was not blocked")
    print("SYNTHETIC_KORTMANN_702_690_OTU_NAMES_WITHOUT_COUNTS_PASS")

def run():
    link = original_file_metadata()         # exact fixed Zenodo version/MD5
    archive = official_get_one_zip(link)   # exact published full ZIP MD5
    if inspect_central_directory_only(archive)["status"] != "SOURCE_ZIP_CENTRAL_DIRECTORY_READY_METADATA_ONLY":
        raise SourceStop("SOURCE_OTU_ZIP_PUBLISHER_DIRECTORY_DRIFT")
    originals = {}
    with zipfile.ZipFile(io.BytesIO(archive), "r") as z:
        members = {i.filename: i for i in z.infolist() if not i.is_dir()}
        for name, declaration in SOURCES.items():
            if name not in members or members[name].file_size != declaration["size"]:
                raise SourceStop("SOURCE_OTU_DECLARED_MEMBER_SIZE_OR_ROLE_DRIFT")
            try:
                raw = z.read(name)
            except (zipfile.BadZipFile, KeyError, OSError):
                raise SourceStop("SOURCE_OTU_DECLARED_MEMBER_READ_STOP") from None
            if len(raw) != declaration["size"]:
                raise SourceStop("SOURCE_OTU_ACTUAL_MEMBER_UNCOMPRESSED_LENGTH_STOP")
            digest = hashlib.sha256(raw).hexdigest()
            if "sha" in declaration and digest != declaration["sha"]:
                raise SourceStop("SOURCE_OTU_PREVIOUS_METHOD_MEMBER_SHA_DRIFT")
            originals[name] = (raw, digest)
    with tempfile.TemporaryDirectory(prefix="kortmann_otu_ID_only_") as dirname:
        paths = []
        for name in SOURCES:
            p = Path(dirname) / Path(name).name
            p.write_bytes(originals[name][0])
            paths.append(str(p))
        actual = run_r(paths)
    return {
        "source_original_dataset_versioned_id": 17775805,
        "original_full_ZIP_MD5_publisher_authenticated": True,
        "original_two_member_SHA256_only": {
            Path(name).name: d[1] for name, d in originals.items()
        },
        "source_RData_schema_and_ID_match_only": actual,
        "original_phylogenetic_tree_RData_UNOPENED": True,
        "original_massive_XLSX_UNOPENED": True,
        "new_biodiversity_effect_estimated": False,
        "status": actual["status"],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    synthetic()
    if a.test:
        return
    if a.out is None:
        ap.error("--out required")
    report = {
        "schema": "structural.Kortmann2026_otu_original_response_deserialized_method_sample_ID_schema.v1",
        "prespec": PRESPEC,
        "original_strict_40_site_HOLD_UNCHANGED": True,
        "new_39_site_exploratory_source_scope_UNCHANGED": True,
        "first_semantic_OTU_RData_opening_authorized": True,
        "first_semantic_OTU_RData_opening_result": "NOT_REACHED",
        "previous_BETAFOR_PREDICTS_BALA_FINLAND_OTHER_EFFECTS_SEALED": True,
        "new_ecological_effects": 0,
        "eBird_used": False,
        "TinyFish_used": False,
    }
    try:
        result = run()
        report["source"] = result
        report["status"] = result["status"]
        report["first_semantic_OTU_RData_opening_result"] = "DESERIALIZED_SCHEMA_ONLY"
    except SourceStop as exc:
        report["status"] = "SOURCE_OTU_IDENTITY_GATE_STOP_" + str(exc)
        report["not_evidence_of_zero_ecological_effect"] = True
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")
    print("KORTMANN_OTU_FIRST_IDENTITY_GATE", report["status"])
    print("BIOLOGICAL_EFFECTS=0; NO_SPECIES_OR_SAMPLE_NAME_OUTPUT")

if __name__ == "__main__":
    main()
