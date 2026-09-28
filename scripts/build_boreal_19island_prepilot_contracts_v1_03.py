#!/usr/bin/env python3
"""Construct fingerprint-bound v0.31/v0.42 for the frozen 19-island intake."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from structural.response_quality_attrition import (  # noqa: E402
    ResponseQualityContractStatus,
    canonical_contract_mapping,
    contract_from_mapping,
    evaluate_response_quality_contract,
)
from structural.transition_pilot_protocol import (  # noqa: E402
    PilotProtocolStatus,
    canonical_protocol_mapping,
    evaluate_transition_pilot_protocol,
    protocol_from_mapping,
)


DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_prepilot_contract_builder_v1_03.json"
)
DEFAULT_INTAKE = (
    ROOT / "development/boreal_19island_response_sealed_intake_v1_02.json"
)
DEFAULT_RECEIPT = (
    ROOT / "development/boreal_19island_response_sealed_intake_receipt_v1_02.json"
)
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class Boreal19PrepilotError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19PrepilotError(f"{path.name} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Mapping) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA64.fullmatch(value):
        raise Boreal19PrepilotError(f"invalid SHA-256: {label}")
    return value


def build(
    intake: Mapping,
    intake_receipt: Mapping,
    *,
    contract: Mapping,
    intake_file_sha256: str,
    intake_receipt_file_sha256: str,
) -> tuple[dict, dict, dict]:
    candidate = contract["candidate_id"]
    required_intake = contract["required_intake"]
    required_receipt = contract["required_receipt"]
    required_parent = contract["required_parent_identity"]
    intake_file_sha256 = _sha(intake_file_sha256, "intake file")
    intake_receipt_file_sha256 = _sha(
        intake_receipt_file_sha256,
        "intake receipt file",
    )

    for key in ("schema", "status", "response_firewall_state"):
        if intake.get(key) != required_intake[key]:
            raise Boreal19PrepilotError(f"intake mismatch: {key}")
    if intake.get("system_id") != candidate:
        raise Boreal19PrepilotError("intake candidate identity mismatch")
    if intake.get("response_values_accessed") is not False:
        raise Boreal19PrepilotError("intake response firewall already opened")
    response = intake.get("response_file")
    if not isinstance(response, dict) or response.get("opened") is not False:
        raise Boreal19PrepilotError("beetle response file is not sealed")

    population = intake.get("population")
    if not isinstance(population, dict):
        raise Boreal19PrepilotError("intake population missing")
    if population.get("island_count") != required_intake["island_count"]:
        raise Boreal19PrepilotError("intake island count drift")
    pilot_blocks = population.get("pilot_block_ids")
    confirmatory_blocks = population.get("confirmatory_block_ids")
    pilot_islands = population.get("pilot_islands")
    confirmatory_islands = population.get("confirmatory_islands")
    if not isinstance(pilot_blocks, list) or len(pilot_blocks) != required_intake["pilot_block_count"]:
        raise Boreal19PrepilotError("pilot block partition drift")
    if not isinstance(confirmatory_blocks, list) or len(confirmatory_blocks) != required_intake["confirmatory_block_count"]:
        raise Boreal19PrepilotError("confirmatory block partition drift")
    if set(pilot_blocks) & set(confirmatory_blocks):
        raise Boreal19PrepilotError("pilot and confirmatory blocks overlap")
    if not isinstance(pilot_islands, list) or not isinstance(confirmatory_islands, list):
        raise Boreal19PrepilotError("island partitions missing")
    if set(pilot_islands) & set(confirmatory_islands):
        raise Boreal19PrepilotError("pilot and confirmatory islands overlap")
    if len(set(pilot_islands) | set(confirmatory_islands)) != required_intake["island_count"]:
        raise Boreal19PrepilotError("island partitions do not cover exact population")

    if intake_receipt.get("schema") != required_receipt["schema"]:
        raise Boreal19PrepilotError("unexpected intake receipt schema")
    if intake_receipt.get("status") != required_receipt["status"]:
        raise Boreal19PrepilotError("intake receipt did not qualify")
    if intake_receipt.get("system_id") != candidate:
        raise Boreal19PrepilotError("intake receipt candidate identity mismatch")
    intake_fingerprint = canonical_sha256(dict(intake))
    if intake_receipt.get("intake_fingerprint") != intake_fingerprint:
        raise Boreal19PrepilotError("intake fingerprint mismatch")
    if intake_fingerprint != required_parent["intake_fingerprint"]:
        raise Boreal19PrepilotError("intake fingerprint drift from frozen parent")
    if intake_file_sha256 != required_parent["intake_file_sha256"]:
        raise Boreal19PrepilotError("intake file SHA drift from frozen parent")
    if intake_receipt_file_sha256 != required_parent["intake_receipt_file_sha256"]:
        raise Boreal19PrepilotError(
            "intake receipt file SHA drift from frozen parent"
        )
    for key, expected in (
        ("v0_31_protocol_construction_authorized", True),
        ("v0_42_quality_contract_construction_authorized", True),
        ("pilot_response_authorized", False),
        ("confirmatory_response_authorized", False),
        ("predictive_denominator_contribution", 0),
        ("counts_as_empirical_evidence", False),
    ):
        if intake_receipt.get(key) != expected:
            raise Boreal19PrepilotError(f"intake receipt ceiling mismatch: {key}")

    boundary = intake.get("response_boundary")
    if not isinstance(boundary, dict):
        raise Boreal19PrepilotError("intake response boundary missing")
    for key, expected in (
        ("biological_response_values_accessed", False),
        ("pilot_response_authorized", False),
        ("confirmatory_response_authorized", False),
        ("mechanism_response_authorized", False),
        ("counts_as_empirical_evidence", False),
        ("predictive_denominator_contribution", 0),
    ):
        if boundary.get(key) != expected:
            raise Boreal19PrepilotError(f"intake response ceiling mismatch: {key}")

    design = intake.get("prepilot_design")
    if not isinstance(design, dict):
        raise Boreal19PrepilotError("pre-pilot design missing")
    v31 = design.get("v0_31")
    v42 = design.get("v0_42")
    if not isinstance(v31, dict) or not isinstance(v42, dict):
        raise Boreal19PrepilotError("v0.31/v0.42 design missing")
    if v42.get("post_open_rescue_forbidden") is not True:
        raise Boreal19PrepilotError("post-open rescue prohibition drift")

    protocol_mapping = {
        "protocol_id": (
            "boreal-19island-beetles-v0.31-" + intake_fingerprint[:12]
        ),
        "system_id": candidate,
        "partition_axis": v31["partition_axis"],
        "pilot_partition": list(pilot_blocks),
        "confirmatory_partition": list(confirmatory_blocks),
        "endpoint_id": v31["endpoint_id"],
        "endpoint_semantics": contract["v0_31_semantics"]["endpoint_semantics"],
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
    pdecision = evaluate_transition_pilot_protocol(protocol)
    if pdecision.status is not PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT:
        raise Boreal19PrepilotError(
            "constructed v0.31 protocol failed generic evaluator"
        )
    protocol_fingerprint = _sha(
        pdecision.protocol_fingerprint,
        "v0.31 protocol fingerprint",
    )

    quality_mapping = {
        "contract_id": (
            "boreal-19island-beetles-quality-v0.42-"
            + protocol_fingerprint[:12]
        ),
        "system_id": candidate,
        "parent_protocol_fingerprint": protocol_fingerprint,
        "minimum_response_qualified_blocks": v42[
            "minimum_response_qualified_blocks"
        ],
        "response_quality_semantics": contract[
            "v0_42_semantics"
        ]["response_quality_semantics"],
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
    }
    quality = contract_from_mapping(quality_mapping)
    qdecision = evaluate_response_quality_contract(
        protocol=protocol,
        contract=quality,
    )
    if qdecision.status is not (
        ResponseQualityContractStatus.QUALIFIED_TO_OPEN_PILOT
    ):
        raise Boreal19PrepilotError(
            "constructed v0.42 contract failed generic evaluator"
        )
    quality_fingerprint = _sha(
        qdecision.contract_fingerprint,
        "v0.42 quality fingerprint",
    )

    operator = intake.get("source_operator")
    if not isinstance(operator, dict):
        raise Boreal19PrepilotError("source operator binding missing")
    operator_fingerprint = _sha(
        operator.get("fingerprint"),
        "source operator fingerprint",
    )
    if operator_fingerprint != required_parent["source_operator_fingerprint"]:
        raise Boreal19PrepilotError(
            "source operator fingerprint drift from frozen parent"
        )

    receipt = {
        "schema": "structural.boreal_19island_prepilot_contract_result.v1_03",
        "status": contract["success_ceiling"]["status"],
        "candidate_id": candidate,
        "parent_intake_fingerprint": intake_fingerprint,
        "source_intake_file_sha256": intake_file_sha256,
        "source_intake_receipt_file_sha256": intake_receipt_file_sha256,
        "source_operator_fingerprint": operator_fingerprint,
        "protocol_fingerprint": protocol_fingerprint,
        "quality_contract_fingerprint": quality_fingerprint,
        "pilot_block_count": len(pilot_blocks),
        "confirmatory_block_count": len(confirmatory_blocks),
        "pilot_island_count": len(pilot_islands),
        "confirmatory_island_count": len(confirmatory_islands),
        "generic_v0_31_status": pdecision.status.value,
        "generic_v0_42_status": qdecision.status.value,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "mechanism_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return (
        canonical_protocol_mapping(protocol),
        canonical_contract_mapping(quality),
        receipt,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--intake", type=Path, default=DEFAULT_INTAKE)
    parser.add_argument("--intake-receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--output-protocol", type=Path)
    parser.add_argument("--output-quality", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_19island_prepilot_contract_builder.v1_03"
        ):
            raise Boreal19PrepilotError("unexpected v1.03 contract schema")
        protocol, quality, receipt = build(
            _load(args.intake),
            _load(args.intake_receipt),
            contract=contract,
            intake_file_sha256=sha256_file(args.intake),
            intake_receipt_file_sha256=sha256_file(args.intake_receipt),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        Boreal19PrepilotError,
    ) as exc:
        protocol = quality = None
        receipt = {
            "schema": "structural.boreal_19island_prepilot_contract_result.v1_03",
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
