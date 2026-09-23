from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "manuscript/submission/release_bundle_contract_v0_1.json"
PREFLIGHT = ROOT / "manuscript/submission/release_preflight_v0_1_0.json"
MANIFEST = ROOT / "manuscript/submission/submission_manifest.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_release_bundle_contract_never_authorizes_publication():
    c = load(CONTRACT)
    boundary = c["release_boundary"]

    assert boundary["builder_authorizes_tag"] is False
    assert boundary["builder_authorizes_github_release"] is False
    assert boundary["builder_authorizes_archive_doi"] is False
    assert boundary["builder_authorizes_journal_submission"] is False
    assert boundary["separate_release_ready_receipt_still_required"] is True


def test_current_ci_bundle_stage_matches_human_policy_hold():
    c = load(CONTRACT)
    p = load(PREFLIGHT)

    assert p["status"] == "HOLD_HUMAN_POLICY_GATES"
    assert (
        c["ci_mode"]["expected_current_stage"]
        == "STAGING_HOLD_HUMAN_POLICY_GATES"
    )
    assert p["release_bundle"]["ci_staging_expected_stage"] == (
        "STAGING_HOLD_HUMAN_POLICY_GATES"
    )
    assert p["release_bundle"]["final_bundle_alone_authorizes_release"] is False


def test_submission_manifest_points_to_canonical_bundle_builder():
    m = load(MANIFEST)

    assert (
        m["release_bundle_contract"]
        == "manuscript/submission/release_bundle_contract_v0_1.json"
    )
    assert m["release_bundle_builder"] == "scripts/build_release_bundle_v0_1.py"
    assert "structural_release_bundle_v0_1.zip" in m["release_bundle_ci_command"]


def test_final_bundle_requires_all_external_artifacts():
    c = load(CONTRACT)
    p = load(PREFLIGHT)

    assert c["final_mode"]["command_requires_all_external_artifacts"] is True
    assert (
        c["final_mode"][
            "all_external_artifacts_must_match_committed_retention_sha256_and_size"
        ]
        is True
    )
    assert (
        p["release_bundle"]["final_bundle_requires_all_retained_external_artifacts"]
        is True
    )
