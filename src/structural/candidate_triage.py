"""Metadata-only triage for prospective connectivity candidates."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MetadataStatus(str, Enum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class TriageStatus(str, Enum):
    ADVANCE_TO_SCHEMA_AUDIT = "advance_to_schema_audit"
    PENDING = "pending"
    STOP = "stop"


@dataclass(frozen=True)
class ConnectivityCandidateMetadata:
    candidate_id: str
    source_id: str
    origin: str
    temporal_replication: MetadataStatus
    immutable_source_identity: MetadataStatus
    spatial_unit_id_documented: MetadataStatus
    coordinates_or_geometry_documented: MetadataStatus
    outcome_file_separable: MetadataStatus
    operator_semantics_declarable: MetadataStatus
    connectivity_question_already_published: MetadataStatus
    response_result_seen_by_project: MetadataStatus


@dataclass(frozen=True)
class TriageDecision:
    status: TriageStatus
    reasons: tuple[str, ...]


def triage_candidate(candidate: ConnectivityCandidateMetadata) -> TriageDecision:
    """Classify a candidate using metadata only; never inspect response values."""

    reasons: list[str] = []

    if candidate.response_result_seen_by_project is MetadataStatus.YES:
        return TriageDecision(
            TriageStatus.STOP,
            ("response_result_already_seen_by_project",),
        )

    if candidate.connectivity_question_already_published is MetadataStatus.YES:
        return TriageDecision(
            TriageStatus.STOP,
            ("connectivity_question_already_published",),
        )

    hard_no = []
    if candidate.immutable_source_identity is MetadataStatus.NO:
        hard_no.append("no_immutable_source_identity")
    if candidate.spatial_unit_id_documented is MetadataStatus.NO:
        hard_no.append("no_spatial_unit_identifier")
    if candidate.coordinates_or_geometry_documented is MetadataStatus.NO:
        hard_no.append("no_reproducible_geometry")
    if candidate.outcome_file_separable is MetadataStatus.NO:
        hard_no.append("response_cannot_be_firewalled")
    if candidate.operator_semantics_declarable is MetadataStatus.NO:
        hard_no.append("operator_semantics_not_declarable")
    if hard_no:
        return TriageDecision(TriageStatus.STOP, tuple(hard_no))

    fields = {
        "temporal_replication": candidate.temporal_replication,
        "immutable_source_identity": candidate.immutable_source_identity,
        "spatial_unit_id_documented": candidate.spatial_unit_id_documented,
        "coordinates_or_geometry_documented": candidate.coordinates_or_geometry_documented,
        "outcome_file_separable": candidate.outcome_file_separable,
        "operator_semantics_declarable": candidate.operator_semantics_declarable,
    }
    unknown = [name for name, value in fields.items() if value is MetadataStatus.UNKNOWN]
    if unknown:
        return TriageDecision(
            TriageStatus.PENDING,
            tuple(f"unknown_{name}" for name in unknown),
        )

    if candidate.temporal_replication is MetadataStatus.NO:
        return TriageDecision(
            TriageStatus.PENDING,
            ("single_time_slice_requires_non_temporal_endpoint_design",),
        )

    return TriageDecision(TriageStatus.ADVANCE_TO_SCHEMA_AUDIT, ())
