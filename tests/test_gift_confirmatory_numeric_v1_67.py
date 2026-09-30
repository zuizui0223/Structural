from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_numeric_freeze_records_pre_response_failure_and_equivalence():
    x=json.loads((ROOT/"development/gift_replay_numeric_equivalence_freeze_v1_67.json").read_text())
    assert x["failed_exact_replay_boundary"]["failed_before_first_confirmatory_checklist_request"] is True
    assert x["failed_exact_replay_boundary"]["confirmatory_response_consumed"] is False
    assert x["equivalence"]["max_abs_probability_difference"] < 1e-12
    assert x["equivalence"]["max_abs_coefficient_difference"] < 1e-12
    assert x["scoring_policy"]["score_original_frozen_predictions_only"] is True

def test_retry_changes_gate_not_science():
    x=json.loads((ROOT/"development/gift_confirmatory_numeric_retry_contract_v1_67.json").read_text())
    assert x["why_retry_is_valid"]["model_or_predictions_retuned"] is False
    assert x["required_gate_before_response"]["max_abs_probability_difference_lte"]==1e-12
    assert x["scoring"]["prediction_sha256"]=="3c87379be8081edd05ad42e56a8b58a39b2ff75e15ba75993147fb21a0992db4"
    assert x["irreversibility"]["rerun_after_first_confirmatory_checklist_request"] is False

def test_workflow_gates_before_response_and_scores_original():
    s=(ROOT/".github/workflows/gift-confirmatory-numeric-v1_67.yml").read_text()
    audit=s.index("Re-audit numeric equivalence before response")
    gate=s.index("Gate first confirmatory checklist request")
    consume=s.index("Consume the 596-list confirmatory response once")
    score=s.index("Score original frozen predictions only")
    assert audit < gate < consume < score
    assert "build/gift_v167/original/confirmatory_predictions.f64le" in s
    assert "build/gift_v167/replay/confirmatory_predictions.f64le" in s
    assert "--tolerance 1e-12" in s

def test_request_is_one_shot_and_exact():
    x=json.loads((ROOT/"development/gift_confirmatory_numeric_retry_request_v1_67.json").read_text())
    assert x["numeric_audit_artifact_id"]==11109932378
    assert x["confirmatory_entities"]==404
    assert x["confirmatory_blocks"]==59
    assert x["focal_species"]==224
    assert x["expected_target_rows"]==90496
    assert x["confirmatory_response_authorized"] is True
    assert x["one_shot"] is True
