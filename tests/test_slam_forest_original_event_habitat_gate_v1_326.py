"""v1.326 original SLAM habitat source-only 42 physical sites, year-quarter gate."""
import copy,json,sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from slam_forest_original_event_habitat_gate_v1_326 import audit,siteid,habitat,_calendar

COUNTS={"FLO":7,"FAI":3,"PIC":10,"GRA":2,"TER":16,"SMG":3,"SMR":1}
LABELS={"FLO":"Flores","FAI":"Faial","PIC":"Pico","GRA":"Graciosa",
        "TER":"Terceira","SMG":"São Miguel","SMR":"Santa Maria"}

def contract():
    return json.loads((ROOT/"development/slam_forest_explicit_habitat_original_event_gate_v1_326.json").read_text(encoding="utf-8"))

def source():
    all_rows=[];sites=[]
    for island,count in COUNTS.items():
        for index in range(count):
            sid=f"FOREST_{island}_{index:02d}"
            if island=="FLO":category="native forest" if index<4 else "mixed forest"
            elif island=="TER":category="native forest" if index<8 else "exotic forest"
            else:category="native forest"
            sites.append((island,sid,category,index))
    assert len(sites)==42
    for i,(island,sid,category,idx) in enumerate(sites):
        for j in range(21+(1 if i<11 else 0)):
            all_rows.append({
                "__original_coreid":f"E-{island}-{idx:02d}-{j:02d}",
                "eventID":f"SOURCE-{island}-{idx:02d}-{j:02d}",
                "eventDate":"2019-06-13" if j%2==0 else "2019-09-16",
                "year":"2019",
                "island":LABELS[island],
                "locationID":sid,
                "habitat":category,
                "samplingProtocol":"SLAM trap",
                "decimalLatitude":str(38.1+i*0.001),
                "decimalLongitude":str(-27.5-i*0.001)
            })
    assert len(all_rows)==893
    return all_rows

def test_exact_source_fields_support_native_vs_altered_two_island_habitat_traps():
    r=audit(source(),contract())
    assert r["status"]=="ORIGINAL_SLAM_FOREST_HABITAT_STRATA_ELIGIBLE_TAXON_RESPONSES_SEALED"
    assert r["original_Event_rows_opened"]==893
    assert r["original_Occurrence_rows_opened"]==0
    assert r["original_distinct_author_island_site_keys"]==42
    assert r["source_recognized_native_mixed_exotic_independent_site_counts"]["FLO"]=={
        "native":4,"mixed":3,"exotic":0}
    assert r["source_recognized_native_mixed_exotic_independent_site_counts"]["TER"]=={
        "native":8,"mixed":0,"exotic":8}
    assert r["islands_with_at_least_one_same_yearquarter_two_native_two_altered_forest_plot_stratum"]==["FLO","TER"]
    assert r["source_selected_physical_plots_with_matched_habitat_period_method"]==23
    assert r["source_selected_original_Event_rows_in_matched_habitat_strata"]==46
    assert r["source_unrecognized_habitat_physical_site_count"]==0
    assert len(r["source_selected_original_Event_coreids_SHA256"])==64
    assert r["original_plot_ids_coordinates_species_habitat_unmapped_values_not_exported"]
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]
    assert "FOREST_FLO" not in json.dumps(r)
    assert "SOURCE-FLO" not in json.dumps(r)

def test_one_island_with_habitat_contrast_is_not_cross_island_replication():
    rows=source()
    for row in rows:
        if row["island"]=="Flores":row["habitat"]="native forest"
    r=audit(rows,contract())
    assert r["status"]=="TERMINAL_NO_TWO_ISLAND_NATIVE_VS_ALTERED_SAME_WINDOW_REPLICATION"
    assert r["islands_with_at_least_one_same_yearquarter_two_native_two_altered_forest_plot_stratum"]==["TER"]
    assert r["original_Occurrence_rows_opened"]==0

def test_site_coordinate_error_forbids_biological_comparisons():
    rows=source()
    rows[1]["decimalLatitude"]="40.9999"
    r=audit(rows,contract())
    assert r["status"]=="TERMINAL_NO_TWO_ISLAND_NATIVE_VS_ALTERED_SAME_WINDOW_REPLICATION"
    assert r["source_plot_coordinate_mismatch_above_0_0003_degrees_count"]==1
    assert r["original_Occurrence_rows_opened"]==0

def test_author_habitat_ontology_is_fixed_before_source():
    d=contract()["habitat_ontology_frozen"]
    assert habitat("Native forest",d)=="native"
    assert habitat("MIXED_FOREST",d)=="mixed"
    assert habitat("Exotic Forest",d)=="exotic"
    assert habitat("native-with-invasive",d) is None
    assert siteid("FLO_São_01")=="FLOSAO01"
    assert _calendar("2020-09-16")==(2020,3)
    with pytest.raises(ValueError,match="eventDate"):
        _calendar("not a date")

def test_original_source_893_events_and_year_field_consistency_strict():
    with pytest.raises(ValueError,match="893"):
        audit(source()[:-1],contract())
    rows=source()
    rows[0]["year"]="2018"
    r=audit(rows,contract())
    assert r["status"]=="TERMINAL_NO_TWO_ISLAND_NATIVE_VS_ALTERED_SAME_WINDOW_REPLICATION"
    assert r["source_bad_Event_metadata_counts"]["original_source_year_date_mismatch"]==1
