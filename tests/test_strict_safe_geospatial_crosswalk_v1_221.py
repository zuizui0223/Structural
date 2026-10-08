import pytest
pytest.importorskip('numpy')
pytest.importorskip('scipy')
import json
from pathlib import Path
import importlib.util
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("geo221",ROOT/"scripts/strict_safe_geospatial_crosswalk_v1_221.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_geography_threshold_is_literal_and_no_id_matching():
    x=json.loads((ROOT/"development/strict_spatial_crosswalk_contract_v1_221.json").read_text())
    a=x["precommitted_algorithm"]
    assert a["maximum_great_circle_km"]==5
    assert a["maximum_larger_to_smaller_area_ratio"]==1.5
    assert a["no_fuzzy_names"] is True
    assert x["source_Barreto_safe"]["rows"]==5592
    assert x["source_Weigelt_safe"]["rows"]==17883
    assert all(v is False for v in x["policy"].values())
def test_candidate_unique_geolocation_and_area():
    b=[{"id":"11","lat":0.,"lon":0.,"area":20.,"selected":True},
       {"id":"12","lat":10.,"lon":10.,"area":20.,"selected":False}]
    w=[{"id":"999","lat":0.001,"lon":0.001,"area":20.},
       {"id":"1000","lat":10.001,"lon":10.002,"area":40.}]
    matches,ambig_a,ambig_b=m.strict_matches(b,w)
    assert len(matches)==1
    assert matches[0][0]==0 and matches[0][1]==0
    assert ambig_a==0 and ambig_b==0
def test_no_ambiguous_close_double_matching():
    b=[{"id":"1","lat":0.,"lon":0.,"area":20.,"selected":True}]
    w=[{"id":"1","lat":0.001,"lon":0.001,"area":20.},
       {"id":"2","lat":0.002,"lon":0.002,"area":20.}]
    matched,ab,aw=m.strict_matches(b,w)
    assert not matched and ab==1
