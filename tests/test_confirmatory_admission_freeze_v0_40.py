from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "development/confirmatory_admission_freeze_v0_40.json"
QUEUE = ROOT / "development/confirmatory_admission_queue_v0_38.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_35.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_freeze_points_to_the_active_empty_queue():
    freeze = load(FREEZE)
    queue = load(QUEUE)

    assert freeze["status"] == "frozen_gate_infrastructure"
    assert freeze["live_queue"] == "development/confirmatory_admission_queue_v0_38.json"
    assert queue["entry_count"] == 0
    assert queue["entries"] == []
    assert freeze["expected_live_queue_count_until_real_qualification"] == 0


def test_frozen_chain_contains_all_active_gate_layers():
    freeze = load(FREEZE)
    chain = " ".join(freeze["frozen_chain"])

    for version in ("v0.31", "v0.32", "v0.39", "v0.38", "v0.37", "v0.33"):
        assert version in chain

    assert freeze["successful_gate_action"] == "freeze_confirmatory_protocol_only"
    assert freeze["confirmatory_response_authorized_by_admission"] is False
    assert freeze["pilot_predictive_denominator_contribution"] == 0


def test_freeze_preserves_gate_first_priority_and_ttf_separation():
    freeze = load(FREEZE)
    priority = load(PRIORITY)

    assert freeze["candidate_hunting_as_primary_objective"] is False
    assert freeze["ttf_is_active_dependency"] is False
    assert priority["priority_rules"]["new_candidate_hunting_as_primary_objective"] is False
    assert priority["priority_rules"]["ttf_handoff_is_active_dependency"] is False


def test_failed_pilot_cannot_be_retuned_under_freeze():
    freeze = load(FREEZE)
    forbidden = " ".join(freeze["forbidden_until_new_protocol_version"])

    assert "lower an estimability threshold after pilot failure" in forbidden
    assert "change endpoint semantics after pilot failure" in forbidden
    assert "change heldout design after pilot failure" in forbidden
    assert "use burned-pilot outcomes as predictive evidence" in forbidden
