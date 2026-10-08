from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
STOP=ROOT/"development/sw_finland_terminal_stop_v1_177.json"
STATUS=ROOT/"development/current_status_v1_177.json"
PRIORITY=ROOT/"development/structural_active_priority_v1_177.json"

def test_sw_finland_stop_is_terminal_and_preoutcome():
    x=json.loads(STOP.read_text())
    assert x["status"]=="TERMINAL_STOP_SOURCE_IDENTITY_NOT_RESPONSE_INDEPENDENTLY_ESTIMABLE"
    assert x["response_boundary"]["future_colonization_outcome_values_opened"]==0
    assert x["rerun_policy"]["same_archive_source_identity_rerun_authorized"] is False
    assert x["rerun_policy"]["threshold_relaxation_authorized"] is False
    dual=[r for r in x["failed_routes"] if r.get("version")=="v1.176"][0]
    assert dual["count_anchor_max_absolute_log10_residual_observed"] > dual["count_anchor_max_absolute_log10_residual_allowed"]

def test_status_keeps_positive_mammal_and_negative_temporal_boundary_separate():
    x=json.loads(STATUS.read_text())
    assert x["mammal_occupancy_regime_evidence"]["ultrarare_1_4"]["actual_better_than_nulls"]=="20/20"
    assert x["independent_temporal_evidence"]["completed_BALA"]["primary_supported"] is False
    assert x["independent_temporal_evidence"]["sw_finland_plants"]["future_outcome_values_opened"]==0
    assert x["independent_temporal_evidence"]["sw_finland_plants"]["biological_hypothesis_tested"] is False

def test_priority_returns_to_manuscript_and_forbids_rescue():
    x=json.loads(PRIORITY.read_text())
    assert "manuscript" in x["status"]
    assert x["project_policy"]["ebird_enabled"] is False
    assert x["project_policy"]["same_SW_Finland_archive_rerun_authorized"] is False
    assert any("do not relax the v1.176" in s for s in x["do_not"])
    assert any("do not delay the manuscript" in s for s in x["do_not"])
