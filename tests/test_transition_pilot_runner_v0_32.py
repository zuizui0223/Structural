from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.run_transition_pilot_v0_32 import run


def write_json(path: Path, data: dict):
    path.write_text(json.dumps(data), encoding="utf-8")


def protocol():
    return {
        "protocol_id":"p1",
        "system_id":"s1",
        "partition_axis":"time_window",
        "pilot_partition":["pilot-A"],
        "confirmatory_partition":["confirm-B"],
        "endpoint_id":"future-state",
        "endpoint_semantics":"binary",
        "heldout_design_id":"blocks",
        "minimum_test_rows":2,
        "minimum_train_positive":2,
        "minimum_train_negative":2,
        "minimum_estimable_blocks":2,
        "pilot_response_accessed":False,
        "confirmatory_response_accessed":False,
        "pilot_used_for_effect_estimation":False
    }


def write_rows(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer=csv.writer(handle)
        writer.writerow(["partition_unit","block","target"])
        writer.writerows(rows)


def test_balanced_pilot_qualifies_without_predictive_output(tmp_path: Path):
    p=tmp_path/"protocol.json"; c=tmp_path/"pilot.csv"
    write_json(p,protocol())
    write_rows(c,[
        ["pilot-A","A",1],["pilot-A","A",0],["pilot-A","A",1],
        ["pilot-A","B",0],["pilot-A","B",1],["pilot-A","B",0],
        ["pilot-A","C",1],["pilot-A","C",0],["pilot-A","C",1],
    ])
    code,out=run(p,c)
    assert code==0
    assert out["status"]=="qualified_for_new_confirmatory_protocol"
    assert out["confirmatory_response_row_count_seen"]==0
    assert out["effect_size"] is None
    assert out["prediction_score"] is None
    assert out["predictive_denominator_contribution"]==0


def test_confirmatory_row_stops_immediately(tmp_path: Path):
    p=tmp_path/"protocol.json"; c=tmp_path/"pilot.csv"
    write_json(p,protocol())
    write_rows(c,[["confirm-B","A",1]])
    code,out=run(p,c)
    assert code==2
    assert out["status"]=="STOP_confirmatory_partition_exposed"


def test_unfrozen_partition_row_stops(tmp_path: Path):
    p=tmp_path/"protocol.json"; c=tmp_path/"pilot.csv"
    write_json(p,protocol())
    write_rows(c,[["other","A",1]])
    code,out=run(p,c)
    assert code==2
    assert out["status"]=="STOP_unfrozen_partition_unit"


def test_collapsed_pilot_stops_without_effect(tmp_path: Path):
    p=tmp_path/"protocol.json"; c=tmp_path/"pilot.csv"
    write_json(p,protocol())
    write_rows(c,[
        ["pilot-A","A",1],["pilot-A","A",1],["pilot-A","A",1],
        ["pilot-A","B",1],["pilot-A","B",1],["pilot-A","B",1],
        ["pilot-A","C",1],["pilot-A","C",1],["pilot-A","C",0],
    ])
    code,out=run(p,c)
    assert code==2
    assert out["status"]=="stop_endpoint_variation"
    assert out["effect_size"] is None
    assert out["predictive_denominator_contribution"]==0
