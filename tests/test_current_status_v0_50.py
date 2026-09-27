from __future__ import annotations

import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/"development/current_status_v0_50.json"
RESULT=ROOT/"development/zenodo_318_island_mammals_preheldout_freeze_result_v0_50.json"
REGISTRY=ROOT/"development/independent_stress_test_registry_v0_50.json"
PRIORITY=ROOT/"development/structural_active_priority_v0_50.json"


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def test_v050_keeps_fresh_denominator_empty():
    s=load(STATUS)
    assert s["fresh_empirical_state"]["active_candidates"]==[]
    assert s["fresh_empirical_state"]["confirmatory_eligible_count"]==0
    assert s["fresh_empirical_state"]["live_confirmatory_queue_entries"]==0
    assert s["pristine_global_mammal_hold"]["raw_presence_absence_response_opened"] is False


def test_stress_pilot_and_preheldout_freeze_are_exact():
    r=load(RESULT)
    assert r["status"]=="HELDOUT_PREDICTIONS_FROZEN_BEFORE_OUTCOME_ACCESS"
    assert r["qualified_pilot"]["species_count"]==233
    assert r["qualified_pilot"]["estimable_blocks"]==65
    assert r["qualified_pilot"]["response_qualified_blocks"]==65
    assert r["qualified_pilot"]["heldout_occurrence_values_parsed"]==0
    assert r["model_freeze"]["heldout_prediction_rows"]==56852
    assert r["model_freeze"]["heldout_prediction_surface_sha256"]==(
        "a5fe8326172e39ca4cf1d3d7afe9b9bd679076ffc10ec08aaa7c2da2fddeaad9"
    )
    assert r["model_freeze"]["R3_irls_iterations"]==9
    assert r["model_freeze"]["C_irls_iterations"]==9


def test_no_heldout_effect_exists_before_scoring():
    r=load(RESULT)
    ceiling=r["evidence_ceiling"]
    assert ceiling["heldout_occurrence_values_opened"]==0
    assert ceiling["heldout_log_loss_computed"] is False
    assert ceiling["primary_effect_computed"] is False
    assert ceiling["effect_size"] is None
    assert ceiling["prediction_score"] is None
    assert ceiling["pilot_coefficient_interpretation_authorized"] is False
    assert r["heldout_response_authorized"] is False


def test_stress_lane_cannot_become_fresh_confirmation():
    reg=load(REGISTRY)
    p=load(PRIORITY)
    row=reg["stress_tests"][0]
    assert reg["fresh_confirmatory_denominator_count"]==0
    assert row["counts_as_fresh_confirmation"] is False
    assert row["heldout_occurrence_accessed"] is False
    assert p["fresh_active_empirical_candidate"] is None
    assert p["fresh_confirmatory_eligible_count"]==0
    assert any("refit" in x.lower() for x in p["prohibited"])
