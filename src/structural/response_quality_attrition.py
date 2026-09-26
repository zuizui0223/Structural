"""Future-only response-quality attrition gate for burned-pilot admission.

v0.42 is a prospective extension layered on top of the frozen v0.31-v0.40
admission chain. It does not re-adjudicate any historical system.

The key distinction is:

1. response-quality survival: does a held-out block retain enough usable target
   rows after the system's predeclared response-quality rules are applied?
2. endpoint estimability: among surviving rows, do the training data retain the
   class support required by the frozen held-out design?

The raw v0.32 three-column pilot surface remains unchanged. System-specific
response-quality failures must be encoded upstream as a missing/non-estimable
target in that frozen pilot surface.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json
from collections.abc import Mapping

from .transition_pilot_protocol import (
    TransitionPilotProtocol,
    protocol_fingerprint,
)


class ResponseQualityContractStatus(str, Enum):
    QUALIFIED_TO_OPEN_PILOT = "qualified_response_quality_contract_before_pilot"
    STOP = "stop"


class ResponseQualityAuditStatus(str, Enum):
    QUALIFIED = "qualified_response_quality_survival"
    STOP_ATTRITION = "stop_response_quality_attrition"
    INVALID = "invalid_response_quality_audit"


@dataclass(frozen=True)
class ResponseQualityAttritionContract:
    contract_id: str
    system_id: str
    parent_protocol_fingerprint: str
    minimum_response_qualified_blocks: int
    response_quality_semantics: str
    pilot_response_accessed: bool = False
    confirmatory_response_accessed: bool = False

    def __post_init__(self) -> None:
        for label, value in (
            ("contract_id", self.contract_id),
            ("system_id", self.system_id),
            ("parent_protocol_fingerprint", self.parent_protocol_fingerprint),
            ("response_quality_semantics", self.response_quality_semantics),
        ):
            if not value.strip():
                raise ValueError(f"{label} must be non-empty")
        if len(self.parent_protocol_fingerprint) != 64:
            raise ValueError("parent_protocol_fingerprint must be a SHA-256 hex digest")
        try:
            int(self.parent_protocol_fingerprint, 16)
        except ValueError as exc:
            raise ValueError(
                "parent_protocol_fingerprint must be a SHA-256 hex digest"
            ) from exc
        if self.minimum_response_qualified_blocks < 1:
            raise ValueError("minimum_response_qualified_blocks must be >=1")


@dataclass(frozen=True)
class ResponseQualityContractDecision:
    status: ResponseQualityContractStatus
    reasons: tuple[str, ...]
    contract_fingerprint: str


@dataclass(frozen=True)
class ResponseQualityAttritionAudit:
    status: ResponseQualityAuditStatus
    reasons: tuple[str, ...]
    protocol_fingerprint: str
    contract_fingerprint: str
    total_blocks: int
    response_qualified_blocks: int
    minimum_response_qualified_blocks: int
    retention_fraction: float
    response_qualified_block_ids: tuple[str, ...]
    attrited_block_ids: tuple[str, ...]
    effect_size: None = None
    prediction_score: None = None
    predictive_denominator_contribution: int = 0


def canonical_contract_mapping(contract: ResponseQualityAttritionContract) -> dict:
    return asdict(contract)


def contract_fingerprint(contract: ResponseQualityAttritionContract) -> str:
    payload = json.dumps(
        canonical_contract_mapping(contract),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def evaluate_response_quality_contract(
    *,
    protocol: TransitionPilotProtocol,
    contract: ResponseQualityAttritionContract,
) -> ResponseQualityContractDecision:
    """Fail closed before any burned-pilot response is opened."""

    reasons: list[str] = []
    expected = protocol_fingerprint(protocol)

    if contract.system_id != protocol.system_id:
        reasons.append("system_id_mismatch")
    if contract.parent_protocol_fingerprint != expected:
        reasons.append("parent_protocol_fingerprint_mismatch")
    if contract.pilot_response_accessed:
        reasons.append("pilot_response_already_accessed_before_quality_freeze")
    if contract.confirmatory_response_accessed:
        reasons.append("confirmatory_response_already_accessed")
    if contract.minimum_response_qualified_blocks < protocol.minimum_estimable_blocks:
        reasons.append("quality_block_minimum_below_estimable_block_minimum")

    return ResponseQualityContractDecision(
        status=(
            ResponseQualityContractStatus.STOP
            if reasons
            else ResponseQualityContractStatus.QUALIFIED_TO_OPEN_PILOT
        ),
        reasons=tuple(reasons),
        contract_fingerprint=contract_fingerprint(contract),
    )


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def audit_response_quality_attrition(
    *,
    protocol: TransitionPilotProtocol,
    contract: ResponseQualityAttritionContract,
    pilot_result: Mapping[str, object],
) -> ResponseQualityAttritionAudit:
    """Audit usable-response block survival without inspecting any effect/score.

    A block is response-qualified when its held-out test portion retains at
    least protocol.minimum_test_rows applicable targets. This criterion is
    intentionally upstream of training-class support, so response attrition and
    endpoint/class collapse remain distinct failure modes.
    """

    pre = evaluate_response_quality_contract(protocol=protocol, contract=contract)
    expected_protocol = protocol_fingerprint(protocol)
    reasons: list[str] = []

    if pre.status is not ResponseQualityContractStatus.QUALIFIED_TO_OPEN_PILOT:
        reasons.extend(f"contract:{reason}" for reason in pre.reasons)

    if pilot_result.get("schema") != "structural.transition_pilot_result.v0_32":
        reasons.append("pilot:unexpected_result_schema")
    if pilot_result.get("protocol_fingerprint") != expected_protocol:
        reasons.append("pilot:protocol_fingerprint_mismatch")
    if pilot_result.get("pilot_consumed") is not True:
        reasons.append("pilot:not_proven_consumed")
    if pilot_result.get("confirmatory_partition_opened") is not False:
        reasons.append("pilot:confirmatory_partition_exposure_not_proven_false")
    if pilot_result.get("confirmatory_response_row_count_seen") != 0:
        reasons.append("pilot:confirmatory_response_rows_seen")
    if pilot_result.get("effect_size") is not None:
        reasons.append("pilot:effect_size_present")
    if pilot_result.get("prediction_score") is not None:
        reasons.append("pilot:prediction_score_present")
    if pilot_result.get("predictive_denominator_contribution") != 0:
        reasons.append("pilot:predictive_denominator_not_exactly_zero")

    block_audits = pilot_result.get("block_audits")
    if not isinstance(block_audits, list):
        reasons.append("pilot:block_audits_missing")
        block_audits = []

    seen: set[str] = set()
    qualified: list[str] = []
    attrited: list[str] = []

    for index, row in enumerate(block_audits):
        prefix = f"pilot:block_{index}"
        if not isinstance(row, dict):
            reasons.append(f"{prefix}_audit_invalid")
            continue

        block = row.get("block")
        if not isinstance(block, str) or not block.strip():
            reasons.append(f"{prefix}_name_invalid")
            continue
        if block in seen:
            reasons.append(f"{prefix}_duplicate_name")
            continue
        seen.add(block)

        test_rows = row.get("test_rows")
        if not _is_int(test_rows) or test_rows < 0:
            reasons.append(f"{prefix}_test_rows_invalid")
            continue

        if test_rows >= protocol.minimum_test_rows:
            qualified.append(block)
        else:
            attrited.append(block)

    total_blocks = len(seen)
    response_qualified_blocks = len(qualified)
    retention_fraction = (
        response_qualified_blocks / total_blocks if total_blocks else 0.0
    )

    if reasons:
        status = ResponseQualityAuditStatus.INVALID
    elif response_qualified_blocks < contract.minimum_response_qualified_blocks:
        status = ResponseQualityAuditStatus.STOP_ATTRITION
    else:
        status = ResponseQualityAuditStatus.QUALIFIED

    return ResponseQualityAttritionAudit(
        status=status,
        reasons=tuple(reasons),
        protocol_fingerprint=expected_protocol,
        contract_fingerprint=pre.contract_fingerprint,
        total_blocks=total_blocks,
        response_qualified_blocks=response_qualified_blocks,
        minimum_response_qualified_blocks=contract.minimum_response_qualified_blocks,
        retention_fraction=retention_fraction,
        response_qualified_block_ids=tuple(sorted(qualified)),
        attrited_block_ids=tuple(sorted(attrited)),
    )


def contract_from_mapping(data: dict) -> ResponseQualityAttritionContract:
    if not isinstance(data, dict):
        raise ValueError("response-quality contract must be a JSON object")

    required = (
        "contract_id",
        "system_id",
        "parent_protocol_fingerprint",
        "minimum_response_qualified_blocks",
        "response_quality_semantics",
        "pilot_response_accessed",
        "confirmatory_response_accessed",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError("missing response-quality contract keys: " + ", ".join(missing))

    for key in ("pilot_response_accessed", "confirmatory_response_accessed"):
        if not isinstance(data[key], bool):
            raise ValueError(f"{key} must be boolean")

    minimum = data["minimum_response_qualified_blocks"]
    if isinstance(minimum, bool) or not isinstance(minimum, int):
        raise ValueError("minimum_response_qualified_blocks must be an integer")

    return ResponseQualityAttritionContract(
        contract_id=str(data["contract_id"]),
        system_id=str(data["system_id"]),
        parent_protocol_fingerprint=str(data["parent_protocol_fingerprint"]),
        minimum_response_qualified_blocks=minimum,
        response_quality_semantics=str(data["response_quality_semantics"]),
        pilot_response_accessed=data["pilot_response_accessed"],
        confirmatory_response_accessed=data["confirmatory_response_accessed"],
    )


def audit_mapping(audit: ResponseQualityAttritionAudit) -> dict[str, object]:
    return {
        "schema": "structural.response_quality_attrition_result.v0_42",
        "status": audit.status.value,
        "reasons": list(audit.reasons),
        "protocol_fingerprint": audit.protocol_fingerprint,
        "contract_fingerprint": audit.contract_fingerprint,
        "total_blocks": audit.total_blocks,
        "response_qualified_blocks": audit.response_qualified_blocks,
        "minimum_response_qualified_blocks": audit.minimum_response_qualified_blocks,
        "retention_fraction": audit.retention_fraction,
        "response_qualified_block_ids": list(audit.response_qualified_block_ids),
        "attrited_block_ids": list(audit.attrited_block_ids),
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "confirmatory_response_authorized": False,
    }
