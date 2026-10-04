from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def load(p):
    return json.loads((ROOT/p).read_text())

def test_ebird_is_hold_not_qualified():
    c=load("development/source_loss_candidate_ebird_global_islands_v1_127.json")
    r=load("development/source_loss_candidate_ebird_global_islands_triage_v1_127.json")
    assert c["ordered_wave_count"]==18
    assert c["public_source"]["represented_islands"]==4205
    assert c["response_values_currently_unopened"] is True
    assert c["response_is_occupancy_or_presence_absence"] is False
    assert r["status"]=="HOLD_METADATA_INCOMPLETE"
    assert r["response_access_authorized"] is False

def test_ebird_hold_reason_is_absence_semantics_not_temporal_structure():
    r=load("development/source_loss_candidate_ebird_global_islands_triage_v1_127.json")
    assert "18 ordered annual waves" in r["what_is_resolved"]
    joined="\n".join(r["what_must_be_resolved_without_opening_species_outcomes"])
    assert "complete checklists" in joined
    assert "effort/detection metadata" in joined
    assert "survey-quality rule" in joined

def test_apostle_islands_is_exposed_stop():
    c=load("development/source_loss_candidate_apostle_carnivores_v1_127.json")
    r=load("development/source_loss_candidate_apostle_carnivores_triage_v1_127.json")
    assert c["ordered_wave_count"]==4
    assert c["public_source"]["monitored_islands"]==19
    assert c["sampling_effort_or_detection_metadata_available"] is True
    assert c["response_values_currently_unopened"] is False
    assert r["status"]=="STOP_RESPONSE_EXPOSED"
    assert r["response_access_authorized"] is False

def test_neither_candidate_counts_as_empirical_evidence():
    e=load("development/source_loss_candidate_ebird_global_islands_triage_v1_127.json")
    a=load("development/source_loss_candidate_apostle_carnivores_triage_v1_127.json")
    assert e["counts_as_empirical_evidence"] is False
    assert a["counts_as_empirical_evidence"] is False
