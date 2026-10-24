"""Event-only post-diagnostic matched hierarchy tests (no plant data)."""
from copy import deepcopy
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from azores_trail_new_event_frame_v1_294 import parse_event,profile
from test_azores_trail_plants_event_hierarchy_v1_292 import records

def protocol(n):
    d=json.loads((ROOT/"development/azores_trail_new_event_frame_v1_294.json").read_text(encoding="utf-8"))
    d["source"]["original_event_rows"]=n
    return d

def test_published_control50_alias_accepted_and_unpublished_label_excluded():
    e={"eventID":"2019.mist.negros.control50.1.50","year":"2019",
       "eventDate":"2019-05-01","island":"Terceira"}
    assert parse_event(e)[0]==("Terceira","2019","mist.negros","control_50","1","50")
    e["eventID"]="2019.mist.negros.fake.1.50"
    assert parse_event(e)[1]=="unrecognized_sampling_area"

def test_new_retrospective_frame_can_pass_physical_gate_without_plant_labels():
    rows=records()
    result=profile(rows,protocol(len(rows)))
    assert result["status"]=="RETROSPECTIVE_MATCHED_FRAME_PASS_ONLY_OCCURRENCE_STILL_SEALED"
    assert result["matched_trails_by_island"]=={"Terceira":2,"São Miguel":1}
    assert result["matched_trail_year_area_groups_by_island"]=={"Terceira":4,"São Miguel":2}
    assert result["number_source_Event_rows_qualifying_for_future_score"]==len(rows)
    assert result["original_Occurrence_rows_opened"]==0
    assert result["new_exploratory_not_pristine_confirmatory"]
    assert result["v1_292_original_gate_terminal_immutable"]
    assert result["new_confirmatory_systems"]==0 and result["GEB_scientific_HOLD"]
    assert not result["eBird_used"]

def test_one_island_or_more_than_fifth_invalid_source_ends_before_biology():
    rows=records()
    for e in rows:
        if e["island"]=="São Miguel":
            parts=e["eventID"].split(".")
            parts[-3]="invalid"+parts[-3]
            e["eventID"]=".".join(parts)
    r=profile(rows,protocol(len(rows)))
    assert r["status"]=="RETROSPECTIVE_PHYSICAL_FRAME_TERMINAL_NO_BIOLOGY"
    assert r["original_Occurrence_rows_opened"]==0

def test_source_fields_must_match_identifier_calendar():
    e={"eventID":"2017.serreta.0.1.100","year":"2019",
       "eventDate":"2017-06-01","island":"Terceira"}
    assert parse_event(e)[1]=="year_source_field_disagreement"
