from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v199_bundle_request_is_response_free():
    x=json.loads((ROOT/"manuscript/submission/GEB_v1_97/anonymous_bundle_request_v1_99.json").read_text())
    assert x["scientific_freeze"]=="development/current_status_v1_97.json"
    assert x["base_anonymous_si_artifact_id"]==11261832785
    assert x["sealed_pilot_artifact_id"]==11267341176
    assert x["sealed_preconfirm_artifact_id"]==11267287545
    assert x["sealed_result_artifact_id"]==11269176943
    assert x["sealed_figure_artifact_id"]==11269267611
    assert x["raw_response_access_authorized"] is False
    assert x["new_scientific_analysis_authorized"] is False

def test_v199_augmentation_includes_sealed_evidence_not_raw_prediction_binary():
    s=(ROOT/"scripts/augment_geb_bundle_sealed_species_v1_99.py").read_text()
    assert "second_layer_pilot_matrix.csv" in s
    assert "second_layer_heldout_matrix.csv" in s
    assert "second_layer_null_scores.csv" in s
    assert "fig4_sealed_species_validation" in s
    assert "second_layer_predictions.f64le" not in s
    assert "raw biological response" not in s.lower()
    assert 'r"from scripts\\.[A-Za-z0-9_]+ import"' in s
    assert 'r"import scripts\\.[A-Za-z0-9_]+"' in s

def test_v199_workflow_uses_exact_frozen_runs_only():
    req=json.loads((ROOT/"manuscript/submission/GEB_v1_97/anonymous_bundle_request_v1_99.json").read_text())
    assert req["base_anonymous_si_artifact_id"]==11261832785
    assert req["sealed_pilot_artifact_id"]==11267341176
    assert req["sealed_preconfirm_artifact_id"]==11267287545
    assert req["sealed_result_artifact_id"]==11269176943
    assert req["sealed_figure_artifact_id"]==11269267611
    s=(ROOT/".github/workflows/geb-anonymous-review-bundle-v1_99.yml").read_text()
    assert "37090054699" in s
    assert "37104248208" in s
    assert "37105060398" in s
    assert "37109723586" in s
    assert "37110412829" in s
    assert "prepare_dryad_token" not in s
    assert "GEB_anonymous_review_SI_v1_99.zip" in s

def test_v199_retry_is_operational_only():
    x=json.loads((ROOT/"manuscript/submission/GEB_v1_97/anonymous_bundle_request_v1_99.json").read_text())
    assert x["operational_retry_revision"]=="v1.99.1"
    assert x["prior_failed_run_id"]==37110743445
    assert x["scientific_inputs_changed"] is False
