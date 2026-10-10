"""Calibration math is known-truth; no live author data needed for tests."""
import math
import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from hopson_sampling_zero_check_v1_224 import (
    p_zero_fixed_density_neighbors,aggregate,category,SCALE_GRID
)

def test_jeffreys_poisson_posterior_exact():
    p=p_zero_fixed_density_neighbors(2,3,.3,.3,.3,1)
    assert p==pytest.approx((2/3)**5.5)
    assert p_zero_fixed_density_neighbors(2,3,.3,.3,.3,.10)>p
    assert p_zero_fixed_density_neighbors(20,30,.3,.3,.3,1)<p

def test_no_central_count_used_for_prediction():
    template=dict(meta=1,block=1,treatment="nn",left_count=9,right_count=9,
                  left_volume=.3,right_volume=.3,middle_volume=.3)
    a=aggregate([{**template,"middle_count":0,"zero":1}],1.0)["all"]
    b=aggregate([{**template,"middle_count":900,"zero":0}],1.0)["all"]
    assert a["conditional_expected_zero_sum"]==b["conditional_expected_zero_sum"]
    assert a["central_sample_zeros"]==1 and b["central_sample_zeros"]==0

def test_mathematical_stability_and_rejections():
    assert 0<=p_zero_fixed_density_neighbors(100000,90000,.298,.33,.3,.1)<=1
    for args in [(0,2,.3,.3,.3,1),(1,2,0,.3,.3,1),
                 (1,2,.3,.3,.3,0),(1.2,2,.3,.3,.3,1)]:
        with pytest.raises(ValueError):p_zero_fixed_density_neighbors(*args)

def test_precommitted_bins_and_no_independent_event_claim():
    assert category(.0002)=="p_lt_0001"
    assert category(.009)=="p_0001_to_001"
    assert category(.03)=="p_001_to_005"
    assert category(.10)=="p_005_to_020"
    assert category(.5)=="p_ge_020"
    assert SCALE_GRID==(1.0,.25,.10)
