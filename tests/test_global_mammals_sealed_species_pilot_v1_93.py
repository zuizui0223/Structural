from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_second_layer_threshold_is_fixed_before_census():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_pilot_contract_v1_93.json").read_text())
    r=x["second_layer_species_rule"]
    assert r["pilot_presence_min_inclusive"]==5
    assert r["pilot_presence_max_inclusive"]==12
    assert r["threshold_change_after_census_authorized"] is False
    assert r["species_identity_exceptions_allowed"] is False
    assert r["heldout_response_may_not_change_species_membership"] is True

def test_previous_heldout_nonfocal_surface_is_explicitly_sealed():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_pilot_contract_v1_93.json").read_text())
    e=x["why_new_response_exists"]
    assert e["source_species_columns"]==5394
    assert e["previously_scored_heldout_species"]==79
    assert e["heldout_nonfocal_species_columns_remaining_sealed"]==5315
    assert e["previous_confirmatory_nonfocal_values_decoded"]==0

def test_pilot_census_parser_never_decodes_heldout_occurrence_fields():
    s=(ROOT/"scripts/freeze_global_mammals_sealed_species_pilot_v1_93.py").read_text()
    assert "elif iid in heldout_set:" in s
    assert "Do not decode any occurrence field from this record." in s
    held=s.split("elif iid in heldout_set:",1)[1].split("else:",1)[0]
    assert "parse_full_record" not in held
    assert "heldout_occurrence_values_decoded" in s

def test_workflow_is_one_shot_pilot_only():
    s=(ROOT/".github/workflows/global-mammals-sealed-species-pilot-v1_93.yml").read_text()
    assert "pilot_presence_min_inclusive" in s
    assert "heldout_occurrence_values_decoded" in s
    assert "heldout_response_authorized" in s
    assert "freeze_global_mammals_sealed_species_pilot_v1_93.py" in s
    assert "score" not in s.lower()

def test_replication_role_is_species_not_geographic_independence():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_pilot_contract_v1_93.json").read_text())
    e=x["evidence_boundary"]
    assert e["same_geographic_system_as_v1_76"] is True
    assert e["geographically_independent_replication"] is False
    assert e["species_response_layer_independent_of_v1_76_heldout_response"] is True
    assert e["fresh_heldout_species_response_available"] is True
