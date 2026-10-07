from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/occupancy_role_inversion_synthesis_v1_179.json"

def test_role_inversion_is_class_specific_not_just_effect_size():
    x=json.loads(P.read_text())
    by={r["label"]:r for r in x["layers"]}
    assert by["13_plus"]["presence_C_minus_R3"] > 0
    assert by["13_plus"]["absence_C_minus_R3"] < 0
    assert by["5_12"]["presence_C_minus_R3"] < 0
    assert by["5_12"]["absence_C_minus_R3"] > 0
    assert by["1_4"]["presence_C_minus_R3"] < 0
    assert by["1_4"]["absence_C_minus_R3"] > 0

def test_graph_term_directions_flip_between_exploratory_and_both_low_occupancy_layers():
    x=json.loads(P.read_text());by={r["label"]:r for r in x["layers"]}
    assert by["13_plus"]["graph_distance_coefficient"] > 0
    assert by["13_plus"]["graph_pressure_coefficient"] < 0
    for k in ("5_12","1_4"):
        assert by[k]["graph_distance_coefficient"] < 0
        assert by[k]["graph_pressure_coefficient"] > 0

def test_no_posthoc_gradient_or_causal_claim():
    x=json.loads(P.read_text())
    b=x["evidence_boundary"]
    assert b["cross_layer_J_trend_test_authorized"] is False
    assert b["continuous_threshold_claim"] is False
    assert b["monotonic_rarity_law"] is False
    assert b["causal_colonization_or_extinction_switch"] is False
    assert x["response_boundary"]["new_response_access"] is False
    assert x["response_boundary"]["same_data_refit"] is False
