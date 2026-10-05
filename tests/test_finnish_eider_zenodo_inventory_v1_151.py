from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_inventory_contract_is_metadata_only():
    x=json.loads((ROOT/"development/finnish_eider_zenodo_inventory_contract_v1_151.json").read_text())
    assert x["source"]["record_id"]==15723441
    assert "download any dataset file" in x["forbidden_access"]
    assert "parse Eider_pairs values" in x["forbidden_access"]
    assert x["evidence_boundary"]["retrospective_only"] is True
    assert x["evidence_boundary"]["may_count_as_confirmation"] is False

def test_inventory_script_only_queries_record_metadata():
    s=(ROOT/"scripts/audit_finnish_eider_zenodo_inventory_v1_151.py").read_text()
    assert "urllib.request.urlopen" in s
    assert "metadata_content_url" in s
    assert "response_values_opened" in s
    assert "read_csv" not in s
    assert "pandas" not in s
    assert "requests.get" not in s
    assert "download" not in s.lower().split("def main",1)[1].split("if __name__",1)[0] or "dataset_files_downloaded" in s

def test_workflow_never_downloads_dataset_files():
    s=(ROOT/".github/workflows/finnish-eider-zenodo-inventory-v1_151.yml").read_text()
    assert "audit_finnish_eider_zenodo_inventory_v1_151.py" in s
    assert "curl " not in s
    assert "wget " not in s
    assert "response_values_opened" in s
    assert "source_loss_events_computed" in s

def test_request_is_one_shot_and_response_closed():
    x=json.loads((ROOT/"development/finnish_eider_zenodo_inventory_request_v1_151.json").read_text())
    assert x["dataset_file_download_authorized"] is False
    assert x["response_value_access_authorized"] is False
    assert x["one_shot"] is True
