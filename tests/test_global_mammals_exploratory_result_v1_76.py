from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_exploratory_result_is_exactly_frozen():
    x=json.loads((ROOT/"development/global_mammals_exploratory_scoring_freeze_v1_76.json").read_text())
    p=x["primary_exploratory_result"]
    assert p["confirmatory_blocks"]==168
    assert p["point_estimate_C_minus_R3_logloss"]<0
    assert p["bootstrap_ci95_high"]<0
    assert p["directional_support_exploratory"] is True
    assert x["artifact_files"]["exploratory_result.json"]["sha256"]=="2a96164730b64ce70660bc04cad1f137f1d90a7cb3094aaaf98fbda2f1c4cf4a"

def test_exploratory_result_never_promotes_confirmation():
    x=json.loads((ROOT/"development/global_mammals_exploratory_scoring_freeze_v1_76.json").read_text())
    g=x["interpretation_guardrails"]
    assert g["fresh_status_restored"] is False
    assert g["counts_as_fresh_confirmatory_evidence"] is False
    assert g["counts_as_primary_confirmatory_evidence"] is False
    assert g["fresh_system_denominator_contribution"]==0
    assert g["terminal_v165_status_unchanged"] is True
    assert g["mechanism_claim_authorized"] is False
    assert g["secondary_analysis_may_rescue_confirmatory_status"] is False

def test_response_firewall_was_minimal():
    x=json.loads((ROOT/"development/global_mammals_exploratory_scoring_freeze_v1_76.json").read_text())
    f=x["response_firewall"]
    assert f["confirmatory_focal_values_decoded"]==325954
    assert f["confirmatory_nonfocal_values_decoded"]==0
    assert f["pilot_occurrence_values_decoded_during_confirmatory"]==0
    assert f["excluded_occurrence_values_decoded"]==0
    assert f["rerun_authorized"] is False
