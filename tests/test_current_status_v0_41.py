from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "development/current_status_v0_41.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_canonical_status_matches_registry_queue_and_freeze():
    status = load(STATUS)

    registry_cfg = status["authoritative_empirical_registry"]
    registry = load(ROOT / registry_cfg["path"])
    assert registry["status"] == registry_cfg["expected_status"]
    assert registry["active_empirical_candidates"] == registry_cfg[
        "expected_active_empirical_candidates"
    ]
    assert status["active_empirical_candidates"] == []

    queue_cfg = status["live_confirmatory_queue"]
    queue = load(ROOT / queue_cfg["path"])
    assert queue["entry_count"] == queue_cfg["expected_entry_count"] == 0
    assert queue["entries"] == []
    assert queue["confirmatory_response_authorized"] is False
    assert queue_cfg["confirmatory_response_authorized"] is False

    freeze_cfg = status["admission_infrastructure"]
    freeze = load(ROOT / freeze_cfg["path"])
    assert freeze["status"] == freeze_cfg["expected_status"]
    assert freeze["expected_live_queue_count_until_real_qualification"] == 0
    assert freeze["candidate_hunting_as_primary_objective"] is False
    assert freeze["ttf_is_active_dependency"] is False


def test_ttf_boundary_remains_later_and_cannot_select_or_rescue_structural():
    status = load(STATUS)
    ttf = status["ttf_boundary"]

    assert ttf["status"] == "later_independent_transferability_layer"
    assert ttf["may_select_structural_candidates"] is False
    assert ttf["may_rescue_failed_structural_systems"] is False
    assert ttf["may_count_burned_pilot_as_transfer_evidence"] is False
    assert ttf["empirical_denominator_shared_with_structural"] is False


def test_active_docs_do_not_restore_superseded_candidate_status():
    status = load(STATUS)
    forbidden = (
        "The priority-1 fresh candidate is now",
        "Rocky Mountain NP remains the only current pristine-fresh candidate",
        "The only current pristine-fresh candidate remains",
        "Rocky Mountain NP also remains pending",
        "The active Structural mainline is the v0.31–v0.33",
    )

    for relative in status["active_docs"]:
        text = (ROOT / relative).read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, f"{relative} contains stale status: {phrase}"


def test_historical_candidate_docs_are_explicitly_marked_historical():
    triage = (
        ROOT / "docs/FRESH_CONNECTIVITY_CANDIDATE_TRIAGE_V0_9.md"
    ).read_text(encoding="utf-8")
    pnw = (ROOT / "docs/PNW_STAGE2_RESULT_V0_21.md").read_text(encoding="utf-8")

    assert "> **Historical snapshot:**" in triage
    assert "Decision at v0.9 — superseded" in triage
    assert "Status note (superseded current-lane text)" in pnw
    assert "Active lane at v0.21 — superseded" in pnw


def test_current_status_points_to_v040_freeze_and_empty_queue():
    status = load(STATUS)

    assert status["admission_infrastructure"]["frozen_through"] == "v0.40"
    assert status["candidate_hunting_as_primary_objective"] is False
    assert (
        "new v0.31 protocol"
        in status["next_valid_scientific_event"]
    )
