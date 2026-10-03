from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_broad_layer_is_disjoint_and_fixed():
    x=json.loads((ROOT/"development/global_mammals_sealed_broad_species_pilot_contract_v1_111.json").read_text())
    r=x["broad_layer_rule"]
    assert r["pilot_absence_min_inclusive"]==1
    assert r["pilot_absence_max_inclusive"]==12
    assert r["exclude_zero_absence_species"] is True
    assert r["threshold_change_after_census_authorized"] is False
    assert r["species_identity_exceptions_allowed"] is False

def test_source_saturation_primary_is_frozen_before_census():
    x=json.loads((ROOT/"development/global_mammals_sealed_broad_species_pilot_contract_v1_111.json").read_text())
    h=x["hypothesis"]
    assert "broad_layer - (C-R3)_original79" in h["primary_future_contrast"]
    assert h["predicted_direction"]=="positive"
    assert "95% lower bound > 0" in h["future_support_rule"]
    assert h["formal_unimodality_claim_authorized"] is False

def test_heldout_response_remains_opaque_in_parser():
    s=(ROOT/"scripts/freeze_global_mammals_sealed_broad_species_pilot_v1_111.py").read_text()
    held=s.split("elif iid in heldout_set:",1)[1].split("else:",1)[0]
    assert "parse_full_record" not in held
    assert "heldout_seen+=1" in held
    assert "heldout_occurrence_values_decoded" in s

def test_workflow_is_pilot_only():
    s=(ROOT/".github/workflows/global-mammals-sealed-broad-species-pilot-v1_111.yml").read_text()
    assert "heldout_occurrence_values_decoded" in s
    assert "broad_species_universe.csv" in s
    assert "score_" not in s
    assert "heldout_occurrence_authorized" in s
