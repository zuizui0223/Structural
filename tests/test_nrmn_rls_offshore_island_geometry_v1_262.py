"""Marine RLS island-nearshore assignment known-truth tests, no biological records."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from nrmn_rls_offshore_island_geometry_v1_262 import (
    shoreline_type, nearest_island_assignment, summarize_regions
)

def test_outside_island_reef_is_distinct_from_mainland_and_land():
    assert shoreline_type(100.0)== "island"
    assert shoreline_type(4.99)=="tiny_islet"
    assert shoreline_type(7_000_000.0)=="mainland"
    assert shoreline_type(6_999_999.0)=="island"

def test_5km_and_one_km_margin_are_both_required():
    assert nearest_island_assignment(
        is_inside_land=False, island_distances=[("I1",1.5)],
        mainland_distance=5.0, small_islet_distance=None) == ("near_island","I1")
    assert nearest_island_assignment(
        is_inside_land=False, island_distances=[("I1",5.1)],
        mainland_distance=None, small_islet_distance=None)[0] == "offshore_or_other"
    assert nearest_island_assignment(
        is_inside_land=False, island_distances=[("I1",1.5)],
        mainland_distance=2.1, small_islet_distance=None)[0] == "ambiguous_competing_coast"
    assert nearest_island_assignment(
        is_inside_land=False, island_distances=[("I1",0.5),("I2",0.7)],
        mainland_distance=20, small_islet_distance=None)[0] == "ambiguous_competing_coast"
    assert nearest_island_assignment(
        is_inside_land=True, island_distances=[("I1",2.0)],
        mainland_distance=20,small_islet_distance=None)[0] == "on_land_or_uncertain"
    assert nearest_island_assignment(
        is_inside_land=False, island_distances=[],
        mainland_distance=0.2,small_islet_distance=None)[0] == "mainland_nearshore"

def test_two_different_island_polygons_require_three_distinct_site_codes_each():
    observed=[
      {"group":("RLS","australia","western australia","rottnest island"),
       "site_key":"a","assignment":"near_island","island_id":"I1","strict_pairs":2},
      {"group":("RLS","australia","western australia","rottnest island"),
       "site_key":"b","assignment":"near_island","island_id":"I1","strict_pairs":2},
      {"group":("RLS","australia","western australia","rottnest island"),
       "site_key":"c","assignment":"near_island","island_id":"I1","strict_pairs":1},
      {"group":("RLS","australia","western australia","rottnest island"),
       "site_key":"d","assignment":"near_island","island_id":"I2","strict_pairs":2},
      {"group":("RLS","australia","western australia","rottnest island"),
       "site_key":"e","assignment":"near_island","island_id":"I2","strict_pairs":1},
    ]
    a=summarize_regions(observed)[0]
    assert a["qualified_archipelago_sampling_network"] is False
    observed.append({
       "group":observed[0]["group"],"site_key":"f",
       "assignment":"near_island","island_id":"I2","strict_pairs":1})
    b=summarize_regions(observed)[0]
    assert b["qualified_archipelago_sampling_network"] is True
    assert b["separate_islands_with_3plus_repeated_sites"]==2
    assert b["near_island_repeated_site_count"]==6

def test_mainland_nearshore_does_not_count_as_island_replication():
    group=("RLS","australia","new south wales","solitary islands")
    rows=[{"group":group,"site_key":str(i),"assignment":"mainland_nearshore",
           "island_id":None,"strict_pairs":2} for i in range(8)]
    assert summarize_regions(rows)[0]["qualified_archipelago_sampling_network"] is False
