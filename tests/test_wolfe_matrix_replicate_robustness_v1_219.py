"""Synthetic matrix jackknife and replicate-label exchangeability check for v1.219."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from wolfe_matrix_replicate_robustness_v1_219 import (
    matrix_contrasts,paired_summary,sub,mean,MATRIX,COR,HET,N
)

def mock():
    return {(n,h,m,c):[(0,0,0)]*4
        for n in N for h in HET for m in MATRIX for c in COR}

def test_complete_design_zero():
    r=matrix_contrasts(mock(),6)
    for val in r["summaries"]["difference_in_differences"]["leave_one_matrix_out"].values():
        assert val == [0.0,0.0]

def test_leave_one_matrix_shows_concentration():
    a=mock()
    a[(6,"heterogeneous","low","low")]=[(1,1,1)]*4
    result=matrix_contrasts(a,6)["summaries"]["difference_in_differences"]
    assert result["all_three_equal_weight"]==[1/3,1/3]
    assert result["leave_one_matrix_out"]["low"]==[0,0]
    assert result["leave_one_matrix_out"]["none"]==[1/2,1/2]

def test_interval_adversarial_independent_missing():
    a=mock()
    a[(6,"heterogeneous","none","high")]=[(0,0,0)]*3
    a[(6,"homogeneous","high","high")]=[(0,0,0)]*3
    r=matrix_contrasts(a,6)["summaries"]["difference_in_differences"]
    assert r["all_three_equal_weight"]==[-1/12,1/12]
    assert r["leave_one_matrix_out"]["low"]==[-1/8,1/8]

def test_replicate_pair_hypothetical_sign_not_claimed_real_p():
    r={}
    for day in range(1,5):
        r[(6,"heterogeneous","none","low",day)]=(1,1,1)
        r[(6,"heterogeneous","none","high",day)]=(0,0,0)
    for m in ("low","high"):
        for day in range(1,5):
            r[(6,"heterogeneous",m,"low",day)]=(0,0,0)
            r[(6,"heterogeneous",m,"high",day)]=(0,0,0)
    result=paired_summary(r,6,"heterogeneous")
    assert result["paired_units"]==12
    assert result["low_positive_only"]==4
    assert result["hypothetical_exchangeable_sign_test_two_sided"]==0.125
    r.pop((6,"heterogeneous","none","high",4))
    a=paired_summary(r,6,"heterogeneous")
    assert a["paired_units"]==11 and a["hypothetical_exchangeable_sign_test_two_sided"]==0.25
    b=paired_summary(r,6,"heterogeneous",missing_high_state=1)
    assert b["low_positive_only"]==3 and b["hypothetical_exchangeable_sign_test_two_sided"]==0.25

def test_subtraction_bounds():
    assert sub([1/4,1/3],[-1/6,-1/12])==[1/3,1/2]
    assert mean([[0,1/4],[1/2,3/4]])==[1/4,1/2]
