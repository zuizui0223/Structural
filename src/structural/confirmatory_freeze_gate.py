"""Gate from a burned-pilot pass to confirmatory-protocol construction."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ConfirmatoryFreezeStatus(str, Enum):
    ELIGIBLE = "eligible_to_freeze_confirmatory_protocol"
    STOP = "stop"


@dataclass(frozen=True)
class ConfirmatoryFreezeDecision:
    status: ConfirmatoryFreezeStatus
    reasons: tuple[str, ...]


def evaluate_confirmatory_freeze_gate(
    *,
    expected_protocol_fingerprint: str,
    pilot_result: dict,
    confirmatory_response_accessed: bool,
) -> ConfirmatoryFreezeDecision:
    reasons: list[str] = []

    if pilot_result.get("protocol_fingerprint") != expected_protocol_fingerprint:
        reasons.append("pilot_protocol_fingerprint_mismatch")

    if pilot_result.get("status") != "qualified_for_new_confirmatory_protocol":
        reasons.append("pilot_did_not_qualify")

    if pilot_result.get("effect_size") is not None:
        reasons.append("pilot_effect_size_present")
    if pilot_result.get("prediction_score") is not None:
        reasons.append("pilot_prediction_score_present")
    if pilot_result.get("predictive_denominator_contribution") not in (0, None):
        reasons.append("pilot_entered_predictive_denominator")

    if pilot_result.get("confirmatory_partition_opened") is not False:
        reasons.append("confirmatory_partition_exposure_not_proven_false")
    if pilot_result.get("confirmatory_response_row_count_seen") not in (0, None):
        reasons.append("confirmatory_response_rows_seen")
    if confirmatory_response_accessed:
        reasons.append("confirmatory_response_already_accessed")

    return ConfirmatoryFreezeDecision(
        status=ConfirmatoryFreezeStatus.STOP if reasons else ConfirmatoryFreezeStatus.ELIGIBLE,
        reasons=tuple(reasons),
    )
