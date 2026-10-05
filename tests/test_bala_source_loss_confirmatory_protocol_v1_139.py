from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/bala_source_loss_confirmatory_protocol_v1_139.json"

def test_primary_is_target_specific_lost_access_fraction_only():
    x=json.loads(P.read_text())
    assert x["primary_exposure"]["name"]=="target_specific_lost_access_fraction_E_i"
    assert x["candidate_C"]["formula"]=="R2 + standardized E_i only"
    assert x["candidate_C"]["event_level_delta_N_eff_in_primary"] is False
    assert x["source_operator"]["self_anchor_exclusion"].startswith("for target island i")

def test_reference_holds_loss_count_and_controls_static_island_state():
    x=json.loads(P.read_text())
    r=x["reference_R2"]
    assert r["static_island_control"].startswith("six dummy variables")
    assert r["exactly_one_loss_count_control"].startswith("held fixed")
    assert "nearest surviving-other-source Euclidean distance in km" in r["continuous_predictors"]
    assert "target_was_occupied_at_t0 indicator" in r["continuous_predictors"]

def test_validation_is_leave_one_taxon_out_and_cluster_macro():
    x=json.loads(P.read_text())
    v=x["validation"];p=x["primary"]
    assert v["outer_unit"]=="MF taxon"
    assert v["scheme"]=="leave-one-eligible-confirmatory-taxon-out"
    assert v["training_complement_minimum_contractions"]==5
    assert v["training_complement_minimum_persistences"]==5
    assert v["minimum_estimable_taxon_clusters_for_primary"]==10
    assert p["bootstrap_unit"]=="MF taxon cluster"
    assert p["bootstrap_replicates"]==10000

def test_t2_is_sealed_until_features_and_folds_are_frozen():
    x=json.loads(P.read_text())
    assert x["t2_endpoint"]["t2_taxon_or_quantity_access_before_full_feature_freeze"] is False
    order="\n".join(x["confirmatory_stage_order"])
    assert order.index("open only BALA1/2") < order.index("only then authorize one BALA3")
    assert x["response_boundary_now"]["confirmatory_t2_semantics_opened"] is False

def test_protocol_does_not_claim_causality():
    x=json.loads(P.read_text())
    cannot="\n".join(x["claim_boundary"]["cannot_claim"])
    assert "causal extinction prevention" in cannot
    assert "demographic rescue" in cannot
    assert "realized dispersal" in cannot
