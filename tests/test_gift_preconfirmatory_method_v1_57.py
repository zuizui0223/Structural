from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_method_is_frozen_without_realized_species_count():
 x=json.loads((ROOT/"development/gift_preconfirmatory_model_contract_v1_57.json").read_text())
 assert x["pilot_parent_requirement"]["focal_species_count_is_not_predeclared"] is True
 assert x["fitting"]["ridge_lambda"]==1.0
 assert x["fitting"]["numpy_version"]=="2.3.3"
 assert x["response_boundary"]["pilot_result_inspected_to_choose_method"] is False
 assert x["response_boundary"]["confirmatory_response_authorized"] is False

def test_nested_ladder_contains_strong_r3_and_graph_only_c():
 x=json.loads((ROOT/"development/gift_preconfirmatory_model_contract_v1_57.json").read_text())
 r3=x["species_source_features_raw"]["R3_add"]
 c=x["species_source_features_raw"]["C_add"]
 assert "regional_pool_prevalence_jeffreys_logit" in r3
 assert "log1p_nearest_euclidean_source_km" in r3
 assert c==["log1p_nearest_graph_source_km","log1p_graph_source_pressure"]
 assert x["species_source_features_raw"]["pilot_row_source_set"].startswith("all frozen pilot islands except every island")

def test_prediction_format_is_response_free_and_deterministic_layout():
 x=json.loads((ROOT/"development/gift_preconfirmatory_model_contract_v1_57.json").read_text())
 p=x["confirmatory_prediction_freeze"]
 assert p["entities"]==404
 assert p["stored_probabilities"]==["R3","C"]
 assert p["confirmatory_target_values_used"] is False
 assert "float64 p_R3 followed by float64 p_C" in p["binary_format"]["body"]

def test_script_never_queries_GIFT_or_reads_confirmatory_targets():
 s=(ROOT/"scripts/freeze_gift_preconfirmatory_model_v1_57.py").read_text()
 assert "GIFT_checklists" not in s
 assert "confirmatory_target_values_used" in s
 assert 'struct.pack("<II"' in s
 assert '"R3":30' in s and '"C":32' in s
