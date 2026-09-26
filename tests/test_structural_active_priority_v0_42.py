from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIORITY = ROOT / "development/structural_active_priority_v0_42.json"
STATUS = ROOT / "development/current_status_v0_42.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_active_priority_points_only_to_current_v042_surfaces():
    priority = load(PRIORITY)
    status = load(STATUS)

    assert priority["status"] == "active_mainline_lock"
    assert priority["canonical_current_status"] == "development/current_status_v0_42.json"
    assert priority["live_confirmatory_queue"] == (
        "development/confirmatory_admission_queue_v0_42.json"
    )
    assert priority["independent_system_intake"] == (
        "development/independent_system_intake_contract_v0_11.json"
    )
    assert status["active_priority"]["path"] == (
        "development/structural_active_priority_v0_42.json"
    )


def test_required_sequence_has_quality_freeze_before_pilot_open():
    priority = load(PRIORITY)
    seq = priority["required_sequence"]

    quality_freeze = next(i for i, x in enumerate(seq) if "v0.42 freeze" in x)
    pilot_open = next(i for i, x in enumerate(seq) if "v0.32 open pilot" in x)
    quality_audit = next(
        i for i, x in enumerate(seq) if "v0.42 independently audit" in x
    )

    assert quality_freeze < pilot_open < quality_audit
    assert priority["priority_rules"]["pilot_access_without_v0_31_and_v0_42_pre_freeze"] is False
    assert priority["priority_rules"]["reopen_landfrag"] is False


def test_old_v035_is_historical_not_current_pointer():
    priority = load(PRIORITY)
    assert priority["supersedes"] == "development/structural_active_priority_v0_35.json"
    assert priority["historical_v0_35_modified"] is False
