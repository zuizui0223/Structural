"""Only synthetic permutation and year-omission known truth, no birds opened."""
import math,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_source_year_alignment_v1_245 import (
    permutation_diagnostic,omission_deltas,ROUTES,YEARS)

def test_identity_is_best_for_matching_frozen_years():
    a=permutation_diagnostic([[0,10,10],[10,0,10],[10,10,0]])
    assert a["assignments"]==6
    assert a["observed_identity_alignment_total_logloss"]==0
    assert a["more_favorable_assignments"]==0
    assert a["exact_tied_assignments"]==1

def test_identity_can_be_worst_out_of_shuffles():
    a=permutation_diagnostic([[10,0],[0,10]])
    assert a["assignments"]==2
    assert a["more_favorable_assignments"]==1
    assert a["fraction_at_least_as_favorable_including_ties"]==1

def test_complete_7_plus_21_year_omission():
    yrs=[{"year":year,"n":1,"delta":d}
         for year,d in zip(YEARS,(1,2,3,4,5,6,7))]
    # Simplify only synthetic count anchor for this unit test.
    from helgeland_source_year_alignment_v1_245 import omission_deltas as orig
    with pytest.raises(ValueError):
        orig(yrs)

def test_only_predeclared_route_and_year_names():
    assert ROUTES==("P0","H","R2","C2")
    assert YEARS==tuple(range(2015,2022))
