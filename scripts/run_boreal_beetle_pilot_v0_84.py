#!/usr/bin/env python3
"""Consume one authorized boreal pilot and persist a model-sufficient snapshot."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Mapping

from scripts.run_boreal_beetle_pilot_v0_82 import (
    BorealPilotExecutionError,
    _load,
    _validate_pre_access,
    load_universe,
)
from scripts.run_transition_pilot_v0_32 import run as run_v032
from structural.boreal_beetle_pilot_router import (
    BorealBeetlePilotRouterError,
    build_boreal_beetle_pilot_surface,
)
from structural.future_admission_v0_42 import (
    FutureAdmissionStatus,
    evaluate_future_admission_v0_42,
    future_admission_receipt_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_beetle_model_sufficient_pilot_contract_v0_84.json"
)


class BorealModelPilotError(RuntimeError):
    pass


def canonical_sha256(value: Mapping) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def build_snapshot(
    *,
    routed,
    candidate_id: str,
    response_file_sha256: str,
    qualified_for_confirmatory: bool,
) -> dict:
    island_to_block = dict(routed.pilot_island_to_block)
    targets = dict(routed.pilot_targets_hex_by_island)

    if tuple(island_to_block) != routed.pilot_island_order:
        raise BorealModelPilotError(
            "pilot island/block snapshot order drift"
        )
    if tuple(targets) != routed.pilot_island_order:
        raise BorealModelPilotError(
            "pilot target snapshot order drift"
        )

    snapshot = {
        "schema": "structural.boreal_beetle_pilot_training_snapshot.v0_84",
        "status": "PILOT_TRAINING_SNAPSHOT_FROZEN_FROM_SINGLE_OPEN",
        "candidate_id": candidate_id,
        "response_file_sha256": response_file_sha256,
        "raw_pilot_surface_sha256": routed.raw_surface_sha256,
        "pilot_species_universe": list(routed.pilot_species_universe),
        "pilot_species_universe_count": routed.pilot_species_universe_count,
        "pilot_species_universe_sha256": routed.pilot_species_universe_sha256,
        "pilot_island_order": list(routed.pilot_island_order),
        "pilot_island_to_block": island_to_block,
        "target_bit_count": routed.pilot_species_universe_count,
        "targets_hex_by_island": targets,
        "pilot_island_count": routed.pilot_island_count,
        "pilot_block_count": routed.pilot_block_count,
        "confirmatory_target_values_parsed": 0,
        "confirmatory_occurrence_values_stored": False,
        "single_semantic_router_pass": True,
        "qualified_for_confirmatory_model_freeze": bool(
            qualified_for_confirmatory
        ),
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
    }
    snapshot["snapshot_fingerprint"] = canonical_sha256(snapshot)
    return snapshot


def execute(
    authorization: dict,
    protocol_mapping: dict,
    quality_mapping: dict,
    spatial_receipt: dict,
    response_bytes: bytes,
    *,
    contract: dict,
    spatial_receipt_sha256: str,
    expected_islands: tuple[str, ...],
) -> tuple[dict, str | None, dict | None]:
    protocol, quality, island_to_block = _validate_pre_access(
        authorization,
        protocol_mapping,
        quality_mapping,
        spatial_receipt,
        response_bytes,
        contract=contract,
        spatial_receipt_sha256=spatial_receipt_sha256,
    )

    try:
        routed = build_boreal_beetle_pilot_surface(
            response_csv_bytes=response_bytes,
            island_to_block=island_to_block,
            pilot_partition=protocol.pilot_partition,
            confirmatory_partition=protocol.confirmatory_partition,
            expected_islands=expected_islands,
            expected_species_count=contract["response_file"][
                "expected_species_columns"
            ],
        )
    except BorealBeetlePilotRouterError as exc:
        return ({
            "schema": "structural.boreal_beetle_burned_pilot_execution.v0_84",
            "status": "TERMINAL_PILOT_ROUTER_STOP",
            "reason": str(exc),
            "authorization_consumed": True,
            "pilot_response_opened": True,
            "confirmatory_target_values_parsed": 0,
            "model_snapshot_frozen": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
            "confirmatory_response_authorized": False,
            "eligible_action": None,
        }, None, None)

    if routed.confirmatory_target_values_parsed != 0:
        return ({
            "schema": "structural.boreal_beetle_burned_pilot_execution.v0_84",
            "status": "TERMINAL_FIREWALL_VIOLATION",
            "authorization_consumed": True,
            "pilot_response_opened": True,
            "confirmatory_target_values_parsed": (
                routed.confirmatory_target_values_parsed
            ),
            "model_snapshot_frozen": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
            "confirmatory_response_authorized": False,
            "eligible_action": None,
        }, None, None)

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        protocol_path = tmpdir / "protocol.json"
        pilot_path = tmpdir / "pilot.csv"
        protocol_path.write_text(
            json.dumps(protocol_mapping, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        pilot_path.write_text(routed.csv_text, encoding="utf-8")
        v032_code, pilot_result = run_v032(
            protocol_path,
            pilot_path,
        )

    admission = evaluate_future_admission_v0_42(
        protocol=protocol,
        pilot_result=pilot_result,
        quality_contract=quality,
        confirmatory_response_accessed=False,
    )
    admission_receipt = future_admission_receipt_mapping(admission)
    qualified = admission.status is FutureAdmissionStatus.ADMITTED

    snapshot = build_snapshot(
        routed=routed,
        candidate_id=contract["candidate_id"],
        response_file_sha256=contract["response_file"]["expected_sha256"],
        qualified_for_confirmatory=qualified,
    )

    result = {
        "schema": "structural.boreal_beetle_burned_pilot_execution.v0_84",
        "status": (
            contract["qualified_ceiling"]["status"]
            if qualified
            else "TERMINAL_PILOT_GATE_STOP"
        ),
        "authorization_consumed": True,
        "pilot_response_opened": True,
        "response_file_sha256": contract["response_file"]["expected_sha256"],
        "raw_pilot_surface_sha256": routed.raw_surface_sha256,
        "source_response_rows_seen": routed.source_response_rows_seen,
        "routing_island_fields_decoded": routed.routing_island_fields_decoded,
        "pilot_island_rows_semantically_parsed": (
            routed.pilot_island_rows_semantically_parsed
        ),
        "pilot_target_values_parsed": routed.pilot_target_values_parsed,
        "confirmatory_target_values_parsed": 0,
        "pilot_species_universe_count": routed.pilot_species_universe_count,
        "pilot_species_universe_sha256": (
            routed.pilot_species_universe_sha256
        ),
        "model_snapshot_frozen": True,
        "model_snapshot_fingerprint": snapshot["snapshot_fingerprint"],
        "pilot_result": pilot_result,
        "v0_32_exit_code": v032_code,
        "future_admission_receipt": admission_receipt,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "confirmatory_response_authorized": False,
        "eligible_action": (
            "freeze_confirmatory_protocol_and_predictions_only"
            if qualified
            else None
        ),
    }
    return result, routed.csv_text, snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("authorization", type=Path)
    parser.add_argument("protocol", type=Path)
    parser.add_argument("quality", type=Path)
    parser.add_argument("spatial_receipt", type=Path)
    parser.add_argument("response_csv", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--execution-receipt", type=Path)
    parser.add_argument("--pilot-surface", type=Path)
    parser.add_argument("--training-snapshot", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_beetle_model_sufficient_pilot_contract.v0_84"
        ):
            raise BorealModelPilotError(
                "unexpected v0.84 contract schema"
            )
        response_bytes = args.response_csv.read_bytes()
        result, pilot_surface, snapshot = execute(
            _load(args.authorization),
            _load(args.protocol),
            _load(args.quality),
            _load(args.spatial_receipt),
            response_bytes,
            contract=contract,
            spatial_receipt_sha256=hashlib.sha256(
                args.spatial_receipt.read_bytes()
            ).hexdigest(),
            expected_islands=load_universe(),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealPilotExecutionError,
        BorealModelPilotError,
    ) as exc:
        result = {
            "schema": "structural.boreal_beetle_burned_pilot_execution.v0_84",
            "status": "STOP_PRE_ACCESS",
            "reason": str(exc),
            "authorization_consumed": False,
            "pilot_response_opened": False,
            "confirmatory_target_values_parsed": 0,
            "model_snapshot_frozen": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
            "confirmatory_response_authorized": False,
            "eligible_action": None,
        }
        pilot_surface = None
        snapshot = None
        code = 2
    else:
        code = 0 if result["status"] == (
            "QUALIFIED_TO_FREEZE_CONFIRMATORY_PROTOCOL_WITH_MODEL_SNAPSHOT"
        ) else 2

    if pilot_surface is not None and args.pilot_surface is not None:
        args.pilot_surface.parent.mkdir(parents=True, exist_ok=True)
        args.pilot_surface.write_text(pilot_surface, encoding="utf-8")

    if snapshot is not None and args.training_snapshot is not None:
        args.training_snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.training_snapshot.write_text(
            json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.execution_receipt is not None:
        args.execution_receipt.parent.mkdir(parents=True, exist_ok=True)
        args.execution_receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
