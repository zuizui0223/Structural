from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_mammal_diagnostics_freeze_is_exact_and_nonrescuing():
    x=json.loads((ROOT/"development/global_mammals_exploratory_diagnostics_freeze_v1_79.json").read_text())
    assert x["source_execution"]["artifact_id"]==11130602935
    assert x["artifact_files"]["diagnostics_result.json"]["sha256"]=="9fbbcf41ffe6c4c9b52802b05fc8192d2226018e428e2f7413484d4c56d90b0d"
    assert x["geographic_breadth"]["negative_blocks"]==108
    assert x["geographic_breadth"]["bioregions_with_negative_mean"]==10
    assert x["interpretation_guardrails"]["counts_as_confirmatory_evidence"] is False

def test_isolation_direction_matches_318_context_without_pooled_inference():
    x=json.loads((ROOT/"development/global_mammals_exploratory_diagnostics_freeze_v1_79.json").read_text())
    assert x["external_isolation_context"]["Current_isolation"]["spearman_rho_equal_block"]>0
    assert x["external_isolation_context"]["Current_isolation"]["spearman_rho_within_bioregion_centered"]>0
    assert x["cross_system_mammal_context"]["historical_318_stress_test"]["extreme_minus_nonextreme"]>0
    assert x["cross_system_mammal_context"]["pooled_inference"] is False

def test_working_hypothesis_is_posthoc_and_noncausal():
    x=json.loads((ROOT/"development/global_mammals_exploratory_diagnostics_freeze_v1_79.json").read_text())
    assert x["ecological_interpretation"]["posthoc"] is True
    assert x["ecological_interpretation"]["causal_mechanism_claimed"] is False
    assert x["interpretation_guardrails"]["may_change_primary_status"] is False
