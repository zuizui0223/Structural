"""Synthetic coastline examples only: never accesses BioTIME species or actual island GIS."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from biotime_v2_gshhg_island_crosswalk_v1_256 import (
    site_class,classify_points_with_polygons,summarize
)
from shapely.geometry import box

def test_landmass_category_thresholds_and_coastline_conservatism():
    assert site_class(50,5)=="island_polygon_interior"
    assert site_class(50,.2)=="shoreline_ambiguity"
    assert site_class(2,5)=="small_landmass_below_threshold"
    assert site_class(9_000_000,0)=="mainland"
    assert site_class(10,.5,threshold=20)=="small_landmass_below_threshold"

def test_fixed_synthetic_islands_not_confused_with_mainland_or_water():
    rows=[
      {"study":"A","realm":"Terrestrial","latitude":"0.5","longitude":"0.5","strict_matched_pair_n":"2"},
      {"study":"A","realm":"Terrestrial","latitude":"0.5","longitude":"2.5","strict_matched_pair_n":"1"},
      {"study":"A","realm":"Terrestrial","latitude":"0.5","longitude":"5.5","strict_matched_pair_n":"2"},
      {"study":"A","realm":"Terrestrial","latitude":"0.0001","longitude":"0.5","strict_matched_pair_n":"1"},
    ]
    islands=[
      ("X",100.0,box(0,0,1,1)),
      ("Y",9_000_000.0,box(2,0,3,1))
    ]
    classified=classify_points_with_polygons(rows,islands)
    assert [r["class"] for r in classified]==[
        "island_polygon_interior","mainland",
        "water_or_no_land_polygon","shoreline_ambiguity"
    ]
    assert classified[0]["polygon_id"]=="X"
    assert classified[0]["interior_shore_distance_km"]>1
    assert classified[3]["interior_shore_distance_km"]<1
    assert not classified[1]["sensitivity_025km_1km2"]

def test_marine_sites_do_not_enter_terrestrial_island_networks():
    cohort={"selected_study_ids_by_realm":{
        "Freshwater":["F"],"Marine":["M"],"Terrestrial":["T"]}}
    classified=[]
    for realm,sid in (("Freshwater","F"),("Marine","M"),("Terrestrial","T")):
        for island in ("A","B"):
            for _ in range(3):
                classified.append({
                    "study":sid,"realm":realm,"polygon_id":island,
                    "class":"island_polygon_interior",
                    "sensitivity_025km_1km2":True,
                    "sensitivity_1km_20km2":True,
                    "strict_matched_pair_n":1
                })
    report,rows=summarize(classified,cohort,{"tag":"synthetic"},{"source_total_polygons":2})
    assert report["strict_multi_island_study_network_total"]==2
    assert next(r for r in rows if r["study"]=="M")["inter_island_network_primary"] is False
    assert next(r for r in rows if r["study"]=="T")["inter_island_network_primary"] is True
