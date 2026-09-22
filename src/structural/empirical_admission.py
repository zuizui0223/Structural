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
    candidate_uses_lagged_state: bool = False
    lagged_state_contract_id: str | None = None


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
    # "candidate_uses_outcome" means future/held-out target information.
    # Lagged/current state is handled separately below.
    if protocol.candidate_uses_outcome:
        reasons.append("candidate_not_response_blind")
        reasons.append("candidate_uses_future_or_heldout_target")

    if protocol.candidate_uses_lagged_state and _blank(protocol.lagged_state_contract_id):
        reasons.append("lagged_state_requires_temporal_access_contract")

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


def protocol_from_mapping(data: dict) -> ConnectivityEmpiricalProtocol:
    """Parse a JSON-like mapping into a typed protocol, failing closed."""

    if not isinstance(data, dict):
        raise ValueError("protocol must be a JSON object")

    required = (
        "protocol_id",
        "system_id",
        "origin",
        "endpoint",
        "heldout_unit",
        "metric",
        "favorable_direction",
        "source_snapshot_id",
        "reference_id",
        "geometry_coordinate",
        "process_operator",
        "process_coordinate",
        "realized_coordinate",
        "operator_semantics",
        "connectivity_scale_rule",
        "origin_history_variable",
        "equivalence_margin",
        "state_adequacy_claim_requested",
        "candidate_uses_outcome",
        "response_accessed",
        "shared_reference_dependence_declared",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError("missing protocol keys: " + ", ".join(missing))

    for key in (
        "state_adequacy_claim_requested",
        "candidate_uses_outcome",
        "response_accessed",
        "shared_reference_dependence_declared",
    ):
        if not isinstance(data[key], bool):
            raise ValueError(f"{key} must be boolean")
    if "candidate_uses_lagged_state" in data and not isinstance(
        data["candidate_uses_lagged_state"], bool
    ):
        raise ValueError("candidate_uses_lagged_state must be boolean")

    for key in (
        "protocol_id",
        "system_id",
        "endpoint",
        "heldout_unit",
        "metric",
        "source_snapshot_id",
        "reference_id",
        "connectivity_scale_rule",
    ):
        if not isinstance(data[key], str):
            raise ValueError(f"{key} must be string")

    for key in (
        "geometry_coordinate",
        "process_operator",
        "process_coordinate",
        "realized_coordinate",
        "operator_semantics",
        "origin_history_variable",
        "shared_reference_group",
    ):
        if data.get(key) is not None and not isinstance(data.get(key), str):
            raise ValueError(f"{key} must be string or null")

    margin = data["equivalence_margin"]
    if margin is not None and (
        isinstance(margin, bool) or not isinstance(margin, (int, float))
    ):
        raise ValueError("equivalence_margin must be numeric or null")

    return ConnectivityEmpiricalProtocol(
        protocol_id=data["protocol_id"],
        system_id=data["system_id"],
        origin=SeparationOrigin(data["origin"]),
        endpoint=data["endpoint"],
        heldout_unit=data["heldout_unit"],
        metric=data["metric"],
        favorable_direction=FavorableDirection(data["favorable_direction"]),
        source_snapshot_id=data["source_snapshot_id"],
        reference_id=data["reference_id"],
        geometry_coordinate=data["geometry_coordinate"],
        process_operator=data["process_operator"],
        process_coordinate=data["process_coordinate"],
        realized_coordinate=data["realized_coordinate"],
        operator_semantics=data["operator_semantics"],
        connectivity_scale_rule=data["connectivity_scale_rule"],
        origin_history_variable=data["origin_history_variable"],
        equivalence_margin=None if margin is None else float(margin),
        state_adequacy_claim_requested=data["state_adequacy_claim_requested"],
        candidate_uses_outcome=data["candidate_uses_outcome"],
        response_accessed=data["response_accessed"],
        shared_reference_dependence_declared=data["shared_reference_dependence_declared"],
        shared_reference_group=data.get("shared_reference_group"),
        candidate_uses_lagged_state=data.get("candidate_uses_lagged_state", False),
        lagged_state_contract_id=data.get("lagged_state_contract_id"),
    )
