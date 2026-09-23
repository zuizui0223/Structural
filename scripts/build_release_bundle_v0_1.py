#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUBMISSION = ROOT / "build/structural_submission_v2"
DEFAULT_OUTPUT = ROOT / "build/structural_release_bundle_v0_1"
DEFAULT_ZIP = ROOT / "build/structural_release_bundle_v0_1.zip"
PREFLIGHT = ROOT / "manuscript/submission/release_preflight_v0_1_0.json"
SUBMISSION_MANIFEST = ROOT / "manuscript/submission/submission_manifest.json"
AIS_RETENTION = (
    ROOT
    / "validation/aislands_isolation_adequacy_20260812/"
    "artifact_retention_receipt_20260923.json"
)
SOURCE_RETENTION = ROOT / "development/exploratory_source_artifact_retention_20260923.json"


class ReleaseBundleError(RuntimeError):
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
        raise ReleaseBundleError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReleaseBundleError(f"{path} must contain a JSON object")
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
        raise ReleaseBundleError("cannot resolve git HEAD") from exc


def git_tracked_files() -> list[str]:
    try:
        output = subprocess.check_output(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseBundleError("cannot enumerate git-tracked files") from exc
    paths = [part.decode("utf-8") for part in output.split(b"\0") if part]
    if not paths:
        raise ReleaseBundleError("git-tracked source snapshot is empty")
    return sorted(paths)


def package_manifest_path(package_dir: Path) -> Path:
    return package_dir / "submission_package_manifest_v2.json"


def verify_submission_package(package_dir: Path, head: str) -> dict:
    manifest_path = package_manifest_path(package_dir)
    if not manifest_path.is_file():
        raise ReleaseBundleError(
            f"missing submission package manifest: {manifest_path}"
        )
    manifest = load_json(manifest_path)
    if manifest.get("source_commit") != head:
        raise ReleaseBundleError(
            "submission package source_commit does not equal git HEAD"
        )
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ReleaseBundleError("submission package manifest files are missing")
    for relative, expected in sorted(files.items()):
        path = package_dir / relative
        if not path.is_file():
            raise ReleaseBundleError(f"submission package file missing: {relative}")
        observed = sha256_file(path)
        if observed != expected:
            raise ReleaseBundleError(
                f"submission package SHA mismatch for {relative}: "
                f"{observed} != {expected}"
            )
    return manifest


def required_external_artifacts() -> list[dict]:
    ais = load_json(AIS_RETENTION)
    source = load_json(SOURCE_RETENTION)

    rows = [
        {
            "key": "aislands_strong_reference_raw",
            "role": "A-Islands strong-reference authoritative raw outcome",
            "file_name": "aislands-isolation-adequacy-authoritative-outcome.zip",
            "sha256": ais["artifact_zip_sha256"],
            "size_bytes": ais["artifact_size_bytes"],
            "source_repository": ais["source_repository"],
            "workflow_run_id": ais["workflow_run_id"],
            "artifact_id": ais["artifact_id"],
        }
    ]

    wanted = {
        "A-Islands original authoritative benchmark":
            "aislands-original",
        "A-Islands frozen isolation contract and geometry":
            "aislands-contract",
        "Tanzania frozen held-out current-flow versus EOG result":
            "tanzania-result",
    }
    artifacts = source.get("artifacts")
    if not isinstance(artifacts, list):
        raise ReleaseBundleError("exploratory source retention artifact list missing")
    by_role = {
        row.get("role"): row
        for row in artifacts
        if isinstance(row, dict)
    }
    for role, key in wanted.items():
        row = by_role.get(role)
        if row is None:
            raise ReleaseBundleError(f"missing retention receipt for {role}")
        rows.append(
            {
                "key": key,
                "role": role,
                "file_name": row["file_name"],
                "sha256": row["sha256"],
                "size_bytes": row["size_bytes"],
                "source_repository": row["source_repository"],
                "workflow_run_id": row["workflow_run_id"],
                "artifact_id": row["artifact_id"],
            }
        )
    return rows


def verify_external_artifact(path: Path, spec: dict) -> dict:
    if not path.is_file():
        raise ReleaseBundleError(f"external artifact not found: {path}")
    size = path.stat().st_size
    if size != spec["size_bytes"]:
        raise ReleaseBundleError(
            f"external artifact size mismatch for {spec['key']}: "
            f"{size} != {spec['size_bytes']}"
        )
    digest = sha256_file(path)
    if digest != spec["sha256"]:
        raise ReleaseBundleError(
            f"external artifact SHA mismatch for {spec['key']}: "
            f"{digest} != {spec['sha256']}"
        )
    return {
        **spec,
        "input_path": str(path.resolve()),
        "verified": True,
    }


def copy_file(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise ReleaseBundleError(f"missing source file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def copy_tree_files(src_root: Path, dst_root: Path) -> None:
    if not src_root.is_dir():
        raise ReleaseBundleError(f"missing source directory: {src_root}")
    for src in sorted(src_root.rglob("*")):
        if src.is_file():
            copy_file(src, dst_root / src.relative_to(src_root))


def build_source_snapshot(destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}
    for relative in git_tracked_files():
        src = ROOT / relative
        if not src.is_file():
            raise ReleaseBundleError(f"tracked file missing from worktree: {relative}")
        dst = destination / relative
        copy_file(src, dst)
        files[relative] = sha256_file(dst)
    return files


def deterministic_zip(source_dir: Path, zip_path: Path) -> str:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    fixed_time = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(
        zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            relative = str(path.relative_to(source_dir)).replace("\\", "/")
            info = zipfile.ZipInfo(relative, date_time=fixed_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    return sha256_file(zip_path)


def bundle_file_manifest(bundle_dir: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in sorted(bundle_dir.rglob("*")):
        if path.is_file() and path.name != "release_bundle_manifest.json":
            result[str(path.relative_to(bundle_dir))] = sha256_file(path)
    return result


def stage_for(preflight: dict, missing_external: list[str]) -> str:
    if preflight.get("status") == "HOLD_HUMAN_POLICY_GATES":
        return "STAGING_HOLD_HUMAN_POLICY_GATES"
    if missing_external:
        return "STAGING_HOLD_MISSING_EXTERNAL_ARTIFACTS"
    return "STAGING_COMPLETE_AWAIT_RELEASE_READY_RECEIPT"


def build(
    *,
    submission_package: Path,
    output_dir: Path,
    zip_path: Path,
    external_paths: dict[str, Path],
    require_complete: bool,
) -> dict:
    head = git_head()
    preflight = load_json(PREFLIGHT)
    submission_contract = load_json(SUBMISSION_MANIFEST)
    package_manifest = verify_submission_package(submission_package, head)
    specs = required_external_artifacts()

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_files = build_source_snapshot(output_dir / "source_snapshot")
    copy_tree_files(submission_package, output_dir / "submission_package")

    verified_external: list[dict] = []
    missing_external: list[str] = []
    for spec in specs:
        path = external_paths.get(spec["key"])
        if path is None:
            missing_external.append(spec["key"])
            continue
        verified = verify_external_artifact(path, spec)
        dst = output_dir / "external_artifacts" / spec["file_name"]
        copy_file(path, dst)
        verified["bundle_path"] = str(dst.relative_to(output_dir))
        verified_external.append(verified)

    if require_complete and missing_external:
        raise ReleaseBundleError(
            "complete release bundle requires external artifacts: "
            + ", ".join(missing_external)
        )

    staging_stage = stage_for(preflight, missing_external)
    manifest = {
        "schema": "structural.release_bundle.v0_1",
        "stage": staging_stage,
        "source_commit": head,
        "candidate_tag": preflight["candidate_tag"],
        "package_version": preflight["package_version"],
        "release_actions_authorized": False,
        "public_or_doi_archive_created": False,
        "submission_package": {
            "manifest": "submission_package/submission_package_manifest_v2.json",
            "manifest_sha256": sha256_file(package_manifest_path(submission_package)),
            "source_commit": package_manifest["source_commit"],
            "file_count": len(package_manifest["files"]),
            "aislands_strong_reference_result_fingerprint":
                package_manifest["aislands_strong_reference_result_fingerprint"],
            "tanzania_result_fingerprint":
                package_manifest["tanzania_result_fingerprint"],
        },
        "source_snapshot": {
            "tracked_file_count": len(source_files),
            "files": source_files,
        },
        "external_artifacts": {
            "required_count": len(specs),
            "verified_count": len(verified_external),
            "missing_keys": missing_external,
            "verified": [
                {
                    key: value
                    for key, value in row.items()
                    if key != "input_path"
                }
                for row in verified_external
            ],
        },
        "frozen_evidence": submission_contract["frozen_evidence"],
        "human_policy_preflight_status": preflight["status"],
        "bundle_files": {},
    }
    manifest["bundle_files"] = bundle_file_manifest(output_dir)
    manifest_path = output_dir / "release_bundle_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    bundle_sha = deterministic_zip(output_dir, zip_path)
    receipt = {
        "schema": "structural.release_bundle_receipt.v0_1",
        "stage": staging_stage,
        "source_commit": head,
        "candidate_tag": preflight["candidate_tag"],
        "bundle_zip": str(zip_path.resolve()),
        "bundle_zip_size_bytes": zip_path.stat().st_size,
        "bundle_zip_sha256": bundle_sha,
        "bundle_manifest_sha256": sha256_file(manifest_path),
        "external_artifacts_complete": not missing_external,
        "missing_external_artifacts": missing_external,
        "release_actions_authorized": False,
        "note": (
            "This receipt proves bundle assembly and content identity only. "
            "It does not authorize DOI publication, tagging, GitHub Release, "
            "or journal submission."
        ),
    }
    receipt_path = zip_path.with_suffix(zip_path.suffix + ".receipt.json")
    receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission-package", type=Path, default=DEFAULT_SUBMISSION)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--zip-path", type=Path, default=DEFAULT_ZIP)
    parser.add_argument("--aislands-strong-raw", type=Path)
    parser.add_argument("--aislands-original", type=Path)
    parser.add_argument("--aislands-contract", type=Path)
    parser.add_argument("--tanzania-result", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    external = {
        key: path
        for key, path in {
            "aislands_strong_reference_raw": args.aislands_strong_raw,
            "aislands-original": args.aislands_original,
            "aislands-contract": args.aislands_contract,
            "tanzania-result": args.tanzania_result,
        }.items()
        if path is not None
    }

    try:
        receipt = build(
            submission_package=args.submission_package.resolve(),
            output_dir=args.output_dir.resolve(),
            zip_path=args.zip_path.resolve(),
            external_paths=external,
            require_complete=args.require_complete,
        )
    except ReleaseBundleError as exc:
        print(f"release bundle build failed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
