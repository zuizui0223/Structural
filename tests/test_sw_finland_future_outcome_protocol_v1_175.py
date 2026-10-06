from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"development/sw_finland_future_outcome_protocol_v1_175.json"

def test_v175_closes_missing_data_selection():
    c=json.loads(C.read_text())
    p=c["response_independent_preprocessing"]
    assert "population median" in p["numeric_missing"]
    assert p["categorical_missing"]=="literal __MISSING__ level"
    assert p["preprocessing_uses_future_outcome"] is False
    assert c["anti_selection"][3]=="no outcome-based feature removal or complete-case filter"

def test_v175_actual_and_null_C_differ_only_in_two_C_features():
    c=json.loads(C.read_text())
    assert len(c["predictor_groups"]["C_numeric_add"])==2
    assert "identical in R3, actual C and all 20 null C models" in c["source_features"]["R2_context_invariant"]
    assert c["model_family"]["hyperparameter_tuning"] is False

def test_v175_pilot_is_non_evidential_and_confirmatory_predictions_freeze_first():
    c=json.loads(C.read_text())
    assert c["pilot_access"]["pilot_effect_estimates_count_as_evidence"] is False
    assert c["preconfirmatory_freeze"]["all_prediction_probabilities_frozen"] is True
    assert c["preconfirmatory_freeze"]["confirmatory_outcome_values_opened"]==0
    assert c["confirmatory_access"]["no_refitting_after_confirmatory_access"] is True

def test_v175_requires_both_nonredundancy_and_topology_specificity():
    c=json.loads(C.read_text())
    p=c["confirmatory_primary"]
    assert "P1 < 0" in p["support_rule"]
    assert "P2 < 0" in p["support_rule"]
    assert p["minimum_success_events"]==50
    assert p["minimum_presence_bearing_blocks"]==5
    assert p["bootstrap_replicates"]==10000

def test_v175_does_not_allow_ebird_or_species_rescue():
    c=json.loads(C.read_text())
    assert c["response_boundary"]["eBird_enabled"] is False
    assert "no re-entry of the 275 nonnumeric species" in c["anti_selection"]
    assert "no confirmatory subgroup rescue" in c["anti_selection"]
