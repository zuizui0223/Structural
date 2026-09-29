from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_pilot_freeze_is_exact_and_confirmatory_sealed():
 x=json.loads((ROOT/"development/gift_pilot_response_freeze_v1_58.json").read_text())
 assert x["result"]["focal_species"]==224
 assert x["result"]["pilot_matrix_rows"]==22176
 assert x["result"]["pilot_matrix_positive"]==1808
 assert x["result"]["pilot_matrix_negative"]==20368
 assert x["response_boundary"]["confirmatory_species_composition_opened"] is False

def test_model_request_is_exactly_90496_cells_and_no_response():
 x=json.loads((ROOT/"development/gift_preconfirmatory_model_request_v1_59.json").read_text())
 assert x["focal_species"]==224
 assert x["confirmatory_entities"]==404
 assert x["expected_prediction_cells"]==90496
 assert x["confirmatory_response_authorized"] is False

def test_workflow_pins_numpy_and_single_threads():
 s=(ROOT/".github/workflows/gift-preconfirmatory-model-v1_59.yml").read_text()
 assert 'numpy==2.3.3' in s
 assert 'OPENBLAS_NUM_THREADS: "1"' in s
 assert "confirmatory_predictions.f64le" in s
 assert "GIFT_checklists" not in s
