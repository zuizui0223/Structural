"""Synthetic known truth for chronological directionality, conservation of probability and heldout-only scoring."""
import sys,math,json
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_directional_route_portability_v1_240 import (
    route_distributions,normalize,PREDECLARED_TAUS,COHORT_TOTALS,matrix_by_era)

def test_three_island_direction_beats_only_undirected_when_direction_matters():
    ids=[1,2,3]
    H={(i,j):0 for i in ids for j in ids if i!=j}
    H[1,2]=9;H[2,1]=1;H[1,3]=1;H[3,1]=9
    # Both undirected pairs involving source 1 have weight ten.
    probs=route_distributions(ids,H,10)
    assert probs[1]["C"][2]>probs[1]["R1"][2]
    assert probs[1]["C"][3]<probs[1]["R1"][3]
    assert set(probs[1]["C"])=={2,3}
    assert sum(probs[1]["C"].values())==pytest.approx(1)

def test_fixed_reference_is_destination_only_and_admissible():
    ids=[1,2,3,4]
    H={(i,j):0 for i in ids for j in ids if i!=j}
    H[1,2]=3;H[2,3]=4;H[3,4]=6;H[4,1]=1
    for tau in PREDECLARED_TAUS:
        p=route_distributions(ids,H,tau)
        for i in ids:
            for k in ("P0","R1","C"):
                assert i not in p[i][k]
                assert all(v>0 for v in p[i][k].values())
                assert sum(p[i][k].values())==pytest.approx(1)

def test_zero_history_still_has_finite_probability():
    ids=[1,2,3]
    H={(i,j):0 for i in ids for j in ids if i!=j}
    p=route_distributions(ids,H,10)
    assert p[1]["P0"]=={2:.5,3:.5}
    assert p[1]["C"]==pytest.approx({2:.5,3:.5})

def test_reject_pseudoreplication_in_era_source():
    fake={"schema":"structural.helgeland_nestling_origin_nextyear_resight_freeze.v1_231",
          "data":{"n_model_islands":2,"source_rows":73593}}
    with pytest.raises(ValueError,match="universe"):
        matrix_by_era(fake)

def test_declared_year_cohorts_and_sensitivity_grid():
    assert COHORT_TOTALS=={"historical":259,"bridge":28,"later":173}
    assert PREDECLARED_TAUS==(5,10,20)
