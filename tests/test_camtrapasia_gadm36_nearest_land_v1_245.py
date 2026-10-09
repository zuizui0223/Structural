import pytest
pytest.importorskip("shapely")
from shapely.geometry import box
from shapely.strtree import STRtree
import importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v245",R/"scripts/camtrapasia_gadm36_nearest_land_v1_245.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_nearest_component_does_not_modify_geometry_or_use_outcome():
    parts=[box(0,0,1,1),box(2,0,3,1)]
    tree=STRtree(parts)
    assert m.point_component((.4,.4),parts,tree)==0
    assert m.point_component((1.1,.4),parts,tree) is None
    assert m.nearest_country_component((1.1,.4),parts,tree)==0
    assert m.nearest_country_component((1.9,.4),parts,tree)==1
def test_frozen_study_and_no_scoring():
    x=json.loads((R/"development/camtrapasia_gadm36_nearest_land_contract_v1_245.json").read_text())
    assert x["frozen_site_set_v241"]["n"]==15
    assert x["precommitted_method"]["no_new_distance_threshold"] is True
    assert x["limits"]["reported_nearest_reassignment_is_posthoc_spatial_diagnostic"] is True
    assert all(z is False for z in x["safeguards"].values())
