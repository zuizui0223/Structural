"""Prospective partition-freeze contract for transition-estimability pilots."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
import json


class PilotProtocolStatus(str, Enum):
    QUALIFIED_TO_OPEN_PILOT = "qualified_to_open_pilot"
    STOP = "stop"


@dataclass(frozen=True)
class TransitionPilotProtocol:
    protocol_id: str
    system_id: str
    partition_axis: str
    pilot_partition: tuple[str, ...]
    confirmatory_partition: tuple[str, ...]
    endpoint_id: str
    endpoint_semantics: str
    heldout_design_id: str
    minimum_test_rows: int
    minimum_train_positive: int
    minimum_train_negative: int
    minimum_estimable_blocks: int
    pilot_response_accessed: bool = False
    confirmatory_response_accessed: bool = False
    pilot_used_for_effect_estimation: bool = False

    def __post_init__(self) -> None:
        for label, value in (
            ("protocol_id", self.protocol_id),
            ("system_id", self.system_id),
            ("partition_axis", self.partition_axis),
            ("endpoint_id", self.endpoint_id),
            ("endpoint_semantics", self.endpoint_semantics),
            ("heldout_design_id", self.heldout_design_id),
        ):
            if not value.strip():
                raise ValueError(f"{label} must be non-empty")

        for label, values in (
            ("pilot_partition", self.pilot_partition),
            ("confirmatory_partition", self.confirmatory_partition),
        ):
            if not values:
                raise ValueError(f"{label} must be non-empty")
            if any(not value.strip() for value in values):
                raise ValueError(f"{label} values must be non-empty")
            if len(values) != len(set(values)):
                raise ValueError(f"{label} contains duplicates")

        if set(self.pilot_partition) & set(self.confirmatory_partition):
            raise ValueError("pilot and confirmatory partitions must be disjoint")

        for label, value in (
            ("minimum_test_rows", self.minimum_test_rows),
            ("minimum_train_positive", self.minimum_train_positive),
            ("minimum_train_negative", self.minimum_train_negative),
            ("minimum_estimable_blocks", self.minimum_estimable_blocks),
        ):
            if value < 1:
                raise ValueError(f"{label} must be >=1")


@dataclass(frozen=True)
class TransitionPilotProtocolDecision:
    status: PilotProtocolStatus
    reasons: tuple[str, ...]
    protocol_fingerprint: str


def canonical_protocol_mapping(protocol: TransitionPilotProtocol) -> dict:
    data = asdict(protocol)
    data["pilot_partition"] = list(protocol.pilot_partition)
    data["confirmatory_partition"] = list(protocol.confirmatory_partition)
    return data


def protocol_fingerprint(protocol: TransitionPilotProtocol) -> str:
    payload = json.dumps(
        canonical_protocol_mapping(protocol),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def evaluate_transition_pilot_protocol(
    protocol: TransitionPilotProtocol,
) -> TransitionPilotProtocolDecision:
    """Fail closed before any pilot response is opened."""

    reasons: list[str] = []
    if protocol.pilot_response_accessed:
        reasons.append("pilot_response_already_accessed_before_partition_freeze")
    if protocol.confirmatory_response_accessed:
        reasons.append("confirmatory_response_already_accessed")
    if protocol.pilot_used_for_effect_estimation:
        reasons.append("pilot_must_not_be_predictive_effect_evidence")

    return TransitionPilotProtocolDecision(
        status=(
            PilotProtocolStatus.STOP
            if reasons
            else PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT
        ),
        reasons=tuple(reasons),
        protocol_fingerprint=protocol_fingerprint(protocol),
    )


def protocol_from_mapping(data: dict) -> TransitionPilotProtocol:
    if not isinstance(data, dict):
        raise ValueError("protocol must be a JSON object")

    required = (
        "protocol_id",
        "system_id",
        "partition_axis",
        "pilot_partition",
        "confirmatory_partition",
        "endpoint_id",
        "endpoint_semantics",
        "heldout_design_id",
        "minimum_test_rows",
        "minimum_train_positive",
        "minimum_train_negative",
        "minimum_estimable_blocks",
        "pilot_response_accessed",
        "confirmatory_response_accessed",
        "pilot_used_for_effect_estimation",
    )
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError("missing protocol keys: " + ", ".join(missing))

    for key in (
        "pilot_response_accessed",
        "confirmatory_response_accessed",
        "pilot_used_for_effect_estimation",
    ):
        if not isinstance(data[key], bool):
            raise ValueError(f"{key} must be boolean")

    for key in (
        "pilot_partition",
        "confirmatory_partition",
    ):
        if (
            not isinstance(data[key], list)
            or not all(isinstance(v, str) for v in data[key])
        ):
            raise ValueError(f"{key} must be a list of strings")

    for key in (
        "minimum_test_rows",
        "minimum_train_positive",
        "minimum_train_negative",
        "minimum_estimable_blocks",
    ):
        if isinstance(data[key], bool) or not isinstance(data[key], int):
            raise ValueError(f"{key} must be an integer")

    return TransitionPilotProtocol(
        protocol_id=str(data["protocol_id"]),
        system_id=str(data["system_id"]),
        partition_axis=str(data["partition_axis"]),
        pilot_partition=tuple(data["pilot_partition"]),
        confirmatory_partition=tuple(data["confirmatory_partition"]),
        endpoint_id=str(data["endpoint_id"]),
        endpoint_semantics=str(data["endpoint_semantics"]),
        heldout_design_id=str(data["heldout_design_id"]),
        minimum_test_rows=data["minimum_test_rows"],
        minimum_train_positive=data["minimum_train_positive"],
        minimum_train_negative=data["minimum_train_negative"],
        minimum_estimable_blocks=data["minimum_estimable_blocks"],
        pilot_response_accessed=data["pilot_response_accessed"],
        confirmatory_response_accessed=data["confirmatory_response_accessed"],
        pilot_used_for_effect_estimation=data["pilot_used_for_effect_estimation"],
    )
