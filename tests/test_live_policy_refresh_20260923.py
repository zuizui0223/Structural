from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_20260923_policy_record_is_historical():
    old = (
        ROOT / "manuscript/submission/live_policy_verification_2026-09-23.md"
    ).read_text(encoding="utf-8")

    assert "Historical policy snapshot — superseded for current submission use." in old
    assert "live_policy_verification_2026-09-26.md" in old


def test_20260812_policy_record_remains_historical_provenance():
    old = (
        ROOT / "manuscript/submission/live_policy_verification_2026-08-12.md"
    ).read_text(encoding="utf-8")

    assert "Historical policy snapshot — superseded for current submission use." in old
    assert "live_policy_verification_2026-09-23.md" in old
