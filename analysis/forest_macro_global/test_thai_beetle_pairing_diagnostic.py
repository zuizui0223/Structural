"""Synthetic canopy/understorey original station and seasonal pairing tests."""
import importlib.util,datetime
from pathlib import Path

p=Path(__file__).with_name("thai_beetle_pairing_diagnostic.py")
spec=importlib.util.spec_from_file_location("thai_original_pairing",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    events=[]
    for forest in ("forestA","forestB"):
        for i in range(9):
            lat=12.0+(0.5 if forest=="forestB" else 0)+0.002*(i//3)
            lon=101.0+0.002*(i%3)
            for season,day in enumerate(("2019-06-01","2019-12-01")):
                for layer in ("canopy","understory"):
                    for jar in ("top","bottom"):
                        eid="e-"+str(len(events))
                        events.append({
                          "_core_id":eid, "eventID":eid,
                          "locationID":forest,
                          "samplingProtocol":f"slam trap ({layer} {jar} jar)",
                          "decimalLatitude":str(lat+(0.0001 if layer=="canopy" else 0)),
                          "decimalLongitude":str(lon),"eventDate":day
                        })
    return events,[]

def test_distances_and_two_campaigns():
    assert m.haversine_m((0,0),(0,0))==0
    assert abs(m.haversine_m((0,0),(0.0001,0))-11.12)<0.1
    group,days=m.campaigns(["2019-06-01","2019-06-10","2019-12-01"])
    assert len(days)==2

def test_original_sites_are_not_144_independent_forests():
    original=m.original_tables
    try:
        m.original_tables=lambda data:fixture()
        x=m.diagnose(b"synthetic")
    finally:
        m.original_tables=original
    assert x["forest_n"]==2
    assert x["total_SLAM_jar_event_rows"]==144
    assert x["expected_station_pairs"]==18
    assert x["all_pairs_unique_reciprocal_and_le_60m"]
    assert len(x["forest_pairing_diagnostics"])==2
    assert all(y["original_temporal_campaign_count_from_60day_gap"]==2 for y in x["forest_pairing_diagnostics"])
    assert not x["biological_taxon_values_used_for_pairing"]
    assert x["no_raw_coords_or_eventIDs_exported"]

def test_unmatched_distinct_strata_fail_spatial_gate():
    events,_=fixture()
    for e in events:
        if "canopy" in e["samplingProtocol"] and e["locationID"]=="forestA":
            e["decimalLatitude"]=str(float(e["decimalLatitude"])+0.01)
    original=m.original_tables
    try:
        m.original_tables=lambda data:(events,[])
        x=m.diagnose(b"synthetic")
    finally:
        m.original_tables=original
    assert not x["all_pairs_unique_reciprocal_and_le_60m"]
