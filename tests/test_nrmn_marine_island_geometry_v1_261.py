"""v1.261 source-free tests: marine physical-site identity, not fish outcomes."""
from pathlib import Path
import sys
from shapely.geometry import box

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from nrmn_marine_island_geometry_v1_261 import (
    methods_have_m1, repeated_m1_site_summary,
    marine_nearest_landmass, network_island_support,
)

GROUP=("RLS","australia","new south wales","solitary islands")
ISLANDS=[("A",100.0,box(0.0,0.0,1.0,1.0)),
         ("B",100.0,box(3.0,0.0,4.0,1.0)),
         ("MAIN",9_000_000.0,box(8.0,0.0,9.0,1.0))]

def synthetic_events():
    rows=[]
    sid=100
    # Six independent reef site codes, three assigned to each island.
    for prefix,lon in (("a",-0.02),("b",2.98)):
        for j,lat in enumerate((0.2,0.5,0.8)):
            code=prefix+str(j)
            for yr in (2020,2021,2022):
                for event in (1,2):
                    sid+=1
                    rows.append({
                        "survey_id":sid, "survey_date":f"{yr}-07-0{event}",
                        "country":"Australia","area":"New South Wales",
                        "location":"Solitary Islands", "site_code":code,
                        "latitude":lat,"longitude":lon,
                        "program":"RLS","methods":"1, 2"})
    # Method 13 alone cannot be counted as Method 1.
    rows.append({
        "survey_id":999,"survey_date":"2021-07-03",
        "country":"Australia","area":"New South Wales",
        "location":"Solitary Islands","site_code":"a0",
        "latitude":0.2,"longitude":-0.02,
        "program":"RLS","methods":"13, 2"})
    # Other program/location must be excluded.
    rows.append({
        "survey_id":1000,"survey_date":"2021-07-03",
        "country":"Australia","area":"New South Wales",
        "location":"Solitary Islands","site_code":"ATRC_ONLY",
        "latitude":0.3,"longitude":-0.02,
        "program":"ATRC","methods":"1, 2"})
    return rows

def test_m1_method_token_required_not_substring():
    assert methods_have_m1("1,2")
    assert methods_have_m1("0, 1, 13, 2")
    assert methods_have_m1(" 2 ; 1 ")
    assert not methods_have_m1("13, 2")
    assert not methods_have_m1("10, 2")
    assert not methods_have_m1("0, 2, 3")
    assert not methods_have_m1(None)

def test_six_sites_two_year_transitions_each_without_fish_fields():
    sites,stats=repeated_m1_site_summary(synthetic_events(),{GROUP})
    assert len(sites)==6
    assert sum(x["strict_pairs"] for x in sites)==12
    assert all(x["n_prior_years"]==2 for x in sites)
    assert all(x["n_observed_years"]==3 for x in sites)
    assert stats["unique_valid_survey_ids"]==38
    assert stats["method1_surveys_in_frozen_groups"]==36
    assert stats["excluded_no_m1_in_frozen_group"]==1
    assert stats["excluded_group_event_count"]==1
    assert not any("species" in str(x).lower() or "biomass" in str(x).lower() for x in sites)

def test_landmass_assignment_marine_point_land_and_coastal_margin():
    near_a=marine_nearest_landmass(-0.02,0.5,ISLANDS)
    assert near_a["class"]=="island_nearshore"
    assert near_a["polygon_id"]=="A"
    assert 0 < near_a["coast_km"] < 5
    assert marine_nearest_landmass(0.5,0.5,ISLANDS)["class"]=="on_land_ambiguous"
    assert marine_nearest_landmass(7.98,0.5,ISLANDS)["class"]=="mainland_nearshore"
    assert marine_nearest_landmass(13,3,ISLANDS)["class"]=="no_polygon_within_radius"

def test_two_island_reef_network_with_three_strict_sites_and_repeated_years_each():
    sites,stats=repeated_m1_site_summary(synthetic_events(),{GROUP})
    for s in sites:
        s.update(marine_nearest_landmass(s["lon"],s["lat"],ISLANDS))
    groups=network_island_support(sites,{GROUP})
    assert len(groups)==1
    g=groups[0]
    assert g["stable_m1_sites_with_strict_pairs"]==6
    assert g["strict_adjacent_year_site_month_pairs"]==12
    assert g["island_polygons_with_3plus_sites_and_3plus_pairs_and_2plus_years"]==2
    assert g["qualified_multi_island_reef_network"] is True
    assert g["island_site_counts"]==6
    assert g["island_strict_pairs"]==12
    assert all("site_code" not in k and "survey_id" not in k for k in g)

def test_one_island_only_never_passes_between_island_support():
    sites,_=repeated_m1_site_summary(synthetic_events(),{GROUP})
    for s in sites:
        s.update(marine_nearest_landmass(s["lon"],s["lat"],ISLANDS))
    for s in sites:
        if s["polygon_id"]=="B":
            s["class"]="unassigned_for_test"
            s["polygon_id"]=None
    g=network_island_support(sites,{GROUP})[0]
    assert g["qualified_multi_island_reef_network"] is False
    assert g["island_polygons_with_3plus_sites_and_3plus_pairs_and_2plus_years"]==1

def test_duplicate_survey_id_does_not_create_fake_replicated_transects():
    events=synthetic_events()
    extra=dict(events[0]);extra["survey_date"]="2020-07-03"
    sites,stats=repeated_m1_site_summary(events+[extra],{GROUP})
    assert stats["duplicated_survey_id"]==1
    assert len(sites)==6
    assert sum(s["strict_pairs"] for s in sites)==12
