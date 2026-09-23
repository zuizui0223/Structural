from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "manuscript/submission/release_preflight_v0_1_0.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def project_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    assert match is not None
    return match.group(1)


def test_release_preflight_matches_package_version_and_tag():
    x = load(PREFLIGHT)
    version = project_version()

    assert x["status"] == "HOLD_HUMAN_POLICY_GATES"
    assert x["package_version"] == version == "0.1.0"
    assert x["candidate_tag"] == f"v{version}"


def test_release_actions_are_all_blocked_while_hold_is_active():
    x = load(PREFLIGHT)

    assert x["release_actions_authorized"]
    assert all(value is False for value in x["release_actions_authorized"].values())
    assert "create or move the final v0.1.0 tag" in x["forbidden_before_gate_clearance"]
    assert "publish a GitHub Release" in x["forbidden_before_gate_clearance"]


def test_identifier_placeholders_remain_unresolved_during_hold():
    x = load(PREFLIGHT)
    availability = (ROOT / x["data_code_availability"]).read_text(encoding="utf-8")

    for placeholder in x["identifier_placeholders_must_remain_until_release_gate_clears"]:
        assert placeholder in availability


def test_author_and_journal_specific_gates_are_not_falsely_cleared():
    x = load(PREFLIGHT)
    metadata = load(ROOT / x["author_metadata_template"])

    assert metadata["competing_interests"]["confirmed_by_all_authors"] is False
    assert metadata["ethics_and_permits"]["review_completed"] is False
    assert metadata["originality_and_submission"]["approved_by_all_authors"] is False
    assert metadata["generative_ai_disclosure"]["reviewed_by_all_authors"] is False
    assert metadata["generative_ai_disclosure"]["journal_specific_guide_checked"] is False
    assert metadata["release_metadata"]["creator_order_confirmed"] is False
    assert metadata["release_metadata"]["software_citation_metadata_approved"] is False

    raw = json.dumps(metadata)
    assert "<AUTHOR_NAME>" in raw
    assert "<FINAL_JOURNAL_COMPLIANT_DISCLOSURE>" in raw


def test_frozen_result_fingerprints_match_submission_manifest():
    x = load(PREFLIGHT)
    manifest = load(ROOT / x["submission_manifest"])

    assert (
        x["frozen_results"]["aislands_strong_reference_result_fingerprint"]
        == manifest["frozen_evidence"]["aislands_strong_reference_result_fingerprint"]
    )
    assert (
        x["frozen_results"]["tanzania_result_fingerprint"]
        == manifest["frozen_evidence"]["tanzania_result_fingerprint"]
    )


def test_submission_manifest_points_back_to_release_preflight():
    manifest = load(ROOT / "manuscript/submission/submission_manifest.json")

    assert (
        manifest["release_preflight"]
        == "manuscript/submission/release_preflight_v0_1_0.json"
    )
