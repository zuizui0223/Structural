from __future__ import annotations

import json
from pathlib import Path

from structural import (
    PhysicalSchemaResolution,
    PhysicalSchemaStatus,
    evaluate_physical_schema_resolution,
)

ROOT = Path(__file__).resolve().parents[1]


def test_complete_physical_resolution_advances():
    decision = evaluate_physical_schema_resolution(
        PhysicalSchemaResolution(
            candidate_id="x",
            source_landing_resolved=True,
            file_level_distribution_resolved=True,
            geometry_verified=True,
            response_firewall_verified=True,
            response_values_read=False,
        )
    )
    assert decision.status is PhysicalSchemaStatus.ADVANCE
    assert decision.reasons == ()


def test_doi_landing_without_files_remains_pending():
    decision = evaluate_physical_schema_resolution(
        PhysicalSchemaResolution(
            candidate_id="x",
            source_landing_resolved=True,
            file_level_distribution_resolved=False,
            geometry_verified=False,
            response_firewall_verified=False,
            response_values_read=False,
        )
    )
    assert decision.status is PhysicalSchemaStatus.PENDING
    assert "file_level_distribution_unresolved" in decision.reasons
    assert "geometry_not_physically_verified" in decision.reasons
    assert "response_firewall_not_verified" in decision.reasons


def test_early_response_access_is_terminal_stop():
    decision = evaluate_physical_schema_resolution(
        PhysicalSchemaResolution(
            candidate_id="x",
            source_landing_resolved=True,
            file_level_distribution_resolved=True,
            geometry_verified=False,
            response_firewall_verified=False,
            response_values_read=True,
        )
    )
    assert decision.status is PhysicalSchemaStatus.STOP
    assert decision.reasons == ("response_values_read_before_protocol_freeze",)


def test_usgs_registry_keeps_both_candidates_pending():
    registry = json.loads(
        (ROOT / "development/usgs_metadata_resolution_v0_10.json").read_text()
    )
    rows = registry["candidates"]
    assert {row["candidate_id"] for row in rows} == {
        "usgs_pnw_montane_ponds_2012_2013",
        "usgs_rmnp_amphibian_surveys_1986_2022",
    }
    assert all(row["decision"] == "pending_physical_schema" for row in rows)
    assert all(row["response_values_read"] is False for row in rows)


def test_pnw_dcat_record_does_not_claim_file_level_resolution():
    registry = json.loads(
        (ROOT / "development/usgs_metadata_resolution_v0_10.json").read_text()
    )
    pnw = next(
        row for row in registry["candidates"]
        if row["candidate_id"] == "usgs_pnw_montane_ponds_2012_2013"
    )
    assert pnw["catalog_distribution_summary"]["resource_count"] == 2
    assert pnw["catalog_distribution_summary"]["file_level_download_urls_present"] is False
    assert pnw["file_level_distribution_resolved"] is False
