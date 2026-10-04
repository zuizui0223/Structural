import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def test_v124_candidate_triage_keeps_confirmation_empty():
    x = load("development/source_loss_temporal_candidate_triage_v1_124.json")
    assert x["preferred_confirmatory_candidate"] is None
    assert x["confirmatory_candidate_status"] == "NONE_QUALIFIED_YET"
    assert x["response_values_opened_for_source_leverage_analysis"] is False
    assert x["source_leverage_effects_computed"] == 0

def test_v124_bala_is_preferred_response_unopened_preintake():
    x = load("development/source_loss_temporal_candidate_triage_v1_124.json")
    b = next(c for c in x["candidates"] if c["candidate_id"] == "azores_bala_arthropods_1997_2022")
    assert b["decision"] == "QUALIFY_RESPONSE_UNOPENED_PREINTAKE"
    assert b["metadata"]["three_wave_core_design"] is True
    assert x["preferred_response_unopened_preintake"]["candidate_id"] == b["candidate_id"]
    assert x["preferred_response_unopened_preintake"]["confirmatory_eligible_now"] is False

def test_v124_slam_is_secondary_preintake():
    x = load("development/source_loss_temporal_candidate_triage_v1_124.json")
    assert x["secondary_response_unopened_preintake"]["candidate_id"] == "azores_slam_arthropods_2012_2021"
    assert x["secondary_response_unopened_preintake"]["confirmatory_eligible_now"] is False

def test_v124_eider_remains_retrospective_only():
    x = load("development/source_loss_temporal_candidate_triage_v1_124.json")
    e = next(c for c in x["candidates"] if c["candidate_id"] == "finnish_common_eider_archipelago_1997_2020")
    assert e["decision"] == "QUALIFY_RETROSPECTIVE_SCHEMA_AUDIT"
    assert e["firewall_status"]["pristine_fresh_confirmatory_eligible"] is False
    assert x["preferred_immediate_retrospective_stress_test"]["may_count_as_confirmation"] is False

def test_v124_aislands_cannot_reconfirm_discovery():
    x = load("development/source_loss_temporal_candidate_triage_v1_124.json")
    a = next(c for c in x["candidates"] if c["candidate_id"] == "a_islands_temporal_plants")
    assert a["decision"] == "STOP_AS_INDEPENDENT_CONFIRMATION"
