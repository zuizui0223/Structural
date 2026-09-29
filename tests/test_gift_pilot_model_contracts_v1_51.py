from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT/path).read_text())

def test_pilot_access_is_still_blocked_by_origin_gate():
    x=load("development/gift_pilot_response_protocol_contract_v1_51.json")
    assert x["geological_origin_gate"]["pilot_access_requires_prior_resolution"] is True
    assert x["geological_origin_gate"]["authorization_now"] is False
    assert x["evidence_boundary"]["pilot_species_response_authorized"] is False
    assert x["first_biological_access"]["confirmatory_list_ID_access"] is False

def test_species_universe_is_block_estimable_and_bounded():
    x=load("development/gift_pilot_response_protocol_contract_v1_51.json")
    u=x["fixed_species_universe"]
    assert u["minimum_present_archipelago_blocks"]==3
    assert u["minimum_absent_archipelago_blocks"]==3
    assert u["minimum_qualifying_species"]==100
    assert u["maximum_species"]==2000
    assert u["post_access_threshold_change_forbidden"] is True

def test_r3_explicitly_controls_regional_pool_and_direct_source_context():
    x=load("development/gift_preconfirmatory_model_contract_v1_52.json")
    r3=x["reference_ladder"]["R3_add"]
    assert "training-only species_x_regional_pool prevalence" in r3
    assert "training-only Euclidean nearest occupied-source distance" in r3
    assert "training-only Euclidean diffuse occupied-source pressure" in r3
    assert x["source_feature_rules"]["pilot_target"].startswith("remove the entire target pilot archipelago")
    assert x["source_feature_rules"]["confirmatory_target"].startswith("source set is the complete frozen 99-island pilot response only")

def test_candidate_c_only_adds_graph_path_terms():
    x=load("development/gift_preconfirmatory_model_contract_v1_52.json")
    assert x["reference_ladder"]["C_add"]==[
        "training-only graph-path nearest occupied-source distance",
        "training-only graph-path diffuse occupied-source pressure",
    ]
    assert x["confirmatory_freeze"]["refit_after_confirmatory_access"] is False
    assert x["primary"]["secondary_moderators_may_rescue"] is False
