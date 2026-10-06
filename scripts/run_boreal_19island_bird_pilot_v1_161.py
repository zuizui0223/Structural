#!/usr/bin/env python3
"""One-shot v1.161 bird pilot executor after routing-header-only exposure."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from structural.boreal_19island_bird_pilot_router_v1_161 import (
    Boreal19BirdPilotRouterV161Error,
    route_bird_pilot_v161,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = ROOT / "development/boreal_19island_birds_pilot_contract_v1_161.json"
DEFAULT_UNIVERSE = ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"


class BirdPilotV161ExecutionError(RuntimeError):
    pass


def execute(response_bytes: bytes, *, contract: dict, universe: dict):
    if contract.get("schema") != "structural.boreal_19island_birds_pilot_contract.v1_161":
        raise BirdPilotV161ExecutionError("unexpected v1.161 contract")
    target = contract["response_file"]
    if len(response_bytes) != int(target["expected_size_bytes"]):
        raise BirdPilotV161ExecutionError("bird response byte-size mismatch")
    if hashlib.sha256(response_bytes).hexdigest() != target["expected_sha256"]:
        raise BirdPilotV161ExecutionError("bird response SHA mismatch")

    full = universe.get("current_study_island_universe", {}).get("codes")
    if not isinstance(full, list) or len(full) != 42 or len(set(full)) != 42:
        raise BirdPilotV161ExecutionError("invalid 42-island universe")

    gate = contract["eligibility_gate"]
    partition = contract["frozen_partition"]
    try:
        routed = route_bird_pilot_v161(
            response_csv_bytes=response_bytes,
            full_expected_islands=full,
            pilot_islands=partition["pilot_islands"],
            confirmatory_islands=partition["confirmatory_islands"],
            expected_species_count=int(target["expected_species_columns"]),
            min_support=int(gate["pilot_support_min"]),
            max_support=int(gate["pilot_support_max"]),
            minimum_eligible_species=int(gate["minimum_eligible_species"]),
        )
    except Boreal19BirdPilotRouterV161Error as exc:
        return ({
            "schema": "structural.boreal_19island_bird_pilot_execution.v1_161",
            "status": "TERMINAL_BIRD_PILOT_V161_STOP",
            "reason": str(exc),
            "authorization_consumed": True,
            "bird_pilot_response_opened": True,
            "confirmatory_target_values_parsed": 0,
            "excluded_target_values_parsed": 0,
            "confirmatory_response_authorized": False,
            "counts_as_empirical_evidence": False,
        }, None)

    snapshot = {
        "schema": "structural.boreal_19island_bird_pilot_snapshot.v1_161",
        "status": "BIRD_PILOT_SNAPSHOT_FROZEN_CONFIRMATORY_REMAINS_SEALED",
        "candidate_id": contract["candidate_id"],
        "evidence_class": "routing_header_exposed_biological_response_prospective",
        "response_file_sha256": target["expected_sha256"],
        "eligible_species": list(routed.eligible_species),
        "eligible_species_count": routed.eligible_species_count,
        "eligible_species_sha256": routed.eligible_species_sha256,
        "pilot_support_counts": [
            {"species": s, "pilot_presences": n}
            for s, n in routed.pilot_support_counts
        ],
        "pilot_island_order": list(routed.pilot_island_order),
        "pilot_targets_hex_by_island": [
            {"island": island, "targets_hex": targets}
            for island, targets in routed.pilot_targets_hex_by_island
        ],
        "raw_pilot_surface_sha256": routed.raw_pilot_surface_sha256,
        "pilot_target_values_parsed": routed.pilot_target_values_parsed,
        "confirmatory_target_values_parsed": 0,
        "excluded_target_values_parsed": 0,
        "confirmatory_occurrence_values_stored": False,
        "excluded_occurrence_values_stored": False,
        "confirmatory_response_authorized": False,
        "counts_as_empirical_evidence": False
    }
    core = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    snapshot["snapshot_fingerprint"] = hashlib.sha256(core.encode()).hexdigest()

    result = {
        "schema": "structural.boreal_19island_bird_pilot_execution.v1_161",
        "status": contract["success_ceiling"]["status"],
        "candidate_id": contract["candidate_id"],
        "authorization_consumed": True,
        "bird_pilot_response_opened": True,
        "eligible_species_count": routed.eligible_species_count,
        "eligible_species_sha256": routed.eligible_species_sha256,
        "pilot_target_values_parsed": routed.pilot_target_values_parsed,
        "confirmatory_target_values_parsed": 0,
        "excluded_target_values_parsed": 0,
        "snapshot_fingerprint": snapshot["snapshot_fingerprint"],
        "confirmatory_response_authorized": False,
        "counts_as_empirical_evidence": False,
        "next_action": contract["success_ceiling"]["next_action"]
    }
    return result, snapshot


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("response_csv", type=Path)
    ap.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    ap.add_argument("--universe", type=Path, default=DEFAULT_UNIVERSE)
    ap.add_argument("--result", type=Path)
    ap.add_argument("--snapshot", type=Path)
    args=ap.parse_args()
    try:
        raw=args.response_csv.read_bytes()
        result,snapshot=execute(
            raw,
            contract=json.loads(args.contract.read_text()),
            universe=json.loads(args.universe.read_text())
        )
        code=0 if result["status"]=="BIRD_PILOT_V161_QUALIFIED_TO_FREEZE_CONFIRMATORY_PREDICTIONS" else 2
    except (OSError,KeyError,ValueError,json.JSONDecodeError,BirdPilotV161ExecutionError) as exc:
        result={
            "schema":"structural.boreal_19island_bird_pilot_execution.v1_161",
            "status":"STOP_PRE_ACCESS",
            "reason":str(exc),
            "authorization_consumed":False,
            "bird_pilot_response_opened":False,
            "confirmatory_target_values_parsed":0,
            "excluded_target_values_parsed":0,
            "confirmatory_response_authorized":False,
            "counts_as_empirical_evidence":False
        }
        snapshot=None;code=2
    if snapshot is not None and args.snapshot:
        args.snapshot.parent.mkdir(parents=True,exist_ok=True)
        args.snapshot.write_text(json.dumps(snapshot,indent=2,sort_keys=True)+"\n")
    text=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.result:
        args.result.parent.mkdir(parents=True,exist_ok=True)
        args.result.write_text(text)
    print(text,end="")
    return code


if __name__=="__main__":
    raise SystemExit(main())
