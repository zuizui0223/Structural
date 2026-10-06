from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"development/boreal_bird_preconfirmatory_contract_v1_164.json"

def test_v164_changes_only_candidate_graph_features_across_nulls():
    x=json.loads(C.read_text())
    assert "identical" in x["reference_ladder"]["critical_invariant"]
    assert x["reference_ladder"]["C_null_add"].startswith("same two graph-path")
    assert x["response_boundary"]["bird_confirmatory_response_authorized"] is False

def test_v164_primary_is_configuration_sensitivity_slope_not_average_gain():
    x=json.loads(C.read_text())
    p=x["primary_scoring"]
    assert "slope beta_S" in p["estimand"]
    assert p["favourable_direction"]=="negative"
    assert p["minimum_presence_blocks"]==4
    assert p["bootstrap_replicates"]==10000
    assert p["support_rule"].endswith("upper bound < 0")

def test_v164_freezes_every_prediction_before_confirmatory_access():
    x=json.loads(C.read_text())
    cols=x["preconfirmatory_outputs"]["prediction_columns"]
    assert "zS_hex" in cols and "p_C_actual_hex" in cols
    assert "p_C_null_20_hex" in cols
    assert x["preconfirmatory_outputs"]["all_probabilities_and_zS_frozen_before_confirmatory_response"] is True

def test_v164_cannot_rescue_beetle_or_enable_ebird():
    x=json.loads(C.read_text())
    assert "reversal of the completed beetle primary" in x["claim_boundary"]["cannot_support"]
    assert x["response_boundary"]["beetle_response_reopened"] is False
    assert x["response_boundary"]["eBird_enabled"] is False
