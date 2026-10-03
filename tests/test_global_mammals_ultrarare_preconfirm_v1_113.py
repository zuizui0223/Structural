from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_ultrarare_preconfirm_contract_is_response_sealed():
    x=json.loads((ROOT/"development/global_mammals_ultrarare_preconfirm_contract_v1_113.json").read_text())
    assert x["population"]["species"]==529
    assert x["population"]["heldout_target_cells"]==2182654
    assert x["response_boundary"]["heldout_target_values_used"] is False
    assert x["response_boundary"]["heldout_response_opened"] is False
    assert x["response_boundary"]["heldout_response_authorized"] is False

def test_preconfirm_outputs_include_predictions_mask_and_isolation():
    x=json.loads((ROOT/"development/global_mammals_ultrarare_preconfirm_contract_v1_113.json").read_text())
    out="\n".join(x["frozen_outputs_before_response"])
    assert "p_R3" in out
    assert "p_C" in out
    assert "graph-source-empty" in out
    assert "Current_isolation" in out

def test_prediction_script_never_reads_heldout_response():
    s=(ROOT/"scripts/freeze_global_mammals_ultrarare_predictions_v1_113.py").read_text()
    assert "Dryad" not in s
    assert "Appendix_1" not in s
    assert "heldout_target_values_used" in s
    assert "heldout_response_opened" in s

def test_workflow_downloads_no_response_artifact():
    s=(ROOT/".github/workflows/global-mammals-ultrarare-preconfirm-v1_113.yml").read_text()
    assert "prepare_dryad_token" not in s
    assert "Appendix_1_presence_absence.csv" not in s
    assert "ultrarare_predictions.f64le" in s
    assert "ultrarare_graph_empty.u8" in s
    assert "ultrarare_block_context.csv" in s
