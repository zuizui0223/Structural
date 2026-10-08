from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def read(p):return json.loads((ROOT/p).read_text())

def test_transport_evidence_is_preoutcome_and_terminal():
    x=read("development/hebert_exact_transport_terminal_v1_200.json")
    a=read("development/hebert_transport_preflight_receipt_v1_198.json")
    b=read("development/hebert_one_byte_transport_receipt_v1_199.json")
    assert a["status"]=="NO_HEAD_CANDIDATE"
    assert b["status"]=="RANGE_UNAVAILABLE"
    assert a["csv_head_candidates"]==0 and b["files_with_range_available"]==0
    assert b["range_probe_bytes_read"]==0
    assert x["response_firewall"]["external_checklist_island_species_0_1_values_opened"]==0
    assert x["response_firewall"]["independent_ecological_prediction_scores"]==0
    assert x["conclusion"]["same_endpoint_automated_retries_authorized"] is False

def test_next_dynamic_data_not_yet_confirmatory():
    x=read("development/independent_dynamic_ecology_metadata_triage_v1_200.json")
    assert x["status"]=="METADATA_ONLY_NO_NEW_TEMPORAL_OUTCOME_ACCESS"
    assert len(x["prospective_candidates"])==2
    assert all(not c["admission_now"] and c["outcomes_opened_by_Structural"]==0 for c in x["prospective_candidates"])
    p=read("development/structural_active_priority_v1_200.json")
    assert "scientific_hold" in p["status"]
    assert p["completed_transport"]["ecological_scores_produced"]==0
