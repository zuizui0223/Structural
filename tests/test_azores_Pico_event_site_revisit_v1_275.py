"""Pico source Event-only fixed-site versus GPS-neighborhood revisit tests."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores_Pico_event_site_revisit_v1_275 import audit_event_core_rows,parse_author_event_day


def event(site,yr,month,day,lat=38.47,lon=-28.34,method="plant survey"):
    return {
        "coreid":f"{site}-{yr}-{month}-{day}",
        "island":"Pico",
        "locationID":site,
        "eventDate":f"{month}/{day}/{yr}",
        "year":str(yr),"month":str(month),"day":str(day),
        "decimalLatitude":str(lat),"decimalLongitude":str(lon),
        "samplingProtocol":method,
        "locality":"Pico", "coordinateUncertaintyInMeters":"12"
    }


def example():
    rows=[]
    for yr in (2020,2021):
        for day in (8,20):
            rows.append(event("LOC-A",yr,6,day))
    rows.append(event("LOC-B",2021,6,7,38.5,-28.4))
    rows.append(event("LOC-C",2021,6,7,38.48,-28.32))
    rows.append(event("LOC-C",2022,6,7,38.60,-28.3))
    rows.append(event("",2020,7,9,38.51111,-28.41231))
    rows.append(event("",2021,7,9,38.51111,-28.41231))
    return rows


def test_pico_author_mdy_days_rebuilt_from_components_not_reverse_order():
    assert parse_author_event_day(event("a",2020,10,13)).isoformat()=="2020-10-13"
    wrong=event("a",2020,10,13);wrong["day"]="12"
    try:parse_author_event_day(wrong)
    except ValueError:pass
    else:raise AssertionError("Mismatch in author day components accepted")


def test_author_site_revisit_vs_gps_neighbor_sensitivity():
    rows=example()
    report=audit_event_core_rows(rows,expected_years=None)
    assert report["original_Event_core_rows"]==9
    assert report["source_author_locationID_site_keys"]==3
    assert report["author_siteIDs_with_repeated_years_unchecked_coordinates"]==2
    assert report["author_siteIDs_rejected_spatial_instability"]==1
    assert report["author_siteIDs_revisited_2plus_years_with_verified_coordinates"]==1
    assert report["author_siteIDs_with_2plus_distinct_dates_each_in_2plus_years"]==1
    assert report["author_siteID_protocols_consistent_over_years"]==1
    assert report["GPS_5decimal_clusters_revisited_2plus_years"]==2
    assert report["positive_plant_species_rows_read"]==0
    assert not any(v in str(report) for v in ("LOC-A","LOC-B","LOC-C","38.47","-28.34"))


def test_invalid_event_date_is_stop_not_false_repeat():
    x=example()
    x[0]["eventDate"]="bad-date"
    try: audit_event_core_rows(x,None)
    except ValueError as e: assert "author date" in str(e).lower()
    else:raise AssertionError("Invalid author date silently accepted")


def test_event_id_cannot_be_site_identity_and_missing_coordinates_are_unknown():
    events=[
        event("a",2020,4,12),event("b",2021,4,13),
        event("NO-GPS",2020,6,14),event("NO-GPS",2021,6,15)
    ]
    for rec in events[-2:]:
        rec["decimalLatitude"]="";rec["decimalLongitude"]=""
    r=audit_event_core_rows(events,None)
    assert r["source_author_locationID_site_keys"]==3
    assert r["author_siteIDs_revisited_2plus_years_with_verified_coordinates"]==0
    assert r["author_siteIDs_with_repeated_years_but_no_all_valid_coordinates"]==1
    assert r["positive_plant_species_rows_read"]==0


def test_repeated_survey_events_on_only_one_day_not_independent_repeat_dates():
    x=[event("one",2020,5,8), event("one",2020,5,8),
       event("one",2021,5,8), event("one",2021,5,8)]
    for i,r in enumerate(x):r["coreid"]=str(i)
    summary=audit_event_core_rows(x,None)
    assert summary["author_siteIDs_revisited_2plus_years_with_verified_coordinates"]==1
    assert summary["author_siteIDs_with_2plus_distinct_dates_each_in_2plus_years"]==0


def test_predeclared_source_date_histogram_mismatch_stops():
    rows=example()
    try:audit_event_core_rows(rows,{"2020":171,"2021":1603,"2022":898,"2024":129})
    except ValueError as e:assert "source years" in str(e).lower()
    else:raise AssertionError("Unverified source cohort accepted")
