from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_common_protocol_species_thresholds_are_scale_adaptive():
 x=json.loads((ROOT/"development/macro_species_response_protocol_v1_50.json").read_text())
 assert x["species_universe"]["plants_m"]==5
 assert x["species_universe"]["mammals_m"]==13
 assert x["fitting"]["ridge_lambda"]==1.0
 assert x["cross_fitted_species_features"]["heldout_block_source_leakage_allowed"] is False

def test_island_type_is_not_duplicate_predictor():
 x=json.loads((ROOT/"development/common_island_type_adjustment_v1_49.json").read_text())
 assert x["model_rule"]["do_not_include_both_numeric_gmmc_and_duplicate_type_dummy_in_same_model"] is True
 assert x["plant_503_audit"]["raw_gmmc_0_disconnected"]==381
 assert x["plant_503_audit"]["raw_gmmc_1_connected"]==122

def test_routing_contracts_open_no_response():
 p=json.loads((ROOT/"development/gift_pilot_routing_contract_v1_51.json").read_text())
 m=json.loads((ROOT/"development/global_mammals_macro_pilot_routing_contract_v1_51.json").read_text())
 assert p["response_boundary"]["species_composition_opened"] is False
 assert m["response_boundary"]["occurrence_values_opened"] is False
 assert p["inputs"]["pilot_islands"]==99
 assert m["input"]["pilot_islands"]==1275
