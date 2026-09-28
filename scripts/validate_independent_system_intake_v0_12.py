#!/usr/bin/env python3
"""Future-only response-sealed intake for v0.55 dual-isolation systems."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.validate_independent_system_intake_v0_10 import (  # noqa: E402
    CLOSED_SYSTEM_IDS,
    IntakeError,
    _string,
    _triage,
    _validate_files,
    _validate_selection_firewall,
)
from structural.candidate_triage import TriageStatus  # noqa: E402


SCHEMA = "structural.independent_system_intake.v0_12"
RECEIPT_SCHEMA = "structural.independent_system_intake_receipt.v0_12"
EXPECTED_BINDINGS = {
    "structural_partition_contract":
        "development/transition_pilot_protocol_contract_v0_31.json",
    "response_quality_gate":
        "development/response_quality_attrition_gate_v0_42.json",
    "ecological_hypothesis":
        "development/prospective_dual_isolation_source_pool_hypothesis_v0_55.json",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def canonical_fingerprint(value: dict) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _zero_receipt(*, status: str, intake: dict | None = None, **extra) -> dict:
    return {
        "schema": RECEIPT_SCHEMA,
        "status": status,
        "system_id": intake.get("system_id") if isinstance(intake, dict) else None,
        "intake_fingerprint": (
            canonical_fingerprint(intake) if isinstance(intake, dict) else None
        ),
        "eligible_action": None,
        "v0_31_protocol_construction_authorized": False,
        "v0_42_quality_contract_construction_authorized": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "mechanism_response_authorized": False,
        "mechanism_claim_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "mechanism_claim_contribution": 0,
        "ttf_handoff_authorized": False,
        **extra,
    }


def _require_bool(mapping: dict, key: str, expected: bool) -> None:
    value = mapping.get(key)
    if value is not expected:
        raise IntakeError(f"{key} must be {str(expected).lower()}")


def _validate_analysis_bindings(intake: dict) -> None:
    bindings = intake.get("analysis_bindings")
    if not isinstance(bindings, dict):
        raise IntakeError("analysis_bindings must be an object")
    if bindings != EXPECTED_BINDINGS:
        drift = {
            key: {
                "expected": value,
                "observed": bindings.get(key),
            }
            for key, value in EXPECTED_BINDINGS.items()
            if bindings.get(key) != value
        }
        extra = sorted(set(bindings) - set(EXPECTED_BINDINGS))
        raise IntakeError(
            "dual-isolation analysis binding drift: "
            + json.dumps({"drift": drift, "extra": extra}, sort_keys=True)
        )


def _validate_endpoint_design(intake: dict) -> dict:
    endpoint = intake.get("endpoint_design")
    if not isinstance(endpoint, dict):
        raise IntakeError("endpoint_design must be an object")
    if endpoint.get("mode") != "static_cross_sectional_occurrence":
        raise IntakeError(
            "endpoint mode must be static_cross_sectional_occurrence"
        )
    _require_bool(endpoint, "temporal_transition_required", False)
    _require_bool(endpoint, "whole_island_occupancy_claim_authorized", False)
    _require_bool(endpoint, "colonization_claim_authorized", False)
    _require_bool(endpoint, "rescue_persistence_claim_authorized", False)
    semantics = endpoint.get("endpoint_semantics")
    if not isinstance(semantics, str) or not semantics.strip():
        raise IntakeError("endpoint_semantics must be non-empty")
    return {
        "mode": endpoint["mode"],
        "endpoint_semantics": semantics.strip(),
        "temporal_transition_required": False,
        "whole_island_occupancy_claim_authorized": False,
        "colonization_claim_authorized": False,
        "rescue_persistence_claim_authorized": False,
    }


def _validate_mechanism_boundary(intake: dict) -> None:
    if intake.get("mechanism_claim_requested") is not False:
        raise IntakeError("mechanism_claim_requested must be false")
    lanes = intake.get("requested_mechanism_lanes")
    if lanes != []:
        raise IntakeError(
            "requested_mechanism_lanes must be an empty list for v0.12"
        )


def _validate_response_blind_support(intake: dict) -> dict:
    support = intake.get("response_blind_data_support")
    if not isinstance(support, dict):
        raise IntakeError("response_blind_data_support must be an object")

    required_true = (
        "environment_predictor_metadata_available",
        "safe_geometry_available",
        "spatial_partition_frozen",
        "habitat_reference_frozen",
    )
    for key in required_true:
        if support.get(key) is not True:
            raise IntakeError(f"response-blind support must be true: {key}")

    optional_bool = (
        "temporal_transition_metadata_available",
        "genetic_sampling_metadata_available",
    )
    for key in optional_bool:
        if not isinstance(support.get(key), bool):
            raise IntakeError(f"{key} must be boolean")

    if support.get("biological_response_values_accessed") is not False:
        raise IntakeError(
            "biological_response_values_accessed must be false"
        )

    receipt_hashes = support.get("preintake_receipt_sha256")
    if not isinstance(receipt_hashes, dict):
        raise IntakeError("preintake_receipt_sha256 must be an object")
    required_hashes = (
        "safe_projection_v0_74",
        "spatial_partition_v0_75",
        "habitat_reference_v0_76",
    )
    for key in required_hashes:
        value = receipt_hashes.get(key)
        if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
            raise IntakeError(f"invalid preintake receipt SHA: {key}")
    if set(receipt_hashes) != set(required_hashes):
        raise IntakeError("preintake receipt SHA keys must be exact")

    return {
        key: support[key]
        for key in (*required_true, *optional_bool)
    } | {
        "biological_response_values_accessed": False,
        "preintake_receipt_sha256": dict(receipt_hashes),
    }


def validate_intake_v0_12(intake: dict) -> tuple[int, dict]:
    if intake.get("schema") != SCHEMA:
        return 1, _zero_receipt(
            status="invalid_intake_schema",
            intake=intake,
            reason="unexpected intake schema",
        )
    if intake.get("status") != "response_sealed_dual_isolation_intake_draft":
        return 1, _zero_receipt(
            status="invalid_intake_schema",
            intake=intake,
            reason="intake must start response_sealed_dual_isolation_intake_draft",
        )

    try:
        system_id = _string(intake, "system_id")
        source_id = _string(intake, "source_id")
        source_version = _string(intake, "source_version")
        source_fingerprint = _string(intake, "source_fingerprint")
        if not SHA256_RE.fullmatch(source_fingerprint):
            raise IntakeError("source_fingerprint must be sha256 hex")

        if system_id in CLOSED_SYSTEM_IDS:
            return 2, _zero_receipt(
                status="STOP_prior_closed_system_cannot_reenter",
                intake=intake,
            )
        if intake.get("is_prior_closed_system") is not False:
            return 2, _zero_receipt(
                status="STOP_prior_closed_system_cannot_reenter",
                intake=intake,
            )
        if intake.get("response_firewall_state") != "response_sealed":
            return 2, _zero_receipt(
                status="STOP_response_firewall_not_sealed",
                intake=intake,
            )
        if intake.get("response_values_accessed") is not False:
            return 2, _zero_receipt(
                status="STOP_response_already_accessed",
                intake=intake,
            )

        _validate_selection_firewall(intake)
        _validate_analysis_bindings(intake)
        file_audit = _validate_files(intake)
        endpoint = _validate_endpoint_design(intake)
        _validate_mechanism_boundary(intake)
        support = _validate_response_blind_support(intake)
        decision = _triage(intake)
    except IntakeError as exc:
        return 1, _zero_receipt(
            status="invalid_intake_schema",
            intake=intake,
            reason=str(exc),
        )

    if decision.status is TriageStatus.STOP:
        return 2, _zero_receipt(
            status="STOP_freshness_triage",
            intake=intake,
            freshness_triage_status=decision.status.value,
            freshness_triage_reasons=list(decision.reasons),
            file_audit=file_audit,
        )

    static_pending = (
        decision.status is TriageStatus.PENDING
        and tuple(decision.reasons)
        == ("single_time_slice_requires_non_temporal_endpoint_design",)
    )
    if decision.status is TriageStatus.PENDING and not static_pending:
        return 2, _zero_receipt(
            status="HOLD_pending_response_blind_metadata",
            intake=intake,
            freshness_triage_status=decision.status.value,
            freshness_triage_reasons=list(decision.reasons),
            file_audit=file_audit,
        )

    fingerprint = canonical_fingerprint(intake)
    return 0, {
        "schema": RECEIPT_SCHEMA,
        "status": "eligible_to_construct_v0_31_and_v0_42_pre_pilot_contracts",
        "system_id": system_id,
        "source_id": source_id,
        "source_version": source_version,
        "source_fingerprint": source_fingerprint,
        "intake_fingerprint": fingerprint,
        "freshness_triage_status": (
            TriageStatus.ADVANCE_TO_SCHEMA_AUDIT.value
            if static_pending
            else decision.status.value
        ),
        "freshness_triage_reasons": (
            ["non_temporal_dual_isolation_endpoint_permitted"]
            if static_pending
            else []
        ),
        "file_audit": file_audit,
        "analysis_bindings": dict(intake["analysis_bindings"]),
        "endpoint_design": endpoint,
        "mechanism_claim_requested": False,
        "requested_mechanism_lanes": [],
        "response_blind_data_support": support,
        "eligible_action": (
            "construct_v0_31_protocol_then_bind_v0_42_quality_contract_only"
        ),
        "v0_31_protocol_construction_authorized": True,
        "v0_42_quality_contract_construction_authorized": True,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "mechanism_response_authorized": False,
        "mechanism_claim_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "mechanism_claim_contribution": 0,
        "ttf_handoff_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("intake", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        intake = json.loads(args.intake.read_text(encoding="utf-8"))
        if not isinstance(intake, dict):
            raise IntakeError("intake must be a JSON object")
        code, payload = validate_intake_v0_12(intake)
    except (OSError, json.JSONDecodeError, IntakeError) as exc:
        code = 1
        payload = _zero_receipt(
            status="invalid_input",
            reason=str(exc),
        )

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
