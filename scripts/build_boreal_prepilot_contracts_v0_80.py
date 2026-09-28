#!/usr/bin/env python3
"""Construct boreal v0.31 + v0.42 pre-pilot contracts after a clean v0.12 intake."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

from scripts.validate_independent_system_intake_v0_12 import canonical_fingerprint
from structural.response_quality_attrition import (
    ResponseQualityContractStatus,
    canonical_contract_mapping,
    contract_from_mapping,
    evaluate_response_quality_contract,
)
from structural.transition_pilot_protocol import (
    PilotProtocolStatus,
    canonical_protocol_mapping,
    evaluate_transition_pilot_protocol,
    protocol_from_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_lake_islands_prepilot_contract_builder_v0_80.json"
)
SHA64 = re.compile(r"^[0-9a-f]{64}$")


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


def _require_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA64.fullmatch(value):
        raise BorealPrepilotBuilderError(f"invalid SHA-256: {label}")
    return value


def _validate_intake_and_receipt(
    intake: Mapping,
    receipt: Mapping,
    *,
    candidate_id: str,
) -> str:
    if intake.get("schema") != "structural.independent_system_intake.v0_12":
        raise BorealPrepilotBuilderError("unexpected v0.12 intake schema")
    if intake.get("status") != "response_sealed_dual_isolation_intake_draft":
        raise BorealPrepilotBuilderError("v0.12 intake status did not qualify")
    if intake.get("system_id") != candidate_id:
        raise BorealPrepilotBuilderError("v0.12 intake candidate identity mismatch")
    if intake.get("response_firewall_state") != "response_sealed":
        raise BorealPrepilotBuilderError("v0.12 response firewall is not sealed")
    if intake.get("response_values_accessed") is not False:
        raise BorealPrepilotBuilderError("v0.12 response already accessed")
    if intake.get("mechanism_claim_requested") is not False:
        raise BorealPrepilotBuilderError("v0.12 mechanism claim boundary violated")
    if intake.get("requested_mechanism_lanes") != []:
        raise BorealPrepilotBuilderError("v0.12 mechanism lanes must remain empty")
    endpoint = intake.get("endpoint_design")
    if not isinstance(endpoint, dict) or endpoint.get("mode") != "static_cross_sectional_occurrence":
        raise BorealPrepilotBuilderError("v0.12 endpoint is not static occurrence")

    if receipt.get("schema") != "structural.independent_system_intake_receipt.v0_12":
        raise BorealPrepilotBuilderError("unexpected v0.12 intake receipt schema")
    if receipt.get("status") != "eligible_to_construct_v0_31_and_v0_42_pre_pilot_contracts":
        raise BorealPrepilotBuilderError("v0.12 intake receipt did not qualify")
    if receipt.get("system_id") != candidate_id:
        raise BorealPrepilotBuilderError("v0.12 receipt candidate identity mismatch")

    fingerprint = canonical_fingerprint(dict(intake))
    if receipt.get("intake_fingerprint") != fingerprint:
        raise BorealPrepilotBuilderError("v0.12 intake fingerprint mismatch")
    if receipt.get("v0_31_protocol_construction_authorized") is not True:
        raise BorealPrepilotBuilderError("v0.31 construction not authorized")
    if receipt.get("v0_42_quality_contract_construction_authorized") is not True:
        raise BorealPrepilotBuilderError("v0.42 construction not authorized")
    for key, expected in (
        ("pilot_response_authorized", False),
        ("confirmatory_response_authorized", False),
        ("mechanism_response_authorized", False),
        ("mechanism_claim_authorized", False),
        ("effect_size", None),
        ("prediction_score", None),
        ("predictive_denominator_contribution", 0),
        ("mechanism_claim_contribution", 0),
    ):
        if receipt.get(key) != expected:
            raise BorealPrepilotBuilderError(
                f"v0.12 receipt ceiling mismatch: {key}"
            )
    return fingerprint


def _validate_spatial(
    spatial: Mapping,
    *,
    candidate_id: str,
    expected_sha256: str,
    observed_sha256: str,
) -> tuple[list[str], list[str]]:
    if observed_sha256 != expected_sha256:
        raise BorealPrepilotBuilderError(
            "v0.75 receipt SHA does not match v0.12 preintake binding"
        )
    if spatial.get("schema") != (
        "structural.boreal_lake_islands_spatial_partition_result.v0_75"
    ):
        raise BorealPrepilotBuilderError("unexpected v0.75 spatial receipt schema")
    if spatial.get("status") != "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY":
        raise BorealPrepilotBuilderError("v0.75 spatial partition did not qualify")
    if spatial.get("candidate_id") != candidate_id:
        raise BorealPrepilotBuilderError("v0.75 candidate identity mismatch")
    if spatial.get("species_occurrence_used") is not False:
        raise BorealPrepilotBuilderError("v0.75 species-response boundary violated")
    if spatial.get("counts_as_empirical_evidence") is not False:
        raise BorealPrepilotBuilderError("v0.75 evidence boundary violated")
    if spatial.get("pilot_response_authorized") is not False:
        raise BorealPrepilotBuilderError("v0.75 pilot ceiling violated")
    if spatial.get("confirmatory_response_authorized") is not False:
        raise BorealPrepilotBuilderError("v0.75 confirmatory ceiling violated")

    pilot = spatial.get("pilot_block_ids")
    confirmatory = spatial.get("confirmatory_block_ids")
    if not isinstance(pilot, list) or not all(isinstance(x, str) and x for x in pilot):
        raise BorealPrepilotBuilderError("v0.75 pilot block list invalid")
    if not isinstance(confirmatory, list) or not all(
        isinstance(x, str) and x for x in confirmatory
    ):
        raise BorealPrepilotBuilderError("v0.75 confirmatory block list invalid")
    if len(pilot) != spatial.get("pilot_block_count"):
        raise BorealPrepilotBuilderError("v0.75 pilot block count mismatch")
    if len(confirmatory) != spatial.get("confirmatory_block_count"):
        raise BorealPrepilotBuilderError("v0.75 confirmatory block count mismatch")
    if len(pilot) < 3 or len(confirmatory) < 6:
        raise BorealPrepilotBuilderError("v0.75 block minima not met")
    if set(pilot) & set(confirmatory):
        raise BorealPrepilotBuilderError("v0.75 block partitions overlap")
    if len(pilot) + len(confirmatory) != spatial.get("spatial_block_count"):
        raise BorealPrepilotBuilderError("v0.75 spatial block total mismatch")
    return list(pilot), list(confirmatory)


def build(
    intake: Mapping,
    intake_receipt: Mapping,
    spatial_receipt: Mapping,
    *,
    spatial_receipt_sha256: str,
    contract: Mapping,
) -> tuple[dict, dict, dict]:
    candidate_id = contract["candidate_id"]
    intake_fingerprint = _validate_intake_and_receipt(
        intake,
        intake_receipt,
        candidate_id=candidate_id,
    )

    support = intake.get("response_blind_data_support")
    if not isinstance(support, dict):
        raise BorealPrepilotBuilderError("v0.12 response-blind support missing")
    hashes = support.get("preintake_receipt_sha256")
    if not isinstance(hashes, dict):
        raise BorealPrepilotBuilderError("v0.12 preintake receipt hashes missing")
    expected_spatial_sha = _require_sha(
        hashes.get("spatial_partition_v0_75"),
        "v0.12 spatial partition receipt",
    )
    pilot_blocks, confirmatory_blocks = _validate_spatial(
        spatial_receipt,
        candidate_id=candidate_id,
        expected_sha256=expected_spatial_sha,
        observed_sha256=spatial_receipt_sha256,
    )

    v31 = contract["v0_31"]
    protocol_mapping = {
        "protocol_id": (
            "boreal-lake-islands-beetles-v0.31-"
            + intake_fingerprint[:12]
        ),
        "system_id": candidate_id,
        "partition_axis": v31["partition_axis"],
        "pilot_partition": pilot_blocks,
        "confirmatory_partition": confirmatory_blocks,
        "endpoint_id": v31["endpoint_id"],
        "endpoint_semantics": (
            "One common burned-pilot-supported beetle species universe is "
            "defined after pilot response opens only: include exactly beetle "
            "species detected on at least two distinct frozen pilot islands. "
            "Apply that identical species universe to every held-out pilot "
            "spatial block. For every pilot island in the held-out block, emit "
            "one exact binary target per fixed-universe species from the "
            "standardized 30 x 30 m assemblage matrix (1=detected, 0=not "
            "detected). Unexpected/nonbinary values, missing frozen pilot "
            "islands, or an empty supported species universe are non-estimable "
            "and cannot be repaired after pilot opening. The burned pilot is "
            "feasibility evidence only and contributes no effect estimate or "
            "predictive score."
        ),
        "heldout_design_id": v31["heldout_design_id"],
        "minimum_test_rows": v31["minimum_test_rows"],
        "minimum_train_positive": v31["minimum_train_positive"],
        "minimum_train_negative": v31["minimum_train_negative"],
        "minimum_estimable_blocks": v31["minimum_estimable_blocks"],
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
        "pilot_used_for_effect_estimation": False,
    }
    protocol = protocol_from_mapping(protocol_mapping)
    protocol_decision = evaluate_transition_pilot_protocol(protocol)
    if protocol_decision.status is not PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT:
        raise BorealPrepilotBuilderError(
            "constructed v0.31 protocol failed generic evaluator"
        )
    protocol_fingerprint = protocol_decision.protocol_fingerprint

    v42 = contract["v0_42"]
    quality_mapping = {
        "contract_id": (
            "boreal-lake-islands-beetles-quality-v0.42-"
            + protocol_fingerprint[:12]
        ),
        "system_id": candidate_id,
        "parent_protocol_fingerprint": protocol_fingerprint,
        "minimum_response_qualified_blocks": v42[
            "minimum_response_qualified_blocks"
        ],
        "response_quality_semantics": (
            "A burned-pilot spatial block is response-qualified only when the "
            "single common fixed pilot-supported beetle species universe yields "
            "at least the frozen minimum_test_rows exact binary island-by-species "
            "targets in that held-out block. The common universe is defined once "
            "from pilot response only as species detected on at least two "
            "distinct frozen pilot islands and is applied identically to every "
            "pilot block. Unexpected values outside 0/1, a missing frozen pilot "
            "island, or inability to construct the common universe is a terminal "
            "STOP. Blocks, islands, species, thresholds and partitions may not be "
            "rescued, substituted, merged, imputed or relaxed after pilot opening."
        ),
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
    }
    quality = contract_from_mapping(quality_mapping)
    quality_decision = evaluate_response_quality_contract(
        protocol=protocol,
        contract=quality,
    )
    if quality_decision.status is not (
        ResponseQualityContractStatus.QUALIFIED_TO_OPEN_PILOT
    ):
        raise BorealPrepilotBuilderError(
            "constructed v0.42 quality contract failed generic evaluator"
        )

    receipt = {
        "schema": "structural.boreal_lake_islands_prepilot_contract_result.v0_80",
        "status": "V031_AND_V042_FROZEN_RESPONSE_REMAINS_SEALED",
        "candidate_id": candidate_id,
        "parent_intake_fingerprint": intake_fingerprint,
        "source_spatial_receipt_sha256": spatial_receipt_sha256,
        "protocol_fingerprint": protocol_fingerprint,
        "quality_contract_fingerprint": quality_decision.contract_fingerprint,
        "pilot_block_count": len(pilot_blocks),
        "confirmatory_block_count": len(confirmatory_blocks),
        "generic_v0_31_status": protocol_decision.status.value,
        "generic_v0_42_status": quality_decision.status.value,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "mechanism_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "next_action": (
            "commit the v0.31 protocol and fingerprint-bound v0.42 contract; "
            "only then may a separate response-access authorization be considered"
        ),
    }
    return (
        canonical_protocol_mapping(protocol),
        canonical_contract_mapping(quality),
        receipt,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("intake", type=Path)
    parser.add_argument("intake_receipt", type=Path)
    parser.add_argument("spatial_receipt", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-protocol", type=Path)
    parser.add_argument("--output-quality", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_lake_islands_prepilot_contract_builder.v0_80"
        ):
            raise BorealPrepilotBuilderError("unexpected v0.80 contract schema")
        protocol, quality, receipt = build(
            _load(args.intake),
            _load(args.intake_receipt),
            _load(args.spatial_receipt),
            spatial_receipt_sha256=sha256_file(args.spatial_receipt),
            contract=contract,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealPrepilotBuilderError,
    ) as exc:
        protocol = quality = None
        receipt = {
            "schema": "structural.boreal_lake_islands_prepilot_contract_result.v0_80",
            "status": "STOP",
            "reason": str(exc),
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
            "mechanism_response_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
        }
        code = 2
    else:
        code = 0

    if protocol is not None and args.output_protocol is not None:
        args.output_protocol.parent.mkdir(parents=True, exist_ok=True)
        args.output_protocol.write_text(
            json.dumps(protocol, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if quality is not None and args.output_quality is not None:
        args.output_quality.parent.mkdir(parents=True, exist_ok=True)
        args.output_quality.write_text(
            json.dumps(quality, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
