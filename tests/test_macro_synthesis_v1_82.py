from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT/path).read_text())

def test_v182_synthesis_keeps_evidence_classes_separate():
    x=load("development/macro_dual_isolation_synthesis_v1_82.json")
    assert x["systems"]["global_5401_mammals"]["evidence_class"]=="nonconfirmatory exploratory macro analysis"
    assert x["systems"]["GIFT_plants"]["fresh_result_available"] is False
    assert x["systems"]["GIFT_plants"]["endpoint_available_retained_entities"]==118
    assert x["systems"]["GIFT_plants"]["endpoint_available_retained_blocks"]==18
    assert "two-taxon confirmatory replication" in x["claim_boundary"]["forbidden"]

def test_v182_global_mammal_numbers_are_frozen():
    x=load("development/macro_dual_isolation_synthesis_v1_82.json")["systems"]["global_5401_mammals"]
    assert x["islands"]==5401
    assert x["heldout_islands"]==4126
    assert x["focal_species"]==79
    assert x["heldout_blocks"]==168
    assert x["negative_blocks"]==108
    assert x["negative_mean_bioregions"]==10
    assert x["negative_species"]==64
    assert x["Current_isolation_spearman_equal_block"]==0.28743057515243015
    assert x["pilot_prevalence_vs_species_C_minus_R3_spearman"]==0.27643959301238685

def test_v182_species_breadth_freeze_is_posthoc_nonrescuing():
    x=load("development/global_mammals_species_breadth_diagnostics_freeze_v1_82.json")
    assert x["result"]["species"]==79
    assert x["result"]["negative_species"]==64
    assert x["result"]["pilot_prevalence_vs_C_minus_R3_spearman_rho"]==0.27643959301238685
    assert x["ecological_interpretation"]["unimodality_claim_authorized"] is False
    assert x["interpretation_guardrails"]["counts_as_confirmatory_evidence"] is False

def test_v182_gift_exploratory_freeze_records_severe_attrition():
    x=load("development/gift_exploratory_availability_freeze_v1_82.json")
    a=x["endpoint_availability"]
    assert a["frozen_confirmatory_entities"]==404
    assert a["retained_entities"]==118
    assert a["excluded_entities"]==286
    assert a["excluded_entities_no_available_list"]==9
    assert a["excluded_entities_available_list_but_zero_accepted_high_confidence_native_rows"]==277
    assert a["retained_blocks"]==18
    assert x["interpretation_guardrails"]["fresh_status_restored"] is False
    assert x["interpretation_guardrails"]["availability_selection_is_severe"] is True

def test_v182_current_status_has_no_live_fresh_queue():
    x=load("development/current_status_v1_82.json")
    assert x["fresh_empirical_state"]["active_candidates"]==[]
    assert x["fresh_empirical_state"]["live_confirmatory_queue_entries"]==0
    assert x["fresh_empirical_state"]["fresh_primary_supported_count"]==0
    assert x["fresh_empirical_state"]["fresh_primary_not_supported_count"]==1
    assert x["queued_nonconfirmatory_work"]==[]

def test_v182_future_hypothesis_is_future_only_and_not_unimodality_claim():
    x=load("development/prospective_source_network_contrast_window_hypothesis_v1_82.json")
    assert x["status"]=="FUTURE_ONLY_INDEPENDENT_RESPONSE_SEALED_HYPOTHESIS"
    assert x["counts_as_current_evidence"] is False
    assert "do not require or claim formal unimodality" in x["guardrails"][2]

def test_manuscript_has_required_claim_boundary():
    s=(ROOT/"manuscript/macro_dual_isolation_mammal_v1_82.md").read_text()
    assert "64 of 79 focal species" in s
    assert "118 of 404 confirmatory islands" in s
    assert "descriptive concordance" in s
    assert "two-taxon replication" in s
    assert "source-network contrast-window hypothesis" in s
