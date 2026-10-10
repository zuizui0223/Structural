"""Response-safe synthetic checks for heldout graph features and no future leakage."""
import math,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from hopson_ring_reappearance_loso_v1_226 import (
    ring_distance,neighbors,FEATURE_ADDITIONS,FEATURE_REFERENCE
)

def test_ring_geometry_correct_wrap():
    assert ring_distance(1,15)==1
    assert ring_distance(1,8)==7
    assert ring_distance(8,1)==7
    assert ring_distance(1,1)==0
    assert ring_distance(3,5)==2
    with pytest.raises(ValueError):ring_distance(0,15)

def test_nearest_only_vs_exact_source_placement():
    x={i:0 for i in range(1,16)}
    a=dict(x); a[2]=1;a[15]=1
    b=dict(x); b[2]=1;b[14]=1
    f=neighbors(a,1);g=neighbors(b,1)
    assert f["nearest"]==g["nearest"]==1
    assert f["total"]==g["total"]==2
    assert f["one"]==2 and g["one"]==1
    assert f["two"]==0 and g["two"]==1

def test_no_sources_sets_nearest_sentinel():
    n=neighbors({i:0 for i in range(1,16)},1)
    assert n=={"nearest":8,"one":0,"two":0,"total":0}

def test_contract_features_stable():
    assert FEATURE_ADDITIONS==("ring_one_step_positive_count","ring_two_step_positive_count")
    assert "prey" not in " ".join(FEATURE_REFERENCE)
    assert len(FEATURE_REFERENCE)==8
