from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_corrected_schema_uses_existing_evidence_only():
    x=json.loads((ROOT/"development/global_mammals_corrected_physical_schema_contract_v1_69.json").read_text())
    assert x["frozen_evidence"]["v168_header_artifact"]["total_header_fields"]==5394
    assert x["frozen_evidence"]["v120_first_data_record"]["data_record_field_count"]==5395
    assert x["frozen_evidence"]["v120_first_data_record"]["occurrence_value_count"]==5394
    assert x["physical_schema"]["species_count"]==5394
    assert x["physical_schema"]["data_record_column_1"].startswith("source-local")
    assert x["correction_scope"]["new_response_download_required"] is False

def test_first_header_is_restored_as_species_not_routing():
    x=json.loads((ROOT/"development/global_mammals_corrected_physical_schema_contract_v1_69.json").read_text())
    assert x["frozen_evidence"]["v168_header_artifact"]["first_header_string"]=="Cephalophus.adersi"
    assert x["correction_scope"]["reclassify_v168_manifest_first_row_from_routing_to_species"] is True
    assert x["physical_schema"]["corrected_species_order_sha256"]=="e596a7424d00ce958a65dae747d5a71a70f106e9dabcf299815c1479cb2fad81"

def test_same_terminal_protocol_cannot_be_retried():
    x=json.loads((ROOT/"development/global_mammals_corrected_physical_schema_contract_v1_69.json").read_text())
    assert x["continuation"]["same_v165_protocol_retry_authorized"] is False
    assert x["continuation"]["fresh_or_confirmatory_claim_allowed"] is False
    assert x["continuation"]["retain_species_threshold_m"]==13

def test_workflow_never_downloads_response():
    s=(ROOT/".github/workflows/global-mammals-corrected-schema-v1_69.yml").read_text()
    assert "prepare_dryad_token" not in s
    assert "fetch_global_mammal_response" not in s
    assert "11111510286" in s
    assert "freeze_global_mammals_corrected_schema_v1_69.py" in s
