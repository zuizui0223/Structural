"""Exact fractions: loss cannot help without feedback; both signs possible with feedback."""
from fractions import Fraction
import sys
from pathlib import Path
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from source_loss_synchrony_mechanism_sign_v1_246 import (
    decompose,run,law,SCENARIOS,BEFORE_SYNC_AB_C_INDEPENDENT,
    AFTER_AB_INDEPENDENT,AFTER_AB_SYNC
)
def exact(result,key):
    return Fraction(result[key]["exact"])

def test_static_deletion_is_monotone_for_every_source():
    b=BEFORE_SYNC_AB_C_INDEPENDENT
    for removed in range(3):
        from collections import defaultdict
        projected={}
        for state,weight in b.items():
            new=state[:removed]+state[removed+1:]
            projected[new]=Fraction(projected.get(new,0))+Fraction(weight)
        d=decompose(b,projected,removed_index=removed)
        assert exact(d,"direct_loss_unique_delivery_term")>=0
        assert exact(d,"remaining_source_joint_reorganization_term")==0
        assert exact(d,"total_change_in_no_viable_delivery")>=0

def test_exact_hydra_gain_requires_feedback_exceed_direct_source_loss():
    x=decompose(BEFORE_SYNC_AB_C_INDEPENDENT,AFTER_AB_INDEPENDENT)
    assert exact(x,"pre_loss_no_viable_delivery_probability")==Fraction(3,10)
    assert exact(x,"counterfactual_no_feedback_after_deletion")==Fraction(1,2)
    assert exact(x,"post_loss_no_viable_delivery_probability")==Fraction(1,4)
    assert exact(x,"direct_loss_unique_delivery_term")==Fraction(1,5)
    assert exact(x,"remaining_source_joint_reorganization_term")==-Fraction(1,4)
    assert exact(x,"total_change_in_no_viable_delivery")==-Fraction(1,20)
    assert x["same_individual_survivor_activity_marginals"]
    assert x["strict_hydra_window_criterion_satisfied"]
    assert exact(x,"mean_viable_sources_after")<exact(x,"mean_viable_sources_before")

def test_static_deleted_donor_has_no_window_hydra():
    x=decompose(BEFORE_SYNC_AB_C_INDEPENDENT,AFTER_AB_SYNC)
    assert exact(x,"total_change_in_no_viable_delivery")==Fraction(1,5)
    assert not x["strict_hydra_window_criterion_satisfied"]

def test_source_removal_can_increase_remaining_cofailure():
    x=run()["examples"]["amplified_cofailure_after_removal"]["calculation"]
    assert exact(x,"pre_loss_no_viable_delivery_probability")==Fraction(3,20)
    assert exact(x,"counterfactual_no_feedback_after_deletion")==Fraction(1,4)
    assert exact(x,"post_loss_no_viable_delivery_probability")==Fraction(1,2)
    assert exact(x,"direct_loss_unique_delivery_term")==Fraction(1,10)
    assert exact(x,"remaining_source_joint_reorganization_term")==Fraction(1,4)
    assert exact(x,"total_change_in_no_viable_delivery")==Fraction(7,20)
    assert x["same_individual_survivor_activity_marginals"]

def test_bad_probability_sum_and_source_identity_fail_closed():
    with pytest.raises(ValueError):
        decompose({"000":"1/4","111":"1/4"},AFTER_AB_SYNC)
    with pytest.raises(ValueError):
        decompose(BEFORE_SYNC_AB_C_INDEPENDENT,{"00":"-1/2","11":"3/2"})
    with pytest.raises(ValueError):
        decompose(BEFORE_SYNC_AB_C_INDEPENDENT,AFTER_AB_SYNC,removed_index=3)
    with pytest.raises(ValueError):
        law({"00":"1/2","01":"1/2"},3)

def test_never_reports_ecological_persistence_or_confirmation():
    x=run()
    assert x["existing_v1_203_pairwise_cofailure_known_truth_not_rebranded"]
    assert x["no_empirical_persistence_or_source_colonization_measured"]
    assert x["GEB_scientific_HOLD"]
    assert x["status"]=="EXACT_KNOWN_TRUTH_NO_EMPIRICAL_SOURCE_DATA_READ"
