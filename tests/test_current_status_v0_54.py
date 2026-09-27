from __future__ import annotations

import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/"development/zenodo_318_island_mammals_stress_result_v0_54.json"
REGISTRY=ROOT/"development/independent_stress_test_registry_v0_54.json"
SYNTHESIS=ROOT/"development/source_pool_handoff_cross_system_synthesis_v0_54.json"
STATUS=ROOT/"development/current_status_v0_54.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_stress_result_is_scored_and_primary_unsupported():
    x=load(RESULT)

    assert x["status"]=="HELDOUT_STRESS_SCORED_PRIMARY_HANDOFF_UNSUPPORTED"
    assert x["frozen_inputs"]["heldout_islands"]==244
    assert x["frozen_inputs"]["pilot_species_count"]==233
    assert x["response_firewall"]["heldout_occurrence_values_parsed"]==56852
    assert x["response_firewall"]["pilot_occurrence_values_parsed_during_heldout_scoring"]==0
    assert x["response_firewall"]["out_of_scope_occurrence_values_parsed"]==0
    assert x["response_firewall"]["nonfixed_species_occurrence_values_parsed"]==0

    p=x["primary"]
    assert p["prediction"]=="negative"
    assert p["point_estimate_extreme_minus_nonextreme"]==0.04545173576685289
    assert p["bootstrap_ci_95_low"]==-0.0031904317577055308
    assert p["bootstrap_ci_95_high"]==0.08835839946973478
    assert p["primary_supported"] is False


def test_descriptive_source_pool_gain_does_not_rescue_primary():
    x=load(RESULT)
    d=x["descriptive_secondary"]

    assert d["overall_mean_C_minus_R3_log_loss"]<0
    assert d["extreme_mean_C_minus_R3_log_loss"]<0
    assert d["nonextreme_mean_C_minus_R3_log_loss"]<0
    assert x["primary"]["primary_supported"] is False
    assert x["evidence_accounting"]["counts_as_fresh_confirmation"] is False
    assert x["rerun_authorized"] is False


def test_cross_system_synthesis_drops_universal_remoteness_switch():
    x=load(SYNTHESIS)

    assert x["systems"]["A_Islands"]["counts_as_confirmation"] is False
    assert x["systems"]["Indo_Pacific_atoll_plants"]["counts_as_confirmation"] is False
    assert x["systems"]["Zenodo_318_island_mammals"]["primary_supported"] is False
    assert "not supported as a universal switch" in x["ecological_update"]["rejected_as_universal"]
    assert x["next_fresh_hypothesis_boundary"]["may_not_mine_318_island_subgroups_to_rescue_handoff"] is True


def test_current_status_keeps_fresh_denominator_zero():
    x=load(STATUS)

    assert x["fresh_empirical_state"]["active_candidates"]==[]
    assert x["fresh_empirical_state"]["confirmatory_eligible_count"]==0
    assert x["fresh_empirical_state"]["live_confirmatory_queue_entries"]==0
    stress=x["completed_independent_stress_test"]
    assert stress["primary_supported"] is False
    assert stress["heldout_response_consumed"] is True
    assert stress["rerun_authorized"] is False
    assert stress["counts_as_fresh_confirmation"] is False


def test_registry_marks_stress_lane_complete_not_fresh():
    x=load(REGISTRY)
    assert x["fresh_confirmatory_denominator_count"]==0
    row=x["stress_tests"][0]
    assert row["heldout_response_accessed"] is True
    assert row["primary_supported"] is False
    assert row["counts_as_fresh_confirmation"] is False
    assert row["rerun_authorized"] is False


def test_v054_priority_forbids_stress_result_rescue_mining():
    status=load(STATUS)
    priority=load(ROOT/status["active_priority"]["path"])

    assert priority["status"] == (
        "stress_test_complete_primary_handoff_unsupported_no_active_fresh_system"
    )
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
    assert priority["completed_stress_test"]["primary_supported"] is False
    assert priority["completed_stress_test"]["heldout_response_consumed"] is True
    assert priority["pristine_hold"]["response_opened"] is False
    prohibited="\n".join(priority["prohibited"])
    assert "mine archipelagos, taxa, dispersal groups" in prohibited
    assert "promote the 318-island stress result" in prohibited
