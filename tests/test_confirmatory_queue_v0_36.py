from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "development/confirmatory_admission_queue_v0_36.json"


def test_queue_metadata_is_fail_closed():
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    assert queue["schema"] == "structural.confirmatory_admission_queue.v0_36"
    assert queue["entry_count"] == len(queue["entries"])
    assert queue["confirmatory_response_authorized"] is False
    assert queue["pilot_predictive_denominator_contribution"] == 0
    assert queue["ttf_handoff_is_dependency"] is False
