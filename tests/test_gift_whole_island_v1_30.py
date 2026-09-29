from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_primary_unit_is_whole_island_and_lists_are_not_replicates():
    x=json.loads((ROOT/"development/gift_whole_island_response_semantics_v1_30.json").read_text())
    assert x["primary_geographic_unit"]["entity_class"]=="Island"
    assert "Island Group" in x["primary_geographic_unit"]["exclude_from_primary"]
    assert "Island Part" in x["primary_geographic_unit"]["exclude_from_primary"]
    assert x["entity_level_checklist_semantics"]["unit"]=="unique GIFT entity_ID"
    assert "union species presences" in x["entity_level_checklist_semantics"]["future_species_response_aggregation"]

def test_metadata_run_selection_cannot_be_result_selected():
    x=json.loads((ROOT/"development/gift_whole_island_response_semantics_v1_30.json").read_text())
    r=x["metadata_run_multiplicity_rule"]
    assert "smallest GitHub workflow run_id" in r["canonical_result"]
    assert "may not replace" in r["later_successful_runs"]

def test_projection_script_never_accepts_species_columns():
    s=(ROOT/"scripts/project_gift_whole_islands_v1_30.R").read_text()
    assert 'meta$entity_class == "Island"' in s
    assert "species-response columns reached metadata stage" in s
    assert "species_composition_opened=FALSE" in s
