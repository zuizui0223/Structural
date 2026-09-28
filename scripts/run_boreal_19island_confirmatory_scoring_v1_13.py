#!/usr/bin/env python3
"""Consume the one-shot 19-island confirmatory response and score frozen predictions."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

from structural.boreal_19island_confirmatory_router import (
    Boreal19ConfirmatoryRouterError,
    build_boreal_19island_confirmatory_surface,
)
from structural.boreal_confirmatory_scoring import (
    BorealConfirmatoryScoringError,
    score_primary,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_confirmatory_scoring_contract_v1_13.json"
)
DEFAULT_AUTHORIZATION = (
    ROOT / "development/boreal_19island_confirmatory_authorization_v1_12.json"
)
DEFAULT_AUTHORIZATION_FREEZE = (
    ROOT
    / "development/boreal_19island_confirmatory_authorization_freeze_v1_12.json"
)
DEFAULT_MODEL_RECEIPT = (
    ROOT / "development/boreal_19island_preconfirmatory_model_receipt_v1_10.json"
)
DEFAULT_PREDICTIONS = (
    ROOT / "development/boreal_19island_confirmatory_predictions_v1_10.csv"
)
DEFAULT_PILOT_SNAPSHOT = (
    ROOT / "development/boreal_19island_pilot_training_snapshot_v1_08.json"
)
DEFAULT_SPATIAL_FREEZE = (
    ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
)


class Boreal19ConfirmatoryExecutionError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19ConfirmatoryExecutionError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _species_sha(species: tuple[str, ...]) -> str:
    raw = "".join(f"{name}\n" for name in species).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_pre_access(
    *,
    authorization: Mapping,
    authorization_freeze: Mapping,
    authorization_file_sha256: str,
    model_receipt: Mapping,
    model_receipt_file_sha256: str,
    predictions_text: str,
    predictions_file_sha256: str,
    pilot_snapshot: Mapping,
    spatial_freeze: Mapping,
    response_bytes: bytes,
    contract: Mapping,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    dict[str, str],
]:
    candidate = contract["candidate_id"]
    required_auth = contract["required_authorization"]
    required_model = contract["required_prediction_freeze"]

    if authorization.get("schema") != required_auth["schema"]:
        raise Boreal19ConfirmatoryExecutionError(
            "unexpected v1.11 authorization schema"
        )
    if authorization.get("status") != required_auth["status"]:
        raise Boreal19ConfirmatoryExecutionError(
            "v1.11 authorization did not qualify"
        )
    if authorization.get("candidate_id") != candidate:
        raise Boreal19ConfirmatoryExecutionError(
            "authorization candidate identity mismatch"
        )
    if authorization.get("authorization_fingerprint") != required_auth[
        "authorization_fingerprint"
    ]:
        raise Boreal19ConfirmatoryExecutionError(
            "authorization fingerprint mismatch"
        )
    if authorization_file_sha256 != required_auth[
        "authorization_json_sha256"
    ]:
        raise Boreal19ConfirmatoryExecutionError(
            "authorization JSON SHA mismatch"
        )
    for key, expected in (
        ("confirmatory_response_authorized", True),
        ("authorization_consumed", False),
        ("effect_size", None),
        ("prediction_score", None),
        ("predictive_denominator_contribution", 0),
        ("counts_as_empirical_evidence", False),
        ("response_values_opened_by_authorization", False),
    ):
        if authorization.get(key) != expected:
            raise Boreal19ConfirmatoryExecutionError(
                f"authorization ceiling mismatch: {key}"
            )
    if authorization.get("eligible_action") != (
        "execute_one_shot_19island_confirmatory_scoring"
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "authorization eligible action drift"
        )

    if authorization_freeze.get("schema") != (
        "structural.boreal_19island_confirmatory_authorization_freeze.v1_12"
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "unexpected v1.12 authorization freeze schema"
        )
    if authorization_freeze.get("status") != (
        "CONFIRMATORY_AUTHORIZATION_COMMITTED_BY_FINGERPRINT_RESPONSE_UNOPENED"
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "v1.12 authorization freeze did not qualify"
        )
    if authorization_freeze.get("candidate_id") != candidate:
        raise Boreal19ConfirmatoryExecutionError(
            "v1.12 candidate identity mismatch"
        )
    if authorization_freeze.get("scoring_execution_may_be_built") is not True:
        raise Boreal19ConfirmatoryExecutionError(
            "v1.12 does not permit scoring execution"
        )
    frozen_auth = authorization_freeze.get("authorization")
    if not isinstance(frozen_auth, dict):
        raise Boreal19ConfirmatoryExecutionError(
            "v1.12 frozen authorization identity missing"
        )
    if frozen_auth.get("authorization_json_sha256") != (
        authorization_file_sha256
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "v1.12 authorization file SHA mismatch"
        )
    if frozen_auth.get("authorization_fingerprint") != (
        authorization["authorization_fingerprint"]
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "v1.12 authorization fingerprint mismatch"
        )
    frozen_boundary = authorization_freeze.get("response_boundary")
    if not isinstance(frozen_boundary, dict):
        raise Boreal19ConfirmatoryExecutionError(
            "v1.12 response boundary missing"
        )
    for key, expected in (
        ("response_values_opened", False),
        ("confirmatory_response_authorized", True),
        ("authorization_consumed", False),
        ("counts_as_empirical_evidence", False),
        ("predictive_denominator_contribution", 0),
    ):
        if frozen_boundary.get(key) != expected:
            raise Boreal19ConfirmatoryExecutionError(
                f"v1.12 response boundary mismatch: {key}"
            )

    if model_receipt.get("schema") != (
        "structural.boreal_19island_preconfirmatory_model_freeze.v1_09"
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "unexpected v1.10 model receipt schema"
        )
    if model_receipt.get("status") != (
        "CONFIRMATORY_PREDICTIONS_FROZEN_BEFORE_RESPONSE"
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "v1.10 model receipt did not qualify"
        )
    if model_receipt.get("candidate_id") != candidate:
        raise Boreal19ConfirmatoryExecutionError(
            "model receipt candidate identity mismatch"
        )
    if model_receipt_file_sha256 != required_model[
        "model_receipt_file_sha256"
    ]:
        raise Boreal19ConfirmatoryExecutionError(
            "model receipt file SHA mismatch"
        )
    if authorization.get("source_model_receipt_sha256") != (
        model_receipt_file_sha256
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "authorization/model receipt SHA mismatch"
        )
    for key, expected in (
        ("models_fingerprint", required_model["models_fingerprint"]),
        (
            "prediction_surface_sha256",
            required_model["prediction_surface_sha256"],
        ),
        (
            "pilot_snapshot_fingerprint",
            required_model["pilot_snapshot_fingerprint"],
        ),
        (
            "pilot_species_universe_sha256",
            required_model["pilot_species_universe_sha256"],
        ),
        ("species_count", required_model["species_count"]),
        ("prediction_row_count", required_model["prediction_row_count"]),
        (
            "confirmatory_island_count",
            required_model["confirmatory_island_count"],
        ),
        (
            "confirmatory_block_count",
            required_model["confirmatory_block_count"],
        ),
        ("confirmatory_target_values_opened", 0),
        ("excluded_target_values_opened", 0),
        ("confirmatory_response_authorized", False),
        ("predictive_denominator_contribution", 0),
        ("counts_as_empirical_evidence", False),
    ):
        if model_receipt.get(key) != expected:
            raise Boreal19ConfirmatoryExecutionError(
                f"model receipt binding drift: {key}"
            )

    if predictions_file_sha256 != required_model[
        "prediction_file_sha256"
    ]:
        raise Boreal19ConfirmatoryExecutionError(
            "prediction file SHA mismatch"
        )
    prediction_sha = sha256_text(predictions_text)
    if prediction_sha != required_model["prediction_surface_sha256"]:
        raise Boreal19ConfirmatoryExecutionError(
            "prediction surface content SHA mismatch"
        )
    if authorization.get("prediction_surface_sha256") != prediction_sha:
        raise Boreal19ConfirmatoryExecutionError(
            "authorization/prediction SHA mismatch"
        )
    if authorization.get("models_fingerprint") != required_model[
        "models_fingerprint"
    ]:
        raise Boreal19ConfirmatoryExecutionError(
            "authorization/model fingerprint mismatch"
        )
    if authorization.get("prediction_row_count") != required_model[
        "prediction_row_count"
    ]:
        raise Boreal19ConfirmatoryExecutionError(
            "authorization prediction row-count mismatch"
        )

    parent_primary = model_receipt.get("primary_scoring")
    if not isinstance(parent_primary, dict):
        raise Boreal19ConfirmatoryExecutionError(
            "model receipt primary scoring rule missing"
        )
    for key in (
        "favourable_direction",
        "bootstrap_replicates",
        "bootstrap_seed",
        "external_isolation_interaction_required",
        "secondary_moderator_may_rescue_failed_primary",
    ):
        if parent_primary.get(key) != contract["primary"].get(key):
            raise Boreal19ConfirmatoryExecutionError(
                f"v1.09/v1.13 primary scoring drift: {key}"
            )

    if pilot_snapshot.get("schema") != (
        "structural.boreal_19island_pilot_training_snapshot.v1_07"
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "unexpected v1.08 pilot snapshot schema"
        )
    if pilot_snapshot.get("status") != (
        "PILOT_TRAINING_SNAPSHOT_FROZEN_FROM_SINGLE_OPEN"
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "pilot snapshot did not qualify"
        )
    if pilot_snapshot.get("snapshot_fingerprint") != required_model[
        "pilot_snapshot_fingerprint"
    ]:
        raise Boreal19ConfirmatoryExecutionError(
            "pilot snapshot fingerprint mismatch"
        )
    species = tuple(pilot_snapshot.get("pilot_species_universe") or ())
    if len(species) != required_model["species_count"]:
        raise Boreal19ConfirmatoryExecutionError(
            "fixed species count mismatch"
        )
    if _species_sha(species) != required_model[
        "pilot_species_universe_sha256"
    ]:
        raise Boreal19ConfirmatoryExecutionError(
            "fixed species universe SHA mismatch"
        )
    if authorization.get("fixed_species_universe_sha256") != (
        required_model["pilot_species_universe_sha256"]
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "authorization fixed-species SHA mismatch"
        )

    if spatial_freeze.get("schema") != (
        "structural.boreal_19island_spatial_partition_freeze.v1_00"
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "unexpected spatial freeze schema"
        )
    if spatial_freeze.get("status") != (
        "SPATIAL_PARTITION_COMMITTED_RESPONSE_INDEPENDENTLY"
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "spatial freeze did not qualify"
        )
    if spatial_freeze.get("candidate_id") != candidate:
        raise Boreal19ConfirmatoryExecutionError(
            "spatial freeze candidate mismatch"
        )
    pilot_blocks = tuple(spatial_freeze.get("pilot_block_ids") or ())
    confirmatory_blocks = tuple(
        spatial_freeze.get("confirmatory_block_ids") or ()
    )
    mapping = spatial_freeze.get("island_to_block")
    pilot_islands = tuple(spatial_freeze.get("pilot_islands") or ())
    confirmatory_islands = tuple(
        spatial_freeze.get("confirmatory_islands") or ()
    )
    if len(confirmatory_blocks) != required_model[
        "confirmatory_block_count"
    ]:
        raise Boreal19ConfirmatoryExecutionError(
            "confirmatory block count mismatch"
        )
    if len(confirmatory_islands) != required_model[
        "confirmatory_island_count"
    ]:
        raise Boreal19ConfirmatoryExecutionError(
            "confirmatory island count mismatch"
        )
    if not isinstance(mapping, dict) or set(mapping) != set(
        pilot_islands + confirmatory_islands
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "analysis island-to-block map mismatch"
        )
    if tuple(authorization.get("pilot_block_ids") or ()) != pilot_blocks:
        raise Boreal19ConfirmatoryExecutionError(
            "authorization pilot block order mismatch"
        )
    if tuple(authorization.get("confirmatory_block_ids") or ()) != (
        confirmatory_blocks
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "authorization confirmatory block order mismatch"
        )
    if tuple(authorization.get("pilot_islands") or ()) != pilot_islands:
        raise Boreal19ConfirmatoryExecutionError(
            "authorization pilot island order mismatch"
        )
    if tuple(authorization.get("confirmatory_islands") or ()) != (
        confirmatory_islands
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "authorization confirmatory island order mismatch"
        )

    full_source = tuple(authorization.get("full_source_island_order") or ())
    analysis = tuple(authorization.get("analysis_island_order") or ())
    excluded = tuple(authorization.get("excluded_islands") or ())
    if (
        len(full_source) != 42
        or len(set(full_source)) != 42
        or len(analysis) != 19
        or len(set(analysis)) != 19
        or len(excluded) != 23
        or set(analysis) | set(excluded) != set(full_source)
        or set(analysis) & set(excluded)
    ):
        raise Boreal19ConfirmatoryExecutionError(
            "authorization source/analysis/excluded universe mismatch"
        )
    if set(analysis) != set(mapping):
        raise Boreal19ConfirmatoryExecutionError(
            "authorization analysis population differs from spatial freeze"
        )

    target = contract["response_file"]
    if len(response_bytes) != target["expected_size_bytes"]:
        raise Boreal19ConfirmatoryExecutionError(
            "response byte size mismatch"
        )
    if sha256_bytes(response_bytes) != target["expected_sha256"]:
        raise Boreal19ConfirmatoryExecutionError(
            "response SHA mismatch"
        )
    if authorization.get("response_file") != {
        "name": target["name"],
        "dryad_file_id": target["dryad_file_id"],
        "size_bytes": target["expected_size_bytes"],
        "sha256": target["expected_sha256"],
        "expected_species_columns": target["expected_species_columns"],
    }:
        raise Boreal19ConfirmatoryExecutionError(
            "authorized response identity drift"
        )

    allowed = authorization.get("allowed_semantic_access")
    if not isinstance(allowed, dict):
        raise Boreal19ConfirmatoryExecutionError(
            "authorization semantic access map missing"
        )
    for key, expected in (
        ("confirmatory_fixed_species_occurrence_cells", True),
        ("confirmatory_nonfocal_species_occurrence_cells", False),
        ("pilot_island_occurrence_cells", False),
        ("excluded_island_occurrence_cells", False),
    ):
        if allowed.get(key) is not expected:
            raise Boreal19ConfirmatoryExecutionError(
                f"authorization semantic access drift: {key}"
            )

    return (
        species,
        full_source,
        analysis,
        pilot_blocks,
        confirmatory_blocks,
        mapping,
    )


def execute(
    *,
    authorization: Mapping,
    authorization_freeze: Mapping,
    authorization_file_sha256: str,
    model_receipt: Mapping,
    model_receipt_file_sha256: str,
    predictions_text: str,
    predictions_file_sha256: str,
    pilot_snapshot: Mapping,
    spatial_freeze: Mapping,
    response_bytes: bytes,
    contract: Mapping,
) -> dict:
    (
        species,
        full_source,
        analysis,
        pilot_blocks,
        confirmatory_blocks,
        mapping,
    ) = _validate_pre_access(
        authorization=authorization,
        authorization_freeze=authorization_freeze,
        authorization_file_sha256=authorization_file_sha256,
        model_receipt=model_receipt,
        model_receipt_file_sha256=model_receipt_file_sha256,
        predictions_text=predictions_text,
        predictions_file_sha256=predictions_file_sha256,
        pilot_snapshot=pilot_snapshot,
        spatial_freeze=spatial_freeze,
        response_bytes=response_bytes,
        contract=contract,
    )

    # From this call onward the v1.12 authorization is irreversibly consumed.
    try:
        routed = build_boreal_19island_confirmatory_surface(
            response_csv_bytes=response_bytes,
            full_expected_islands=full_source,
            analysis_expected_islands=analysis,
            analysis_island_to_block=mapping,
            pilot_partition=pilot_blocks,
            confirmatory_partition=confirmatory_blocks,
            fixed_species=species,
            expected_species_count=contract["response_file"][
                "expected_species_columns"
            ],
        )
    except Boreal19ConfirmatoryRouterError as exc:
        return {
            "schema": (
                "structural.boreal_19island_confirmatory_scoring_result.v1_13"
            ),
            "status": "TERMINAL_CONFIRMATORY_ROUTER_STOP",
            "reason": str(exc),
            "candidate_id": contract["candidate_id"],
            "authorization_consumed": True,
            "confirmatory_response_opened": True,
            "counts_as_fresh_confirmatory_evidence": False,
            "fresh_system_denominator_contribution": 0,
            "primary_supported": None,
            "mechanism_claim_authorized": False,
            "rerun_authorized": False,
        }

    semantic = contract["semantic_access"]
    for observed, expected, label in (
        (
            routed.routing_island_fields_decoded,
            semantic["routing_island_fields_decoded_required"],
            "routing_island_fields_decoded",
        ),
        (
            routed.confirmatory_target_values_parsed,
            semantic["confirmatory_target_values_parsed_required"],
            "confirmatory_target_values_parsed",
        ),
        (
            routed.pilot_target_values_parsed,
            semantic["pilot_target_values_parsed_required"],
            "pilot_target_values_parsed",
        ),
        (
            routed.excluded_target_values_parsed,
            semantic["excluded_target_values_parsed_required"],
            "excluded_target_values_parsed",
        ),
        (
            routed.nonfocal_confirmatory_target_values_parsed,
            semantic[
                "nonfocal_confirmatory_target_values_parsed_required"
            ],
            "nonfocal_confirmatory_target_values_parsed",
        ),
    ):
        if observed != expected:
            return {
                "schema": (
                    "structural.boreal_19island_confirmatory_scoring_result.v1_13"
                ),
                "status": "TERMINAL_CONFIRMATORY_FIREWALL_VIOLATION",
                "reason": (
                    f"{label} expected {expected}, observed {observed}"
                ),
                "candidate_id": contract["candidate_id"],
                "authorization_consumed": True,
                "confirmatory_response_opened": True,
                "confirmatory_target_values_parsed": (
                    routed.confirmatory_target_values_parsed
                ),
                "pilot_target_values_parsed": (
                    routed.pilot_target_values_parsed
                ),
                "excluded_target_values_parsed": (
                    routed.excluded_target_values_parsed
                ),
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
            bootstrap_replicates=contract["primary"][
                "bootstrap_replicates"
            ],
            bootstrap_seed=contract["primary"]["bootstrap_seed"],
        )
    except BorealConfirmatoryScoringError as exc:
        return {
            "schema": (
                "structural.boreal_19island_confirmatory_scoring_result.v1_13"
            ),
            "status": "TERMINAL_CONFIRMATORY_SCORING_STOP",
            "reason": str(exc),
            "candidate_id": contract["candidate_id"],
            "authorization_consumed": True,
            "confirmatory_response_opened": True,
            "confirmatory_target_values_parsed": (
                routed.confirmatory_target_values_parsed
            ),
            "pilot_target_values_parsed": 0,
            "excluded_target_values_parsed": 0,
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
        "schema": (
            "structural.boreal_19island_confirmatory_scoring_result.v1_13"
        ),
        "status": status,
        "candidate_id": contract["candidate_id"],
        "authorization_fingerprint": authorization[
            "authorization_fingerprint"
        ],
        "authorization_consumed": True,
        "confirmatory_response_opened": True,
        "response_file_sha256": contract["response_file"][
            "expected_sha256"
        ],
        "prediction_surface_sha256": sha256_text(predictions_text),
        "models_fingerprint": model_receipt["models_fingerprint"],
        "confirmatory_target_surface_sha256": routed.surface_sha256,
        "routing_island_fields_decoded": (
            routed.routing_island_fields_decoded
        ),
        "confirmatory_target_values_parsed": (
            routed.confirmatory_target_values_parsed
        ),
        "pilot_target_values_parsed": 0,
        "excluded_target_values_parsed": 0,
        "nonfocal_confirmatory_target_values_parsed": 0,
        "fixed_species_count": routed.fixed_species_count,
        "confirmatory_island_count": routed.confirmatory_island_count,
        "confirmatory_block_count": routed.confirmatory_block_count,
        "excluded_island_count": routed.excluded_island_count,
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
            "freeze this one-shot fresh system result by exact artifact "
            "provenance; primary status is final for this system and may not "
            "be rescued or reversed by secondary analyses"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--authorization", type=Path, default=DEFAULT_AUTHORIZATION
    )
    parser.add_argument(
        "--authorization-freeze",
        type=Path,
        default=DEFAULT_AUTHORIZATION_FREEZE,
    )
    parser.add_argument(
        "--model-receipt", type=Path, default=DEFAULT_MODEL_RECEIPT
    )
    parser.add_argument(
        "--predictions", type=Path, default=DEFAULT_PREDICTIONS
    )
    parser.add_argument(
        "--pilot-snapshot", type=Path, default=DEFAULT_PILOT_SNAPSHOT
    )
    parser.add_argument(
        "--spatial-freeze", type=Path, default=DEFAULT_SPATIAL_FREEZE
    )
    parser.add_argument("response_csv", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--result", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_19island_confirmatory_scoring_contract.v1_13"
        ):
            raise Boreal19ConfirmatoryExecutionError(
                "unexpected v1.13 scoring contract schema"
            )
        response_bytes = args.response_csv.read_bytes()
        predictions_text = args.predictions.read_text(encoding="utf-8")
        result = execute(
            authorization=_load(args.authorization),
            authorization_freeze=_load(args.authorization_freeze),
            authorization_file_sha256=sha256_file(args.authorization),
            model_receipt=_load(args.model_receipt),
            model_receipt_file_sha256=sha256_file(args.model_receipt),
            predictions_text=predictions_text,
            predictions_file_sha256=sha256_file(args.predictions),
            pilot_snapshot=_load(args.pilot_snapshot),
            spatial_freeze=_load(args.spatial_freeze),
            response_bytes=response_bytes,
            contract=contract,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        Boreal19ConfirmatoryExecutionError,
    ) as exc:
        result = {
            "schema": (
                "structural.boreal_19island_confirmatory_scoring_result.v1_13"
            ),
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
        code = (
            0
            if result.get("counts_as_fresh_confirmatory_evidence") is True
            else 2
        )

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.result is not None:
        args.result.parent.mkdir(parents=True, exist_ok=True)
        args.result.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
