from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_corrected_schema_artifact_is_frozen_exactly():
    x=json.loads((ROOT/"development/global_mammals_corrected_physical_schema_freeze_v1_71.json").read_text())
    assert x["source_execution"]["artifact_id"]==11112070309
    assert x["artifact_files"]["corrected_species_manifest.csv"]["sha256"]=="882af8216d94dcb18fdafe8f9b3d363cadc2e7afbc1c227ba65d29848dea63d6"
    assert x["result"]["species_count"]==5394
    assert x["same_v165_protocol_retry_authorized"] is False

def test_exploratory_request_never_claims_confirmation():
    x=json.loads((ROOT/"development/global_mammals_exploratory_pilot_request_v1_71.json").read_text())
    assert x["exploratory_pilot_response_authorized"] is True
    assert x["confirmatory_occurrence_authorized"] is False
    assert x["fresh_status_restored"] is False
    assert x["counts_as_confirmatory_evidence"] is False
    assert x["one_shot"] is True

def test_workflow_opens_only_pilot_occurrence():
    s=(ROOT/".github/workflows/global-mammals-exploratory-pilot-v1_71.yml").read_text()
    assert "run_global_mammals_exploratory_pilot_v1_70.py" in s
    assert '"confirmatory_occurrence_values_decoded"]==0' in s
    assert '"excluded_occurrence_values_decoded"]==0' in s
    assert "counts_as_primary_confirmatory_evidence" in s
