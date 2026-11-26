"""Reproducible known-truth canopy trap-height × capture ratio checks."""
import importlib.util
import math
from pathlib import Path

p=Path(__file__).with_name("thai_beetle_trap_height_association.py")
spec=importlib.util.spec_from_file_location("thai_beetle_height",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_original_source_height_field_numeric_and_missing_fail():
    assert m.numeric_trap_height({"dynamicProperties":"trap height in meters:24.5"})==24.5
    for bad in ({"dynamicProperties":""},
                {"dynamicProperties":"trap height in meters:10","eventRemarks":"trap height in meters:20"}):
        try:
            m.numeric_trap_height(bad)
            assert False
        except ValueError as e:
            assert "missing_or_conflicting" in str(e)


def test_forest_centering_and_permutation_detect_known_height_association():
    st=[]
    for f in ("A","B"):
        for i in range(9):
            height=12+i
            y=(height-16)*0.08 + (2 if f=="B" else 0)
            st.append({"forest":f,"height_m":height,"log_canopy_over_lower":y})
    assert abs(m.forest_centered_slope_10m(st)-.8)<1e-12
    r=m.inference(st,permutations=99,bootstraps=300)
    assert r["within_forest_centered_log_ratio_slope_per_10m"]>.79
    assert r["two_sided_station_height_permutation_p_within_2_forests"]<=.05
    assert r["within_forest_station_bootstrap_95CI_log_ratio_slope_per_10m"][0]>.70
    assert r["leave_one_station_out_same_sign_count"]==18


def source_fixture():
    ev=[];occ=[]
    canopy_source_count=0
    for f,base in (("SourceX",12.),("SourceY",14.)):
        for i in range(9):
            lat=base+(i//3)*.003
            lon=100+(i%3)*.003
            for day in ("2019-06-01","2019-12-01"):
                for layer in ("canopy","understory"):
                    for jar in ("top","bottom"):
                        eid="private-evt-"+str(len(ev))
                        event={
                          "_core_id":eid,"eventID":eid,"locationID":f,
                          "samplingProtocol":f"SLAM trap ({layer} {jar} jar)",
                          "decimalLatitude":str(lat+(.0001 if layer=="canopy" else 0)),
                          "decimalLongitude":str(lon),
                          "eventDate":day,
                          "sampleSizeUnit":"days","sampleSizeValue":"10",
                          "samplingEffort":"10 days",
                          "dynamicProperties":("trap height in meters:"+str(13+i if layer=="canopy" else 2)),
                          "eventRemarks":"","locationRemarks":""
                        }
                        ev.append(event)
                        n=7 if layer=="understory" else 12+i
                        if layer=="canopy":
                            if canopy_source_count<34:n-=1
                            canopy_source_count+=1
                        occ.append({"_core_id":eid,"individualCount":str(n),
                                    "family":"Curculionidae","taxonRank":"family"})
    assert sum(int(x["individualCount"]) for x in occ)==1622
    return ev,occ


def test_exact_jars_two_campaigns_and_18_station_support():
    e,o=source_fixture()
    x=m.study(e,o)
    assert x["original_forest_n"]==2 and x["physical_stations_n"]==18
    assert x["source_original_SLAM_jar_events"]==144
    assert x["source_original_beetle_individuals"]==1622
    assert x["source_canopy_trap_height_m_min"]==13
    assert x["source_canopy_trap_height_m_max"]==21
    assert x["understory_trap_height_m"]==2
    assert x["association_estimate"]["within_forest_centered_log_ratio_slope_per_10m"]>0
    assert x["temperature_and_light_logger_time_series_not_used"]
    assert x["not_evidence_of_thermal_escape_behavior_or_warming_response"]
    assert x["raw_station_forest_identifiers_and_coordinates_not_exported"]
    assert "SourceX" not in str(x) and "private-evt" not in str(x)


def test_trap_height_unverified_source_cannot_be_backfilled_from_elevation():
    e,o=source_fixture()
    e[0]["dynamicProperties"]=""
    e[0]["minimumElevationInMeters"]="249"
    try:
        m.study(e,o)
        assert False
    except ValueError as exc:
        assert "trap_height" in str(exc)
