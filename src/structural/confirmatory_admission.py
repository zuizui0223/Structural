"""Integrated v0.31-v0.33 admission gate for confirmatory-protocol construction."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from .confirmatory_freeze_gate import (
    ConfirmatoryFreezeStatus,
    evaluate_confirmatory_freeze_gate,
)
from .transition_pilot_protocol import (
    PilotProtocolStatus,
    TransitionPilotProtocol,
    evaluate_transition_pilot_protocol,
)


class ConfirmatoryAdmissionStatus(str, Enum):
    ADMITTED = "admitted_to_confirmatory_protocol_queue"
    STOP = "stop"


@dataclass(frozen=True)
class ConfirmatoryAdmissionDecision:
    status: ConfirmatoryAdmissionStatus
    reasons: tuple[str, ...]
    system_id: str
    protocol_id: str
    protocol_fingerprint: str
    eligible_action: str | None
    confirmatory_response_authorized: bool


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _audit_v0_32_payload(
    protocol: TransitionPilotProtocol,
    pilot_result: Mapping[str, object],
) -> tuple[str, ...]:
    """Verify that the supplied result has the exact burned-pilot evidence ceiling."""

    reasons: list[str] = []

    if pilot_result.get("schema") != "structural.transition_pilot_result.v0_32":
        reasons.append("v0_32:unexpected_result_schema")
    if pilot_result.get("pilot_consumed") is not True:
        reasons.append("v0_32:pilot_not_proven_consumed")
    if pilot_result.get("status") != "qualified_for_new_confirmatory_protocol":
        reasons.append("v0_32:pilot_did_not_qualify")

    if pilot_result.get("pilot_partition") != list(protocol.pilot_partition):
        reasons.append("v0_32:pilot_partition_mismatch")
    if pilot_result.get("confirmatory_partition_opened") is not False:
        reasons.append("v0_32:confirmatory_partition_exposure_not_proven_false")
    if pilot_result.get("confirmatory_response_row_count_seen") != 0:
        reasons.append("v0_32:confirmatory_response_rows_seen")

    if pilot_result.get("effect_size") is not None:
        reasons.append("v0_32:pilot_effect_size_present")
    if pilot_result.get("prediction_score") is not None:
        reasons.append("v0_32:pilot_prediction_score_present")
    if pilot_result.get("predictive_denominator_contribution") != 0:
        reasons.append("v0_32:pilot_predictive_denominator_not_exactly_zero")

    minimum = pilot_result.get("minimum_estimable_blocks")
    estimable = pilot_result.get("estimable_blocks")
    total = pilot_result.get("total_blocks")
    block_audits = pilot_result.get("block_audits")

    if not _is_int(minimum) or minimum != protocol.minimum_estimable_blocks:
        reasons.append("v0_32:minimum_estimable_blocks_mismatch")
    if not _is_int(estimable):
        reasons.append("v0_32:estimable_blocks_invalid")
    elif estimable < protocol.minimum_estimable_blocks:
        reasons.append("v0_32:estimable_blocks_below_frozen_gate")

    if not isinstance(block_audits, list):
        reasons.append("v0_32:block_audits_missing")
    else:
        if not _is_int(total) or total != len(block_audits):
            reasons.append("v0_32:total_blocks_inconsistent")
        if any(not isinstance(row, dict) for row in block_audits):
            reasons.append("v0_32:block_audit_invalid")
        else:
            counted = sum(row.get("estimable") is True for row in block_audits)
            if _is_int(estimable) and counted != estimable:
                reasons.append("v0_32:estimable_block_count_inconsistent")

    return tuple(reasons)


def evaluate_confirmatory_admission(
    *,
    protocol: TransitionPilotProtocol,
    pilot_result: Mapping[str, object],
    confirmatory_response_accessed: bool = False,
) -> ConfirmatoryAdmissionDecision:
    """Recompute the v0.31-v0.33 chain and fail closed.

    A successful decision authorizes only construction/freezing of a separate
    confirmatory protocol. It never authorizes confirmatory response access.
    """

    if not isinstance(confirmatory_response_accessed, bool):
        raise ValueError("confirmatory_response_accessed must be boolean")

    reasons: list[str] = []
    pre = evaluate_transition_pilot_protocol(protocol)

    if pre.status is not PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT:
        reasons.extend(f"v0_31:{reason}" for reason in pre.reasons)

    if not isinstance(pilot_result, Mapping):
        reasons.append("v0_32:pilot_result_must_be_mapping")
        pilot_mapping: dict[str, object] = {}
    else:
        pilot_mapping = dict(pilot_result)
        reasons.extend(_audit_v0_32_payload(protocol, pilot_result))

    freeze = evaluate_confirmatory_freeze_gate(
        expected_protocol_fingerprint=pre.protocol_fingerprint,
        pilot_result=pilot_mapping,
        confirmatory_response_accessed=confirmatory_response_accessed,
    )
    if freeze.status is not ConfirmatoryFreezeStatus.ELIGIBLE:
        reasons.extend(f"v0_33:{reason}" for reason in freeze.reasons)

    # Preserve order while removing duplicate reasons emitted by adjacent gates.
    unique_reasons = tuple(dict.fromkeys(reasons))
    admitted = not unique_reasons

    return ConfirmatoryAdmissionDecision(
        status=(
            ConfirmatoryAdmissionStatus.ADMITTED
            if admitted
            else ConfirmatoryAdmissionStatus.STOP
        ),
        reasons=unique_reasons,
        system_id=protocol.system_id,
        protocol_id=protocol.protocol_id,
        protocol_fingerprint=pre.protocol_fingerprint,
        eligible_action="freeze_confirmatory_protocol_only" if admitted else None,
        confirmatory_response_authorized=False,
    )


def admission_receipt_mapping(decision: ConfirmatoryAdmissionDecision) -> dict[str, object]:
    """Return the deterministic, reviewable receipt stored beside a queue entry."""

    return {
        "schema": "structural.confirmatory_admission_receipt.v0_36",
        "status": decision.status.value,
        "gate_versions": ["v0.31", "v0.32", "v0.33"],
        "system_id": decision.system_id,
        "protocol_id": decision.protocol_id,
        "protocol_fingerprint": decision.protocol_fingerprint,
        "reasons": list(decision.reasons),
        "eligible_action": decision.eligible_action,
        "confirmatory_response_authorized": decision.confirmatory_response_authorized,
        "predictive_denominator_contribution": 0,
        "ttf_handoff_authorized": False,
    }
