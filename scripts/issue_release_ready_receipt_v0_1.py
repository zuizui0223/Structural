#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.verify_release_candidate_v0_2 import (  # noqa: E402
    ReleaseCandidateError,
    evaluate as evaluate_candidate,
)

DEFAULT_SUBMISSION = ROOT / "build/structural_submission_v2"
DEFAULT_BUNDLE = ROOT / "build/structural_release_bundle_v0_1.zip"
DEFAULT_BUNDLE_RECEIPT = ROOT / "build/structural_release_bundle_v0_1.zip.receipt.json"
DEFAULT_OUTPUT = ROOT / "build/release_ready_receipt_v0_1.json"
PREFLIGHT = ROOT / "manuscript/submission/release_preflight_v0_1_0.json"


class ReleaseReadyError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseReadyError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseReadyError(f"{path} must contain a JSON object")
    return value


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseReadyError("cannot resolve git HEAD") from exc


def read_bundle_manifest(bundle_zip: Path) -> dict:
    if not bundle_zip.is_file():
        raise ReleaseReadyError(f"release bundle ZIP not found: {bundle_zip}")
    try:
        with zipfile.ZipFile(bundle_zip, "r") as archive:
            try:
                raw = archive.read("release_bundle_manifest.json")
            except KeyError as exc:
                raise ReleaseReadyError(
                    "release bundle lacks release_bundle_manifest.json"
                ) from exc
    except zipfile.BadZipFile as exc:
        raise ReleaseReadyError(f"invalid release bundle ZIP: {exc}") from exc

    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReleaseReadyError(
            f"invalid release bundle manifest JSON: {exc}"
        ) from exc
    if not isinstance(manifest, dict):
        raise ReleaseReadyError("release bundle manifest must be a JSON object")
    return manifest


def verify_bundle(
    *,
    bundle_zip: Path,
    bundle_receipt_path: Path,
    head: str,
    candidate_tag: str,
) -> dict:
    if not bundle_receipt_path.is_file():
        raise ReleaseReadyError(
            f"release bundle receipt not found: {bundle_receipt_path}"
        )
    receipt = load_json(bundle_receipt_path)
    if receipt.get("schema") != "structural.release_bundle_receipt.v0_1":
        raise ReleaseReadyError("unexpected release bundle receipt schema")
    if receipt.get("source_commit") != head:
        raise ReleaseReadyError("release bundle receipt source_commit != git HEAD")
    if receipt.get("candidate_tag") != candidate_tag:
        raise ReleaseReadyError("release bundle receipt candidate_tag mismatch")

    observed_size = bundle_zip.stat().st_size
    if receipt.get("bundle_zip_size_bytes") != observed_size:
        raise ReleaseReadyError("release bundle ZIP size does not match receipt")

    observed_sha = sha256_file(bundle_zip)
    if receipt.get("bundle_zip_sha256") != observed_sha:
        raise ReleaseReadyError("release bundle ZIP SHA-256 does not match receipt")

    manifest = read_bundle_manifest(bundle_zip)
    if manifest.get("schema") != "structural.release_bundle.v0_1":
        raise ReleaseReadyError("unexpected release bundle manifest schema")
    if manifest.get("source_commit") != head:
        raise ReleaseReadyError("release bundle manifest source_commit != git HEAD")
    if manifest.get("candidate_tag") != candidate_tag:
        raise ReleaseReadyError("release bundle manifest candidate_tag mismatch")
    if manifest.get("release_actions_authorized") is not False:
        raise ReleaseReadyError(
            "bundle manifest itself must not authorize release actions"
        )

    external = manifest.get("external_artifacts")
    if not isinstance(external, dict):
        raise ReleaseReadyError("release bundle external_artifacts block missing")
    required_count = external.get("required_count")
    verified_count = external.get("verified_count")
    missing = external.get("missing_keys")
    complete = (
        isinstance(required_count, int)
        and required_count > 0
        and verified_count == required_count
        and missing == []
        and receipt.get("external_artifacts_complete") is True
        and receipt.get("missing_external_artifacts") == []
    )

    return {
        "receipt": receipt,
        "manifest": manifest,
        "bundle_zip_sha256": observed_sha,
        "bundle_zip_size_bytes": observed_size,
        "external_artifacts_complete": complete,
    }


