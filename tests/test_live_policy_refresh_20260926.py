from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "manuscript/submission/live_policy_verification_2026-09-26.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_submission_manifest_and_preflight_point_to_20260926_policy():
    manifest = load_json(ROOT / "manuscript/submission/submission_manifest.json")
    preflight = load_json(ROOT / "manuscript/submission/release_preflight_v0_1_0.json")

    expected = "manuscript/submission/live_policy_verification_2026-09-26.md"
    assert manifest["live_policy_verification"] == expected
    assert preflight["current_policy_record"] == expected


def test_current_policy_keeps_journal_specific_gate_open():
    current = CURRENT.read_text(encoding="utf-8")
    metadata = load_json(ROOT / "manuscript/submission/author_metadata.template.json")
    checklist = (
        ROOT / "manuscript/structural_submission_checklist.md"
    ).read_text(encoding="utf-8")

    assert "HTTP 403" in current
    assert "submission-day/manual-browser gates" in current
    assert (
        "- [ ] Re-open the current *Ecological Informatics* journal-specific Guide for Authors"
        in checklist
    )
    assert metadata["generative_ai_disclosure"]["journal_specific_guide_checked"] is False
    assert metadata["generative_ai_disclosure"]["live_journal_policy_checked"] is False


def test_current_elsevier_wide_guards_are_recorded():
    current = CURRENT.read_text(encoding="utf-8")

    assert "3–5 bullet points" in current
    assert "85 characters or fewer" in current
    assert "maximum of 6 keywords" in current
    assert "general-purpose generative-AI image tools must not be used" in current
    assert "AI-assisted writing or editing of research code" in current


def test_research_code_ai_disclosure_requires_human_adjudication():
    metadata = load_json(ROOT / "manuscript/submission/author_metadata.template.json")
    preflight = load_json(ROOT / "manuscript/submission/release_preflight_v0_1_0.json")
    declarations = (
        ROOT / "manuscript/submission/declarations.md"
    ).read_text(encoding="utf-8")

    ai = metadata["generative_ai_disclosure"]
    assert ai["elsevier_wide_policy_rechecked_on"] == "2026-09-26"
    assert ai["research_code_methods_disclosure_reviewed"] is False
    assert "<AUTHOR_APPROVED_METHODS_STATEMENT_OR_NOT_APPLICABLE>" in (
        ai["research_code_methods_statement"]
    )
    assert (
        "AI-assisted research-code Methods disclosure applicability confirmed"
        in preflight["human_or_manual_blockers"]
    )
    assert "AUTHOR CONFIRMATION REQUIRED" in declarations
    assert "research code" in declarations


def test_refresh_does_not_clear_release_hold():
    preflight = load_json(ROOT / "manuscript/submission/release_preflight_v0_1_0.json")
    release = (
        ROOT / "manuscript/submission/release_readiness.md"
    ).read_text(encoding="utf-8")

    assert preflight["status"] == "HOLD_HUMAN_POLICY_GATES"
    assert all(value is False for value in preflight["release_actions_authorized"].values())
    assert "Live-policy refresh: **2026-09-26**" in release
    assert "Do **not** reserve/publish the final Zenodo record" in release
