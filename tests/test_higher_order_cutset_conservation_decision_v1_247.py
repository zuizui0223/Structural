import sys
from fractions import Fraction as F
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from higher_order_cutset_conservation_decision_v1_247 import (
    audit,action_result,Q_GRID)

def test_one_supplement_reduces_target_risk_only():
    d=action_result({"A":F(3,16),"B":F(1,16)},"A",F(1))
    assert d["aggregate_residual_cutset_risk_AplusB"]["exact"]=="1/16"
    assert d["per_receiver_residual_risk"]["A"]["exact"]=="0"
    assert d["per_receiver_residual_risk"]["B"]["exact"]=="1/16"

def test_nonperfect_supplement_has_proportional_expected_benefit():
    d=action_result({"A":F(3,16),"B":F(1,16)},"A",F(1,2))
    assert d["expected_potential_cutset_failures_avoided"]["exact"]=="3/32"
    assert d["aggregate_residual_cutset_risk_AplusB"]["exact"]=="5/32"

def test_both_worlds_have_identical_cost_and_global_source_reliability_stats():
    x=audit()
    assert x["all_worlds_and_equal_cost_actions"]["minus"]["baseline_sum_AplusB"]["exact"]=="1/4"
    assert x["all_worlds_and_equal_cost_actions"]["plus"]["baseline_sum_AplusB"]["exact"]=="1/4"

def test_precommitted_three_supplement_reliability_levels_all_reverse_actions():
    x=audit()
    assert Q_GRID==(F(1,4),F(1,2),F(1))
    for q in Q_GRID:
        m=x["all_worlds_and_equal_cost_actions"]["minus"]["by_supplemental_source_viability_probability"][str(q)]
        p=x["all_worlds_and_equal_cost_actions"]["plus"]["by_supplemental_source_viability_probability"][str(q)]
        assert m["optimal_target_under_FULL_joint_viability_law"]=="B"
        assert p["optimal_target_under_FULL_joint_viability_law"]=="A"
        assert m["wrong_target_expected_cutset_loss_reduction_regret"]["exact"]==str(q*F(1,8))

def test_concrete_equal_cost_regret_is_one_eighth_at_q_one():
    x=audit()
    assert x["when_q_is_one"]["wrong_choice_regret"]["exact"]=="1/8"
    assert x["when_q_is_one_half"]["wrong_choice_regret"]["exact"]=="1/16"

def test_invalid_hypothetical_intervention_stops():
    with pytest.raises(ValueError):action_result({"A":F(1,16),"B":F(3,16)},"A",F(-1,3))
    with pytest.raises(ValueError):action_result({"A":F(1,16),"B":F(3,16)},"C",F(1,2))

def test_no_fabricated_real_world_ecological_effect():
    x=audit()
    assert x["observed_biological_source_and_recipient_records"]==0
    assert x["does_not_estimate_colonization_or_population_fitness"]
    assert x["new_confirmatory_systems"]==0
    assert x["original_GEB_scientific_HOLD"]
