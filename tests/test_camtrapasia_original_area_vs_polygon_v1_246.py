import pytest
pytest.importorskip("shapely")
pytest.importorskip("pyproj")
import importlib.util,json
from pathlib import Path
from shapely.geometry import box
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v246",R/"scripts/camtrapasia_original_island_vs_GADM_area_v1_246.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_GADM_ellipsoidal_polygon_area_km2_and_pinned_safety():
    area=m.geodetic_polygon_area_km2(box(0,0,1,1))
    assert 12000<area<13000
    d=json.loads((R/"development/camtrapasia_original_island_area_contract_v1_246.json").read_text())
    assert d["method"]["strict_ratio_threshold_primary"]==2
    assert d["method"]["sensitivity_thresholds"]==[1.5,5]
    assert d["interpretation"]["offland_source_nearest_polygon_heuristic_remains_unverified"] is True
    assert all(x is False for x in d["guards"].values())
