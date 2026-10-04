from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def test_failed_v129_is_frozen_as_response_unopened_stop():
    x=json.loads((ROOT/"development/bala_core_panel_stop_v1_130.json").read_text())
    assert x["status"]=="RESPONSE_UNOPENED_CORE_PANEL_RULE_STOPPED_ON_EVENT_COUNT_MISMATCH"
    assert "5467" in x["failed_execution"]["failure"]
    assert "4929" in x["failed_execution"]["failure"]
    assert x["scientific_boundary"]["occurrence_extension_semantically_opened"] is False
    assert x["same_rule_retry_authorized"] is False

def test_v130_audits_only_predeclared_event_metadata_fields():
    x=json.loads((ROOT/"development/bala_core_event_excess_audit_contract_v1_130.json").read_text())
    assert x["candidate_event_metadata_discriminators"]==[
      "habitat","samplingProtocol","locationRemarks","locationID","fieldNumber","event year","eventDate"
    ]
    assert "do not inspect Occurrence extension rows" in x["anti_selection"]
    assert "do not search combinations of Event fields solely to force the total to 4929" in x["anti_selection"]

def test_v130_script_does_not_choose_a_core_filter():
    s=(ROOT/"scripts/audit_bala_core_event_excess_v1_130.py").read_text()
    assert '"final_core_rule_selected":False' in s
    assert "taxon_occurrence_values_opened" in s
    assert "event_by_taxon_rows_parsed" in s
    assert "habitat_phase_counts.csv" in s
    assert "fieldNumber_phase_counts.csv" in s

def test_v130_workflow_keeps_response_closed():
    s=(ROOT/".github/workflows/bala-core-event-excess-audit-v1_130.yml").read_text()
    assert "occurrence_extension_semantically_opened" in s
    assert "taxon_occurrence_values_opened" in s
    assert "final_core_rule_selected" in s
    assert "occurrence.txt" not in s
