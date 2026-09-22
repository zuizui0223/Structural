"""Physical-schema resolution gate for pending connectivity candidates."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PhysicalSchemaStatus(str, Enum):
    ADVANCE = "advance_to_protocol_freeze"
    PENDING = "pending_physical_schema"
    STOP = "stop"


@dataclass(frozen=True)
class PhysicalSchemaResolution:
    candidate_id: str
    source_landing_resolved: bool
    file_level_distribution_resolved: bool
    geometry_verified: bool
    response_firewall_verified: bool
    response_values_read: bool


@dataclass(frozen=True)
class PhysicalSchemaDecision:
    status: PhysicalSchemaStatus
    reasons: tuple[str, ...]


def evaluate_physical_schema_resolution(
    resolution: PhysicalSchemaResolution,
) -> PhysicalSchemaDecision:
    """Fail closed between metadata discovery and protocol freezing."""

    if resolution.response_values_read:
        return PhysicalSchemaDecision(
            PhysicalSchemaStatus.STOP,
            ("response_values_read_before_protocol_freeze",),
        )

    reasons: list[str] = []
    if not resolution.source_landing_resolved:
        reasons.append("source_landing_unresolved")
    if not resolution.file_level_distribution_resolved:
        reasons.append("file_level_distribution_unresolved")
    if not resolution.geometry_verified:
        reasons.append("geometry_not_physically_verified")
    if not resolution.response_firewall_verified:
        reasons.append("response_firewall_not_verified")

    if reasons:
        return PhysicalSchemaDecision(
            PhysicalSchemaStatus.PENDING,
            tuple(reasons),
        )

    return PhysicalSchemaDecision(
        PhysicalSchemaStatus.ADVANCE,
        (),
    )
