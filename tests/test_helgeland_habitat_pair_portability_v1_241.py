"""Known-truth tests: source-class metadata, historical-only habitat fitting and no self destination."""
import math,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_habitat_pair_portability_v1_241 import (
    FARM,NON_FARM,same_habitat,habitat_destination,historical_habitat_coef,
    predict,TAUS,BETA_GRID)

def test_original_published_farm_nonfarm_classification():
    assert len(FARM)==6 and len(NON_FARM)==5 and not(FARM&NON_FARM)
    assert set(FARM|NON_FARM)=={20,22,23,24,26,27,28,33,34,35,38}
    assert same_habitat(20,26)
    assert same_habitat(23,35)
    assert not same_habitat(23,27)
    with pytest.raises(ValueError):same_habitat(23,23)

def test_habitat_probabilities_move_weight_only_in_class():
    p={22:.5,26:.5}
    h=habitat_destination(20,p,2)
    assert h[26]>p[26]
    assert h[22]<p[22]
    assert sum(h.values())==pytest.approx(1)

def test_historical_beta_fitted_only_on_historical_edges():
    ids=[20,26,23,35]
    hist={(i,j):0 for i in ids for j in ids if i!=j}
    hist[20,26]=20
    hist[26,20]=20
    hist[23,35]=20
    hist[35,23]=20
    P0={i:{j:1/3 for j in ids if i!=j} for i in ids}
    beta,score=historical_habitat_coef(ids,hist,P0)
    assert beta>0
    assert math.isfinite(score)
    assert len(BETA_GRID)==801

def test_historical_pair_reference_and_orientation_are_valid():
    ids=[20,26,23,35]
    hist={(i,j):0 for i in ids for j in ids if i!=j}
    hist[20,26]=10;hist[26,20]=1
    P0={i:{j:1/3 for j in ids if i!=j} for i in ids}
    d=predict(ids,hist,P0,1.5,10)
    for i in ids:
        for m in ("P0","H","R2","C2"):
            assert set(d[i][m])==set(ids)-{i}
            assert sum(d[i][m].values())==pytest.approx(1)
            assert all(v>0 for v in d[i][m].values())

def test_predeclared_smoothing_not_posthoc():
    assert TAUS==(5,10,20)
    ids=[20,26,23,35]
    hist={(i,j):0 for i in ids for j in ids if i!=j}
    P0={i:{j:1/3 for j in ids if i!=j} for i in ids}
    with pytest.raises(ValueError):
        predict(ids,hist,P0,1,11)
