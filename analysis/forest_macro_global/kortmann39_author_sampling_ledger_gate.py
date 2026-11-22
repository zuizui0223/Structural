#!/usr/bin/env python3
"""Offline response-free author-ledger SHAPE checks for Kortmann 2026.

Scientific limit: self-consistency is NOT independent source authentication.
Never open original OTU, RData, or ecological effects. Emit no source IDs.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter, defaultdict
from datetime import date, timedelta
import io
import json
from pathlib import Path
import re
import sys

PRESPEC = "docs/FOREST_MACRO_KORTMANN39_AUTHOR_LEDGER_ADMISSION_PREFREEZE_20261122.md"
COLUMNS = [
    "triplet_id", "plot_id", "treatment_code", "round_index",
    "collection_start", "collection_end", "trap_status", "otu_column_id",
    "method_record_id", "offset"
]
CODEBOOK_KEYS = {
    "dataset_versioned_doi", "mapping_basis", "treatment_code_to_role",
    "offset_units_and_transform", "sampling_time_definition",
}
SEMANTIC_ROLES = {"undisturbed", "disturbed_unmanaged", "cleared_salvage"}
DOI = "10.5281/zenodo.17775805"
BASIS = {"author_provided_record_key", "author_certified_composite_key"}
D0, D1 = date(2022, 4, 1), date(2022, 8, 31)
ISO_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_LEDGER_BYTES = 2 * 1024 * 1024
MAX_CODEBOOK_BYTES = 16384


class GateHold(Exception):
    pass


def load_bounded_text(path: Path, max_bytes: int) -> str:
    try:
        with path.open("rb") as f:
            raw = f.read(max_bytes + 1)
    except OSError:
        raise GateHold("FILE_UNAVAILABLE") from None
    if not raw or len(raw) > max_bytes:
        raise GateHold("INPUT_SIZE_OR_EMPTY")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeError:
        raise GateHold("INPUT_NOT_UTF8") from None


def codebook_from_text(text: str) -> dict:
    try:
        x = json.loads(text)
    except (ValueError, TypeError):
        raise GateHold("CODEBOOK_BAD_JSON") from None
    if not isinstance(x, dict) or set(x) != CODEBOOK_KEYS:
        raise GateHold("CODEBOOK_REQUIRED_FIELDS")
    if x["dataset_versioned_doi"] != DOI or x["mapping_basis"] not in BASIS:
        raise GateHold("CODEBOOK_PROVENANCE_OR_MAPPING_BASIS")
    treatment = x["treatment_code_to_role"]
    if (not isinstance(treatment, dict) or len(treatment) != 3
        or not all(isinstance(k, str) and k.strip() and len(k) <= 128
                   for k in treatment)
        or set(treatment.values()) != SEMANTIC_ROLES):
        raise GateHold("CODEBOOK_TREATMENT_ROLES")
    for key in ("offset_units_and_transform", "sampling_time_definition"):
        value = x[key]
        if not isinstance(value, str) or not (8 <= len(value.strip()) <= 500):
            raise GateHold("CODEBOOK_METHOD_DEFINITION_MISSING")
    return x


def ledger_rows_from_text(text: str) -> list[dict]:
    try:
        reader = csv.DictReader(io.StringIO(text), restkey="__UNEXPECTED__", strict=True)
        if reader.fieldnames != COLUMNS:
            raise GateHold("UNEXPECTED_OR_RESPONSE_COLUMN")
        rows = list(reader)
    except csv.Error:
        raise GateHold("BAD_CSV_STRUCTURE") from None
    if len(rows) not in (702, 720):
        raise GateHold("UNEXPECTED_ORIGINAL_OBSERVATION_DENOMINATOR")
    for r in rows:
        if set(r) != set(COLUMNS) or any(v is None for v in r.values()):
            raise GateHold("CSV_ROW_MISSING_OR_EXTRA_FIELDS")
    return rows


def parse_day(x: str) -> date:
    if not ISO_DAY.fullmatch(x):
        raise GateHold("COLLECTION_DATE_FORMAT")
    try:
        d = date.fromisoformat(x)
    except ValueError:
        raise GateHold("COLLECTION_DATE_INVALID") from None
    if not (D0 <= d <= D1):
        raise GateHold("COLLECTION_DATE_OUTSIDE_STUDY_WINDOW")
    return d


def not_position_only(ids: list[str]):
    if len(ids) == 702 and set(ids) == {str(i) for i in range(1, 703)}:
        raise GateHold("POSITIONAL_ROW_ORDER_USED_AS_SAMPLE_ID")


def evaluate(rows: list[dict], codebook: dict) -> dict:
    if len(rows) not in (702, 720):
        raise GateHold("LEDGER_COUNT_DRIFT")
    treatment_codes = set(codebook["treatment_code_to_role"])
    all_round_keys = set()
    patch_treatment: dict[tuple[str, str], str] = {}
    treatment_patch: dict[tuple[str, str], str] = {}
    sites, observed_sites = set(), defaultdict(set)
    observed_counts = Counter()
    planned_counts = Counter()
    id_otu, id_method = [], []
    observed_intervals = defaultdict(list)
    n_observed, n_missing = 0, 0
    for r in rows:
        site = r["triplet_id"]
        patch = r["plot_id"]
        treat = r["treatment_code"]
        if (not site.strip() or not patch.strip() or
            len(site) > 128 or len(patch) > 128 or
            treat not in treatment_codes):
            raise GateHold("SITE_PATCH_OR_TREATMENT_INVALID")
        rd = r["round_index"]
        if rd not in ("1", "2", "3", "4", "5", "6"):
            raise GateHold("ORIGINAL_SAMPLING_ROUND_INVALID")
        key = (site, patch, rd)
        if key in all_round_keys:
            raise GateHold("DUPLICATE_SITE_PATCH_ROUND")
        all_round_keys.add(key)
        pair = (site, patch)
        statepair = (site, treat)
        if pair in patch_treatment and patch_treatment[pair] != treat:
            raise GateHold("PATCH_TREATMENT_DRIFT")
        if statepair in treatment_patch and treatment_patch[statepair] != patch:
            raise GateHold("MORE_THAN_ONE_PATCH_PER_SITE_STATE")
        patch_treatment[pair] = treat
        treatment_patch[statepair] = patch
        planned_counts[pair] += 1
        sites.add(site)
        status = r["trap_status"]
        if status not in {"observed", "missing"}:
            raise GateHold("UNRECOGNIZED_ORIGINAL_TRAP_STATUS")
        if status == "missing":
            n_missing += 1
            if r["otu_column_id"] or r["method_record_id"] or r["offset"]:
                raise GateHold("MISSING_TRAP_MUST_NOT_IMPUTE_BIOLOGY")
            # Planned event dates may not be known when a trap never ran.
            if bool(r["collection_start"]) != bool(r["collection_end"]):
                raise GateHold("PARTIAL_PLANNED_DATE_PAIR")
            if r["collection_start"]:
                a, b = parse_day(r["collection_start"]), parse_day(r["collection_end"])
                if b < a:
                    raise GateHold("PLANNED_END_BEFORE_START")
            continue
        n_observed += 1
        if (not r["otu_column_id"] or not r["method_record_id"] or
            len(r["otu_column_id"]) > 160 or len(r["method_record_id"]) > 160):
            raise GateHold("AUTHOR_RECORD_ID_MISSING")
        id_otu.append(r["otu_column_id"])
        id_method.append(r["method_record_id"])
        if not r["collection_start"] or not r["collection_end"]:
            raise GateHold("OBSERVED_COLLECTION_DATES_MISSING")
        a, b = parse_day(r["collection_start"]), parse_day(r["collection_end"])
        if b <= a:
            raise GateHold("OBSERVED_NONPOSITIVE_COLLECTION_DURATION")
        try:
            off = float(r["offset"])
        except (TypeError, ValueError):
            raise GateHold("OFFSET_NOT_FINITE_NUMERIC") from None
        if not (-1e6 < off < 1e6):
            raise GateHold("OFFSET_NOT_FINITE_NUMERIC")
        observed_intervals[(site, rd)].append((treat, a, b))
        observed_sites[site].add(treat)
        observed_counts[pair] += 1
    if n_observed != 702:
        raise GateHold("AUTHOR_OBSERVED_702_NOT_REPRODUCED")
    if n_missing not in (0, 18) or (len(rows) == 720 and n_missing != 18):
        raise GateHold("AUTHOR_MISSING_OPPORTUNITY_DENOMINATOR")
    if (len(id_otu) != 702 or len(set(id_otu)) != 702 or
        len(set(id_method)) != 702 or
        any(not i.strip() for i in id_otu + id_method)):
        raise GateHold("NONUNIQUE_OR_BLANK_AUTHOR_SAMPLE_IDENTIFIERS")
    not_position_only(id_otu)
    not_position_only(id_method)
    if len(sites) != 40 or len(observed_counts) != 119:
        raise GateHold("ORIGINAL_SITE_OR_SAMPLED_PATCH_COUNT_MISMATCH")
    if Counter(observed_counts.values()) != Counter({6: 107, 5: 12}):
        raise GateHold("ORIGINAL_PATCH_SAMPLED_RECORD_COUNTS_MISMATCH")
    complete = {s for s in sites if observed_sites[s] == treatment_codes}
    incomplete = sites - complete
    if len(complete) != 39 or len(incomplete) != 1:
        raise GateHold("ORIGINAL_COMPLETE_39_AND_ONE_INCOMPLETE_GATE")
    incomplete_site = next(iter(incomplete))
    if len(observed_sites[incomplete_site]) != 2:
        raise GateHold("EXCLUDED_SITE_NOT_TWO_OBSERVED_STATES")
    excluded_n = sum(n for (s, _), n in observed_counts.items() if s == incomplete_site)
    if excluded_n != 12:
        raise GateHold("EXCLUDED_SITE_OBSERVED_12_MISMATCH")
    retained_counts = Counter()
    retained_patches = set()
    retained_observed = 0
    for (s, p), n in observed_counts.items():
        if s in complete:
            retained_patches.add((s, p))
            retained_counts[patch_treatment[(s, p)]] += n
            retained_observed += n
    if (len(retained_patches) != 117 or retained_observed != 690 or
        sorted(retained_counts.values()) != [230, 230, 230]):
        raise GateHold("ORIGINAL_39_SUBSET_690_OR_STATE_BALANCE_DRIFT")
    if len(rows) == 720:
        if len(planned_counts) != 120 or set(planned_counts.values()) != {6}:
            raise GateHold("ORIGINAL_720_PLAN_NOT_COMPLETE")
        for s in sites:
            if {t for (ss, t) in treatment_patch if ss == s} != treatment_codes:
                raise GateHold("FULL_PLAN_MISSING_TREATMENT")
        unsampled = {(s, p) for (s, p) in planned_counts if (s, p) not in observed_counts}
        if (len(unsampled) != 1 or next(iter(unsampled))[0] != incomplete_site):
            raise GateHold("ORIGINAL_ONE_ABSENT_PATCH_UNVERIFIED")
    else:
        if set(planned_counts.values()) != {5, 6}:
            raise GateHold("OBSERVED_ONLY_ROWS_UNEXPECTED")
    # A matched collection round is not necessarily comparable in exposure.
    completely_observed_rounds = 0
    overlap_rounds = 0
    for site in complete:
        for rd in ("1", "2", "3", "4", "5", "6"):
            intervals = observed_intervals.get((site, rd), [])
            if len(intervals) == 3 and {it[0] for it in intervals} == treatment_codes:
                completely_observed_rounds += 1
                if max(it[1] for it in intervals) <= min(it[2] for it in intervals):
                    overlap_rounds += 1
    return {
        "status": "AUTHOR_LEDGER_SHAPE_PASS_NOT_SOURCE_AUTHENTICATED",
        "strength": "COMPLETE_720_OPPORTUNITY_FRAME" if len(rows) == 720 else
                    "OBSERVED_ONLY_702_NO_MISSING_EXPOSURE_LEDGER",
        "anonymous_counts_only": {
            "author_ledger_rows": len(rows),
            "sampled_collections": n_observed,
            "declared_missing_opportunities": n_missing,
            "source_triplet_candidates": len(sites),
            "observed_patch_candidates": len(observed_counts),
            "retained_complete_triplets": len(complete),
            "retained_sampled_patches": len(retained_patches),
            "retained_observed_collections": retained_observed,
            "excluded_observed_collections": excluded_n,
            "original_observed_patches_with_six": 107,
            "original_observed_patches_with_five": 12,
            "retained_collections_per_state_sorted": sorted(retained_counts.values()),
            "fully_observed_triplet_rounds": completely_observed_rounds,
            "triplet_rounds_with_overlapping_collection_dates": overlap_rounds,
        },
        "no_raw_ID_or_dates_or_offset_values_exported": True,
        "original_publisher_OTU_column_IDs_NOT_INDEPENDENTLY_MATCHED": True,
        "original_diversity_RData_method_record_IDs_NOT_INDEPENDENTLY_MATCHED": True,
        "codebook_text_NOT_INDEPENDENTLY_SOURCE_VERIFIED": True,
        "no_biological_data_read_or_effect_scored": True,
        "cross_source_ORIGINAL_RECORD_ID_GATE_still_HOLD": True,
    }


def inspect(ledger_path: Path, codebook_path: Path) -> dict:
    cb = codebook_from_text(load_bounded_text(codebook_path, MAX_CODEBOOK_BYTES))
    rows = ledger_rows_from_text(load_bounded_text(ledger_path, MAX_LEDGER_BYTES))
    return evaluate(rows, cb)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--codebook", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = {
        "schema": "structural.kortmann39_author_responsefree_ledger_shape_only.v1",
        "prespec": PRESPEC,
        "no_original_RData_or_OTU_requested": True,
        "original_sample_link_HOLD_unchanged": True,
        "original_40_triplet_strict_gate_HOLD_unchanged": True,
        "biological_effects_fitted": 0,
    }
    try:
        result["ledger_admission"] = inspect(args.ledger, args.codebook)
        result["status"] = result["ledger_admission"]["status"]
    except GateHold as exc:
        result["status"] = "AUTHOR_LEDGER_SHAPE_HOLD_" + str(exc)
    # Do not report original author-provided values or paths to stdout/JSON.
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
    print("KORTMANN39_AUTHOR_LEDGER_SOURCE_FREE", result["status"])
    print("NO_ORIGINAL_OTU_OR_RDATA_VALUES_READ; NO_SOURCE_AUTHENTICATION")


if __name__ == "__main__":
    main()
