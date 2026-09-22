from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "development/fresh_connectivity_candidate_registry_v0_9.json"


def test_v09_registry_prioritizes_rmnp_without_qualifying_it():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = registry["candidates"]
    assert rows[0]["candidate_id"] == "usgs_rmnp_amphibian_surveys_1986_2022"
    assert rows[0]["priority"] == 1
    assert rows[0]["current_decision"] == "pending"
    assert rows[0]["response_result_seen_by_project"] == "no"
    assert rows[0]["connectivity_question_already_published"] == "no"


def test_rmnp_pending_reasons_are_physical_schema_only():
    row = json.loads(REGISTRY.read_text(encoding="utf-8"))["candidates"][0]
    assert row["current_reasons"] == [
        "unknown_coordinates_or_geometry_documented",
        "unknown_outcome_file_separable",
    ]
    assert row["operator_candidate"] == "whole_individual_dispersal_between_breeding_waterbodies"


def test_stop_candidates_remain_stop():
    rows = json.loads(REGISTRY.read_text(encoding="utf-8"))["candidates"]
    stopped = {row["candidate_id"]: row for row in rows if row["current_decision"] == "stop"}
    assert "great_lakes_frog_2011_2023" in stopped
    assert "hungary_amphibian_100_ponds_2023" in stopped
    assert all(row["response_result_seen_by_project"] == "yes" for row in stopped.values())


def test_next_action_forbids_response_access():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    action = registry["next_action"]
    assert action["primary_candidate"] == "usgs_rmnp_amphibian_surveys_1986_2022"
    assert action["response_values_may_be_opened"] is False
