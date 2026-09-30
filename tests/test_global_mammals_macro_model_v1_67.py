from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_mammal_model_method_is_frozen_before_pilot_response():
    x=json.loads((ROOT/"development/global_mammals_macro_model_contract_v1_67.json").read_text())
    assert x["status"].endswith("BEFORE_MACRO_PILOT_RESPONSE")
    assert x["fixed_population"]["islands"]==5401
    assert x["fixed_population"]["pilot_islands"]==1275
    assert x["fixed_population"]["confirmatory_islands"]==4126
    assert x["pilot_parent_requirement"]["minimum_presence"]==13
    assert x["pilot_parent_requirement"]["minimum_absence"]==13
    assert x["response_boundary"]["macro_pilot_response_opened_at_contract_freeze"] is False

def test_mammal_r3_controls_species_by_region_and_leave_block_out():
    x=json.loads((ROOT/"development/global_mammals_macro_model_contract_v1_67.json").read_text())
    assert "bioregion_prevalence_jeffreys_logit" in x["species_source_features_raw"]["R3_add"]
    assert "except every island in the focal 10-degree validation block" in x["species_source_features_raw"]["pilot_row_source_set"]
    assert x["fitting"]["response_based_hyperparameter_tuning"] is False
    assert x["primary_scoring_later"]["mammal_result_counts_as_fresh_confirmation"] is False
