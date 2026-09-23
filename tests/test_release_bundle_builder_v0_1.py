from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

import scripts.build_release_bundle_v0_1 as builder


ROOT = Path(__file__).resolve().parents[1]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_submission_package(tmp_path: Path) -> Path:
    package = tmp_path / "submission"
    package.mkdir()
    payload = package / "payload.txt"
    payload.write_text("frozen submission payload\n", encoding="utf-8")

    manifest = {
        "schema": "eog.structural_submission_package.v3",
        "source_commit": builder.git_head(),
        "files": {"payload.txt": builder.sha256_file(payload)},
        "aislands_strong_reference_result_fingerprint":
            "5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a",
        "tanzania_result_fingerprint":
            "6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4",
    }
    (package / "submission_package_manifest_v2.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    return package


def test_external_artifact_verifier_rejects_tamper(tmp_path: Path):
    path = tmp_path / "artifact.zip"
    payload = b"authoritative bytes"
    path.write_bytes(payload)
    spec = {
        "key": "synthetic",
        "size_bytes": len(payload),
        "sha256": sha(payload),
    }

    verified = builder.verify_external_artifact(path, spec)
    assert verified["verified"] is True

    path.write_bytes(payload + b"x")
    with pytest.raises(builder.ReleaseBundleError, match="size mismatch"):
        builder.verify_external_artifact(path, spec)


def test_current_staging_bundle_is_hold_and_records_all_missing_external_artifacts(
    tmp_path: Path,
):
    package = make_submission_package(tmp_path)
    output = tmp_path / "bundle"
    zip_path = tmp_path / "bundle.zip"

    receipt = builder.build(
        submission_package=package,
        output_dir=output,
        zip_path=zip_path,
        external_paths={},
        require_complete=False,
    )

    assert receipt["stage"] == "STAGING_HOLD_HUMAN_POLICY_GATES"
    assert receipt["release_actions_authorized"] is False
    assert receipt["external_artifacts_complete"] is False
    assert len(receipt["missing_external_artifacts"]) == 4
    assert zip_path.is_file()

    manifest = json.loads(
        (output / "release_bundle_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["source_commit"] == builder.git_head()
    assert manifest["release_actions_authorized"] is False
    assert manifest["public_or_doi_archive_created"] is False
    assert manifest["external_artifacts"]["required_count"] == 4
    assert manifest["external_artifacts"]["verified_count"] == 0
    assert manifest["source_snapshot"]["tracked_file_count"] > 0


def test_require_complete_rejects_missing_external_artifacts(tmp_path: Path):
    package = make_submission_package(tmp_path)

    with pytest.raises(
        builder.ReleaseBundleError,
        match="complete release bundle requires external artifacts",
    ):
        builder.build(
            submission_package=package,
            output_dir=tmp_path / "bundle",
            zip_path=tmp_path / "bundle.zip",
            external_paths={},
            require_complete=True,
        )


def test_release_zip_is_deterministic_for_same_inputs(tmp_path: Path):
    package = make_submission_package(tmp_path)

    first = builder.build(
        submission_package=package,
        output_dir=tmp_path / "bundle1",
        zip_path=tmp_path / "bundle1.zip",
        external_paths={},
        require_complete=False,
    )
    second = builder.build(
        submission_package=package,
        output_dir=tmp_path / "bundle2",
        zip_path=tmp_path / "bundle2.zip",
        external_paths={},
        require_complete=False,
    )

    assert first["bundle_zip_sha256"] == second["bundle_zip_sha256"]
    assert (tmp_path / "bundle1.zip").read_bytes() == (
        tmp_path / "bundle2.zip"
    ).read_bytes()


def test_required_external_specs_match_committed_retention_receipts():
    specs = builder.required_external_artifacts()

    assert len(specs) == 4
    by_key = {row["key"]: row for row in specs}
    assert by_key["aislands_strong_reference_raw"]["sha256"] == (
        "59363bc82924e74445ad10a1d9732511e9bd5bcd056bef17ac89166f45b8355e"
    )
    assert by_key["aislands-original"]["sha256"] == (
        "31ff22edf214b48ae99fa8a5510e0e2752b6787dbe6e22602bada0ec96398501"
    )
    assert by_key["aislands-contract"]["sha256"] == (
        "e1c2c6b80187ecae3a031170759a7a1cbbe2848b227c45b04837127acdc2556a"
    )
    assert by_key["tanzania-result"]["sha256"] == (
        "6f05cb4987300b78c627bb201a2c0da31d8e4a21a7aee83a658de0758f66d4d5"
    )


def test_submission_package_source_commit_must_match_head(tmp_path: Path):
    package = make_submission_package(tmp_path)
    manifest_path = package / "submission_package_manifest_v2.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_commit"] = "0" * 40
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(builder.ReleaseBundleError, match="source_commit"):
        builder.verify_submission_package(package, builder.git_head())
