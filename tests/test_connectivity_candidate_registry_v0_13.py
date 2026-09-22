from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "development/connectivity_candidate_registry_v0_13.json"


def test_only_rmnp_remains_in_pristine_fresh_lane():
    x = json.loads(REGISTRY.read_text())
    pristine = x["pristine_fresh_lane"]
    assert len(pristine) == 1
    assert pristine[0]["candidate_id"] == "usgs_rmnp_amphibian_surveys_1986_2022"
    assert pristine[0]["evidence_class"] == "pristine_fresh_pending"


def test_pnw_is_permanently_design_exposed_not_pristine():
    x = json.loads(REGISTRY.read_text())
    pnw = x["response_unopened_design_exposed_lane"][0]
    assert pnw["candidate_id"] == "usgs_pnw_montane_ponds_2012_2013"
    assert pnw["counts_as_pristine_fresh_evidence"] is False
    assert pnw["historical_analysis_code_seen_by_project"] is True
    assert pnw["current_decision"] == "advance_to_protocol_freeze_with_design_exposure_caveat"


def test_evidence_class_only_moves_downward():
    x = json.loads(REGISTRY.read_text())
    assert "evidence class may only move downward after additional exposure, never upward" in x["invariants"]
    assert "PNW can never be reclassified as pristine fresh" in x["invariants"]
