from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUEST = (
    ROOT / "development/boreal_19island_preconfirmatory_freeze_request_v1_10.json"
)
WORKFLOW = (
    ROOT / ".github/workflows/boreal-19island-preconfirmatory-freeze-v1_10.yml"
)


def test_v110_request_freezes_exact_successful_v109_artifact():
    x = json.loads(REQUEST.read_text(encoding="utf-8"))
    assert x["schema"] == (
        "structural.boreal_19island_preconfirmatory_freeze_request.v1_10"
    )
    assert x["status"] == "REQUEST_EXACT_PRECONFIRMATORY_ARTIFACT_FREEZE"
    assert x["source_execution"] == {
        "workflow": ".github/workflows/boreal-19island-preconfirmatory-v1_09.yml",
        "workflow_run_id": 36481729833,
        "workflow_head_sha": "0f03431d98149c6c1114b3bf91a5d0592ef41716",
        "artifact_id": 10996718466,
        "artifact_name": (
            "boreal-v109-preconfirmatory-"
            "0f03431d98149c6c1114b3bf91a5d0592ef41716-36481729833"
        ),
        "artifact_digest": (
            "sha256:188028a93b91f0f8dc00adbeda6c84c9be6510130c726649ba62864ea0b5b1b1"
        ),
    }
    assert x["file_sha256"] == {
        "confirmatory_predictions.csv": (
            "26e13914b69faa3a342ce0fc137a1b4b9badeb0f3ff2ec24aa82097780ba5ded"
        ),
        "model_receipt.json": (
            "be0ea3c8d277aff00533afd47177f47fba3209d49d80126debdd6817777b3393"
        ),
    }
    expected = x["expected_model_result"]
    assert expected["models_fingerprint"] == (
        "2f94fd0ea0eda73013340d417d6827778ebcec97eec7686bdd9ddd59e07790ff"
    )
    assert expected["prediction_row_count"] == 1287
    assert expected["confirmatory_target_values_opened"] == 0
    assert expected["excluded_target_values_opened"] == 0
    assert expected["confirmatory_response_authorized"] is False
    assert expected["predictive_denominator_contribution"] == 0
    assert expected["counts_as_empirical_evidence"] is False
    assert x["one_shot"] is True


def test_v110_workflow_requires_exact_replay_before_commit():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "artifact-ids: 10996718466" in text
    assert "run-id: 36481729833" in text
    assert "cmp -s" in text
    assert "freeze_boreal_19island_preconfirmatory_model_v1_09.py" in text
    assert "confirmatory_predictions_v1_10.csv" in text
    assert "preconfirmatory_model_receipt_v1_10.json" in text
    assert "preconfirmatory_freeze_v1_10.json" in text
    assert "confirmatory_response_authorized" in text
    assert "counts_as_empirical_evidence" in text
    assert "contents: write" in text
