from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_pilot_gate_thresholds_are_frozen_before_semantic_access():
    x=json.loads((ROOT/"development/bala_pilot_estimability_contract_v1_137.json").read_text())
    g=x["advance_gate"]
    assert g["minimum_taxonomically_eligible_pilot_taxa"]==30
    assert g["minimum_exactly_one_source_loss_taxa"]==5
    assert g["minimum_exactly_one_loss_target_rows"]==20
    assert g["minimum_t2_contractions_across_exactly_one_loss_targets"]==5
    assert g["minimum_t2_persistences_across_exactly_one_loss_targets"]==5
    assert g["all_conditions_required"] is True

def test_taxonomic_scope_is_predeclared_and_same_for_confirmation():
    x=json.loads((ROOT/"development/bala_pilot_estimability_contract_v1_137.json").read_text())
    t=x["taxonomic_scope_rule"]
    assert t["exclude_order"]==["Diptera"]
    assert "Formicidae" in t["hymenoptera_rule"]
    assert t["exclude_if_taxonomy_mentions"]==["Acari","Collembola"]
    assert t["same_rule_must_later_apply_to_confirmatory_taxa"] is True
    assert t["pilot_outcomes_may_not_change_rule"] is True

def test_pilot_runner_never_computes_leverage_or_effect():
    s=(ROOT/"scripts/run_bala_pilot_estimability_v1_137.py").read_text()
    assert "source_leverage_values_computed" in s
    assert "candidate_minus_reference_effects_computed" in s
    assert "graph_distance" not in s
    assert "kernel_lambda" not in s
    assert "C_minus_R2" not in s

def test_pilot_workflow_never_passes_confirmatory_surface_to_runner():
    s=(ROOT/".github/workflows/bala-pilot-estimability-v1_137.yml").read_text()
    cmd=s.split("python scripts/run_bala_pilot_estimability_v1_137.py",1)[1].split("Enforce no pilot effect",1)[0]
    assert "confirmatory_occurrence_rows.sealed.tsv" not in cmd
    assert "pilot_occurrence_rows.tsv" in cmd
    assert "source_leverage_values_computed" in s
    assert "confirmatory_occurrence_values_opened" in s

def test_pilot_is_estimability_not_evidence():
    x=json.loads((ROOT/"development/bala_pilot_estimability_contract_v1_137.json").read_text())
    e=x["evidence_boundary"]
    assert e["pilot_contributes_predictive_effect_evidence"] is False
    assert e["pilot_source_loss_effect_estimate_authorized"] is False
    assert e["confirmatory_occurrence_semantic_access_authorized"] is False
    assert e["counts_as_empirical_support_or_non_support"] is False