def evaluate(
    *,
    submission_package: Path,
    bundle_zip: Path,
    bundle_receipt_path: Path,
) -> dict:
    head = git_head()
    preflight = load_json(PREFLIGHT)
    candidate_tag = preflight.get("candidate_tag")
    if not isinstance(candidate_tag, str) or not candidate_tag:
        raise ReleaseReadyError("preflight candidate_tag missing")

    blockers: list[str] = []

    try:
        candidate = evaluate_candidate(submission_package)
    except ReleaseCandidateError as exc:
        raise ReleaseReadyError(f"release candidate verification failed: {exc}") from exc

    if candidate.get("stage") != "READY_FOR_RELEASE_CANDIDATE_RECEIPT":
        blockers.append(
            "candidate_verifier_stage:"
            + str(candidate.get("stage"))
        )

    if preflight.get("status") != "READY_FOR_RELEASE_CANDIDATE_RECEIPT":
        blockers.append(
            "preflight_status:"
            + str(preflight.get("status"))
        )

    bundle = verify_bundle(
        bundle_zip=bundle_zip,
        bundle_receipt_path=bundle_receipt_path,
        head=head,
        candidate_tag=candidate_tag,
    )
    if not bundle["external_artifacts_complete"]:
        blockers.append("release_bundle_external_artifacts_incomplete")

    if candidate.get("git_head") != head:
        blockers.append("candidate_verifier_git_head_mismatch")
    if candidate.get("candidate_tag") != candidate_tag:
        blockers.append("candidate_verifier_tag_mismatch")
    if candidate.get("package_verified") is not True:
        blockers.append("submission_package_not_verified")

    if blockers:
        return {
            "schema": "structural.release_ready_evaluation.v0_1",
            "status": "HOLD_NOT_RELEASE_READY",
            "source_commit": head,
            "candidate_tag": candidate_tag,
            "blockers": blockers,
            "candidate_verifier_stage": candidate.get("stage"),
            "bundle_external_artifacts_complete":
                bundle["external_artifacts_complete"],
            "bundle_zip_sha256": bundle["bundle_zip_sha256"],
            "release_actions_authorized": False,
        }

    package = candidate.get("package")
    if not isinstance(package, dict):
        raise ReleaseReadyError("verified candidate package receipt missing")

    return {
        "schema": "structural.release_ready_receipt.v0_1",
        "status": "RELEASE_READY_RECEIPT_ISSUED",
        "source_commit": head,
        "candidate_tag": candidate_tag,
        "tag_must_point_exactly_to_source_commit": True,
        "tag_may_move_after_creation": False,
        "submission_package_manifest_sha256": package["manifest_sha256"],
        "release_bundle_zip_sha256": bundle["bundle_zip_sha256"],
        "release_bundle_zip_size_bytes": bundle["bundle_zip_size_bytes"],
        "frozen_results": {
            "aislands_strong_reference_result_fingerprint":
                bundle["manifest"]["submission_package"][
                    "aislands_strong_reference_result_fingerprint"
                ],
            "tanzania_result_fingerprint":
                bundle["manifest"]["submission_package"][
                    "tanzania_result_fingerprint"
                ],
        },
        "authorizations": {
            "create_final_tag": True,
            "create_github_release": True,
            "publish_archive_record": True,
            "submit_to_journal": False,
        },
        "receipt_lifecycle": {
            "generated_from_exact_candidate_commit": True,
            "must_not_be_committed_before_tag_creation": True,
            "reason": (
                "committing this receipt before tagging would move HEAD and "
                "invalidate the exact-commit binding"
            ),
        },
        "next_actions": [
            "create candidate_tag exactly at source_commit without moving it later",
            "publish the matching GitHub Release",
            "publish the reserved archive record using the verified complete release bundle",
            "verify public DOI/tag/bundle provenance after publication",
            "complete publisher-rendered journal preview before final journal submission",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission-package", type=Path, default=DEFAULT_SUBMISSION)
    parser.add_argument("--release-bundle-zip", type=Path, default=DEFAULT_BUNDLE)
    parser.add_argument(
        "--release-bundle-receipt",
        type=Path,
        default=DEFAULT_BUNDLE_RECEIPT,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--allow-hold",
        action="store_true",
        help="Exit zero when current state correctly remains HOLD.",
    )
    args = parser.parse_args()

    try:
        result = evaluate(
            submission_package=args.submission_package.resolve(),
            bundle_zip=args.release_bundle_zip.resolve(),
            bundle_receipt_path=args.release_bundle_receipt.resolve(),
        )
    except ReleaseReadyError as exc:
        print(f"release-ready evaluation failed: {exc}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))

    if result["status"] == "HOLD_NOT_RELEASE_READY" and not args.allow_hold:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
