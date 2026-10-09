import pytest,importlib.util,json
from pathlib import Path
pytest.importorskip("shapely");pytest.importorskip("pyproj")
from shapely.geometry import box
R=Path(__file__).resolve().parents[1]
sp=importlib.util.spec_from_file_location("test248",R/"scripts/camtrapasia_all239_polygon_v1_248.py")
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def test_true_area_and_geometry_matching():
    poly=box(0,0,1,1)
    area=m.geodetic_polygon_area_km2(poly)
    cand={"point":(.2,.3),"area":area,"block":"X"}
    assert len(m.eligible(poly,area,{"1":cand}))==1
    assert m.eligible(poly,area,{"1":{**cand,"area":area/100}})==[]
    assert m.eligible(poly,area,{"1":{**cand,"point":(5,5)}})==[]
def test_original_locks_and_no_initial_radius():
    a=json.loads((R/"development/camtrapasia_full239_polygon_identity_contract_v1_248.json").read_text())
    assert a["prespecified_match"]["NO_25km_survey_center_to_centroid_filter"] is True
    assert a["prespecified_match"]["original_heldout_island_area_ratio_to_polygon_max"]==2
    assert a["prespecified_match"]["original_heldout_centroid_covered_or_at_most_km_from_polygon"]==5
    assert all(z is False for z in a["safeguards"].values())
