#!/usr/bin/env python3
"""Conservative response-independent overlap audit for historical 318 vs fresh 5,592 islands."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "development/global_mammals_historical_overlap_gate_contract_v0_90.json"
INTEGERISH = re.compile(r"^[0-9]+(?:\.0+)?$")


class OverlapAuditError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_contract(path: Path) -> dict:
    x = json.loads(path.read_text(encoding="utf-8"))
    if x.get("schema") != "structural.global_mammals_historical_overlap_gate_contract.v0_90":
        raise OverlapAuditError("unexpected overlap contract schema")
    return x


def normalize_id(value: str) -> str:
    value = value.strip()
    if not value:
        raise OverlapAuditError("blank island ID")
    if INTEGERISH.fullmatch(value):
        return str(int(value.split(".", 1)[0]))
    return value


def normalize_name(value: str) -> str:
    value = str(value or "").strip()
    if not value:
        return ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = value.casefold().replace("&", " and ")
    value = re.sub(r"[^0-9a-z]+", " ", value)
    return " ".join(value.split())


def read_routing_ids(path: Path, expected: int) -> list[str]:
    ids = [normalize_id(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    if len(ids) != expected:
        raise OverlapAuditError(f"expected {expected} routing IDs, observed {len(ids)}")
    if len(set(ids)) != len(ids):
        raise OverlapAuditError("routing IDs are not unique")
    return ids


def target_name_surfaces(row: dict[str, str]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for field in ("island", "gazetteer", "name_alt"):
        raw = (row.get(field) or "").strip()
        if not raw:
            continue
        pieces = [raw]
        if field == "name_alt":
            pieces.extend(x.strip() for x in re.split(r"[;|]", raw) if x.strip())
        norms = {normalize_name(x) for x in pieces}
        norms.discard("")
        if norms:
            out[field] = norms
    return out


def read_weigelt_target_rows(path: Path, routing_ids: list[str], contract: dict) -> dict[str, dict[str, str]]:
    spec = contract["fresh_identity_inputs"]["weigelt_safe_rows"]
    if sha256_file(path) != spec["sha256"]:
        raise OverlapAuditError("Weigelt safe-row SHA-256 mismatch")
    routing = set(routing_ids)
    all_rows: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        required = set(spec["allowed_identity_fields"])
        if not required <= set(reader.fieldnames or []):
            raise OverlapAuditError("Weigelt safe identity columns missing")
        for row in reader:
            iid = normalize_id(row["id"])
            if iid in all_rows:
                raise OverlapAuditError(f"duplicate Weigelt ID {iid}")
            all_rows[iid] = row
    if len(all_rows) != int(spec["rows"]):
        raise OverlapAuditError(
            f"expected {spec['rows']} Weigelt rows, observed {len(all_rows)}"
        )
    missing = routing - set(all_rows)
    if missing:
        raise OverlapAuditError(f"{len(missing)} routing IDs missing from Weigelt safe rows")
    return {iid: all_rows[iid] for iid in routing_ids}


def read_historical(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        expected = ["historical_id", "historical_island", "historical_group"]
        if reader.fieldnames != expected:
            raise OverlapAuditError("historical identity schema drift")
        rows = list(reader)
    if len(rows) != 318:
        raise OverlapAuditError(f"expected 318 historical identity rows, observed {len(rows)}")
    ids = [r["historical_id"].strip() for r in rows]
    if len(set(ids)) != len(ids) or any(not x for x in ids):
        raise OverlapAuditError("historical IDs must be unique and nonblank")
    return rows


def load_adjudication(path: Path | None, unmatched: set[str], target_ids: set[str]) -> tuple[dict[str, dict[str, str]], set[str]]:
    if path is None:
        return {}, set()
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        required = ["historical_id", "decision", "additional_target_ids", "evidence"]
        if reader.fieldnames != required:
            raise OverlapAuditError("adjudication schema drift")
        rows = list(reader)

    by_id: dict[str, dict[str, str]] = {}
    extra_exclusions: set[str] = set()
    for row in rows:
        hid = row["historical_id"].strip()
        if hid not in unmatched:
            raise OverlapAuditError(f"adjudication contains non-unmatched historical ID {hid}")
        if hid in by_id:
            raise OverlapAuditError(f"duplicate adjudication for {hid}")
        decision = row["decision"].strip()
        evidence = row["evidence"].strip()
        if decision not in {"NOT_IN_RETAINED_TARGET", "EXCLUDE_TARGET_IDS"}:
            raise OverlapAuditError(f"invalid adjudication decision for {hid}")
        if not evidence:
            raise OverlapAuditError(f"missing response-independent evidence for {hid}")
        ids = {
            normalize_id(x)
            for x in re.split(r"[;,\s]+", row["additional_target_ids"].strip())
            if x.strip()
        }
        if decision == "EXCLUDE_TARGET_IDS":
            if not ids:
                raise OverlapAuditError(f"EXCLUDE_TARGET_IDS requires IDs for {hid}")
            unknown = ids - target_ids
            if unknown:
                raise OverlapAuditError(f"adjudication for {hid} names unknown target IDs")
            extra_exclusions |= ids
        elif ids:
            raise OverlapAuditError(f"NOT_IN_RETAINED_TARGET must not list target IDs for {hid}")
        by_id[hid] = row

    if set(by_id) != unmatched:
        missing = sorted(unmatched - set(by_id))
        raise OverlapAuditError(f"incomplete adjudication: {len(missing)} historical IDs unresolved")
    return by_id, extra_exclusions


def audit(
    routing_path: Path,
    weigelt_path: Path,
    historical_path: Path,
    matches_path: Path,
    exclusions_path: Path,
    template_path: Path,
    receipt_path: Path,
    contract: dict,
    adjudication_path: Path | None = None,
    eligible_path: Path | None = None,
) -> dict:
    expected = int(contract["fresh_identity_inputs"]["routing_ids"]["expected_rows"])
    routing_ids = read_routing_ids(routing_path, expected)
    target_rows = read_weigelt_target_rows(weigelt_path, routing_ids, contract)
    historical = read_historical(historical_path)

    name_index: dict[str, list[tuple[str, str]]] = defaultdict(list)
    unnamed: set[str] = set()
    for iid, row in target_rows.items():
        surfaces = target_name_surfaces(row)
        if not surfaces:
            unnamed.add(iid)
        for field, norms in surfaces.items():
            for norm in norms:
                name_index[norm].append((iid, field))

    numeric_collisions = {
        normalize_id(h["historical_id"])
        for h in historical
        if normalize_id(h["historical_id"]) in target_rows
    }

    auto_name_exclusions: set[str] = set()
    matched_historical: set[str] = set()
    match_rows: list[list[str]] = []
    for h in historical:
        hid = h["historical_id"].strip()
        norm = normalize_name(h["historical_island"])
        found = sorted(set(name_index.get(norm, [])))
        if found:
            matched_historical.add(hid)
            for iid, field in found:
                auto_name_exclusions.add(iid)
                t = target_rows[iid]
                match_rows.append([
                    hid,
                    h["historical_island"],
                    h["historical_group"],
                    norm,
                    iid,
                    t.get("island", ""),
                    t.get("archip", ""),
                    t.get("country", ""),
                    field,
                ])

    auto_exclusions = auto_name_exclusions | unnamed
    unmatched = {h["historical_id"].strip() for h in historical} - matched_historical
    adjudication, extra_exclusions = load_adjudication(
        adjudication_path, unmatched, set(target_rows)
    )
    all_exclusions = auto_exclusions | extra_exclusions

    matches_path.parent.mkdir(parents=True, exist_ok=True)
    with matches_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow([
            "historical_id", "historical_island", "historical_group",
            "normalized_historical_name", "target_id", "target_island",
            "target_archip", "target_country", "matched_identity_field"
        ])
        w.writerows(match_rows)

    exclusions_path.write_text(
        "\n".join(sorted(all_exclusions, key=lambda x: (not x.isdigit(), int(x) if x.isdigit() else x))) + ("\n" if all_exclusions else ""),
        encoding="utf-8",
    )

    with template_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["historical_id", "decision", "additional_target_ids", "evidence"])
        for h in historical:
            hid = h["historical_id"].strip()
            if hid in unmatched:
                w.writerow([hid, "", "", f"{h['historical_island']} | {h['historical_group']}"])

    passed = len(unmatched) == 0 or bool(adjudication)
    eligible_count = None
    if passed:
        if eligible_path is None:
            raise OverlapAuditError("eligible output path required when overlap gate passes")
        eligible = [iid for iid in routing_ids if iid not in all_exclusions]
        if not eligible:
            raise OverlapAuditError("overlap gate exclusions removed every fresh target island")
        eligible_path.write_text("\n".join(eligible) + "\n", encoding="utf-8")
        eligible_count = len(eligible)

    result = {
        "schema": "structural.global_mammals_historical_overlap_gate_result.v0_90",
        "status": (
            "PASS_response_independent_historical_overlap_excluded"
            if passed
            else "HOLD_manual_geographic_adjudication_required"
        ),
        "fresh_routing_ids": len(routing_ids),
        "fresh_target_rows_joined_to_weigelt": len(target_rows),
        "historical_islands": len(historical),
        "numeric_id_collision_count_diagnostic_only": len(numeric_collisions),
        "numeric_id_collision_may_establish_independence": False,
        "historical_exact_name_match_count": len(matched_historical),
        "historical_unmatched_count": len(unmatched),
        "automatic_exact_name_excluded_target_ids": len(auto_name_exclusions),
        "automatic_missing_name_excluded_target_ids": len(unnamed),
        "manual_additional_excluded_target_ids": len(extra_exclusions),
        "total_excluded_target_ids": len(all_exclusions),
        "eligible_target_ids_emitted": eligible_count,
        "mammal_species_header_fields_opened": 0,
        "mammal_occurrence_cells_opened": 0,
        "historical_species_header_fields_opened_by_identity_extractor": 0,
        "historical_occurrence_cells_opened_by_identity_extractor": 0,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "next_action": (
            "freeze spatial blocks and the final pre-response mammal design using only eligible_target_ids"
            if passed
            else "complete the emitted adjudication template using response-independent island geography, commit it, and rerun this exact gate"
        ),
    }
    receipt_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--routing-ids", type=Path, required=True)
    p.add_argument("--weigelt-safe", type=Path, required=True)
    p.add_argument("--historical-identity", type=Path, required=True)
    p.add_argument("--matches", type=Path, required=True)
    p.add_argument("--exclusions", type=Path, required=True)
    p.add_argument("--adjudication-template", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--eligible-output", type=Path)
    p.add_argument("--adjudication", type=Path)
    p.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    args = p.parse_args()

    try:
        result = audit(
            args.routing_ids,
            args.weigelt_safe,
            args.historical_identity,
            args.matches,
            args.exclusions,
            args.adjudication_template,
            args.receipt,
            load_contract(args.contract),
            adjudication_path=args.adjudication,
            eligible_path=args.eligible_output,
        )
        code = 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError, OverlapAuditError) as exc:
        result = {
            "schema": "structural.global_mammals_historical_overlap_gate_result.v0_90",
            "status": "STOP",
            "reason": str(exc),
            "mammal_species_header_fields_opened": 0,
            "mammal_occurrence_cells_opened": 0,
            "counts_as_empirical_evidence": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
        }
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        code = 2

    print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
