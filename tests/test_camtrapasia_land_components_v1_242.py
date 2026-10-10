import pytest
pytest.importorskip("shapely")
import importlib.util,json
from pathlib import Path
from shapely.geometry import box
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location("v242",R/"scripts/check_camtrapasia_land_components_v1_242.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def test_same_landmass_and_ocean_separated_synthetic():
    land=[box(0,0,1,1),box(2,0,3,1)]
    assert m.land_component((.2,.2),(.8,.8),land)=="same_land_component"
    assert m.land_component((.2,.2),(2.2,.2),land)=="distinct_land_components_in_local_clip"
    assert m.land_component((.2,.2),(1.5,.2),land)=="one_or_both_points_outside_mapped_land"
def test_frozen_coastline_is_independent_and_biology_untouched():
    d=json.loads((R/"development/camtrapasia_land_component_contract_v1_242.json").read_text())
    assert d["fixed_geometric_rule"]["focal_study_count"]==15
    assert d["source_land"]["official_url"]==m.URL
    assert d["fixed_geometric_rule"]["local_polygon_bbox_expand_degrees"]==.5
    assert d["fixed_geometric_rule"]["no_biological_or_site_specific_score"] is True
    assert all(v is False for v in d["safeguards"].values())
