from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_submission_manifest_points_to_current_policy_record():
    manifest = json.loads(
        (ROOT / "manuscript/submission/submission_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert (
        manifest["live_policy_verification"]
        == "manuscript/submission/live_policy_verification_2026-09-23.md"
    )


def test_current_policy_keeps_journal_specific_gate_open():
    current = (
        ROOT / "manuscript/submission/live_policy_verification_2026-09-23.md"
    ).read_text(encoding="utf-8")
    checklist = (
        ROOT / "manuscript/structural_submission_checklist.md"
    ).read_text(encoding="utf-8")
    metadata = json.loads(
        (ROOT / "manuscript/submission/author_metadata.template.json").read_text(
            encoding="utf-8"
        )
    )

    assert "HTTP 403" in current
    assert "submission-day/manual-browser gates" in current
    assert (
        "- [ ] Re-open the current *Ecological Informatics* journal-specific Guide for Authors"
        in checklist
    )
    assert metadata["generative_ai_disclosure"]["live_journal_policy_checked"] is False
    assert metadata["generative_ai_disclosure"]["journal_specific_guide_checked"] is False


def test_ai_image_policy_is_not_the_superseded_blanket_prohibition():
    declarations = (
        ROOT / "manuscript/submission/declarations.md"
    ).read_text(encoding="utf-8")
    current = (
        ROOT / "manuscript/submission/live_policy_verification_2026-09-23.md"
    ).read_text(encoding="utf-8")

    assert (
        "prohibits generative-AI creation or alteration of manuscript figures/images"
        not in declarations
    )
    assert "explanatory images" in declarations
    assert "data visualizations" in declarations
    assert "primary research images" in declarations
    assert "graphical abstracts" in declarations

    assert "updated in **June 2026**" in current
    assert "general-purpose generative-AI image tools must not be used" in current


def test_old_policy_record_is_explicitly_historical():
    old = (
        ROOT / "manuscript/submission/live_policy_verification_2026-08-12.md"
    ).read_text(encoding="utf-8")

    assert "Historical policy snapshot — superseded for current submission use." in old
    assert "live_policy_verification_2026-09-23.md" in old


def test_elsevier_wide_refresh_is_recorded_without_clearing_release_gate():
    checklist = (
        ROOT / "manuscript/structural_submission_checklist.md"
    ).read_text(encoding="utf-8")
    release = (
        ROOT / "manuscript/submission/release_readiness.md"
    ).read_text(encoding="utf-8")

    assert "reverified on 2026-09-23" in checklist
    assert "Highlights guidance reverified on 2026-09-23" in checklist
    assert "Live-policy refresh: **2026-09-23**" in release
    assert "Do **not** reserve/publish the final Zenodo record" in release
