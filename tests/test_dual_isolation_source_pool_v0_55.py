from __future__ import annotations

import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
HYP=ROOT/"development/prospective_dual_isolation_source_pool_hypothesis_v0_55.json"
STATUS=ROOT/"development/current_status_v0_55.json"
PRIORITY=ROOT/"development/structural_active_priority_v0_55.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v055_replaces_remote_switch_only_for_future_tests():
    x=load(HYP)

    assert x["status"]=="next_generation_fresh_hypothesis_not_yet_tested"
    assert x["supersedes_for_future_fresh_tests"] == (
        "development/prospective_source_pool_handoff_hypothesis_v0_1.json"
    )
    assert x["prior_results_may_count_as_confirmation"] is False
    assert x["current_fresh_confirmatory_systems"]==[]
    assert x["confirmatory_response_authorized"] is False


def test_dual_isolation_primary_is_overall_source_information_not_q75_interaction():
    x=load(HYP)

    primary=x["primary_prediction"]
    assert primary["name"]=="internal_source_isolation_is_nonredundant"
    assert primary["favourable_direction"]=="negative"
    assert "cluster-bootstrap 95% upper confidence limit < 0" in primary["support_rule"]
    assert primary["external_isolation_interaction_required_for_support"] is False

    isolation=x["external_isolation_rule"]
    assert isolation["universal_directional_interaction_prediction"] is None
    assert "do not require or rescue" in isolation["forbidden_primary"]


def test_future_reference_separates_external_and_internal_isolation():
    x=load(HYP)
    ladder=x["required_reference_ladder"]

    assert "external current isolation" in ladder["R1_add"]
    assert "response-independent generic archipelago permeability/network context" in ladder["R2_add"]
    assert "training-only global occupancy breadth" in ladder["R3_add"]
    assert any("species-conditioned internal source-pool continuity" in s for s in ladder["C_add"])


def test_secondary_moderators_are_prospective_and_cannot_rescue_primary():
    x=load(HYP)
    mods=x["prospective_moderators"]

    assert mods["archipelago_permeability"]["may_rescue_failed_primary"] is False
    assert mods["dispersal_mode"]["may_rescue_failed_primary"] is False
    assert mods["source_saturation"]["may_rescue_failed_primary"] is False
    assert "before any response access" in mods["archipelago_permeability"]["required_freeze"]
    assert "external taxonomy/trait source" in mods["dispersal_mode"]["source"]


def test_v055_status_keeps_fresh_denominator_zero_and_5592_sealed():
    status=load(STATUS)

    assert status["fresh_empirical_state"]["active_candidates"]==[]
    assert status["fresh_empirical_state"]["confirmatory_eligible_count"]==0
    assert status["fresh_empirical_state"]["live_confirmatory_queue_entries"]==0
    assert status["pristine_global_mammal_hold"]["response_opened"] is False
    assert status["next_generation_hypothesis"]["remote_amplification_is_required"] is False


def test_v055_priority_prohibits_rescue_mining():
    p=load(PRIORITY)

    assert p["fresh_active_empirical_candidate"] is None
    assert p["fresh_confirmatory_eligible_count"]==0
    assert p["completed_stress_test"]["may_be_mined_for_v0_55_support"] is False
    prohibited="\n".join(p["prohibited"])
    assert "subgroup-mine" in prohibited
    assert "universal primary" in prohibited
    assert "after response access" in prohibited
