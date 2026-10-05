from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_retry_is_operational_only():
    x=json.loads((ROOT/"development/finnish_eider_zenodo_inventory_stop_v1_151_1.json").read_text())
    assert x["failed_execution"]["dataset_files_downloaded"]==0
    assert x["failed_execution"]["response_values_opened"]==0
    assert x["scientific_contract_changed"] is False

def test_corrected_identity_rule_accepts_version_or_concept_identity():
    x=json.loads((ROOT/"development/finnish_eider_zenodo_inventory_contract_v1_151_1.json").read_text())
    rule=x["source_identity"]["accept_if"]
    assert "returned id" in rule
    assert "conceptrecid" in rule
    assert "returned doi" in rule
    assert x["scientific_rules_unchanged_from_v151"] is True

def test_retry_script_never_follows_file_content_urls():
    s=(ROOT/"scripts/audit_finnish_eider_zenodo_inventory_v1_151_1.py").read_text()
    assert "metadata_content_url" in s
    assert "urlopen(req" in s
    assert "source_loss_events_computed" in s
    assert "response_values_opened" in s
    # The only network request is the record API request.
    assert s.count("urlopen(")==1

def test_retry_workflow_preserves_zero_dataset_access():
    s=(ROOT/".github/workflows/finnish-eider-zenodo-inventory-v1_151_1.yml").read_text()
    assert "dataset_file_download_authorized" in s
    assert "response_value_access_authorized" in s
    assert "source_loss_events_computed" in s
    assert "curl " not in s
    assert "wget " not in s
