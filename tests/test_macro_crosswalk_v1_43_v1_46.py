from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]

def load_module():
 p=ROOT/"scripts/crosswalk_gift_weigelt_v1_45.py"
 spec=importlib.util.spec_from_file_location("gw",p)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_name_normalization_and_core_are_deterministic():
 m=load_module()
 assert m.norm("Île-de-Ré")=="ile de re"
 assert m.core("Île de Ré")=="de re"

def test_crosswalk_contract_is_strict_and_response_independent():
 x=json.loads((ROOT/"development/gift_weigelt_crosswalk_contract_v1_45.json").read_text())
 tiers=x["match_tiers_in_priority_order"]
 assert tiers[0]["maximum_haversine_km"]==25.0
 assert tiers[1]["maximum_haversine_km"]==10.0
 assert tiers[2]["maximum_nearest_haversine_km"]==2.0
 assert x["one_to_one_rule"]["manual_resolution_allowed"] is False
 assert x["unmatched_rule"]["manual_or_outcome_informed_rescue_forbidden"] is True
 assert x["response_boundary"]["plant_species_composition_authorized"] is False

def test_mammal_reference_retry_is_operational_only():
 x=json.loads((ROOT/"development/global_mammals_reference_operator_retry_request_v1_43.json").read_text())
 assert x["scientific_contract_changed"] is False
 assert x["failed_run"]["failed_before_reference_operator_execution"] is True
 assert x["Appendix1_access_authorized"] is False

def test_gift_geography_freeze_is_1373_and_pristine():
 x=json.loads((ROOT/"development/gift_whole_island_geography_freeze_v1_44.json").read_text())
 assert x["result"]["retained_complete_geography_entities"]==1373
 assert x["response_boundary"]["species_composition_opened"] is False
