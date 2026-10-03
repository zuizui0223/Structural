from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v199_bundle_request_is_response_free():
    x=json.loads((ROOT/"manuscript/submission/GEB_v1_97/anonymous_bundle_request_v1_99.json").read_text())
    assert x["scientific_freeze"]=="development/current_status_v1_97.json"
    assert x["sealed_result_artifact_id"]==11269176943
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

def test_v199_workflow_uses_exact_frozen_artifacts_only():
    s=(ROOT/".github/workflows/geb-anonymous-review-bundle-v1_99.yml").read_text()
    assert "11261832785" in s
    assert "11267341176" in s
    assert "11267287545" in s
    assert "11269176943" in s
    assert "11269267611" in s
    assert "prepare_dryad_token" not in s
    assert "GEB_anonymous_review_SI_v1_99.zip" in s
