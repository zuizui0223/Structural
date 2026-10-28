"""Frozen source-Event-only diagnostic after an originally failed gate."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tests"))
from foresteco2_event_imbalance_diagnostic_v1_287 import diagnostic
from test_foresteco2_event_only_qualification_v1_286 import make_rows

ROOT=Path(__file__).resolve().parents[1]
def contract():
    return json.loads((ROOT/"development/foresteco2_event_only_qualification_protocol_v1_286.json").read_text())

def test_imbalanced_original_event_sample_is_reported_without_score():
    e=make_rows()
    e[0]["habitat"]="EW"
    r=diagnostic(e,contract())
    assert r["status"]=="V1_286_REMAINS_TERMINAL_RESPONSE_UNOPENED"
    assert r["island_forest_type_counts"]["Pico"]=={"NF":9,"EW":11,"PF":10}
    assert r["island_totals"]["Pico"]==30
    assert not r["exact_predeclared_10_per_type_gate_met"]
    assert r["Occurrence_data_rows_opened"]==0
    assert r["focal_prediction_scores"]==0
    assert r["strict_v1_286_fail_must_not_be_overridden"]
    assert r["confirmatory_admissions"]==0
    assert r["GEB_scientific_HOLD"] and not r["eBird_used"]

def test_even_perfect_grid_does_not_reopen_failed_protocol():
    r=diagnostic(make_rows(),contract())
    assert r["exact_predeclared_10_per_type_gate_met"]
    assert r["status"]=="V1_286_REMAINS_TERMINAL_RESPONSE_UNOPENED"
