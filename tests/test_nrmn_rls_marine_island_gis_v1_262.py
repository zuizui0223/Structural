"""Pure synthetic marine-coastline and Method 1 site frame tests; no fish or raw GIS data."""
import json
from pathlib import Path
import sys

import pytest
from shapely.geometry import box

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from nrmn_rls_marine_island_gis_v1_262 import (
    classify_marine_site, summarize_island_regions, strict_eligible_RLS_sites
)

ROOT=Path(__file__).resolve().parents[1]
G=json.loads((ROOT/"development/nrmn_rls_marine_island_gis_protocol_v1_262.json").read_text())
M=json.loads((ROOT/"development/nrmn_rls_method1_physical_protocol_v1_261.json").read_text())

def sample(sid,site,year,month=7,method="1, 2",longitude=0,latitude=0,place="rottnest island"):
    return {"survey_id":sid,"survey_date":f"{year}-{month:02d}-15",
            "country":"Australia","area":"Western Australia","location":place,
            "site_code":site,"latitude":latitude,"longitude":longitude,
            "depth":8.0,"program":"RLS","methods":method}

def test_method1_event_frame_requires_true_repeated_two_transects():
    records=[]; i=1
    for site,lon in (("A",1.05),("B",1.06),("C",1.07)):
        for year in (2020,2021,2022):
            for _ in range(2):
                records.append(sample(i,site,year,longitude=lon,latitude=.5));i+=1
    for year in (2020,2021,2022):
        for _ in range(2):
            records.append(sample(i,"off",year,method="0, 2",longitude=1.04,latitude=.5));i+=1
    sites,stats=strict_eligible_RLS_sites(records,G,M)
    assert len(sites)==3
    assert sum(s["strict_pairs"] for s in sites)==6
    assert stats["method1_strict_pairs_in_frozen_10_groups"]==6
    assert stats["method1_eligible_unique_sites_in_frozen_10_groups"]==3
    assert stats["fish_responses_read"] is False

def test_single_island_nearshore_vs_mainland_closer():
    polygon=[
      ("ISLAND",20.0,box(0,0,1,1)),
      ("MAIN",8_000_000.0,box(1.08,0,2,1))
    ]
    # Marine site nearer to island at lon=1.02 than mainland at 1.08.
    near=classify_marine_site(.5,1.02,polygon,G)
    assert near["class"]=="island_nearby"
    assert near["island_id"]=="ISLAND"
    # This marine site is much closer to mainland than to island.
    near_m=classify_marine_site(.5,1.07,polygon,G)
    assert near_m["class"]=="mainland_or_ambiguous"

def test_ambiguous_two_islands_not_assigned_arbitrarily():
    polygon=[
      ("LEFT",5.0,box(0,0,1,1)),
      ("RIGHT",5.0,box(1.04,0,2.04,1))
    ]
    r=classify_marine_site(.5,1.02,polygon,G)
    assert r["class"]=="ambiguous_near_two_islands"
    assert r["island_id"] is None

def test_marine_points_inside_landmass_not_classed_as_reefs():
    polygon=[("ISLAND",5.0,box(0,0,1,1))]
    r=classify_marine_site(.5,.5,polygon,G)
    assert r["class"]=="marine_location_inside_landmass_polygon"
    assert r["island_id"] is None

def test_two_distinct_islands_need_three_sites_each():
    prefix={"country":"australia","area":"western australia","location":"rottnest island"}
    sites=[]
    for p,n in (("L",3),("R",3)):
        for i in range(n):
            sites.append({**prefix,"program":"RLS","lat":.5,
                "lon":1.02+i*.001 if p=="L" else 3.02+i*.001,
                "strict_pairs":2,"source_site_label":p+str(i)})
    polygon=[
      ("LEFT",10.0,box(0,0,1,1)),
      ("RIGHT",10.0,box(2,0,3,1))
    ]
    report=summarize_island_regions(sites,polygon,G,M)
    row=next(x for x in report["frozen_ten_RLS_regions"] if x["location"]=="rottnest island")
    assert row["island_polygons_with_3plus_eligible_sites"]==2
    assert row["two_island_survey_geometry_eligible"] is True
    assert row["method1_annual_pairs_at_island_assigned_sites"]==12
    assert report["fish_biological_rows_accessed"]==0
    assert "source_site_label" not in str(report)
    # Remove one source site: strict 3-per-island condition fails.
    sites.pop()
    fail=summarize_island_regions(sites,polygon,G,M)
    assert next(x for x in fail["frozen_ten_RLS_regions"]
                if x["location"]=="rottnest island")["two_island_survey_geometry_eligible"] is False

def test_polygon_area_floor_uses_marine_islet_limit_not_fake_mainland():
    polygon=[("TINY",0.03,box(0,0,1,1))]
    r=classify_marine_site(.5,1.02,polygon,G)
    assert r["class"]=="no_eligible_island_within_5km"

def test_freeze_guard_rejects_changed_polygon_threshold():
    bad=json.loads(json.dumps(G))
    bad["geography"]["max_site_to_island_shore_km"]=15
    with pytest.raises(ValueError):
        classify_marine_site(.5,1.02,[("I",5.0,box(0,0,1,1))],bad)
