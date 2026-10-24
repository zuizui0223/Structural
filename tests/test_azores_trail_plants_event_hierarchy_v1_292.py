"""Synthetic only: Event hierarchy respects physical plot and nested transect lines."""
import json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from azores_trail_plants_event_hierarchy_v1_292 import audit,parse_event_label

def protocol():
    return json.loads((ROOT/"development/azores_trail_event_hierarchy_contract_v1_292.json").read_text())

def records(two_islands=True):
    out=[]
    for island,trail in (("Terceira","mist.negros"),("Terceira","serreta"),("São Miguel","malhadas")):
        if not two_islands and island=="São Miguel":continue
        for area in ("0","50"):
            for plot in ("1","2","3"):
                for line in ("50","100","150"):
                    name=f"2019.{trail}.{area}.{plot}.{line}"
                    out.append({"eventID":name,"original_coreid":name,"year":"2019",
                                "eventDate":"2019-06-01","island":island})
    return out

def test_valid_nested_trails_are_two_islands_not_54_independent_plots():
    r=audit(records(),protocol())
    assert r["status"]=="MATCHED_TRAIL_LINE_FRAME_POSSIBLE_OCCURRENCE_UNOPENED"
    assert r["number_unique_source_trails_by_island"]=={"Terceira":2,"São Miguel":1}
    assert r["matched_fully_sampled_area_year_groups_by_island"]=={"Terceira":4,"São Miguel":2}
    assert r["original_Event_rows_opened"]==54
    assert r["original_Occurrence_rows_opened"]==0
    assert r["excluded_25cm_line_from_future_matched_comparison"]
    assert not r["eBird_used"] and r["GEB_scientific_HOLD"]

def test_island_replication_not_replaced_by_more_trails_on_one_island():
    r=audit(records(two_islands=False),protocol())
    assert r["status"]=="SOURCE_ONLY_TERMINAL_NO_MATCHED_TRAIL_FRAME"
    assert r["number_complete_edge_and_interior_trails_by_island"]["São Miguel"]==0

def test_frozen_event_grammar_handles_dotted_trail_names_and_forbids_line25_on_interior():
    assert parse_event_label("2019.mist.negros.250.1.150")==("2019","mist.negros","250","1","150")
    with pytest.raises(ValueError):
        parse_event_label("2019.mist.negros.250.2.25")

def test_duplicate_source_key_and_misdated_year_are_not_silently_accepted():
    original=records()
    with pytest.raises(ValueError,match="Nonunique"):
        audit(original+[original[0]],protocol())
    x=records();x[0]["eventDate"]="2018-01-01"
    with pytest.raises(ValueError,match="Date/year"):
        audit(x,protocol())

def test_extra_edge_only_line_does_not_increase_matched_physical_replication():
    base=records()
    added=[]
    for rec in base:
        if rec["eventID"].endswith(".1.150"):
            label=rec["eventID"][:-3]+"25"
            added.append({**rec,"eventID":label,"original_coreid":label})
    r=audit(base+added,protocol())
    assert r["matched_fully_sampled_area_year_groups_by_island"]=={"Terceira":4,"São Miguel":2}
    assert r["excluded_25cm_line_from_future_matched_comparison"]
