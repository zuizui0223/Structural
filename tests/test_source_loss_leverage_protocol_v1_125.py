from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def test_three_wave_temporal_order_is_required():
    x=json.loads((ROOT/"development/source_loss_leverage_protocol_v1_125.json").read_text())
    t=x["minimum_temporal_structure"]
    assert t["required_waves"]==3
    assert "baseline occupancy" in t["t0"]
    assert "source losses" in t["t0_to_t1"]
    assert "subsequent target-population persistence/loss" in t["t1_to_t2"]
    assert "must not be defined from the same transition window" in t["reason"]

def test_primary_holds_population_loss_count_apart_from_leverage():
    x=json.loads((ROOT/"development/source_loss_leverage_protocol_v1_125.json").read_text())
    a=x["analysis_population"]
    assert "exactly one source loss" in a["event_count_rule"]
    assert a["lost_source_is_never_scored_as_its_own_target"] is True
    m=x["matching_and_adjustment_requirements"]["must_control_or_match"]
    assert "nominal t0 source count" in m
    assert "number of source losses" in m
    assert "ordinary Euclidean source distance" in m

def test_future_exposure_is_preoutcome_and_continuous_by_default():
    x=json.loads((ROOT/"development/source_loss_leverage_protocol_v1_125.json").read_text())
    l=x["preloss_source_leverage"]
    assert "t0 occupancy only" in l["information_allowed"]
    assert "any t2 occupancy" in l["information_forbidden"]
    d=x["directional_secondary"]
    assert "continuous leverage preferred" in d["thresholding"]
    assert "cannot be chosen from the outcome" in d["thresholding"]

def test_same_global_mammal_dataset_is_closed():
    x=json.loads((ROOT/"development/source_loss_leverage_protocol_v1_125.json").read_text())
    rel=x["relationship_to_current_structural_evidence"]
    assert rel["current_results_count_as_future_confirmation"] is False
    assert rel["same_global_mammal_dataset_may_not_be_used_for_this_confirmatory test"] is True

def test_mechanism_claims_remain_bounded():
    x=json.loads((ROOT/"development/source_loss_leverage_protocol_v1_125.json").read_text())
    forbidden=x["mechanism_claim_boundary"]["cannot_claim_without_additional_data"]
    assert "realized dispersal along graph paths" in forbidden
    assert "demographic rescue" in forbidden
    assert "causal extinction prevention" in forbidden
    assert "management intervention benefit" in forbidden

def test_active_priority_stops_same_dataset_mining():
    x=json.loads((ROOT/"development/structural_active_priority_v1_125.json").read_text())
    assert x["status"]=="independent_source_loss_leverage_validation_only"
    joined="\n".join(x["do_not"])
    assert "existing global mammal dataset" in joined
    assert "alternative leverage kernels" in joined
    assert "two-wave source-loss/outcome design" in joined
