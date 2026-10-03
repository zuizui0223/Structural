from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_preconfirm_freeze_binds_exact_prediction_surface():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_preconfirm_freeze_v1_96.json").read_text())
    assert x["source_execution"]["artifact_id"]==11267287545
    assert x["files"]["second_layer_predictions.f64le"]["sha256"]=="5aa63c4be6344598f8d641f092ee4e9a6801eec8869eda48479e5bbec38f304c"
    assert x["files"]["actual_graph_empty_mask.u8"]["sha256"]=="ebc4321888f2f3b9c12530037c20f1ea4d9df369482fe516c065f2882cdde0b3"
    assert x["response_independent_estimability"]["cells_with_abs_pC_minus_pR3_gt_1e_12"]==396096
    assert x["response_independent_estimability"]["cells_with_abs_actualC_minus_mean_rewiredC_gt_1e_12"]==396096
    assert x["response_boundary"]["heldout_second_layer_response_opened"] is False

def test_execution_request_is_irreversible_and_one_shot():
    x=json.loads((ROOT/"development/global_mammals_sealed_species_execution_request_v1_96.json").read_text())
    assert x["heldout_response_authorized"] is True
    assert x["decode_only_second_layer_species"] is True
    assert x["score_P1_P2_P3_P4_immediately"] is True
    assert x["refit_after_heldout_access"] is False
    assert x["threshold_change_after_heldout_access"] is False
    assert x["null_change_after_heldout_access"] is False
    assert x["same_lineage_rerun_after_first_decode"] is False
    assert x["one_shot"] is True

def test_execution_workflow_preflights_before_token_and_response():
    s=(ROOT/".github/workflows/global-mammals-sealed-species-execute-v1_96.yml").read_text()
    pre=s.index("Verify every frozen input and prediction surface before response")
    token=s.index("Prepare exact Dryad token only after prediction preflight passes")
    consume=s.index("Consume exactly the 96 sealed heldout species once")
    score=s.index("Score preregistered P1-P4 immediately with no refit")
    assert pre < token < consume < score
    assert "numpy==2.3.3" in s
    assert "heldout_non_second_layer_values_decoded" in s
    assert "actual_graph_empty_mask.u8" in s
    assert "second_layer_null_scores.csv" in s
