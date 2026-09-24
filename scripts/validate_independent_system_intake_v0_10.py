#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from structural.candidate_triage import (  # noqa: E402
    ConnectivityCandidateMetadata,
    MetadataStatus,
    TriageStatus,
    triage_candidate,
)

SCHEMA = "structural.independent_system_intake.v0_10"
RECEIPT_SCHEMA = "structural.independent_system_intake_receipt.v0_10"

M1 = "M1_contemporary_colonization"
M2 = "M2_rescue_persistence"
M3 = "M3_historical_colonization_legacy"
M4 = "M4_environmental_proxy"
ALLOWED_LANES = {M1, M2, M3, M4}

CLOSED_SYSTEM_IDS = {
    "usgs_pnw_montane_ponds_2012_2013",
    "usgs_rmnp_amphibian_surveys_1986_2022",
    "great_lakes_frog_2011_2023",
    "hungary_amphibian_100_ponds_2023",
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class IntakeError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntakeError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise IntakeError("intake must be a JSON object")
    return value


def canonical_fingerprint(value: dict) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _string(value: dict, key: str) -> str:
    out = value.get(key)
    if not isinstance(out, str) or not out.strip():
        raise IntakeError(f"{key} must be a non-empty string")
    return out.strip()


def _bool(value: dict, key: str) -> bool:
    out = value.get(key)
    if not isinstance(out, bool):
        raise IntakeError(f"{key} must be boolean")
    return out


def _metadata_status(value: object, key: str) -> MetadataStatus:
    if not isinstance(value, str):
        raise IntakeError(f"{key} must be yes/no/unknown")
    try:
        return MetadataStatus(value)
    except ValueError as exc:
        raise IntakeError(f"{key} must be yes/no/unknown") from exc


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


def _validate_files(intake: dict) -> dict:
    rows = intake.get("source_files")
    if not isinstance(rows, list) or not rows:
        raise IntakeError("source_files must be a non-empty list")

    allowed_roles = {"safe_metadata", "geometry", "response", "unknown"}
    seen_ids: set[str] = set()
    role_counts = {role: 0 for role in allowed_roles}
    opened_counts = {role: 0 for role in allowed_roles}

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise IntakeError(f"source_files[{index}] must be an object")
        file_id = _string(row, "file_id")
        if file_id in seen_ids:
            raise IntakeError(f"duplicate source file id: {file_id}")
        seen_ids.add(file_id)

        sha = _string(row, "sha256")
        if not SHA256_RE.match(sha):
            raise IntakeError(f"invalid sha256 for source file {file_id}")

        role = _string(row, "role")
        if role not in allowed_roles:
            raise IntakeError(f"invalid file role for {file_id}: {role}")
        opened = row.get("opened")
        if not isinstance(opened, bool):
            raise IntakeError(f"opened must be boolean for {file_id}")

        role_counts[role] += 1
        opened_counts[role] += int(opened)

        if role in {"response", "unknown"} and opened:
            raise IntakeError(
                f"response/unknown file was opened before intake freeze: {file_id}"
            )

    if role_counts["response"] < 1:
        raise IntakeError("at least one response file must be identified")
    if role_counts["safe_metadata"] + role_counts["geometry"] < 1:
        raise IntakeError("at least one safe metadata/geometry file is required")

    return {
        "file_count": len(rows),
        "role_counts": role_counts,
        "opened_counts": opened_counts,
        "response_files_opened": opened_counts["response"],
        "unknown_files_opened": opened_counts["unknown"],
    }


def _validate_hypothesis_bindings(intake: dict) -> None:
    expected = {
        "structural_partition_contract":
            "development/transition_pilot_protocol_contract_v0_31.json",
        "ecological_hypothesis":
            "development/prospective_extreme_isolation_topology_hypothesis_v0_3.json",
        "mechanism_framework":
            "development/prospective_mechanism_discrimination_v0_1.json",
    }
    bindings = intake.get("hypothesis_bindings")
    if not isinstance(bindings, dict):
        raise IntakeError("hypothesis_bindings must be an object")
    for key, value in expected.items():
        if bindings.get(key) != value:
            raise IntakeError(f"hypothesis binding drift: {key}")


def _triage(intake: dict):
    triage = intake.get("freshness_metadata")
    if not isinstance(triage, dict):
        raise IntakeError("freshness_metadata must be an object")

    candidate = ConnectivityCandidateMetadata(
        candidate_id=_string(intake, "system_id"),
        source_id=_string(intake, "source_id"),
        origin=_string(intake, "origin"),
        temporal_replication=_metadata_status(
            triage.get("temporal_replication"), "temporal_replication"
        ),
        immutable_source_identity=_metadata_status(
            triage.get("immutable_source_identity"), "immutable_source_identity"
        ),
        spatial_unit_id_documented=_metadata_status(
            triage.get("spatial_unit_id_documented"), "spatial_unit_id_documented"
        ),
        coordinates_or_geometry_documented=_metadata_status(
            triage.get("coordinates_or_geometry_documented"),
            "coordinates_or_geometry_documented",
        ),
        outcome_file_separable=_metadata_status(
            triage.get("outcome_file_separable"), "outcome_file_separable"
        ),
        operator_semantics_declarable=_metadata_status(
            triage.get("operator_semantics_declarable"),
            "operator_semantics_declarable",
        ),
        connectivity_question_already_published=_metadata_status(
            triage.get("connectivity_question_already_published"),
            "connectivity_question_already_published",
        ),
        response_result_seen_by_project=_metadata_status(
            triage.get("response_result_seen_by_project"),
            "response_result_seen_by_project",
        ),
    )
    return triage_candidate(candidate)


def _validate_selection_firewall(intake: dict) -> None:
    firewall = intake.get("selection_firewall")
    if not isinstance(firewall, dict):
        raise IntakeError("selection_firewall must be an object")

    must_be_false = (
        "system_selected_using_response_direction",
        "system_selected_using_connectivity_result",
        "mechanism_lanes_selected_using_response_direction",
        "graph_scale_selected_using_response_direction",
        "endpoint_selected_using_response_direction",
        "published_effect_direction_used_for_selection",
    )
    for key in must_be_false:
        if firewall.get(key) is not False:
            raise IntakeError(f"selection firewall must be false: {key}")

    if firewall.get("candidate_hunt_active") is not False:
        raise IntakeError("candidate_hunt_active must be false")


def _validate_lane_support(intake: dict) -> tuple[list[str], dict]:
    lanes = intake.get("requested_mechanism_lanes")
    if not isinstance(lanes, list) or not lanes:
        raise IntakeError("requested_mechanism_lanes must be a non-empty list")
    if not all(isinstance(lane, str) and lane for lane in lanes):
        raise IntakeError("requested_mechanism_lanes must contain strings")
    if len(lanes) != len(set(lanes)):
        raise IntakeError("requested_mechanism_lanes contains duplicates")

    unknown = sorted(set(lanes) - ALLOWED_LANES)
    if unknown:
        raise IntakeError("unknown mechanism lanes: " + ", ".join(unknown))

    support = intake.get("response_blind_data_support")
    if not isinstance(support, dict):
        raise IntakeError("response_blind_data_support must be an object")

    temporal = _bool(support, "temporal_transition_metadata_available")
    genetic = _bool(support, "genetic_sampling_metadata_available")
    environment = _bool(support, "environment_predictor_metadata_available")

    reasons: list[str] = []
    if (M1 in lanes or M2 in lanes) and not temporal:
        reasons.append("dynamic_lane_requested_without_temporal_transition_metadata")
    if M3 in lanes and not genetic:
        reasons.append("M3_requested_without_genetic_sampling_metadata")
    if M4 in lanes and not environment:
        reasons.append("M4_requested_without_environment_predictor_metadata")

    return lanes, {
        "temporal_transition_metadata_available": temporal,
        "genetic_sampling_metadata_available": genetic,
        "environment_predictor_metadata_available": environment,
        "support_reasons": reasons,
    }


def validate_intake(intake: dict) -> tuple[int, dict]:
    if intake.get("schema") != SCHEMA:
        return 1, _zero_receipt(
            status="invalid_intake_schema",
            intake=intake,
            reason="unexpected intake schema",
        )
    if intake.get("status") != "response_sealed_intake_draft":
        return 1, _zero_receipt(
            status="invalid_intake_schema",
            intake=intake,
            reason="intake must start response_sealed_intake_draft",
        )

    try:
        system_id = _string(intake, "system_id")
        source_id = _string(intake, "source_id")
        source_version = _string(intake, "source_version")
        source_fingerprint = _string(intake, "source_fingerprint")
        if not SHA256_RE.match(source_fingerprint):
            raise IntakeError("source_fingerprint must be a sha256 hex digest")

        if system_id in CLOSED_SYSTEM_IDS:
            return 2, _zero_receipt(
                status="STOP_prior_closed_system_cannot_reenter",
                intake=intake,
                closed_system_id=system_id,
            )

        if intake.get("is_prior_closed_system") is not False:
            return 2, _zero_receipt(
                status="STOP_prior_closed_system_cannot_reenter",
                intake=intake,
                reason="is_prior_closed_system must be false",
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
        _validate_hypothesis_bindings(intake)
        file_audit = _validate_files(intake)
        lanes, support = _validate_lane_support(intake)
        if support["support_reasons"]:
            return 2, _zero_receipt(
                status="STOP_requested_mechanism_lane_lacks_response_blind_support",
                intake=intake,
                requested_mechanism_lanes=lanes,
                response_blind_data_support=support,
            )

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

    if decision.status is TriageStatus.PENDING:
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
        "status": "eligible_to_construct_v0_31_partition_protocol",
        "system_id": system_id,
        "source_id": source_id,
        "source_version": source_version,
        "source_fingerprint": source_fingerprint,
        "intake_fingerprint": fingerprint,
        "freshness_triage_status": decision.status.value,
        "freshness_triage_reasons": [],
        "file_audit": file_audit,
        "requested_mechanism_lanes": lanes,
        "response_blind_data_support": support,
        "hypothesis_bindings": intake["hypothesis_bindings"],
        "eligible_action": "construct_v0_31_partition_protocol_only",
        "v0_31_protocol_construction_authorized": True,
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
        code, receipt = validate_intake(load_json(args.intake))
    except IntakeError as exc:
        code, receipt = 1, _zero_receipt(
            status="invalid_input",
            reason=str(exc),
        )

    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
