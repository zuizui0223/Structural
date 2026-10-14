"""Synthetic: changing source marked counts changes destination while no target leaks."""
import math,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_annual_natal_supply_v1_244 import (
   predict_receiving,HISTORY_YEARS,FUTURE_YEARS,PRIMARY_ROUTE,ISLANDS)
def test_known_source_state_changes_recipient_without_future_inputs():
    ids=[1,2,3]
    r={1:{2:.9,3:.1},2:{1:.6,3:.4},3:{1:.2,2:.8}}
    h={1:.1,2:.1,3:.1}
    equal=predict_receiving(ids,r,{1:10,2:10,3:10},h)
    source1=predict_receiving(ids,r,{1:100,2:10,3:10},h)
    assert source1[2]>equal[2]
    assert sum(source1.values())==pytest.approx(1)
def test_no_supply_stops_instead_of_imputing():
    ids=[1,2,3];r={1:{2:.5,3:.5},2:{1:.5,3:.5},3:{1:.5,2:.5}}
    with pytest.raises(ValueError):predict_receiving(ids,r,{1:0,2:0,3:0},{1:.1,2:.1,3:.1})
def test_years_and_ref_are_predeclared():
    assert HISTORY_YEARS[0]==1994 and HISTORY_YEARS[-1]==2013
    assert FUTURE_YEARS==(2015,2016,2017,2018,2019,2020,2021)
    assert PRIMARY_ROUTE=="R2"
    assert len(ISLANDS)==11
