from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def test_v132_is_explicitly_corrected_not_reinterpreted_as_failure():
    x=json.loads((ROOT/"development/bala_protocol_grammar_stop_v1_133.json").read_text())
    assert x["status"]=="V132_AUDIT_SEMANTIC_ASSUMPTION_CORRECTED_RESPONSE_UNOPENED"
    assert x["scientific_consequence"]["occurrence_opened"] is False
    assert x["scientific_consequence"]["source_loss_effect_computed"] is False
    assert x["scientific_consequence"]["v132_may_not_define_core_denominator"] is True

def test_pitfall_core_is_response_independent_and_methodologically_motivated():
    x=json.loads((ROOT/"development/bala_pitfall_core_audit_contract_v1_133.json").read_text())
    assert x["event_semantics"]["pitfall_position_range"]==[1,30]
    assert x["event_semantics"]["expected_positions_per_site_phase"]==30
    assert x["publication_basis"]["beating_protocol"]=="10 samples from each of the three most common native tree species"
    assert "do not use the 4929 total to delete pitfall events" in x["anti_selection"]
    assert any("beating events are excluded from the proposed primary method for comparability" in z for z in x["anti_selection"])

def test_pitfall_audit_does_not_select_surveyed_zero_threshold():
    x=json.loads((ROOT/"development/bala_pitfall_core_audit_contract_v1_133.json").read_text())
    assert x["decision_rule"]["final_surveyed_zero_threshold_selected_here"] is False
    assert x["response_boundary"]["confirmatory_eligible_after_this_audit"] is False

def test_workflow_keeps_occurrence_closed():
    s=(ROOT/".github/workflows/bala-pitfall-core-v1_133.yml").read_text()
    assert "occurrence_extension_semantically_opened" in s
    assert "taxon_occurrence_values_opened" in s
    assert "source_loss_effects_computed" in s
    assert "audit_bala_pitfall_core_v1_133.py" in s
