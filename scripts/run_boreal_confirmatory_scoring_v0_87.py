#!/usr/bin/env python3
"""Consume one authorized boreal confirmatory response and score frozen predictions."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

from structural.boreal_confirmatory_router import (
    BorealConfirmatoryRouterError,
    build_boreal_confirmatory_surface,
)
from structural.boreal_confirmatory_scoring import (
    BorealConfirmatoryScoringError,
    score_primary,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_confirmatory_scoring_contract_v0_87.json"
)
DEFAULT_UNIVERSE = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)


class BorealConfirmatoryExecutionError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BorealConfirmatoryExecutionError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_universe(path: Path = DEFAULT_UNIVERSE) -> tuple[str, ...]:
    x = _load(path)
    codes = tuple(x["current_study_island_universe"]["codes"])
    if len(codes) != 42 or len(set(codes)) != 42:
        raise BorealConfirmatoryExecutionError(
            "unexpected frozen 42-island universe"
        )
    return codes


def _validate_pre_access(
    *,
    authorization: Mapping,
    model_receipt: Mapping,
    predictions_text: str,
    pilot_snapshot: Mapping,
    spatial_receipt: Mapping,
    response_bytes: bytes,
    contract: Mapping,
    model_receipt_sha256: str,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    dict[str, str],
]:
    required = contract["required_authorization"]
    if authorization.get("schema") != required["schema"]:
        raise BorealConfirmatoryExecutionError(
            "unexpected v0.86 authorization schema"
        )
    if authorization.get("status") != required["status"]:
        raise BorealConfirmatoryExecutionError(
            "v0.86 authorization did not qualify"
        )
    if authorization.get("candidate_id") != contract["candidate_id"]:
        raise BorealConfirmatoryExecutionError(
            "authorization candidate identity mismatch"
        )
    for key, expected in (
        ("confirmatory_response_authorized", True),
        ("authorization_consumed", False),
        ("effect_size", None),
        ("prediction_score", None),
        ("counts_as_empirical_evidence", False),
    ):
        if authorization.get(key) != expected:
            raise BorealConfirmatoryExecutionError(
                f"authorization ceiling mismatch: {key}"
            )
    if authorization.get("eligible_action") != (
        "execute_one_shot_confirmatory_scoring"
    ):
        raise BorealConfirmatoryExecutionError(
            "authorization eligible action drift"
        )

    model_req = contract["required_model_freeze"]
    if model_receipt.get("schema") != model_req["schema"]:
        raise BorealConfirmatoryExecutionError(
            "unexpected v0.85 model receipt schema"
        )
    if model_receipt.get("status") != model_req["status"]:
        raise BorealConfirmatoryExecutionError(
            "v0.85 model receipt did not qualify"
        )
    if model_receipt.get("candidate_id") != contract["candidate_id"]:
        raise BorealConfirmatoryExecutionError(
            "model receipt candidate identity mismatch"
        )
    if model_receipt.get("confirmatory_target_values_opened") != 0:
        raise BorealConfirmatoryExecutionError(
            "v0.85 confirmatory target boundary violated"
        )
    if model_receipt.get("confirmatory_response_authorized") is not False:
        raise BorealConfirmatoryExecutionError(
            "v0.85 response ceiling violated"
        )

    if authorization.get("source_model_receipt_sha256") != model_receipt_sha256:
        raise BorealConfirmatoryExecutionError(
            "model receipt SHA mismatch with v0.86 authorization"
        )

    parent_primary = model_receipt.get("primary_scoring")
    if not isinstance(parent_primary, dict):
        raise BorealConfirmatoryExecutionError(
            "v0.85 primary scoring contract missing"
        )
    for key in (
        "favourable_direction",
        "bootstrap_replicates",
        "bootstrap_seed",
        "external_isolation_interaction_required",
        "secondary_moderator_may_rescue_failed_primary",
    ):
        if parent_primary.get(key) != contract["primary"].get(key):
            raise BorealConfirmatoryExecutionError(
                f"v0.85/v0.87 primary scoring drift: {key}"
            )

    prediction_sha = sha256_text(predictions_text)
    if prediction_sha != model_receipt.get("prediction_surface_sha256"):
        raise BorealConfirmatoryExecutionError(
            "prediction surface SHA mismatch with v0.85"
        )
    if prediction_sha != authorization.get("prediction_surface_sha256"):
        raise BorealConfirmatoryExecutionError(
            "prediction surface SHA mismatch with v0.86"
        )
    if model_receipt.get("prediction_row_count") != authorization.get(
        "prediction_row_count"
    ):
        raise BorealConfirmatoryExecutionError(
            "prediction row-count binding mismatch"
        )
    if model_receipt.get("species_count") != authorization.get("species_count"):
        raise BorealConfirmatoryExecutionError(
            "species-count binding mismatch"
        )

    if pilot_snapshot.get("schema") != (
        "structural.boreal_beetle_pilot_training_snapshot.v0_84"
    ):
        raise BorealConfirmatoryExecutionError(
            "unexpected v0.84 pilot snapshot"
        )
    if pilot_snapshot.get("status") != (
        "PILOT_TRAINING_SNAPSHOT_FROZEN_FROM_SINGLE_OPEN"
    ):
        raise BorealConfirmatoryExecutionError(
            "v0.84 pilot snapshot did not qualify"
        )
    species = tuple(pilot_snapshot.get("pilot_species_universe") or ())
    if not species or len(species) != model_receipt.get("species_count"):
        raise BorealConfirmatoryExecutionError(
            "fixed species universe mismatch"
        )

    if spatial_receipt.get("schema") != (
        "structural.boreal_lake_islands_spatial_partition_result.v0_75"
    ):
        raise BorealConfirmatoryExecutionError(
            "unexpected v0.75 spatial receipt"
        )
    if spatial_receipt.get("status") != (
        "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY"
    ):
        raise BorealConfirmatoryExecutionError(
            "v0.75 spatial partition did not qualify"
        )
    if spatial_receipt.get("candidate_id") != contract["candidate_id"]:
        raise BorealConfirmatoryExecutionError(
            "v0.75 candidate identity mismatch"
        )
    mapping = spatial_receipt.get("island_to_block")
    if not isinstance(mapping, dict) or not mapping:
        raise BorealConfirmatoryExecutionError(
            "invalid frozen island-to-block map"
        )
    pilot_blocks = tuple(spatial_receipt.get("pilot_block_ids") or ())
    confirmatory_blocks = tuple(
        spatial_receipt.get("confirmatory_block_ids") or ()
    )
    if not pilot_blocks or not confirmatory_blocks:
        raise BorealConfirmatoryExecutionError(
            "frozen block partitions missing"
        )
    if len(confirmatory_blocks) != model_receipt.get(
        "confirmatory_block_count"
    ):
        raise BorealConfirmatoryExecutionError(
            "confirmatory block-count binding mismatch"
        )
    if len(confirmatory_blocks) < 6:
        raise BorealConfirmatoryExecutionError(
            "confirmatory spatial support fell below frozen minimum"
        )

    target = contract["response_file"]
    if len(response_bytes) != target["expected_size_bytes"]:
        raise BorealConfirmatoryExecutionError(
            "response byte size mismatch"
        )
    if sha256_bytes(response_bytes) != target["expected_sha256"]:
        raise BorealConfirmatoryExecutionError(
            "response SHA mismatch"
        )
    if authorization.get("response_file") != {
        "name": target["name"],
        "dryad_file_id": target["dryad_file_id"],
        "size_bytes": target["expected_size_bytes"],
        "sha256": target["expected_sha256"],
    }:
        raise BorealConfirmatoryExecutionError(
            "authorized response identity drift"
        )

    allowed = authorization.get("allowed_semantic_access")
    if not isinstance(allowed, dict):
        raise BorealConfirmatoryExecutionError(
            "authorization semantic-access map missing"
        )
    for key, expected in (
        ("confirmatory_fixed_species_occurrence_cells", True),
        ("confirmatory_nonfocal_species_occurrence_cells", False),
        ("pilot_island_occurrence_cells", False),
    ):
        if allowed.get(key) is not expected:
            raise BorealConfirmatoryExecutionError(
                f"authorization semantic-access drift: {key}"
            )

    return species, pilot_blocks, confirmatory_blocks, mapping


def execute(
    *,
    authorization: Mapping,
    model_receipt: Mapping,
    predictions_text: str,
    pilot_snapshot: Mapping,
    spatial_receipt: Mapping,
    response_bytes: bytes,
    contract: Mapping,
    expected_islands: tuple[str, ...],
    model_receipt_sha256: str,
) -> dict:
    species, pilot_blocks, confirmatory_blocks, mapping = _validate_pre_access(
        authorization=authorization,
        model_receipt=model_receipt,
        predictions_text=predictions_text,
        pilot_snapshot=pilot_snapshot,
        spatial_receipt=spatial_receipt,
        response_bytes=response_bytes,
        contract=contract,
        model_receipt_sha256=model_receipt_sha256,
    )

    # From this call onward, confirmatory authorization is irreversibly consumed.
    try:
        routed = build_boreal_confirmatory_surface(
            response_csv_bytes=response_bytes,
            island_to_block=mapping,
            pilot_partition=pilot_blocks,
            confirmatory_partition=confirmatory_blocks,
            expected_islands=expected_islands,
            fixed_species=species,
            expected_species_count=466,
        )
    except BorealConfirmatoryRouterError as exc:
        return {
            "schema": "structural.boreal_confirmatory_scoring_result.v0_87",
            "status": "TERMINAL_CONFIRMATORY_ROUTER_STOP",
            "reason": str(exc),
            "authorization_consumed": True,
            "confirmatory_response_opened": True,
            "pilot_target_values_parsed": 0,
            "nonfocal_confirmatory_target_values_parsed": 0,
            "counts_as_fresh_confirmatory_evidence": False,
            "fresh_system_denominator_contribution": 0,
            "primary_supported": None,
            "mechanism_claim_authorized": False,
            "rerun_authorized": False,
        }

    if (
        routed.pilot_target_values_parsed != 0
        or routed.nonfocal_confirmatory_target_values_parsed != 0
    ):
        return {
            "schema": "structural.boreal_confirmatory_scoring_result.v0_87",
            "status": "TERMINAL_CONFIRMATORY_FIREWALL_VIOLATION",
            "authorization_consumed": True,
            "confirmatory_response_opened": True,
            "pilot_target_values_parsed": routed.pilot_target_values_parsed,
            "nonfocal_confirmatory_target_values_parsed": (
                routed.nonfocal_confirmatory_target_values_parsed
            ),
            "counts_as_fresh_confirmatory_evidence": False,
            "fresh_system_denominator_contribution": 0,
            "primary_supported": None,
            "mechanism_claim_authorized": False,
            "rerun_authorized": False,
        }

    try:
        primary = score_primary(
            predictions_text,
            routed.csv_text,
            expected_blocks=confirmatory_blocks,
            bootstrap_replicates=contract["primary"]["bootstrap_replicates"],
            bootstrap_seed=contract["primary"]["bootstrap_seed"],
        )
    except BorealConfirmatoryScoringError as exc:
        return {
            "schema": "structural.boreal_confirmatory_scoring_result.v0_87",
            "status": "TERMINAL_CONFIRMATORY_SCORING_STOP",
            "reason": str(exc),
            "authorization_consumed": True,
            "confirmatory_response_opened": True,
            "confirmatory_target_values_parsed": (
                routed.confirmatory_target_values_parsed
            ),
            "pilot_target_values_parsed": 0,
            "nonfocal_confirmatory_target_values_parsed": 0,
            "counts_as_fresh_confirmatory_evidence": False,
            "fresh_system_denominator_contribution": 0,
            "primary_supported": None,
            "mechanism_claim_authorized": False,
            "rerun_authorized": False,
        }

    supported = bool(primary["primary_supported"])
    status = (
        contract["interpretation"]["supported_status"]
        if supported
        else contract["interpretation"]["not_supported_status"]
    )
    return {
        "schema": "structural.boreal_confirmatory_scoring_result.v0_87",
        "status": status,
        "candidate_id": contract["candidate_id"],
        "authorization_consumed": True,
        "confirmatory_response_opened": True,
        "response_file_sha256": contract["response_file"]["expected_sha256"],
        "prediction_surface_sha256": sha256_text(predictions_text),
        "confirmatory_target_surface_sha256": routed.surface_sha256,
        "confirmatory_target_values_parsed": routed.confirmatory_target_values_parsed,
        "pilot_target_values_parsed": 0,
        "nonfocal_confirmatory_target_values_parsed": 0,
        "fixed_species_count": routed.fixed_species_count,
        "confirmatory_island_count": routed.confirmatory_island_count,
        "confirmatory_block_count": routed.confirmatory_block_count,
        "primary": primary,
        "primary_supported": supported,
        "fresh_system_denominator_contribution": 1,
        "counts_as_fresh_confirmatory_evidence": True,
        "counts_as_primary_confirmatory_evidence": True,
        "confirmatory_response_authorized_after_completion": False,
        "secondary_analysis_may_change_primary_status": False,
        "mechanism_claim_authorized": False,
        "rerun_authorized": False,
        "next_action": (
            "record this one-shot fresh result as the complete v0.55 system-level "
            "primary outcome; no threshold, subgroup or secondary moderator may "
            "rescue or reverse the primary status"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("authorization", type=Path)
    parser.add_argument("model_receipt", type=Path)
    parser.add_argument("predictions", type=Path)
    parser.add_argument("pilot_snapshot", type=Path)
    parser.add_argument("spatial_receipt", type=Path)
    parser.add_argument("response_csv", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_confirmatory_scoring_contract.v0_87"
        ):
            raise BorealConfirmatoryExecutionError(
                "unexpected v0.87 contract schema"
            )
        response_bytes = args.response_csv.read_bytes()
        predictions_text = args.predictions.read_text(encoding="utf-8")
        result = execute(
            authorization=_load(args.authorization),
            model_receipt=_load(args.model_receipt),
            predictions_text=predictions_text,
            pilot_snapshot=_load(args.pilot_snapshot),
            spatial_receipt=_load(args.spatial_receipt),
            response_bytes=response_bytes,
            contract=contract,
            expected_islands=load_universe(),
            model_receipt_sha256=sha256_bytes(
                args.model_receipt.read_bytes()
            ),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealConfirmatoryExecutionError,
    ) as exc:
        result = {
            "schema": "structural.boreal_confirmatory_scoring_result.v0_87",
            "status": "STOP_PRE_ACCESS",
            "reason": str(exc),
            "authorization_consumed": False,
            "confirmatory_response_opened": False,
            "counts_as_fresh_confirmatory_evidence": False,
            "fresh_system_denominator_contribution": 0,
            "primary_supported": None,
            "mechanism_claim_authorized": False,
            "rerun_authorized": True,
        }
        code = 2
    else:
        code = 0 if result.get(
            "counts_as_fresh_confirmatory_evidence"
        ) is True else 2

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.result is not None:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
