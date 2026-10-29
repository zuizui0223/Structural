"""2024 Terceira original Event elevation common-support before any species.

20 original native/exotic physical plots under 326 source Event rows,
with separate GRD/UND/CAN SLAM and epigean pitfall opportunities.
"""
import copy,json,math,sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from terceira2024_original_forest_elevation_event_v1_333 import (
    audit_source,habitat,locationID,method,vertical
)

def contract():
    return json.loads((ROOT/"development/terceira2024_forest_elevation_overlap_event_gate_v1_333.json").read_text())

def fixture(*,elevation_overlap=False):
    rows=[]
    for site in range(20):
        native=site<10
        label=f"TER_{'NAT' if native else 'EXO'}_{site:02d}"
        ht="Native forest" if native else "Exotic forest"
        e=(590.+site*25) if native else (610.+(site-10)*15 if elevation_overlap else 256.+(site-10)*20)
        base={
            "locationID":label,
            "habitat":ht,
            "island":"Terceira",
            "eventDate":"2024-09-15",
            "minimumElevationInMeters":str(e),
            "decimalLatitude":str(38.6+site*.002),
            "decimalLongitude":str(-27.4+site*.002),
        }
        for layer in ("GRD","UND","CAN"):
            idx=len(rows)
            rows.append({
                **base,"__author_original_coreid":f"original_slam_{site}_{layer}",
                "eventID":f"orig_event_{idx:03d}",
                "samplingProtocol":"SLAM trap",
                "eventRemarks":layer,
                "locationRemarks":layer
            })
    for num in range(266):
        site=num%20
        native=site<10
        e=(590.+site*25) if native else (610.+(site-10)*15 if elevation_overlap else 256.+(site-10)*20)
        rows.append({
            "__author_original_coreid":f"original_pitfall_{num:03d}",
            "eventID":f"orig_pitfall_{num:03d}",
            "eventDate":"2024-08-01",
            "locationID":f"TER_{'NAT' if native else 'EXO'}_{site:02d}",
            "habitat":"Native forest" if native else "Exotic forest",
            "island":"Terceira",
            "samplingProtocol":"Pitfall trap",
            "eventRemarks":"EPI",
            "locationRemarks":"EPI",
            "minimumElevationInMeters":str(e),
            "decimalLatitude":str(38.6+site*.002),
            "decimalLongitude":str(-27.4+site*.002),
        })
    assert len(rows)==326
    return rows

def test_balanced_20_native_exotic_but_no_environment_overlap_IS_terminal():
    r=audit_source(fixture(),contract())
    assert r["status"]=="TERMINAL_2024_FOREST_ELEVATION_NO_COMMON_SUPPORT"
    assert r["original_Event_rows_examined"]==326
    assert r["original_Occurrence_rows_opened"]==0
    assert r["author_original_physical_plot_id_count"]==20
    assert r["author_original_native_exotic_plot_counts"]=={"native":10,"exotic":10}
    assert r["native_plot_elevation_range_m"]==[590,815]
    assert r["exotic_plot_elevation_range_m"]==[256,436]
    assert r["original_native_exotic_common_elevation_interval_m"] is None
    assert not r["forest_type_elevation_common_support_sufficient"]
    assert r["SLAM_ground_physical_plot_sites_by_forest_type"]=={"native":10,"exotic":10}
    assert not r["original_species_response_scoring_allowed"]
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]

def test_environment_overlap_allows_already_locked_habitat_response_if_sampling_equal():
    r=audit_source(fixture(elevation_overlap=True),contract())
    assert r["status"]=="ORIGINAL_2024_NATIVE_EXOTIC_SAME_STRATUM_ELEVATION_SUPPORT_ADMITTED_SPECIES_SEALED"
    assert r["original_native_exotic_common_elevation_interval_m"]==[610,745]
    assert r["original_physical_sites_inside_common_elevation_support"]["native"]>=2
    assert r["original_physical_sites_inside_common_elevation_support"]["exotic"]>=2
    assert r["original_species_response_scoring_allowed"]
    assert r["original_Occurrence_rows_opened"]==0

def test_source_plot_differing_repeated_elevation_is_scientific_Stop():
    records=fixture(elevation_overlap=True)
    records[1]["minimumElevationInMeters"]="1000"
    r=audit_source(records,contract())
    assert r["status"]=="TERMINAL_2024_ORIGINAL_PHYSICAL_SITE_HABITAT_ELEVATION_QUALITY"
    assert r["source_site_metadata_conflicts"]["repeated_site_elevation_inconsistent"]>0

def test_not_equal_methods_or_lack_of_slam_ground_stops_scoring():
    records=fixture(elevation_overlap=True)
    for row in records:
        if row["samplingProtocol"]=="SLAM trap" and row["eventRemarks"]=="GRD":
            row["eventRemarks"]="UNSPECIFIED"
            row["locationRemarks"]="UNSPECIFIED"
    r=audit_source(records,contract())
    assert r["status"]=="TERMINAL_2024_SLAM_GROUND_EFFORT_NOT_ESTIMABLE"
    assert r["SLAM_ground_physical_plot_sites_by_forest_type"]=={"native":0,"exotic":0}
    assert r["original_Occurrence_rows_opened"]==0

def test_only_original_source_author_ontology_not_after_taxon_labels():
    p=contract()
    assert habitat("Native forest",p)=="native"
    assert habitat("Exotic forest",p)=="exotic"
    assert habitat("Mixed native forest",p)=="unknown"
    assert method("SLAM trap")=="SLAM"
    assert method("pitfall")=="Pitfall"
    assert vertical({"eventRemarks":"GRD","locationRemarks":"GRD"},"SLAM")=="GRD"
    assert vertical({"eventRemarks":"UND","locationRemarks":"UND"},"SLAM")=="UND"
    assert vertical({"eventRemarks":"CAN","locationRemarks":"CAN"},"SLAM")=="CAN"
    assert vertical({"eventRemarks":"EPI"},"Pitfall")=="EPI"
    assert locationID("TER-EXO-T01")=="TEREXOT01"

def test_2024_original_Event_count_and_no_taxa_firewall_fail_closed():
    records=fixture()
    with pytest.raises(ValueError,match="326"):
        audit_source(records[:-1],contract())
    records=fixture()
    records[0]["locationID"]=""
    r=audit_source(records,contract())
    assert r["status"]=="TERMINAL_2024_ORIGINAL_PHYSICAL_SITE_HABITAT_ELEVATION_QUALITY"
    assert r["original_Occurrence_rows_opened"]==0
