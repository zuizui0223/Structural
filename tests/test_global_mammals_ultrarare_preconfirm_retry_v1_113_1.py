from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_retry_changes_only_environment():
    x=json.loads((ROOT/"development/global_mammals_ultrarare_preconfirm_retry_request_v1_113_1.json").read_text())
    assert x["status"]=="REQUEST_OPERATIONAL_RETRY_SAME_V113_SCIENTIFIC_CONTRACT"
    assert x["failed_run"]["failed_before_prediction_script_body"] is True
    assert x["failed_run"]["heldout_response_opened"] is False
    assert x["scientific_contract_changed"] is False
    assert x["heldout_response_authorized"] is False

def test_retry_workflow_sets_pythonpath_and_uses_same_script():
    s=(ROOT/".github/workflows/global-mammals-ultrarare-preconfirm-retry-v1_113_1.yml").read_text()
    assert "PYTHONPATH:" in s
    assert "freeze_global_mammals_ultrarare_predictions_v1_113.py" in s
    assert "numpy==2.3.3" in s
    assert "Appendix_1_presence_absence.csv" not in s
