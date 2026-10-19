"""Exact rational known-truth ecology operator constraints, no study outcomes."""
import itertools,sys
from fractions import Fraction as F
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from higher_order_donor_cutset_known_truth_v1_246 import (
    distribution,moment,count_law,no_local_donor,analyze,DONORS,RECIPIENTS,perturbation)
def test_sixteen_state_valid_probability_laws():
    for sign in (-1,1):
        p=distribution(sign)
        assert len(p)==16 and min(p.values())==0 and max(p.values())==F(1,8)
        assert sum(p.values())==1
def test_exact_same_four_marginals():
    for sign in (-1,1):
        assert all(moment(distribution(sign),[i])==F(1,2) for i in DONORS)
def test_exact_same_six_joint_pairs_and_zero_covariance():
    for sign in (-1,1):
        p=distribution(sign)
        for i,j in itertools.combinations(DONORS,2):
            assert moment(p,[i,j])==F(1,4)
            assert moment(p,[i,j])-moment(p,[i])*moment(p,[j])==0
def test_entire_count_histogram_not_just_mean():
    want={k:F(n,16) for k,n in enumerate((1,4,6,4,1))}
    assert count_law(distribution(-1))==count_law(distribution(1))==want
def test_same_recipient_source_number_opposite_loss_probabilities():
    assert len(RECIPIENTS["A"])==len(RECIPIENTS["B"])==3
    neg,pos=distribution(-1),distribution(1)
    assert no_local_donor(neg,RECIPIENTS["A"])==F(1,16)
    assert no_local_donor(pos,RECIPIENTS["A"])==F(3,16)
    assert no_local_donor(neg,RECIPIENTS["B"])==F(3,16)
    assert no_local_donor(pos,RECIPIENTS["B"])==F(1,16)
def test_global_four_donor_failure_and_aggregate_recipient_risk_unchanged():
    for sign in (-1,1):
        p=distribution(sign)
        assert no_local_donor(p,DONORS)==F(1,16)
        assert sum(no_local_donor(p,v) for v in RECIPIENTS.values())==F(1,4)
def test_pairwise_independence_does_not_imply_higher_order_independence():
    for sign in (-1,1):
        assert no_local_donor(distribution(sign),(1,2,3))!=F(1,8)
def test_result_explicitly_not_an_ecological_effect():
    receipt=analyze()
    assert receipt["exact_A_cutset_plus_minus_difference"]["exact"]=="1/8"
    assert receipt["exact_B_cutset_plus_minus_difference"]["exact"]=="-1/8"
    assert receipt["exact_higher_to_lower_cutset_risk_ratio"]["exact"]=="3"
    assert receipt["actual_source_loss_migration_colonization_or_fitness_observations"]==0
    assert receipt["GEB_scientific_HOLD"]
def test_invalid_input_fails_closed():
    with pytest.raises(ValueError):distribution(0)
    with pytest.raises(ValueError):perturbation((0,0,9,1))
    with pytest.raises(ValueError):no_local_donor(distribution(1),())
def test_graph_topology_predeclared():
    assert RECIPIENTS=={"A":(1,2,3),"B":(1,2,4)}
