from pathlib import Path
import importlib.util,json
import pytest
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/freeze_ala_island_geometry_crosswalk_v1_191.py"
CONTRACT=ROOT/"development/global_mammals_ala_island_geometry_gate_v1_191.json"

def module():
    spec=importlib.util.spec_from_file_location("ala_v191",SCRIPT)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def test_one_to_one_geometry_accepts_polygon_interior():
    shape=pytest.importorskip("shapely.geometry")
    tree=pytest.importorskip("shapely.strtree")
    m=module()
    p=shape.Polygon([(0,0),(2000,0),(2000,2000),(0,2000)])
    geom=[p]
    res=m.select_match(shape.Point(1000,1000),4.0,tree.STRtree(geom),geom,["FID1"],.25,4.0)
    assert res[0]=="FID1" and res[2]=="candidate"
    assert abs(res[1]-1.0)<1e-12

def test_ambiguous_polygon_is_excluded():
    shape=pytest.importorskip("shapely.geometry")
    tree=pytest.importorskip("shapely.strtree")
    m=module()
    p=shape.Polygon([(0,0),(2000,0),(2000,2000),(0,2000)])
    geoms=[p,p]
    res=m.select_match(shape.Point(1000,1000),4.0,tree.STRtree(geoms),geoms,["FID1","FID2"],.25,4.0)
    assert res[2]=="ambiguous_geometry"

def test_area_drift_is_excluded_even_when_centroid_matches():
    shape=pytest.importorskip("shapely.geometry")
    tree=pytest.importorskip("shapely.strtree")
    m=module()
    p=shape.Polygon([(0,0),(2000,0),(2000,2000),(0,2000)])
    res=m.select_match(shape.Point(1000,1000),.1,tree.STRtree([p]),[p],["FID1"],.25,4.0)
    assert res[2]=="area_mismatch"

def test_contract_forbids_both_biological_label_sources():
    c=json.loads(CONTRACT.read_text())
    assert c["geometry_gate"]["min_exact_one_to_one_heldout_islands"]==30
    assert c["source"]["response_mammals_zip_must_not_be_downloaded"] is True
    assert c["endpoint_boundary"]["external_ala_mammal_event_values_opened"]==0
    assert c["endpoint_boundary"]["original_heldout_occurrence_values_opened"]==0
    assert c["endpoint_boundary"]["model_refit_authorized"] is False
    assert c["endpoint_boundary"]["external_biological_scoring_authorized"] is False
    assert c["endpoint_boundary"]["eBird_enabled"] is False
