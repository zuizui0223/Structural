#!/usr/bin/env python3
"""One-shot semantic pilot executor for the sealed boreal bird route v1.160."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from structural.boreal_19island_bird_pilot_router import (
    Boreal19BirdPilotRouterError,
    route_bird_pilot,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_birds_pilot_contract_v1_159.json"
)
DEFAULT_UNIVERSE = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)


class BirdPilotExecutionError(RuntimeError):
    pass


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def execute(response_bytes: bytes, *, contract: dict, universe: dict) -> tuple[dict, dict | None]:
    if contract.get("schema") != "structural.boreal_19island_birds_pilot_contract.v1_159":
        raise BirdPilotExecutionError("unexpected pilot contract schema")
    target = contract["response_file"]
    if len(response_bytes) != int(target["expected_size_bytes"]):
        raise BirdPilotExecutionError("bird response byte-size mismatch before semantic access")
    if sha256_bytes(response_bytes) != target["expected_sha256"]:
        raise BirdPilotExecutionError("bird response SHA mismatch before semantic access")

    codes = universe.get("current_study_island_universe", {}).get("codes")
    if not isinstance(codes, list) or len(codes) != 42 or len(set(codes)) != 42:
        raise BirdPilotExecutionError("invalid frozen 42-island universe")

    partition = contract["frozen_partition"]
    gate = contract["eligibility_gate"]

    # Irreversible semantic boundary begins here.
    try:
        routed = route_bird_pilot(
            response_csv_bytes=response_bytes,
            full_expected_islands=codes,
            pilot_islands=partition["pilot_islands"],
            confirmatory_islands=partition["confirmatory_islands"],
            expected_species_count=int(target["expected_species_columns"]),
            min_support=int(gate["pilot_support_min"]),
            max_support=int(gate["pilot_support_max"]),
            minimum_eligible_species=int(gate["minimum_eligible_species"]),
        )
    except Boreal19BirdPilotRouterError as exc:
        return ({
            "schema": "structural.boreal_19island_bird_pilot_execution.v1_160",
            "status": "TERMINAL_BIRD_PILOT_STOP",
            "reason": str(exc),
            "authorization_consumed": True,
            "bird_pilot_response_opened": True,
            "confirmatory_target_values_parsed": 0,
            "excluded_target_values_parsed": 0,
            "confirmatory_response_authorized": False,
            "counts_as_empirical_evidence": False,
        }, None)

    snapshot = {
        "schema": "structural.boreal_19island_bird_pilot_snapshot.v1_160",
        "status": contract["success_ceiling"]["status"],
        "candidate_id": contract["candidate_id"],
        "response_file_sha256": target["expected_sha256"],
        "eligible_species": list(routed.eligible_species),
        "eligible_species_count": routed.eligible_species_count,
        "eligible_species_sha256": routed.eligible_species_sha256,
        "pilot_support_counts": [
            {"species": species, "pilot_presences": count}
            for species, count in routed.pilot_support_counts
        ],
        "pilot_island_order": list(routed.pilot_island_order),
        "pilot_targets_hex_by_island": [
            {"island": island, "targets_hex": targets}
            for island, targets in routed.pilot_targets_hex_by_island
        ],
        "raw_pilot_surface_sha256": routed.raw_pilot_surface_sha256,
        "source_response_rows_seen": routed.source_response_rows_seen,
        "routing_island_fields_decoded": routed.routing_island_fields_decoded,
        "pilot_island_rows_semantically_parsed": (
            routed.pilot_island_rows_semantically_parsed
        ),
        "pilot_target_values_parsed": routed.pilot_target_values_parsed,
        "confirmatory_target_values_parsed": 0,
        "excluded_target_values_parsed": 0,
        "confirmatory_occurrence_values_stored": False,
        "excluded_occurrence_values_stored": False,
        "counts_as_empirical_evidence": False,
        "confirmatory_response_authorized": False,
    }
    snapshot_raw = json.dumps(
        snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    snapshot["snapshot_fingerprint"] = hashlib.sha256(snapshot_raw).hexdigest()

    result = {
        "schema": "structural.boreal_19island_bird_pilot_execution.v1_160",
        "status": "BIRD_PILOT_QUALIFIED_TO_FREEZE_CONFIRMATORY_PREDICTIONS",
        "candidate_id": contract["candidate_id"],
        "authorization_consumed": True,
        "bird_pilot_response_opened": True,
        "response_file_sha256": target["expected_sha256"],
        "pilot_target_values_parsed": routed.pilot_target_values_parsed,
        "eligible_species_count": routed.eligible_species_count,
        "eligible_species_sha256": routed.eligible_species_sha256,
        "snapshot_fingerprint": snapshot["snapshot_fingerprint"],
        "confirmatory_target_values_parsed": 0,
        "excluded_target_values_parsed": 0,
        "confirmatory_response_authorized": False,
        "counts_as_empirical_evidence": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return result, snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("response_csv", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--universe", type=Path, default=DEFAULT_UNIVERSE)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()

    try:
        response = args.response_csv.read_bytes()
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        universe = json.loads(args.universe.read_text(encoding="utf-8"))
        result, snapshot = execute(response, contract=contract, universe=universe)
        code = 0 if result["status"] == (
            "BIRD_PILOT_QUALIFIED_TO_FREEZE_CONFIRMATORY_PREDICTIONS"
        ) else 2
    except (OSError, KeyError, ValueError, json.JSONDecodeError, BirdPilotExecutionError) as exc:
        result = {
            "schema": "structural.boreal_19island_bird_pilot_execution.v1_160",
            "status": "STOP_PRE_ACCESS",
            "reason": str(exc),
            "authorization_consumed": False,
            "bird_pilot_response_opened": False,
            "confirmatory_target_values_parsed": 0,
            "excluded_target_values_parsed": 0,
            "confirmatory_response_authorized": False,
            "counts_as_empirical_evidence": False,
        }
        snapshot = None
        code = 2

    if snapshot is not None and args.snapshot is not None:
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.result is not None:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
