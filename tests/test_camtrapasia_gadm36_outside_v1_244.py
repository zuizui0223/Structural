import pytest
pytest.importorskip("shapely")
from shapely.geometry import box
from shapely.strtree import STRtree
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v244",ROOT/"scripts/camtrapasia_gadm36_outside_diagnostic_v1_244.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_shoreline_distance_when_outside():
    ps=[box(0,0,1,1)]
    t=STRtree(ps)
    assert m.point_status((.4,.6),ps,t)["inside"] is True
    r=m.point_status((1.01,.6),ps,t)
    assert r["inside"] is False
    assert r["distance_to_land_km"]>0
def test_no_reclassification_for_unknown_source():
    x=json.loads((ROOT/"development/camtrapasia_gadm36_outside_diagnostic_v1_244.json").read_text())
    assert x["scientific_ceiling"]["no_retroactive_assignment_of_unknown_to_same_land_component"] is True
    assert x["scientific_ceiling"]["source_biological_observations_unopened"] is True
    assert all(v is False for v in x["policy"].values())
