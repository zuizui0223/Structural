from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_ebird_candidate_waits_for_sampling_event_data_not_species_archive():
    x=json.loads((ROOT/"development/ebird_sampling_event_gate_v1_146.json").read_text())
    assert x["candidate_status"]["current"]=="HOLD_SAMPLING_EVENT_DATA_REQUIRED"
    assert x["dryad_response_boundary"]["species_archive_may_open_now"] is False
    assert x["official_ebird_sampling_event_resolution"]["critical_absence_field"]=="ALL SPECIES REPORTED"
    assert "SCI_NAME" in x["dryad_response_boundary"]["documented_columns"]
    assert x["response_access_authorized"] is False

def test_slam_event_audit_is_pre_bala_registered_and_response_unopened():
    x=json.loads((ROOT/"development/azores_slam_event_core_audit_contract_v1_146.json").read_text())
    assert x["independence"]["registered_before_BALA_outcome"] is True
    assert x["independence"]["selected_because_BALA_failed"] is False
    assert x["occurrence_extension_firewall"]["text_decode_allowed"] is False
    assert x["event_coverage_audit"]["window_selection_here"] is False

def test_slam_auditor_never_decodes_occurrence_extension():
    s=(ROOT/"scripts/audit_azores_slam_event_core_v1_146.py").read_text()
    assert "occ_bytes.decode" not in s
    assert "physical_data_rows(occ_bytes" in s
    assert '"occurrence_extension_semantically_opened":False' in s
    assert '"taxon_occurrence_values_opened":0' in s

def test_slam_workflow_opens_only_event_semantics():
    s=(ROOT/".github/workflows/azores-slam-event-audit-v1_146.yml").read_text()
    assert "occurrence_semantic_access_authorized" in s
    assert "taxon_response_access_authorized" in s
    assert "event_by_taxon_rows_parsed" in s
    assert "source_loss_effects_computed" in s
