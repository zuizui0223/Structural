from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def load(name):
    return json.loads((ROOT/name).read_text())

def test_slam_event_audit_freeze_preserves_response_boundary():
    x=load("development/azores_slam_event_core_audit_freeze_v1_148.json")
    assert x["result"]["event_records"]==893
    assert x["result"]["sites"]==42
    assert x["result"]["islands"]==7
    assert x["result"]["occurrence_extension_physical_rows"]==14922
    assert x["response_boundary"]["occurrence_extension_semantically_opened"] is False
    assert x["response_boundary"]["event_by_taxon_rows_parsed"]==0
    assert x["response_boundary"]["source_loss_effects_computed"]==0

def test_only_eligible_slam_windows_overlap():
    x=load("development/azores_slam_window_selection_stop_v1_148.json")
    ws=x["adjudication"]["eligible_three_year_windows"]
    assert [(w["start"],w["end"]) for w in ws]==[(2013,2015),(2014,2016)]
    assert x["adjudication"]["nonoverlapping_pairs"]==0
    assert ws[0]["end"] >= ws[1]["start"]
    assert x["status"]=="STOP_NO_DISJOINT_PILOT_CONFIRMATORY_THREE_YEAR_WINDOWS"

def test_no_post_audit_slam_rescue_is_allowed():
    x=load("development/azores_slam_window_selection_stop_v1_148.json")
    joined="\n".join(x["forbidden_repairs"])
    assert "minimum islands" in joined
    assert "overlapping pilot and confirmatory years" in joined
    assert "open Occurrence rows" in joined
    assert x["confirmatory_eligible"] is False
    assert x["occurrence_response_opened"] is False
    assert x["counts_as_confirmatory_evidence"] is False

def test_priority_moves_only_to_pre_bala_ebird_metadata():
    x=load("development/structural_active_priority_v1_148.json")
    assert x["active_candidate"]["candidate_id"]=="ebird_global_islands_2002_2019"
    assert x["active_candidate"]["status"]=="HOLD_SAMPLING_EVENT_DATA_REQUIRED"
    assert "response-independent eBird Sampling Event Data audit" in x["next_scientific_event"]
    assert any("infer species absences" in s for s in x["do_not"])
