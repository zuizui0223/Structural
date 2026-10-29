"""Madeira original Event-only native-vs-altered forest UV source design tests.

All data here is invented source-independent known truth. Never import
any original species or biogeographic establishment values.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from madeira_night_original_event_forest_gate_v1_330 import (
    audit,classify_habitat,classify_method,site_id,year_quarter
)

def protocol():
    return json.loads((ROOT/"development/madeira_night_forest_original_event_gate_v1_330.json").read_text())

def mock():
    rows=[]
    for s in range(48):
        habitat=("Laurissilva native forest" if s<16 else
                 "Mixed forest" if s<26 else
                 "Exotic woodland" if s<32 else
                 "coastal dunes")
        lat=32.72+s*.0009
        lon=-16.95-s*.0009
        for year,quarter in ((2022,3),(2023,2)):
            idx=len(rows)
            rows.append({
                "__original_coreid":f"eLight{idx:03}",
                "eventID":f"MADA{idx:03}",
                "eventDate":f"{year}-0{(quarter-1)*3+1}-15",
                "year":str(year),
                "locationID":f"MADEIRA_SITE_{s:02}",
                "habitat":habitat,
                "samplingProtocol":"Heath UV light trap",
                "decimalLatitude":str(lat),
                "decimalLongitude":str(lon),
            })
        if s<38:
            idx=len(rows)
            rows.append({
                "__original_coreid":f"eBait{idx:03}",
                "eventID":f"MADB{idx:03}",
                "eventDate":"2022-07-15",
                "year":"2022",
                "locationID":f"MADEIRA_SITE_{s:02}",
                "habitat":habitat,
                "samplingProtocol":"Wine-rope bait trap",
                "decimalLatitude":str(lat),
                "decimalLongitude":str(lon),
            })
    assert len(rows)==134
    return rows

def test_native_vs_altered_UV_sample_48_sites_two_seasons_source_ready():
    o=audit(mock(),protocol())
    assert o["status"]=="MADEIRA_UV_NATIVE_VS_ALTERED_FOREST_EVENT_FRAME_QUALIFIED_TAXA_SEALED"
    assert o["original_Events_opened"]==134
    assert o["original_Occurrences_opened"]==0
    assert o["actual_unique_physical_source_locationIDs"]==48
    assert o["original_47_vs_48_physical_site_claim_resolved"]
    assert o["original_source_habitat_physical_plot_counts"]=={
       "native":16,"mixed":10,"exotic":6,"nonforest":16,"unknown":0}
    assert o["source_method_Event_counts"]=={"BAIT":38,"LIGHT":96}
    assert o["original_eligible_year_quarter_strata_n"]==2
    assert o["original_selected_unique_forest_plot_n"]==32
    assert o["original_selected_LIGHT_Event_rows"]==64
    assert not o["source_original_bad_metadata_counts"]
    assert o["GEB_scientific_HOLD"] and o["new_confirmatory_systems"]==0 and not o["eBird_used"]
    assert "MADEIRA_SITE" not in json.dumps(o)

def test_source_forest_ontology_separates_coastal_and_agricultural():
    c=protocol()
    assert classify_habitat("Laurissilva native forest",c)=="native"
    assert classify_habitat("Mixed Forest - Native and Exotic",c)=="mixed"
    assert classify_habitat("Exotic woodland",c)=="exotic"
    assert classify_habitat("coastal scrub",c)=="nonforest"
    assert classify_habitat("agricultural land",c)=="nonforest"
    assert classify_habitat("unmeasured high altitude site",c)=="unknown"
    assert classify_method("Heath UV light trap",c)=="LIGHT"
    assert classify_method("Wine-rope bait trap",c)=="BAIT"
    assert classify_method("Heath UV light and wine-rope bait traps",c)=="ambiguous"
    assert site_id("MADEIRA_ São - 01")=="MADEIRASAO01"
    assert year_quarter("2022-08-15")==(2022,3)

def test_missing_second_temporal_forest_stratum_scientific_STOP():
    rows=mock()
    for e in rows:
        if (e["eventDate"]=="2023-04-15"
            and "native" not in e["habitat"].lower()
            and "coastal" not in e["habitat"].lower()):
            e["samplingProtocol"]="Wine-rope bait trap"
    o=audit(rows,protocol())
    assert o["status"]=="TERMINAL_MADEIRA_NO_EXACT_SAME_SEASON_UV_FOREST_PLOT_FRAME"
    assert o["original_eligible_year_quarter_strata_n"]==1
    assert o["original_Occurrences_opened"]==0

def test_same_author_site_habitat_switch_prohibits_fake_replication():
    rows=mock()
    rows[1]["habitat"]="Exotic woodland"
    o=audit(rows,protocol())
    assert o["status"]=="TERMINAL_MADEIRA_NO_EXACT_SAME_SEASON_UV_FOREST_PLOT_FRAME"
    assert o["source_original_habitat_per_site_contradictions"]>0
    assert o["original_Occurrences_opened"]==0

def test_original_repeat_site_coordinate_errors_and_134_Event_count_fail():
    rows=mock()
    rows[1]["decimalLatitude"]="39.99"
    o=audit(rows,protocol())
    assert o["status"]=="TERMINAL_MADEIRA_NO_EXACT_SAME_SEASON_UV_FOREST_PLOT_FRAME"
    assert o["source_original_coordinate_mismatch_over_0_0003deg"]>=1
    with pytest.raises(ValueError,match="134"):
        audit(rows[:-1],protocol())

def test_source_year_date_invalid_does_not_choose_an_alternative_season():
    rows=mock()
    rows[0]["eventDate"]="May 2022"
    with pytest.raises(ValueError,match="YYYY-MM-DD"):
        audit(rows,protocol())
