"""BALA physical-transect 3-wave source Event tests; no species rows."""
import json,sys,copy
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_repeated_transect_event_only_v1_311 import summarize,assign_phase
def contract():
    return json.loads((ROOT/"development/bala_original_event_repeat_gate_v1_311.json").read_text())
def source():
    arr=[]
    for island in ("flores","faial","pico","são jorge","terceira","são miguel","santa maria"):
        for site in range(3):
            for phase,year in (("B1",2001),("B2",2011),("B3",2021)):
                for mode in ("pitfall","beating"):
                    key=f"{island}-{site}-{phase}-{mode}"
                    arr.append({"__original_coreid":key,"eventID":key,"year":str(year),
                       "eventDate":str(year)+"-07-01","island":island,
                       "locationID":f"same-transect-{site}","samplingProtocol":mode,
                       "fieldNumber":str(site)})
    return arr
def test_only_same_author_transect_counts_as_temporal_replication():
    rows=source();r=summarize(rows,contract(),expected_n=len(rows))
    assert r["status"]=="EVENT_SAME_TRANSECT_THREE_PHASE_DESIGN_QUALIFIED_OCCURRENCE_SEALED"
    assert r["same_physical_transect_all_three_phase_site_count"]==21
    assert r["same_physical_transect_paired_site_count_B1_B3"]==21
    assert r["island_count_with_B1_B3_repeated_transects"]==7
    assert r["original_published_source_Event_rows"]==126
    assert r["complete_three_phase_sampling_events_min_max"]["B1"]==[2,2]
    assert r["original_Occurrence_rows_opened"]==0
    assert r["all_site_labels_and_coordinates_redacted"] and r["GEB_scientific_HOLD"]
    assert "same-transect" not in json.dumps(r)
    assert not r["eBird_used"]
def test_missing_third_phase_does_not_invent_persistence():
    rows=[x for x in source() if not(x["island"]=="flores" and x["year"]=="2021")]
    r=summarize(rows,contract(),expected_n=len(rows))
    assert r["status"]=="EVENT_REPEATED_SITE_SUPPORT_INSUFFICIENT_TERMINAL_NO_BIOLOGICAL_SCORE"
    assert r["same_physical_transect_all_three_phase_site_count"]==18
    assert r["original_Occurrence_rows_opened"]==0
def test_duplicate_eventids_hard_stop():
    rows=source();rows[1]["eventID"]=rows[0]["eventID"]
    with pytest.raises(ValueError,match="duplicate"):
        summarize(rows,contract(),expected_n=len(rows))
def test_no_two_campaign_years_are_outside_original_bala_1_to_3_periods():
    assert assign_phase(2007) is None
    assert assign_phase(2024) is None
    assert assign_phase(1999)=="B1"
    assert assign_phase(2011)=="B2"
    assert assign_phase(2021)=="B3"
