from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_gift_freeze_has_1373_pristine_islands():
 x=json.loads((ROOT/"development/gift_whole_island_geography_freeze_v1_43.json").read_text())
 assert x["result"]["retained_complete_geography_entities"]==1373
 assert x["response_boundary"]["species_composition_opened"] is False

def test_crosswalk_thresholds_are_frozen_before_results():
 x=json.loads((ROOT/"development/gift_weigelt_crosswalk_contract_v1_44.json").read_text())
 tiers={t["tier"]:t for t in x["match_tiers_in_order"]}
 assert "2.0" in tiers["A_exact_name_area"]["rule"]
 assert "5 km" in tiers["B_mutual_nearest_strict"]["rule"]
 assert "1.25" in tiers["B_mutual_nearest_strict"]["rule"]
 assert x["global_one_to_one_rule"]["manual_matching_forbidden"] is True
 assert x["response_boundary"]["plant_species_composition_authorized"] is False

def test_mammal_retry_only_repairs_artifact_path():
 x=json.loads((ROOT/"development/global_mammals_reference_retry_request_v1_43.json").read_text())
 assert x["scientific_rules_changed"] is False
 assert x["failed_run"]["failed_before_reference_script_execution"] is True
 s=(ROOT/".github/workflows/global-mammals-reference-retry-v1_43.yml").read_text()
 assert "overlap/output/island_partition_after_historical_overlap.csv" in s
