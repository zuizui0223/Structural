"""Future-system admission wrapper with the prospective v0.42 attrition gate."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from collections.abc import Mapping

from .confirmatory_admission import (
    ConfirmatoryAdmissionStatus,
    evaluate_confirmatory_admission,
)
from .response_quality_attrition import (
    ResponseQualityAttritionContract,
    ResponseQualityAttritionAudit,
    ResponseQualityAuditStatus,
    audit_response_quality_attrition,
)
from .transition_pilot_protocol import TransitionPilotProtocol


class FutureAdmissionStatus(str, Enum):
    ADMITTED = "admitted_to_confirmatory_protocol_queue_v0_42"
    STOP = "stop"


@dataclass(frozen=True)
class FutureAdmissionDecision:
    status: FutureAdmissionStatus
    reasons: tuple[str, ...]
    system_id: str
    protocol_id: str
    protocol_fingerprint: str
    quality_contract_fingerprint: str
    response_qualified_blocks: int
    minimum_response_qualified_blocks: int
    quality_retention_fraction: float
    eligible_action: str | None
    confirmatory_response_authorized: bool


def evaluate_future_admission_v0_42(
    *,
    protocol: TransitionPilotProtocol,
    pilot_result: Mapping[str, object],
    quality_contract: ResponseQualityAttritionContract,
    confirmatory_response_accessed: bool = False,
) -> FutureAdmissionDecision:
    """Require both the frozen v0.31-v0.33 chain and v0.42 quality survival."""

    base = evaluate_confirmatory_admission(
        protocol=protocol,
        pilot_result=pilot_result,
        confirmatory_response_accessed=confirmatory_response_accessed,
    )
    quality: ResponseQualityAttritionAudit = audit_response_quality_attrition(
        protocol=protocol,
        contract=quality_contract,
        pilot_result=pilot_result,
    )

    reasons = list(base.reasons)
    if quality.status is not ResponseQualityAuditStatus.QUALIFIED:
        reasons.append(f"v0_42:{quality.status.value}")
        reasons.extend(f"v0_42:{reason}" for reason in quality.reasons)

    unique_reasons = tuple(dict.fromkeys(reasons))
    admitted = (
        base.status is ConfirmatoryAdmissionStatus.ADMITTED
        and quality.status is ResponseQualityAuditStatus.QUALIFIED
        and not unique_reasons
    )

    return FutureAdmissionDecision(
        status=FutureAdmissionStatus.ADMITTED if admitted else FutureAdmissionStatus.STOP,
        reasons=unique_reasons,
        system_id=protocol.system_id,
        protocol_id=protocol.protocol_id,
        protocol_fingerprint=quality.protocol_fingerprint,
        quality_contract_fingerprint=quality.contract_fingerprint,
        response_qualified_blocks=quality.response_qualified_blocks,
        minimum_response_qualified_blocks=quality.minimum_response_qualified_blocks,
        quality_retention_fraction=quality.retention_fraction,
        eligible_action="freeze_confirmatory_protocol_only" if admitted else None,
        confirmatory_response_authorized=False,
    )


def future_admission_receipt_mapping(
    decision: FutureAdmissionDecision,
) -> dict[str, object]:
    return {
        "schema": "structural.future_confirmatory_admission_receipt.v0_42",
        "status": decision.status.value,
        "gate_versions": ["v0.31", "v0.32", "v0.33", "v0.42"],
        "system_id": decision.system_id,
        "protocol_id": decision.protocol_id,
        "protocol_fingerprint": decision.protocol_fingerprint,
        "quality_contract_fingerprint": decision.quality_contract_fingerprint,
        "response_qualified_blocks": decision.response_qualified_blocks,
        "minimum_response_qualified_blocks": decision.minimum_response_qualified_blocks,
        "quality_retention_fraction": decision.quality_retention_fraction,
        "reasons": list(decision.reasons),
        "eligible_action": decision.eligible_action,
        "confirmatory_response_authorized": False,
        "predictive_denominator_contribution": 0,
        "historical_systems_re_adjudicated": False,
        "ttf_handoff_authorized": False,
    }
