from __future__ import annotations

import json
from pathlib import Path

from structural import (
    ConnectivityCandidateMetadata,
    MetadataStatus,
    TriageStatus,
    triage_candidate,
)

ROOT = Path(__file__).resolve().parents[1]


def c(**overrides):
    data = dict(
        candidate_id="x",
        source_id="source",
        origin="habitat_fragmentation",
        temporal_replication=MetadataStatus.YES,
        immutable_source_identity=MetadataStatus.YES,
        spatial_unit_id_documented=MetadataStatus.YES,
        coordinates_or_geometry_documented=MetadataStatus.YES,
        outcome_file_separable=MetadataStatus.YES,
        operator_semantics_declarable=MetadataStatus.YES,
        connectivity_question_already_published=MetadataStatus.NO,
        response_result_seen_by_project=MetadataStatus.NO,
    )
    data.update(overrides)
    return ConnectivityCandidateMetadata(**data)


def test_complete_metadata_advances():
    assert triage_candidate(c()).status is TriageStatus.ADVANCE_TO_SCHEMA_AUDIT


def test_seen_response_is_permanent_stop():
    decision = triage_candidate(
        c(response_result_seen_by_project=MetadataStatus.YES)
    )
    assert decision.status is TriageStatus.STOP
    assert decision.reasons == ("response_result_already_seen_by_project",)


def test_missing_geometry_is_stop():
    decision = triage_candidate(
        c(coordinates_or_geometry_documented=MetadataStatus.NO)
    )
    assert decision.status is TriageStatus.STOP
    assert "no_reproducible_geometry" in decision.reasons


def test_unknown_geometry_is_pending_not_stop():
    decision = triage_candidate(
        c(coordinates_or_geometry_documented=MetadataStatus.UNKNOWN)
    )
    assert decision.status is TriageStatus.PENDING
    assert "unknown_coordinates_or_geometry_documented" in decision.reasons


def test_single_time_slice_is_pending():
    decision = triage_candidate(c(temporal_replication=MetadataStatus.NO))
    assert decision.status is TriageStatus.PENDING
    assert decision.reasons == ("single_time_slice_requires_non_temporal_endpoint_design",)


def test_registry_never_promotes_seen_response_candidates():
    registry = json.loads(
        (ROOT / "development/fresh_connectivity_candidate_registry_v0_8.json").read_text()
    )
    seen = [
        row for row in registry["candidates"]
        if row["response_result_seen_by_project"] == "yes"
    ]
    assert seen
    assert all(row["current_decision"] == "stop" for row in seen)
    assert registry["candidates"][0]["candidate_id"] == "usgs_pnw_montane_ponds_2012_2013"
    assert registry["candidates"][0]["current_decision"] == "pending"
