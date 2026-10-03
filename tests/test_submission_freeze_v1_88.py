from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT/path).read_text())

def test_v188_scientific_analysis_is_frozen_for_submission():
    x=load("development/current_status_v1_88.json")
    s=x["scientific_analysis_state"]
    assert s["status"]=="FROZEN_FOR_SUBMISSION_PACKAGING"
    assert s["new_response_access_authorized"] is False
    assert s["new_same_data_mechanism_search_authorized"] is False
    assert s["primary_estimand_change_authorized"] is False
    assert s["species_block_bioregion_removal_authorized"] is False

def test_v188_primary_and_prediction_behavior_numbers_are_locked():
    x=load("development/current_status_v1_88.json")["global_mammal_macro"]
    assert x["islands"]==5401
    assert x["heldout_islands"]==4126
    assert x["focal_species"]==79
    assert x["heldout_blocks"]==168
    assert x["primary_C_minus_R3"]==-0.0018141589038615496
    assert x["block_weighted_relative_logloss_reduction"]==0.03770988990745495
    assert x["absence_C_minus_R3"]==-0.005801435444703651
    assert x["presence_C_minus_R3"]==0.11643800501898788
    assert x["class_balanced_equal_block_C_minus_R3"]==0.04941170770534662
    assert x["graph_nonempty_C_minus_R3"]==-0.014109851236894143
    assert x["graph_empty_C_minus_R3"]==-0.0007992552987686575

def test_v188_isolation_attenuation_is_not_empty_support_duplicate():
    x=load("development/global_mammals_isolation_empty_support_audit_freeze_v1_88.json")
    raw=x["result"]["raw"]
    within=x["result"]["within_bioregion_centered"]
    assert raw["rho_isolation_vs_graph_empty_fraction"]==0.04713918029646398
    assert raw["rho_isolation_vs_C_minus_R3"]==0.28743057515243015
    assert raw["partial_rho_isolation_vs_C_minus_R3_given_graph_empty_fraction"]==0.2860809953580879
    assert within["rho_isolation_vs_graph_empty_fraction"]==0.006140461653862857
    assert within["rho_isolation_vs_C_minus_R3"]==0.2278413095720483
    assert within["partial_rho_isolation_vs_C_minus_R3_given_graph_empty_fraction"]==0.227838815483369
    assert x["guardrails"]["causal_mediation_claimed"] is False
    assert x["guardrails"]["counts_as_confirmatory_evidence"] is False

def test_v188_prediction_behavior_figure_is_exactly_frozen():
    x=load("development/macro_prediction_behavior_figure_freeze_v1_88.json")
    assert x["source_execution"]["artifact_id"]==11259686592
    assert x["source_execution"]["artifact_digest"]=="sha256:4f3276751603d66d3228aa722c4d0332806566fcb1d7c41b51871c0ec933b33a"
    assert x["files"]["figS2_prediction_behavior.png"]["sha256"]=="a38635b69dcf53fb54403b2c070e6dac9989e17afb3d4dea2fd40dc101046556"
    assert x["files"]["figS2_prediction_behavior.svg"]["sha256"]=="e728e9149bebc87405e127567689bb5ad80067582db7c624db608727ee455427"
    assert x["new_response_accessed"] is False

def test_v188_submission_assets_keep_evidence_boundaries_explicit():
    x=load("development/current_status_v1_88.json")
    assert x["global_mammal_macro"]["evidence_status"]=="nonconfirmatory exploratory"
    assert x["cross_system_context"]["GIFT_fresh"]=="terminal unscored fresh attempt"
    assert "descriptive concordance" in x["cross_system_context"]["GIFT_endpoint_available"]
    assert x["cross_system_context"]["boreal_19island_beetles"]=="valid fresh local non-support"
    c=x["current_ecological_synthesis"]
    assert c["causal_mechanism_claim_authorized"] is False
    assert c["fresh_global_confirmation_authorized"] is False
    assert c["cross_taxon_confirmation_authorized"] is False

def test_v188_manuscript_states_asymmetry_and_confound_defense():
    s=(ROOT/"manuscript/macro_dual_isolation_mammal_v1_88.md").read_text()
    assert "v1.88 submission-freeze candidate" in s
    assert "class-balanced block diagnostic" in s
    assert "Supplementary Fig. S2" in s
    assert "Current isolation and graph-empty fraction were nearly uncorrelated" in s
    assert "partial Spearman association" in s
    assert "nonconfirmatory exploratory" in s
    assert "fresh global confirmation" in s
    assert "two-taxon replication" in s

def test_v188_priority_prohibits_new_same_data_science():
    x=load("development/structural_active_priority_v1_88.json")
    assert x["status"]=="submission_packaging_only_scientific_analysis_frozen"
    prohibited="\n".join(x["do_not"])
    assert "open any new biological response" in prohibited
    assert "new same-data mechanism or subgroup searches" in prohibited
    assert "change the natural-prevalence primary" in prohibited
    assert "promote exploratory mammal or GIFT evidence to fresh confirmation" in prohibited

def test_v188_readiness_separates_submission_tasks_from_science():
    s=(ROOT/"manuscript/submission/macro_dual_isolation_submission_readiness_v1_88.md").read_text()
    assert "**Analysis is frozen for submission packaging.**" in s
    assert "These are submission tasks, not reasons to reopen the analysis" in s
    assert "select the first journal" in s
    assert "confirm final author list" in s
    assert "archive figures before GitHub Actions artifact expiry" in s
