"""Only exact known-truth mathematical assertions; zero biological response reads."""
from fractions import Fraction as F
import math,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from source_loss_synchrony_gate_v1_246 import cases,joint_validate,at_least_one_establishment,no_live_donors,run,exact_sample

def test_fixed_marginal_donor_survival_in_both_opposite_dependence_regimes():
    d=cases()
    for k,x in d.items():
        assert joint_validate(x,3 if k.startswith("three") else 2)==[F(1,2)]*(3 if k.startswith("three") else 2)
    assert no_live_donors(d["two_anticorrelated_post"])==0
    assert no_live_donors(d["two_perfectly_synchronized_post"])==F(1,2)

def test_depletion_is_negative_even_with_unchanged_independent_survivors():
    for q in (F(1,2),F(4,5),F(9,10),F(1)):
        x=exact_sample(q)
        assert x["direct_donor_depletion_component"]<0
        assert x["post_depletion_asynchrony_component"]>0
        assert x["post_depletion_synchrony_component"]<0

def test_sign_switch_requires_sufficient_per_source_colonization_efficiency():
    a=exact_sample(F(1,2))
    b=exact_sample(F(9,10))
    assert a["net_anticorrelated_minus_preloss"]<0
    assert b["net_anticorrelated_minus_preloss"]>0
    assert b["net_synchronized_minus_preloss"]<0
    assert b["preloss_P_establishment"]==pytest.approx(1-(1-.9/2)**3)
    assert b["postloss_anticorrelated_P_establishment"]==pytest.approx(.9)

def test_crossing_is_not_inferred_from_data():
    o=run()
    assert o["analytical_crossover_q"]=="3-sqrt(5)"
    assert o["crossover_q_float"]==pytest.approx(3-math.sqrt(5),abs=1e-12)
    assert not o["biological_data_accessed"]
    assert o["GEB_scientific_HOLD"]
    assert o["no_new_confirmatory_systems_admitted"]

def test_fail_closed_if_wrong_probability_or_marginal():
    with pytest.raises(ValueError):
        at_least_one_establishment(cases()["two_independent_post"],F(5,4))
    with pytest.raises(ValueError):
        joint_validate({(0,0):F(1,1)},2)
