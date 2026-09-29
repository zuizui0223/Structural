from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v138_is_response_independent_complete_case_supersession():
    x=json.loads((ROOT/"development/gift_whole_island_geography_contract_v1_38.json").read_text())
    assert x["failure_basis"]["species_composition_opened"] is False
    assert x["geography_complete_case_rule"]["replacement_entities_allowed"] is False
    assert x["geography_complete_case_rule"]["outcome_informed_recovery_forbidden"] is True

def test_v138_script_excludes_missing_geography_without_species():
    s=(ROOT/"scripts/freeze_gift_whole_island_geography_v1_38.R").read_text()
    assert "not_returned_by_GIFT_env" in s
    assert "invalid_or_incomplete_longitude_latitude_area" in s
    assert "species_composition_opened=FALSE" in s

def test_v138_workflow_uses_canonical_metadata_only():
    s=(ROOT/".github/workflows/gift-whole-island-geography-v1_38.yml").read_text()
    assert "36582542511" in s
    assert "gift_excluded_missing_geography.csv" in s
    assert "GIFT_checklists" not in s
