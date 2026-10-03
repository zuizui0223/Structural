from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_retry_changes_only_python_import_path():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_preconfirm_retry_request_v1_94_1.json").read_text())
    assert x["status"]=="REQUEST_OPERATIONAL_RETRY_SAME_V194_SCIENTIFIC_CONTRACT"
    assert x["failed_run"]["workflow_run_id"]==37104726789
    assert x["failed_run"]["failed_before_prediction_script_body"] is True
    assert x["failed_run"]["heldout_response_accessed"] is False
    assert x["scientific_contract_changed"] is False
    assert x["heldout_response_authorized"] is False
    assert x["one_retry_only"] is True

def test_retry_workflow_adds_pythonpath_and_same_prediction_script():
    s=(ROOT/".github/workflows/global-mammals-sealed-species-preconfirm-retry-v1_94_1.yml").read_text()
    assert "PYTHONPATH:" in s
    assert "freeze_global_mammals_sealed_species_predictions_v1_94.py" in s
    assert "numpy==2.3.3" in s
    assert "null_graphs" in s
    assert "prepare_dryad_token" not in s
