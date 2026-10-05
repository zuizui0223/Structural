from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def test_bala_pilot_contract_freezes_taxon_sampling_and_loss_rules():
    x=json.loads((ROOT/"development/bala_burned_pilot_contract_v1_137.json").read_text())
    assert x["sampling_endpoint"]["method"]=="pitfall only"
    assert x["taxon_eligibility"]["exclude_order"]==["Diptera"]
    assert "Formicidae" in x["taxon_eligibility"]["hymenoptera_rule"]
    assert x["taxon_eligibility"]["rule_change_after_pilot_access_authorized"] is False
    assert x["three_wave_transition"]["primary_pilot_route"]=="exactly one lost source between BALA1 and BALA2"
    assert x["three_wave_transition"]["source_loss_effect_size_or_association"]=="forbidden in pilot"

def test_bala_pilot_thresholds_are_frozen_before_access():
    x=json.loads((ROOT/"development/bala_burned_pilot_contract_v1_137.json").read_text())
    g=x["estimability_gate"]
    assert g["minimum_eligible_pilot_taxa"]==20
    assert g["minimum_exactly_one_loss_taxa"]==8
    assert g["minimum_t1_surviving_target_rows"]==20
    assert g["minimum_t2_contraction_rows"]==5
    assert g["minimum_t2_persistence_rows"]==10
    assert g["minimum_distinct_lost_source_islands"]==3
    assert "no threshold" in g["if_fail"]

def test_bala_pilot_script_computes_no_predictive_effect():
    s=(ROOT/"scripts/run_bala_burned_pilot_v1_137.py").read_text().lower()
    for forbidden in ("logloss","spearman","pearson","odds ratio","sklearn","statsmodels"):
        assert forbidden not in s
    assert '"effect_estimate_computed":false' in s.replace(" ","")
    assert '"leverage_outcome_association_computed":false' in s.replace(" ","")

def test_confirmatory_surface_is_not_input_to_pilot_runner():
    w=(ROOT/".github/workflows/bala-burned-pilot-v1_137.yml").read_text()
    command=w.split("Open burned pilot only and audit three-wave estimability",1)[1].split("Enforce burned-pilot evidence ceiling",1)[0]
    assert "confirmatory_occurrence_rows.sealed.tsv" not in command
    assert "pilot_occurrence_rows.tsv" in command
    assert "confirmatory_surface_semantically_opened" in w

def test_pilot_outputs_do_not_claim_evidence():
    x=json.loads((ROOT/"development/bala_burned_pilot_request_v1_137.json").read_text())
    assert x["pilot_occurrence_semantic_access_authorized"] is True
    assert x["confirmatory_occurrence_semantic_access_authorized"] is False
    assert x["source_leverage_effect_estimation_authorized"] is False
    assert x["one_shot"] is True
