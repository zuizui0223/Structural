#!/usr/bin/env python3
"""Build boreal v0.31 + v0.42 pre-pilot contracts from a clean v0.12 intake."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

from scripts.validate_independent_system_intake_v0_12 import (
    canonical_fingerprint,
)
from structural.response_quality_attrition import (
    ResponseQualityAttritionContract,
    ResponseQualityContractStatus,
    canonical_contract_mapping,
    contract_fingerprint,
    evaluate_response_quality_contract,
)
from structural.transition_pilot_protocol import (
    PilotProtocolStatus,
    TransitionPilotProtocol,
    canonical_protocol_mapping,
    evaluate_transition_pilot_protocol,
    protocol_fingerprint,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_lake_islands_prepilot_contract_builder_v0_80.json"
)
SHA64 = set("0123456789abcdef")


class BorealPrepilotBuilderError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BorealPrepilotBuilderError(f"{path.name} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and set(value.lower()) <= SHA64
    )


def _validate_intake(
    intake: Mapping,
    receipt: Mapping,
    *,
    candidate_id: str,
) -> None:
    if intake.get("schema") != "structural.independent_system_intake.v0_12":
        raise BorealPrepilotBuilderError("unexpected v0.12 intake schema")
    if intake.get("status") != "response_sealed_dual_isolation_intake_draft":
        raise BorealPrepilotBuilderError("v0.12 intake is not response-sealed draft")
    if intake.get("system_id") != candidate_id:
        raise BorealPrepilotBuilderError("v0.12 system identity mismatch")
    if intake.get("response_firewall_state") != "response_sealed":
        raise BorealPrepilotBuilderError("v0.12 response firewall is not sealed")
    if intake.get("response_values_accessed") is not False:
        raise BorealPrepilotBuilderError("v0.12 response already accessed")

    response_files = [
        row for row in intake.get("source_files", [])
        if isinstance(row, dict) and row.get("role") == "response"
    ]
    if len(response_files) != 1:
        raise BorealPrepilotBuilderError("v0.12 must identify exactly one response file")
    response = response_files[0]
    if response.get("file_id") != "beetles_speciesmatrix_presenceabsence.csv":
        raise BorealPrepilotBuilderError("unexpected primary response file")
    if response.get("opened") is not False:
        raise BorealPrepilotBuilderError("primary beetle response is not sealed")
    if not _is_sha256(response.get("sha256")):
        raise BorealPrepilotBuilderError("invalid primary beetle response SHA")

    if receipt.get("schema") != "structural.independent_system_intake_receipt.v0_12":
        raise BorealPrepilotBuilderError("unexpected v0.12 validation receipt schema")
    if receipt.get("status") != (
        "eligible_to_construct_v0_31_and_v0_42_pre_pilot_contracts"
    ):
        raise BorealPrepilotBuilderError("v0.12 validation receipt did not qualify")
    if receipt.get("system_id") != candidate_id:
        raise BorealPrepilotBuilderError("v0.12 receipt system identity mismatch")
    if receipt.get("intake_fingerprint") != canonical_fingerprint(dict(intake)):
        raise BorealPrepilotBuilderError("v0.12 intake fingerprint mismatch")
    if receipt.get("v0_31_protocol_construction_authorized") is not True:
        raise BorealPrepilotBuilderError("v0.31 construction not authorized")
    if receipt.get("v0_42_quality_contract_construction_authorized") is not True:
        raise BorealPrepilotBuilderError("v0.42 construction not authorized")
    for key in (
        "pilot_response_authorized",
        "confirmatory_response_authorized",
        "mechanism_response_authorized",
        "mechanism_claim_authorized",
        "ttf_handoff_authorized",
    ):
        if receipt.get(key) is not False:
            raise BorealPrepilotBuilderError(f"v0.12 ceiling violated: {key}")
    if receipt.get("effect_size") is not None or receipt.get("prediction_score") is not None:
        raise BorealPrepilotBuilderError("v0.12 receipt contains predictive output")
    if receipt.get("predictive_denominator_contribution") != 0:
        raise BorealPrepilotBuilderError("v0.12 predictive denominator is nonzero")


def _validate_spatial(
    spatial: Mapping,
    *,
    intake: Mapping,
    spatial_receipt_sha256: str | None,
    candidate_id: str,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, str]]:
    if spatial.get("schema") != (
        "structural.boreal_lake_islands_spatial_partition_result.v0_75"
    ):
        raise BorealPrepilotBuilderError("unexpected v0.75 spatial receipt schema")
    if spatial.get("status") != "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY":
        raise BorealPrepilotBuilderError("v0.75 spatial partition did not qualify")
    if spatial.get("candidate_id") != candidate_id:
        raise BorealPrepilotBuilderError("v0.75 candidate identity mismatch")
    for key in (
        "species_occurrence_used",
        "richness_used",
        "habitat_values_used",
        "counts_as_empirical_evidence",
        "pilot_response_authorized",
        "confirmatory_response_authorized",
    ):
        if spatial.get(key) is not False:
            raise BorealPrepilotBuilderError(f"v0.75 boundary violated: {key}")

    if spatial.get("pilot_block_count", 0) < 3:
        raise BorealPrepilotBuilderError("v0.75 has fewer than three pilot blocks")
    if spatial.get("confirmatory_block_count", 0) < 6:
        raise BorealPrepilotBuilderError("v0.75 has fewer than six confirmatory blocks")

    pilot_islands = tuple(spatial.get("pilot_islands") or ())
    confirmatory_islands = tuple(spatial.get("confirmatory_islands") or ())
    pilot_blocks = set(spatial.get("pilot_block_ids") or ())
    confirmatory_blocks = set(spatial.get("confirmatory_block_ids") or ())
    island_to_block = spatial.get("island_to_block")

    if not pilot_islands or not confirmatory_islands:
        raise BorealPrepilotBuilderError("v0.75 island partitions are empty")
    if set(pilot_islands) & set(confirmatory_islands):
        raise BorealPrepilotBuilderError("v0.75 pilot/confirmatory islands overlap")
    if len(set(pilot_islands) | set(confirmatory_islands)) != 42:
        raise BorealPrepilotBuilderError("v0.75 island partitions do not cover 42 islands")
    if pilot_blocks & confirmatory_blocks:
        raise BorealPrepilotBuilderError("v0.75 pilot/confirmatory blocks overlap")
    if not isinstance(island_to_block, dict) or len(island_to_block) != 42:
        raise BorealPrepilotBuilderError("v0.75 island-to-block map invalid")

    for island in pilot_islands:
        if island_to_block.get(island) not in pilot_blocks:
            raise BorealPrepilotBuilderError("pilot island mapped outside pilot blocks")
    for island in confirmatory_islands:
        if island_to_block.get(island) not in confirmatory_blocks:
            raise BorealPrepilotBuilderError(
                "confirmatory island mapped outside confirmatory blocks"
            )

    support = intake.get("response_blind_data_support")
    if not isinstance(support, dict):
        raise BorealPrepilotBuilderError("v0.12 response-blind support missing")
    hashes = support.get("preintake_receipt_sha256")
    if not isinstance(hashes, dict):
        raise BorealPrepilotBuilderError("v0.12 preintake receipt hashes missing")
    expected_spatial_hash = hashes.get("spatial_partition_v0_75")
    if not _is_sha256(expected_spatial_hash):
        raise BorealPrepilotBuilderError("v0.12 spatial receipt SHA invalid")
    if spatial_receipt_sha256 is not None and spatial_receipt_sha256 != expected_spatial_hash:
        raise BorealPrepilotBuilderError("v0.75 receipt SHA does not bind v0.12 intake")

    return (
        pilot_islands,
        confirmatory_islands,
        {str(k): str(v) for k, v in island_to_block.items()},
    )


def build(
    intake: Mapping,
    intake_receipt: Mapping,
    spatial_receipt: Mapping,
    *,
    contract: Mapping,
    spatial_receipt_sha256: str | None = None,
) -> dict:
    candidate_id = contract["candidate_id"]
    _validate_intake(intake, intake_receipt, candidate_id=candidate_id)
    pilot_islands, confirmatory_islands, island_to_block = _validate_spatial(
        spatial_receipt,
        intake=intake,
        spatial_receipt_sha256=spatial_receipt_sha256,
        candidate_id=candidate_id,
    )

    p = contract["protocol"]
    protocol = TransitionPilotProtocol(
        protocol_id=p["protocol_id"],
        system_id=candidate_id,
        partition_axis=p["partition_axis"],
        pilot_partition=pilot_islands,
        confirmatory_partition=confirmatory_islands,
        endpoint_id=p["endpoint_id"],
        endpoint_semantics=p["endpoint_semantics"],
        heldout_design_id=p["heldout_design_id"],
        minimum_test_rows=p["minimum_test_rows"],
        minimum_train_positive=p["minimum_train_positive"],
        minimum_train_negative=p["minimum_train_negative"],
        minimum_estimable_blocks=p["minimum_estimable_blocks"],
        pilot_response_accessed=False,
        confirmatory_response_accessed=False,
        pilot_used_for_effect_estimation=False,
    )
    protocol_decision = evaluate_transition_pilot_protocol(protocol)
    if protocol_decision.status is not PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT:
        raise BorealPrepilotBuilderError(
            "constructed v0.31 component failed generic pre-response gate"
        )
    protocol_map = canonical_protocol_mapping(protocol)
    protocol_fp = protocol_fingerprint(protocol)

    q = contract["quality_contract"]
    quality = ResponseQualityAttritionContract(
        contract_id=q["contract_id"],
        system_id=candidate_id,
        parent_protocol_fingerprint=protocol_fp,
        minimum_response_qualified_blocks=q[
            "minimum_response_qualified_blocks"
        ],
        response_quality_semantics=q["response_quality_semantics"],
        pilot_response_accessed=False,
        confirmatory_response_accessed=False,
    )
    quality_decision = evaluate_response_quality_contract(
        protocol=protocol,
        contract=quality,
    )
    if quality_decision.status is not ResponseQualityContractStatus.QUALIFIED_TO_OPEN_PILOT:
        raise BorealPrepilotBuilderError(
            "constructed v0.42 component failed generic pre-response gate"
        )
    quality_map = canonical_contract_mapping(quality)
    quality_fp = contract_fingerprint(quality)

    pilot_map = {
        island: island_to_block[island] for island in pilot_islands
    }
    confirmatory_map = {
        island: island_to_block[island] for island in confirmatory_islands
    }
    response_row = next(
        row for row in intake["source_files"]
        if row["role"] == "response"
    )

    return {
        "schema": "structural.boreal_lake_islands_prepilot_bundle.v0_80",
        "status": "V031_V042_COMPONENTS_FROZEN_RESPONSE_REMAINS_SEALED",
        "candidate_id": candidate_id,
        "parent_intake_fingerprint": intake_receipt["intake_fingerprint"],
        "parent_spatial_receipt_sha256": (
            spatial_receipt_sha256
            or intake["response_blind_data_support"][
                "preintake_receipt_sha256"
            ]["spatial_partition_v0_75"]
        ),
        "v0_31_protocol": protocol_map,
        "v0_31_protocol_fingerprint": protocol_fp,
        "v0_31_component_status": protocol_decision.status.value,
        "v0_42_quality_contract": quality_map,
        "v0_42_quality_contract_fingerprint": quality_fp,
        "v0_42_component_status": quality_decision.status.value,
        "pilot_surface_routing": {
            **contract["pilot_surface_routing"],
            "pilot_island_to_block": pilot_map,
            "confirmatory_island_to_block": confirmatory_map,
            "pilot_block_ids": list(spatial_receipt["pilot_block_ids"]),
            "confirmatory_block_ids": list(
                spatial_receipt["confirmatory_block_ids"]
            ),
            "response_file_id": response_row["file_id"],
            "response_file_sha256": response_row["sha256"],
        },
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("intake", type=Path)
    parser.add_argument("intake_receipt", type=Path)
    parser.add_argument("spatial_receipt", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-bundle", type=Path)
    parser.add_argument("--output-v031", type=Path)
    parser.add_argument("--output-v042", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_lake_islands_prepilot_contract_builder.v0_80"
        ):
            raise BorealPrepilotBuilderError("unexpected v0.80 contract schema")
        result = build(
            _load(args.intake),
            _load(args.intake_receipt),
            _load(args.spatial_receipt),
            contract=contract,
            spatial_receipt_sha256=sha256_file(args.spatial_receipt),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealPrepilotBuilderError,
    ) as exc:
        result = {
            "schema": "structural.boreal_lake_islands_prepilot_bundle.v0_80",
            "status": "STOP",
            "reason": str(exc),
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
        }
        code = 2
    else:
        code = 0

    if code == 0:
        if args.output_v031 is not None:
            args.output_v031.parent.mkdir(parents=True, exist_ok=True)
            args.output_v031.write_text(
                json.dumps(
                    result["v0_31_protocol"], indent=2, sort_keys=True
                ) + "\n",
                encoding="utf-8",
            )
        if args.output_v042 is not None:
            args.output_v042.parent.mkdir(parents=True, exist_ok=True)
            args.output_v042.write_text(
                json.dumps(
                    result["v0_42_quality_contract"],
                    indent=2,
                    sort_keys=True,
                ) + "\n",
                encoding="utf-8",
            )

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output_bundle is not None:
        args.output_bundle.parent.mkdir(parents=True, exist_ok=True)
        args.output_bundle.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
