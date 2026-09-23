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
    """Recompute the burned-pilot feasibility audit from its committed counts."""

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
    if not _is_int(estimable) or estimable < 0:
        reasons.append("v0_32:estimable_blocks_invalid")

    aggregate_keys = ("applicable_rows", "positive", "negative", "non_estimable")
    aggregate: dict[str, int] = {}
    for key in aggregate_keys:
        value = pilot_result.get(key)
        if not _is_int(value) or value < 0:
            reasons.append(f"v0_32:{key}_invalid")
        else:
            aggregate[key] = value

    if all(key in aggregate for key in ("applicable_rows", "positive", "negative")):
        if aggregate["positive"] + aggregate["negative"] != aggregate["applicable_rows"]:
            reasons.append("v0_32:applicable_class_counts_inconsistent")

    if not isinstance(block_audits, list):
        reasons.append("v0_32:block_audits_missing")
        return tuple(reasons)

    if not _is_int(total) or total < 0 or total != len(block_audits):
        reasons.append("v0_32:total_blocks_inconsistent")

    seen_blocks: set[str] = set()
    recomputed_estimable = 0
    test_rows_sum = 0
    test_positive_sum = 0
    test_negative_sum = 0

    for index, row in enumerate(block_audits):
        prefix = f"v0_32:block_{index}"
        if not isinstance(row, dict):
            reasons.append(f"{prefix}_audit_invalid")
            continue

        block = row.get("block")
        if not isinstance(block, str) or not block.strip():
            reasons.append(f"{prefix}_name_invalid")
        elif block in seen_blocks:
            reasons.append(f"{prefix}_duplicate_name")
        else:
            seen_blocks.add(block)

        count_keys = (
            "test_rows",
            "test_positive",
            "test_negative",
            "train_rows",
            "train_positive",
            "train_negative",
        )
        counts: dict[str, int] = {}
        for key in count_keys:
            value = row.get(key)
            if not _is_int(value) or value < 0:
                reasons.append(f"{prefix}_{key}_invalid")
            else:
                counts[key] = value

        if len(counts) != len(count_keys):
            continue

        if counts["test_positive"] + counts["test_negative"] != counts["test_rows"]:
            reasons.append(f"{prefix}_test_class_counts_inconsistent")
        if counts["train_positive"] + counts["train_negative"] != counts["train_rows"]:
            reasons.append(f"{prefix}_train_class_counts_inconsistent")

        if all(key in aggregate for key in ("applicable_rows", "positive", "negative")):
            if counts["train_rows"] != aggregate["applicable_rows"] - counts["test_rows"]:
                reasons.append(f"{prefix}_train_rows_not_heldout_complement")
            if counts["train_positive"] != aggregate["positive"] - counts["test_positive"]:
                reasons.append(f"{prefix}_train_positive_not_heldout_complement")
            if counts["train_negative"] != aggregate["negative"] - counts["test_negative"]:
                reasons.append(f"{prefix}_train_negative_not_heldout_complement")

        expected_reasons: list[str] = []
        if counts["test_rows"] < protocol.minimum_test_rows:
            expected_reasons.append("test_rows_below_minimum")
        if counts["train_positive"] < protocol.minimum_train_positive:
            expected_reasons.append("training_positive_count_below_minimum")
        if counts["train_negative"] < protocol.minimum_train_negative:
            expected_reasons.append("training_negative_count_below_minimum")

        expected_estimable = not expected_reasons
        if row.get("estimable") is not expected_estimable:
            reasons.append(f"{prefix}_estimability_inconsistent")
        if row.get("reasons") != expected_reasons:
            reasons.append(f"{prefix}_reasons_inconsistent")

        recomputed_estimable += int(expected_estimable)
        test_rows_sum += counts["test_rows"]
        test_positive_sum += counts["test_positive"]
        test_negative_sum += counts["test_negative"]

    if "applicable_rows" in aggregate and test_rows_sum != aggregate["applicable_rows"]:
        reasons.append("v0_32:test_rows_do_not_partition_applicable_rows")
    if "positive" in aggregate and test_positive_sum != aggregate["positive"]:
        reasons.append("v0_32:test_positive_do_not_partition_positive")
    if "negative" in aggregate and test_negative_sum != aggregate["negative"]:
        reasons.append("v0_32:test_negative_do_not_partition_negative")

    if _is_int(estimable) and estimable != recomputed_estimable:
        reasons.append("v0_32:estimable_block_count_inconsistent")
    if recomputed_estimable < protocol.minimum_estimable_blocks:
        reasons.append("v0_32:recomputed_estimable_blocks_below_frozen_gate")

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
