"""Formal synthetic truth checks only, not biology evidence."""
import math,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from source_loss_correlation_competition_v1_260 import (
    no_delivery,exact_small_enumeration,pair_failure_correlation,
    nonzero_sign_threshold,run,expected_successful_arrivals)

def test_closed_form_equals_exact_joint_state_enumeration():
    for n in (2,3,4,5):
        for c in (0,.01,.2):
            for a in (.25,.5,.75,1):
                assert no_delivery(n,.35,c,a)==pytest.approx(
                    exact_small_enumeration(n,.35,c,a),abs=1e-13)

def test_fixed_marginal_failure_and_covariance_not_source_number():
    q=.35
    assert pair_failure_correlation(q,.22)==pytest.approx(.523809523809524)
    assert pair_failure_correlation(q,.01)==pytest.approx(.018759018759018763)
    for c in (0,.01,.22):
        p=(q-c)/(1-c)
        marginal=c+(1-c)*p
        assert marginal==pytest.approx(q)

def test_loss_always_reduces_expected_successes_even_if_risk_improves():
    for a in (.1,.3,.75,1):
        assert expected_successful_arrivals(3,.35,a)<expected_successful_arrivals(4,.35,a)
    assert no_delivery(3,.35,.01,.75)<no_delivery(4,.35,.22,.75)

def test_without_decoupling_same_local_loss_worsens_shortage():
    for a in (.3,.75,1):
        assert no_delivery(3,.35,.22,a)>no_delivery(4,.35,.22,a)

def test_nonzero_threshold_has_both_sides_and_not_zero_artifact():
    a=nonzero_sign_threshold(4,.22,3,.01,.35)
    assert a==pytest.approx(.49927179513163855,abs=1e-9)
    assert no_delivery(3,.35,.01,.30)>no_delivery(4,.35,.22,.30)
    assert no_delivery(3,.35,.01,.75)<no_delivery(4,.35,.22,.75)
    assert no_delivery(3,.35,.01,a)==pytest.approx(
        no_delivery(4,.35,.22,a),abs=1e-12)

def test_invalid_mixture_and_overlarge_enumerator_fail_closed():
    for args in [(0,.35,.01,.3),(3,.35,.4,.3),(3,.35,.01,1.2),
                 (3,.35,float("nan"),.3)]:
        with pytest.raises(ValueError):no_delivery(*args)
    with pytest.raises(ValueError):exact_small_enumeration(11,.35,.01,.5)

def test_full_output_is_not_empirical_or_confirmatory():
    r=run()
    assert r["no_real_observation_rows_used"]
    assert r["GEB_scientific_HOLD"]
    assert r["nontrivial_arrival_success_threshold_a"]>0
    assert len(r["examples"])==8
