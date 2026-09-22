"""Two-stage response firewall for dynamic connectivity prediction."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TemporalAccessStage(str, Enum):
    SCHEMA_ONLY = "schema_only"
    LAGGED_STATE_OPENED = "lagged_state_opened"
    FEATURES_FROZEN = "features_frozen"
    FUTURE_TARGET_OPENED = "future_target_opened"


class TemporalAccessAction(str, Enum):
    OPEN_LAGGED_STATE = "open_lagged_state"
    FREEZE_FEATURES = "freeze_features"
    OPEN_FUTURE_TARGET = "open_future_target"


class TemporalAccessError(RuntimeError):
    pass


@dataclass(frozen=True)
class TemporalResponseProtocol:
    protocol_id: str
    lagged_state_time: str
    future_target_time: str
    ecological_unit: str
    endpoint_id: str
    species_or_taxon_rule: str
    geometry_rule_id: str
    reference_rule_id: str
    connectivity_rule_id: str
    split_rule_id: str
    metric_id: str


@dataclass(frozen=True)
class TemporalAccessState:
    protocol: TemporalResponseProtocol
    stage: TemporalAccessStage = TemporalAccessStage.SCHEMA_ONLY
    lagged_state_receipt: str | None = None
    feature_fingerprint: str | None = None
    future_target_receipt: str | None = None


def validate_temporal_protocol(protocol: TemporalResponseProtocol) -> None:
    for label, value in (
        ("protocol_id", protocol.protocol_id),
        ("lagged_state_time", protocol.lagged_state_time),
        ("future_target_time", protocol.future_target_time),
        ("ecological_unit", protocol.ecological_unit),
        ("endpoint_id", protocol.endpoint_id),
        ("species_or_taxon_rule", protocol.species_or_taxon_rule),
        ("geometry_rule_id", protocol.geometry_rule_id),
        ("reference_rule_id", protocol.reference_rule_id),
        ("connectivity_rule_id", protocol.connectivity_rule_id),
        ("split_rule_id", protocol.split_rule_id),
        ("metric_id", protocol.metric_id),
    ):
        if not value.strip():
            raise TemporalAccessError(f"missing_{label}")
    if protocol.lagged_state_time == protocol.future_target_time:
        raise TemporalAccessError("lagged and target times must differ")


def advance_temporal_access(
    state: TemporalAccessState,
    action: TemporalAccessAction,
    *,
    receipt_or_fingerprint: str,
) -> TemporalAccessState:
    """Advance the dynamic response firewall in one irreversible direction."""

    validate_temporal_protocol(state.protocol)
    if not receipt_or_fingerprint.strip():
        raise TemporalAccessError("receipt_or_fingerprint must be non-empty")

    if action is TemporalAccessAction.OPEN_LAGGED_STATE:
        if state.stage is not TemporalAccessStage.SCHEMA_ONLY:
            raise TemporalAccessError("lagged state can only open from schema_only")
        return TemporalAccessState(
            protocol=state.protocol,
            stage=TemporalAccessStage.LAGGED_STATE_OPENED,
            lagged_state_receipt=receipt_or_fingerprint,
        )

    if action is TemporalAccessAction.FREEZE_FEATURES:
        if state.stage is not TemporalAccessStage.LAGGED_STATE_OPENED:
            raise TemporalAccessError("features freeze requires lagged_state_opened")
        return TemporalAccessState(
            protocol=state.protocol,
            stage=TemporalAccessStage.FEATURES_FROZEN,
            lagged_state_receipt=state.lagged_state_receipt,
            feature_fingerprint=receipt_or_fingerprint,
        )

    if action is TemporalAccessAction.OPEN_FUTURE_TARGET:
        if state.stage is not TemporalAccessStage.FEATURES_FROZEN:
            raise TemporalAccessError("future target requires frozen features")
        return TemporalAccessState(
            protocol=state.protocol,
            stage=TemporalAccessStage.FUTURE_TARGET_OPENED,
            lagged_state_receipt=state.lagged_state_receipt,
            feature_fingerprint=state.feature_fingerprint,
            future_target_receipt=receipt_or_fingerprint,
        )

    raise TemporalAccessError(f"unsupported action: {action}")


def lagged_state_may_inform_connectivity(state: TemporalAccessState) -> bool:
    """Lagged/current state is legitimate predictor information after stage 1."""

    return state.stage in {
        TemporalAccessStage.LAGGED_STATE_OPENED,
        TemporalAccessStage.FEATURES_FROZEN,
        TemporalAccessStage.FUTURE_TARGET_OPENED,
    }


def future_target_may_inform_features(state: TemporalAccessState) -> bool:
    """Future target must never inform candidate/reference feature construction."""

    return False
