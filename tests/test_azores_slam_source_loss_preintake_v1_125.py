import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def test_azores_v125_is_event_first_and_response_unopened():
    x = load("development/azores_slam_source_loss_preintake_v1_125.json")
    assert x["status"] == "RESPONSE_UNOPENED_EVENT_FIRST_PREINTAKE"
    assert x["evidence_status"]["source_leverage_effect_computed"] is False
    assert x["evidence_status"]["focal_occurrence_values_opened_by_structural"] is False
    assert x["evidence_status"]["confirmatory_eligible"] is False
    assert "sampling geometry and effort" in x["file_role_firewall"]["event_core_role"]
    assert any("Occurrence extension taxon identity" == s for s in x["file_role_firewall"]["must_remain_unparsed"])

def test_azores_v125_freezes_spider_completeness_boundary():
    x = load("development/azores_slam_source_loss_preintake_v1_125.json")
    t = x["taxonomic_completeness_firewall"]
    assert t["primary_universe_rule"].startswith("Araneae are excluded")
    assert t["universe_must_be_frozen_before_occurrence_parse"] is True

def test_azores_v125_does_not_pick_years_from_occurrence():
    x = load("development/azores_slam_source_loss_preintake_v1_125.json")
    a = x["event_only_admission_audit"]
    assert a["provisional_three_time_windows"] == "NOT_FROZEN"
    assert "Event rows only" in a["coverage_rule"]
    assert "earliest eligible window" in a["window_selection_rule_to_freeze_after_event_audit"]
    assert a["effect_estimation_allowed"] is False

def test_azores_v125_preserves_temporal_self_anchor_rule():
    x = load("development/azores_slam_source_loss_preintake_v1_125.json")
    assert x["future_endpoint_semantics"]["self_anchor_exclusion_required"] is True
    assert x["future_endpoint_semantics"]["three_time_order_required"] is True
