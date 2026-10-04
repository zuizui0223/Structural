import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def test_v124_candidate_triage_keeps_confirmation_empty():
    x = load("development/source_loss_temporal_candidate_triage_v1_124.json")
    assert x["status"].startswith("METADATA_ONLY")
    assert x["preferred_confirmatory_candidate"] is None
    assert x["confirmatory_candidate_status"] == "NONE_QUALIFIED_YET"
    assert x["response_values_opened_for_source_leverage_analysis"] is False
    assert x["source_leverage_effects_computed"] == 0

def test_v124_eider_is_retrospective_not_fresh():
    x = load("development/source_loss_temporal_candidate_triage_v1_124.json")
    e = next(c for c in x["candidates"] if c["candidate_id"] == "finnish_common_eider_archipelago_1997_2020")
    assert e["decision"] == "QUALIFY_RETROSPECTIVE_SCHEMA_AUDIT"
    assert e["firewall_status"]["candidate_response_direction_broadly_public"] is True
    assert e["firewall_status"]["pristine_fresh_confirmatory_eligible"] is False
    assert x["preferred_immediate_stress_test"]["may_count_as_confirmation"] is False

def test_v124_presence_only_ebird_does_not_define_absence():
    x = load("development/source_loss_temporal_candidate_triage_v1_124.json")
    e = next(c for c in x["candidates"] if c["candidate_id"] == "global_ebird_islands_2002_2019")
    assert e["decision"] == "HOLD_ENDPOINT"
    assert "absence" in e["decision_reason"].lower() or "zero" in e["decision_reason"].lower()

def test_v124_aislands_cannot_reconfirm_structural_discovery():
    x = load("development/source_loss_temporal_candidate_triage_v1_124.json")
    a = next(c for c in x["candidates"] if c["candidate_id"] == "a_islands_temporal_plants")
    assert a["decision"] == "STOP_AS_INDEPENDENT_CONFIRMATION"
