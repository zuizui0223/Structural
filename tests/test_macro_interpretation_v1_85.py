from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT/path).read_text())

def test_v185_prediction_behavior_freeze_exact_values():
    x=load("development/global_mammals_prediction_behavior_freeze_v1_85.json")
    assert x["source_execution"]["artifact_id"]==11139081593
    assert x["effect_scale"]["block_weighted"]["C_minus_R3"]==-0.0018141589038615496
    assert x["effect_scale"]["block_weighted"]["relative_logloss_reduction"]==0.03770988990745495
    assert x["outcome_asymmetry"]["absence"]["C_minus_R3"]==-0.005801435444703651
    assert x["outcome_asymmetry"]["presence"]["C_minus_R3"]==0.11643800501898788
    assert x["outcome_asymmetry"]["class_balanced_equal_block_C_minus_R3"]==0.04941170770534662

def test_v185_prediction_behavior_is_not_sentinel_artifact():
    x=load("development/global_mammals_prediction_behavior_freeze_v1_85.json")
    g=x["graph_empty_support"]
    assert g["empty_cells"]==255071
    assert g["nonempty_cells"]==70883
    assert g["nonempty_cell_mean_C_minus_R3"] < g["empty_cell_mean_C_minus_R3"]
    assert g["block_empty_fraction_vs_C_minus_R3_spearman_rho"]==0.2827513281311377
    assert "sentinel" in g["interpretation"]

def test_v185_ranking_context_is_mixed_not_presence_claim():
    x=load("development/global_mammals_prediction_behavior_freeze_v1_85.json")
    r=x["ranking_context"]
    assert r["C_ROC_AUC"] > r["R3_ROC_AUC"]
    assert r["C_average_precision"] < r["R3_average_precision"]
    assert "C improves presence detection" in x["interpretation_guardrails"]["forbidden"]

def test_v185_synthesis_keeps_primary_and_balanced_guardrail_separate():
    x=load("development/macro_dual_isolation_synthesis_v1_85.json")
    assert x["global_mammals"]["primary_C_minus_R3"]==-0.0018141589038615496
    assert x["global_mammals"]["prediction_behavior"]["class_balanced_equal_block_C_minus_R3"]==0.04941170770534662
    assert "C improves presence detection" in x["claim_boundary"]["forbidden"]
    assert x["counts_as_new_confirmatory_evidence"] is False

def test_v185_future_hypothesis_predeclares_opportunity_vs_constraint():
    x=load("development/prospective_source_network_contrast_window_hypothesis_v1_85.json")
    assert x["status"]=="FUTURE_ONLY_INDEPENDENT_RESPONSE_SEALED_HYPOTHESIS"
    assert "opportunity_signature" in x["competing_interpretations"]
    assert "constraint_signature" in x["competing_interpretations"]
    assert x["counts_as_current_evidence"] is False

def test_v185_status_has_no_new_response_queue():
    x=load("development/current_status_v1_85.json")
    assert x["fresh_empirical_state"]["active_candidates"]==[]
    assert x["fresh_empirical_state"]["live_confirmatory_queue_entries"]==0
    assert x["global_mammal_macro"]["prediction_behavior"]["presence_C_minus_R3"]>0
    assert x["global_mammal_macro"]["prediction_behavior"]["absence_C_minus_R3"]<0

def test_v185_manuscript_states_class_imbalance_limitation():
    s=(ROOT/"manuscript/macro_dual_isolation_mammal_v1_85.md").read_text()
    assert "1.724%" in s
    assert "class-balanced" in s
    assert "true-presence log loss" in s
    assert "ROC-AUC" in s
    assert "empty-source sentinel" in s
    assert "occupancy-constraint information" in s
