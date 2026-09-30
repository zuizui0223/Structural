from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_numeric_audit_freeze_is_far_inside_tolerance():
    x=json.loads((ROOT/"development/gift_replay_numeric_equivalence_freeze_v1_64.json").read_text())
    assert x["result"]["absolute_tolerance"]==1e-12
    assert x["result"]["max_abs_probability_difference"]<4.1e-15
    assert x["result"]["max_abs_coefficient_difference"]<4.7e-14
    assert x["prior_confirmatory_attempt"]["confirmatory_response_consumed"] is False

def test_retry_changes_no_science_and_scores_original_surface():
    x=json.loads((ROOT/"development/gift_confirmatory_numeric_retry_contract_v1_65.json").read_text())
    assert x["scientific_design_changes"] is False
    assert x["primary_estimand_changes"] is False
    assert x["species_universe_changes"] is False
    assert x["block_changes"] is False
    assert x["prediction_surface_changes"] is False
    assert x["scoring_prediction_surface"]["use_original_frozen_predictions_only"] is True
    assert x["scoring_prediction_surface"]["replay_is_gate_only"] is True

def test_retry_workflow_gates_before_response():
    s=(ROOT/".github/workflows/gift-confirmatory-numeric-retry-v1_66.yml").read_text()
    gate=s.index("Verify exact frozen inputs and numerical gate")
    access=s.index("Consume the 596-list confirmatory response once")
    score=s.index("Score original frozen primary immediately")
    assert gate < access < score
    assert "gift_v166/frozen/confirmatory_predictions.f64le" in s
    assert "gift_v166/audit/confirmatory_predictions.f64le" not in s
