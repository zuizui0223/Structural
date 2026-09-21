"""Response-blind admission gate for future typed-connectivity tests."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite

from .connectivity_adequacy import FavorableDirection, SeparationOrigin


class AdmissionStatus(str, Enum):
    QUALIFIED = "qualified"
    STOP = "stop"


@dataclass(frozen=True)
class ConnectivityEmpiricalProtocol:
    protocol_id: str
    system_id: str
    origin: SeparationOrigin
    endpoint: str
    heldout_unit: str
    metric: str
    favorable_direction: FavorableDirection
    source_snapshot_id: str
    reference_id: str
    geometry_coordinate: str | None
    process_operator: str | None
    process_coordinate: str | None
    realized_coordinate: str | None
    operator_semantics: str | None
    connectivity_scale_rule: str
    origin_history_variable: str | None
    equivalence_margin: float | None
    state_adequacy_claim_requested: bool
    candidate_uses_outcome: bool
    response_accessed: bool
    shared_reference_dependence_declared: bool
    shared_reference_group: str | None = None


@dataclass(frozen=True)
class AdmissionDecision:
    status: AdmissionStatus
    reasons: tuple[str, ...]


def _blank(value: str | None) -> bool:
    return value is None or not value.strip()


def evaluate_empirical_admission(protocol: ConnectivityEmpiricalProtocol) -> AdmissionDecision:
    """Fail closed unless a future empirical test is fully response-blind and typed."""

    reasons: list[str] = []

    for label, value in (
        ("protocol_id", protocol.protocol_id),
        ("system_id", protocol.system_id),
        ("endpoint", protocol.endpoint),
        ("heldout_unit", protocol.heldout_unit),
        ("metric", protocol.metric),
        ("source_snapshot_id", protocol.source_snapshot_id),
        ("reference_id", protocol.reference_id),
        ("connectivity_scale_rule", protocol.connectivity_scale_rule),
    ):
        if _blank(value):
            reasons.append(f"missing_{label}")

    if protocol.response_accessed:
        reasons.append("response_already_accessed")
    if protocol.candidate_uses_outcome:
        reasons.append("candidate_not_response_blind")

    if all(
        _blank(value)
        for value in (
            protocol.geometry_coordinate,
            protocol.process_coordinate,
            protocol.realized_coordinate,
        )
    ):
        reasons.append("no_connectivity_candidate_declared")

    if not _blank(protocol.process_coordinate) or not _blank(protocol.realized_coordinate):
        if _blank(protocol.process_operator):
            reasons.append("missing_process_operator")
        if _blank(protocol.operator_semantics):
            reasons.append("missing_operator_semantics")

    if not protocol.shared_reference_dependence_declared:
        reasons.append("shared_reference_dependence_not_declared")

    if protocol.equivalence_margin is not None:
        if (
            not isfinite(protocol.equivalence_margin)
            or protocol.equivalence_margin <= 0
        ):
            reasons.append("invalid_equivalence_margin")

    if protocol.state_adequacy_claim_requested:
        if _blank(protocol.origin_history_variable):
            reasons.append("state_adequacy_requires_origin_history_variable")
        if protocol.equivalence_margin is None:
            reasons.append("state_adequacy_requires_predeclared_equivalence_margin")

    return AdmissionDecision(
        status=AdmissionStatus.STOP if reasons else AdmissionStatus.QUALIFIED,
        reasons=tuple(reasons),
    )
