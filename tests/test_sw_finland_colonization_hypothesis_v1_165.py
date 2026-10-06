from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_sw_finland_hypothesis_is_temporal_and_nonfresh():
    x=json.loads((ROOT/"development/sw_finland_colonization_topology_hypothesis_v1_165.json").read_text())
    assert x["causal_order"]["global_t0_source_state_may_be_used_for_all_targets"] is True
    assert "not pristine fresh" in x["evidence_class"]
    assert x["response_boundary"]["future_outcome_values_opened"]==0
    assert x["matched_topology_nulls"]["count"]==20

def test_primary_beats_simple_source_controls_and_null_topologies():
    x=json.loads((ROOT/"development/sw_finland_colonization_topology_hypothesis_v1_165.json").read_text())
    r3=x["reference_ladder"]["R3_add"]
    assert any("source count" in s for s in r3)
    assert any("nearest Euclidean" in s for s in r3)
    assert "P1" not in x["confirmatory_primary"]  # keys are descriptive, not mutable numbered aliases
    assert x["confirmatory_primary"]["favourable_direction"]=="negative for both"

def test_mechanism_secondary_cannot_rescue():
    x=json.loads((ROOT/"development/sw_finland_colonization_topology_hypothesis_v1_165.json").read_text())
    assert x["mechanistic_secondary"]["may_rescue_failed_primary"] is False
