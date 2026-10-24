"""Source-only 90 x 9 forest-type grid audit; all plant labels remain opaque."""
import json
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from foresteco2_event_only_qualification_v1_286 import audit_event_grid

ROOT=Path(__file__).resolve().parents[1]
def protocol():
    return json.loads((ROOT/"development/foresteco2_event_only_qualification_protocol_v1_286.json").read_text(encoding="utf-8"))

def make_rows():
    rows=[]
    for island in ("Pico","Terceira","São Miguel"):
        for typ in ("NF","EW","PF"):
            for k in range(10):
                ident=f"{island}-{typ}-{k}"
                rows.append({
                    "source_coreid":ident,
                    "eventID":ident,
                    "locationID":ident,
                    "island":island,
                    "habitat":typ,
                    "eventDate":"2017-05-01" if island!="Pico" else "2018-05-01",
                    "sampleSizeValue":"100",
                    "scientificName":"NEVER_ACCESS_THIS_IS_EVENT_ONLY"
                })
    return rows

def test_exact_90_original_author_sites_biological_response_stays_sealed():
    r=audit_event_grid(make_rows(),protocol())
    assert r["status"]=="EVENT_90_BY_9_PHYSICAL_DESIGN_QUALIFIED_OCCURRENCE_UNOPENED"
    assert r["original_author_events"]==90
    assert r["distinct_original_site_ids"]==90
    assert r["Occurrence_data_rows_opened"]==0
    assert r["S1_workbook_rows_opened"]==0
    assert r["new_confirmatory_systems"]==0
    assert r["GEB_scientific_HOLD"]
    assert not r["eBird_used"]
    assert "NEVER_ACCESS_THIS_IS_EVENT_ONLY" not in json.dumps(r)

def test_105_in_methods_cannot_override_frozen_90_events():
    with pytest.raises(ValueError,match="105"):
        audit_event_grid(make_rows()+make_rows()[:15],protocol())

def test_outcome_selected_merged_habitat_is_stop():
    e=make_rows()
    e[0]["habitat"]="Forest with high focal species cover"
    with pytest.raises(ValueError,match="unknown"):
        audit_event_grid(e,protocol())

def test_missing_10_per_island_cell_must_stop():
    e=make_rows()
    e[0]["habitat"]="EW"
    with pytest.raises(ValueError,match="Incomplete"):
        audit_event_grid(e,protocol())

def test_duplicate_author_site_stop():
    e=make_rows()
    e[1]["locationID"]=e[0]["locationID"]
    with pytest.raises(ValueError,match="Duplicate original author"):
        audit_event_grid(e,protocol())
