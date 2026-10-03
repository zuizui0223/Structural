from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_ultrarare_rule_is_fixed_before_census():
    x=json.loads((ROOT/"development/global_mammals_sealed_ultrarare_species_pilot_contract_v1_112.json").read_text())
    r=x["layer_rule"]
    assert r["pilot_presence_min_inclusive"]==1
    assert r["pilot_presence_max_inclusive"]==4
    assert r["threshold_change_after_census_authorized"] is False
    assert r["species_identity_exceptions_allowed"] is False

def test_presence_opportunity_is_primary():
    x=json.loads((ROOT/"development/global_mammals_sealed_ultrarare_species_pilot_contract_v1_112.json").read_text())
    h=x["hypotheses"]["primary_presence_opportunity"]
    assert h["prediction"]=="negative"
    assert "95% upper bound < 0" in h["support_rule"]
    assert h["minimum_presence_blocks"]==10

def test_external_isolation_attenuation_is_predeclared_secondary():
    x=json.loads((ROOT/"development/global_mammals_sealed_ultrarare_species_pilot_contract_v1_112.json").read_text())
    h=x["hypotheses"]["secondary_external_isolation_attenuation"]
    assert h["prediction"].startswith("positive")
    assert "cannot rescue" in h["role"]

def test_heldout_parser_remains_opaque():
    s=(ROOT/"scripts/freeze_global_mammals_sealed_ultrarare_species_pilot_v1_112.py").read_text()
    held=s.split("elif iid in heldout_set:",1)[1].split("else:",1)[0]
    assert "parse_full_record" not in held
    assert "heldout_seen+=1" in held

def test_broad_layer_stop_is_not_reinterpreted():
    x=json.loads((ROOT/"development/global_mammals_sealed_broad_species_pilot_terminal_v1_112.json").read_text())
    assert x["result"]["selected_species"]==0
    assert x["same_dataset_retry_with_wider_broad_threshold_authorized"] is False
    assert x["counts_as_empirical_support_or_non_support"] is False
