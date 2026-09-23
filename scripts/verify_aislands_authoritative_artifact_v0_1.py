#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = (
    ROOT
    / "validation/aislands_isolation_adequacy_20260812/"
    "artifact_retention_receipt_20260923.json"
)
PROVENANCE = (
    ROOT
    / "validation/aislands_isolation_adequacy_20260812/"
    "authoritative_execution_provenance.json"
)


class ArtifactVerificationError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ArtifactVerificationError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ArtifactVerificationError(f"{path} must contain a JSON object")
    return value


def verify(zip_path: Path) -> dict[str, object]:
    receipt = load_json(RECEIPT)
    provenance = load_json(PROVENANCE)

    if not zip_path.is_file():
        raise ArtifactVerificationError(f"artifact ZIP not found: {zip_path}")

    observed_zip_sha = sha256_file(zip_path)
    expected_zip_sha = receipt["artifact_zip_sha256"]
    if observed_zip_sha != expected_zip_sha:
        raise ArtifactVerificationError(
            f"artifact ZIP SHA-256 mismatch: {observed_zip_sha} != {expected_zip_sha}"
        )

    if provenance.get("artifact_digest") != f"sha256:{expected_zip_sha}":
        raise ArtifactVerificationError(
            "committed provenance artifact_digest does not match retention receipt"
        )
    if provenance.get("artifact_id") != receipt.get("artifact_id"):
        raise ArtifactVerificationError("artifact ID mismatch")
    if provenance.get("workflow_run_id") != receipt.get("workflow_run_id"):
        raise ArtifactVerificationError("workflow run ID mismatch")
    if provenance.get("git_commit") != receipt.get("source_commit"):
        raise ArtifactVerificationError("source commit mismatch")
    if provenance.get("result_fingerprint") != receipt.get("result_fingerprint"):
        raise ArtifactVerificationError("result fingerprint mismatch")

    verified_members: dict[str, str] = {}
    try:
        with zipfile.ZipFile(zip_path, "r") as archive:
            names = set(archive.namelist())

            for logical_name, spec in receipt["verified_member_hashes"].items():
                member = spec["artifact_member"]
                if member not in names:
                    raise ArtifactVerificationError(
                        f"required artifact member missing: {member}"
                    )
                raw = archive.read(member)
                if spec["hash_mode"] == "sha256_raw_member_bytes":
                    observed = sha256_bytes(raw)
                elif spec["hash_mode"] == "sha256_of_gzip_decompressed_bytes":
                    try:
                        decompressed = gzip.GzipFile(fileobj=io.BytesIO(raw)).read()
                    except OSError as exc:
                        raise ArtifactVerificationError(
                            f"cannot decompress {member}: {exc}"
                        ) from exc
                    observed = sha256_bytes(decompressed)
                else:
                    raise ArtifactVerificationError(
                        f"unknown hash_mode for {logical_name}: {spec['hash_mode']}"
                    )

                expected = spec["sha256"]
                if observed != expected:
                    raise ArtifactVerificationError(
                        f"member SHA-256 mismatch for {logical_name}: "
                        f"{observed} != {expected}"
                    )
                verified_members[logical_name] = observed

            embedded_provenance = json.loads(
                archive.read("outcome/execution_provenance.json").decode("utf-8")
            )
    except (zipfile.BadZipFile, KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArtifactVerificationError(f"invalid authoritative artifact ZIP: {exc}") from exc

    for key in (
        "git_commit",
        "workflow_run_id",
        "workflow_run_attempt",
        "result_fingerprint",
    ):
        if embedded_provenance.get(key) != provenance.get(key):
            raise ArtifactVerificationError(
                f"embedded provenance mismatch for {key}"
            )

    embedded_hashes = embedded_provenance.get("file_sha256")
    if not isinstance(embedded_hashes, dict):
        raise ArtifactVerificationError("embedded file_sha256 missing")

    for logical_name, spec in receipt["verified_member_hashes"].items():
        basename = Path(logical_name).name
        if embedded_hashes.get(basename) != spec["sha256"]:
            raise ArtifactVerificationError(
                f"embedded provenance hash mismatch for {basename}"
            )

    return {
        "schema": "structural.aislands_authoritative_artifact_verification.v0_1",
        "status": "VERIFIED",
        "artifact_id": receipt["artifact_id"],
        "workflow_run_id": receipt["workflow_run_id"],
        "source_repository": receipt["source_repository"],
        "source_commit": receipt["source_commit"],
        "artifact_zip_sha256": observed_zip_sha,
        "result_fingerprint": receipt["result_fingerprint"],
        "verified_members": verified_members,
        "artifact_expires_at": receipt["artifact_expires_at"],
        "preserved_outside_github_actions": receipt["long_term_preservation"][
            "preserved_outside_github_actions"
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        result = verify(args.artifact_zip)
    except ArtifactVerificationError as exc:
        print(f"authoritative artifact verification failed: {exc}", file=sys.stderr)
        return 1

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
