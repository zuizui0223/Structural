from __future__ import annotations

import json
from pathlib import Path
import zipfile

import pytest

import scripts.issue_release_ready_receipt_v0_1 as issuer


def write_bundle(
    tmp_path: Path,
    *,
    head: str,
    candidate_tag: str,
    complete: bool,
) -> tuple[Path, Path]:
    bundle_zip = tmp_path / "bundle.zip"
    manifest = {
        "schema": "structural.release_bundle.v0_1",
        "source_commit": head,
        "candidate_tag": candidate_tag,
        "release_actions_authorized": False,
        "submission_package": {
            "aislands_strong_reference_result_fingerprint":
                "5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a",
            "tanzania_result_fingerprint":
                "6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4",
        },
        "external_artifacts": {
            "required_count": 4,
            "verified_count": 4 if complete else 0,
            "missing_keys": [] if complete else [
                "aislands_strong_reference_raw",
                "aislands-original",
                "aislands-contract",
                "tanzania-result",
            ],
        },
    }
    with zipfile.ZipFile(bundle_zip, "w") as archive:
        archive.writestr(
            "release_bundle_manifest.json",
            json.dumps(manifest),
        )

    receipt_path = tmp_path / "bundle.zip.receipt.json"
    receipt = {
        "schema": "structural.release_bundle_receipt.v0_1",
        "source_commit": head,
        "candidate_tag": candidate_tag,
        "bundle_zip_size_bytes": bundle_zip.stat().st_size,
        "bundle_zip_sha256": issuer.sha256_file(bundle_zip),
        "external_artifacts_complete": complete,
        "missing_external_artifacts":
            [] if complete else manifest["external_artifacts"]["missing_keys"],
    }
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    return bundle_zip, receipt_path


def candidate(head: str, stage: str) -> dict:
    return {
        "stage": stage,
        "git_head": head,
        "candidate_tag": "v0.1.0",
        "package_verified": True,
        "package": {
            "manifest_sha256": "a" * 64,
        },
    }


def test_bundle_verification_rejects_tampering(tmp_path: Path):
    head = "1" * 40
    bundle, receipt = write_bundle(
        tmp_path,
        head=head,
        candidate_tag="v0.1.0",
        complete=True,
    )

    verified = issuer.verify_bundle(
        bundle_zip=bundle,
        bundle_receipt_path=receipt,
        head=head,
        candidate_tag="v0.1.0",
    )
    assert verified["external_artifacts_complete"] is True

    bundle.write_bytes(bundle.read_bytes() + b"tamper")
    with pytest.raises(issuer.ReleaseReadyError, match="size"):
        issuer.verify_bundle(
            bundle_zip=bundle,
            bundle_receipt_path=receipt,
            head=head,
            candidate_tag="v0.1.0",
        )


def test_hold_state_never_authorizes_release(tmp_path: Path, monkeypatch):
    head = "2" * 40
    bundle, receipt = write_bundle(
        tmp_path,
        head=head,
        candidate_tag="v0.1.0",
        complete=False,
    )
    preflight = tmp_path / "preflight.json"
    preflight.write_text(
        json.dumps({
            "status": "HOLD_HUMAN_POLICY_GATES",
            "candidate_tag": "v0.1.0",
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(issuer, "PREFLIGHT", preflight)
    monkeypatch.setattr(issuer, "git_head", lambda: head)
    monkeypatch.setattr(
        issuer,
        "evaluate_candidate",
        lambda package: candidate(head, "HOLD_HUMAN_POLICY_GATES"),
    )

    result = issuer.evaluate(
        submission_package=tmp_path / "submission",
        bundle_zip=bundle,
        bundle_receipt_path=receipt,
    )

    assert result["status"] == "HOLD_NOT_RELEASE_READY"
    assert result["release_actions_authorized"] is False
    assert "release_bundle_external_artifacts_incomplete" in result["blockers"]
    assert any(
        blocker.startswith("candidate_verifier_stage:")
        for blocker in result["blockers"]
    )
    assert any(
        blocker.startswith("preflight_status:")
        for blocker in result["blockers"]
    )


def test_ready_receipt_requires_all_gates_and_does_not_authorize_journal(
    tmp_path: Path,
    monkeypatch,
):
    head = "3" * 40
    bundle, receipt = write_bundle(
        tmp_path,
        head=head,
        candidate_tag="v0.1.0",
        complete=True,
    )
    preflight = tmp_path / "preflight.json"
    preflight.write_text(
        json.dumps({
            "status": "READY_FOR_RELEASE_CANDIDATE_RECEIPT",
            "candidate_tag": "v0.1.0",
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(issuer, "PREFLIGHT", preflight)
    monkeypatch.setattr(issuer, "git_head", lambda: head)
    monkeypatch.setattr(
        issuer,
        "evaluate_candidate",
        lambda package: candidate(head, "READY_FOR_RELEASE_CANDIDATE_RECEIPT"),
    )

    result = issuer.evaluate(
        submission_package=tmp_path / "submission",
        bundle_zip=bundle,
        bundle_receipt_path=receipt,
    )

    assert result["status"] == "RELEASE_READY_RECEIPT_ISSUED"
    assert result["source_commit"] == head
    assert result["candidate_tag"] == "v0.1.0"
    assert result["tag_must_point_exactly_to_source_commit"] is True
    assert result["tag_may_move_after_creation"] is False

    auth = result["authorizations"]
    assert auth["create_final_tag"] is True
    assert auth["create_github_release"] is True
    assert auth["publish_archive_record"] is True
    assert auth["submit_to_journal"] is False

    lifecycle = result["receipt_lifecycle"]
    assert lifecycle["must_not_be_committed_before_tag_creation"] is True


def test_ready_receipt_fails_if_preflight_not_explicitly_advanced(
    tmp_path: Path,
    monkeypatch,
):
    head = "4" * 40
    bundle, receipt = write_bundle(
        tmp_path,
        head=head,
        candidate_tag="v0.1.0",
        complete=True,
    )
    preflight = tmp_path / "preflight.json"
    preflight.write_text(
        json.dumps({
            "status": "HOLD_HUMAN_POLICY_GATES",
            "candidate_tag": "v0.1.0",
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(issuer, "PREFLIGHT", preflight)
    monkeypatch.setattr(issuer, "git_head", lambda: head)
    monkeypatch.setattr(
        issuer,
        "evaluate_candidate",
        lambda package: candidate(head, "READY_FOR_RELEASE_CANDIDATE_RECEIPT"),
    )

    result = issuer.evaluate(
        submission_package=tmp_path / "submission",
        bundle_zip=bundle,
        bundle_receipt_path=receipt,
    )

    assert result["status"] == "HOLD_NOT_RELEASE_READY"
    assert "preflight_status:HOLD_HUMAN_POLICY_GATES" in result["blockers"]
