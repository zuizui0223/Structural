import pytest
shapely=pytest.importorskip("shapely")
import importlib.util,json
from pathlib import Path
from shapely.geometry import box
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v243",R/"scripts/check_camtrapasia_gadm36_landmass_v1_243.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_landmass_polygon_same_vs_distinct_and_outside():
    land=[box(0,0,1,1),box(2,0,3,1)]
    assert m.classify((.2,.3),(.7,.7),land)=="same_component"
    assert m.classify((.2,.3),(2.2,.3),land)=="different_component"
    assert m.classify((.2,.3),(1.4,.3),land)=="one_or_both_outside"
def test_original_gadm_file_pinned_no_species_values():
    d=json.loads((R/"development/camtrapasia_gadm36_landmass_contract_v1_243.json").read_text())
    assert d["data_source"]["git_commit"]==m.PIN
    assert d["specified_decision"]["no_species_incidence_or_presence_values_read"] is True
    assert d["reliability"]["full_original_GADM_polygon_island_ID_not_recovered"] is True
    assert all(v is False for v in d["safeguards"].values())
