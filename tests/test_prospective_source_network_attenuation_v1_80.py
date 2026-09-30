from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_future_attenuation_hypothesis_is_not_retroactive_confirmation():
    x=json.loads((ROOT/"development/prospective_source_network_attenuation_hypothesis_v1_80.json").read_text())
    assert x["status"].startswith("FUTURE_ONLY")
    assert x["current_evidence_accounting"]["counts_as_new_confirmatory_evidence"] is False
    assert x["current_evidence_accounting"]["changes_any_existing_primary_status"] is False
    assert x["current_evidence_accounting"]["GIFT_terminal_fresh_attempt_remains_terminal"] is True

def test_future_primary_requires_both_overall_gain_and_attenuation():
    x=json.loads((ROOT/"development/prospective_source_network_attenuation_hypothesis_v1_80.json").read_text())
    p=x["prospective_primary_for_future_system"]
    assert "point estimate < 0" in p["estimand_1_support"]
    assert p["estimand_2_direction"].startswith("positive")
    assert "both estimand_1 and estimand_2" in p["joint_support"]
    assert "cannot be rescued" in p["anti_rescue"]

def test_future_reference_keeps_species_by_region_and_leave_block_out():
    x=json.loads((ROOT/"development/prospective_source_network_attenuation_hypothesis_v1_80.json").read_text())
    req=x["future_independent_test"]
    assert "species_x_regional_pool prevalence or membership" in req["R3_must_control"]
    assert "leave the complete held-out validation block out" in req["source_features"]
