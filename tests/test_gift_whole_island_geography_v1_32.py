from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_geography_contract_is_species_free_and_whole_island_only():
    x=json.loads((ROOT/"development/gift_whole_island_geography_contract_v1_32.json").read_text())
    assert x["primary_unit"]["entity_class"]=="Island"
    assert x["overlap_resolution"]["function"]=="GIFT_no_overlap"
    assert x["geography_query"]["miscellaneous"]==["longitude","latitude","area"]
    assert x["evidence_boundary"]["species_response_authorized"] is False

def test_external_isolation_crosswalk_is_not_pretuned():
    x=json.loads((ROOT/"development/gift_whole_island_geography_contract_v1_32.json").read_text())
    b=x["external_isolation_bridge"]
    assert b["matching_rule_not_yet_authorized"] is True
    assert b["outcome_informed_matching_forbidden"] is True

def test_script_queries_no_species_surface():
    s=(ROOT/"scripts/freeze_gift_whole_island_geography_v1_32.R").read_text()
    assert "GIFT_no_overlap" in s
    assert "GIFT_env" in s
    assert 'miscellaneous=c("longitude","latitude","area")' in s
    assert "GIFT_checklists_raw" not in s
    assert "GIFT_species" not in s
