from __future__ import annotations

import gzip
import hashlib
import io
import json
from pathlib import Path
import zipfile

import pytest

import scripts.verify_aislands_authoritative_artifact_v0_1 as verifier


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    heldout = b"site,pred\nA,0.1\n"
    fold = b"fold,score\nA,1\n"
    species = b"species,delta\nsp1,0.1\n"
    aggregate = b'{"result":"ok"}\n'

    provenance = {
        "git_commit": "abc123",
        "workflow_run_id": 42,
        "workflow_run_attempt": 1,
        "result_fingerprint": "f" * 64,
        "file_sha256": {
            "heldout_predictions.csv": sha(heldout),
            "fold_applicability_and_scores.csv": sha(fold),
            "species_summary.csv": sha(species),
            "aggregate_result.json": sha(aggregate),
        },
    }

    zip_path = tmp_path / "artifact.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        buf = io.BytesIO()
        with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
            gz.write(heldout)
        z.writestr("outcome/heldout_predictions.csv.gz", buf.getvalue())
        z.writestr("outcome/fold_applicability_and_scores.csv", fold)
        z.writestr("outcome/species_summary.csv", species)
        z.writestr("outcome/aggregate_result.json", aggregate)
        z.writestr(
            "outcome/execution_provenance.json",
            json.dumps(provenance),
        )

    receipt = {
        "artifact_zip_sha256": verifier.sha256_file(zip_path),
        "artifact_id": 7,
        "workflow_run_id": 42,
        "source_repository": "owner/source",
        "source_commit": "abc123",
        "result_fingerprint": "f" * 64,
        "artifact_expires_at": "2099-01-01T00:00:00Z",
        "verified_member_hashes": {
            "outcome/heldout_predictions.csv": {
                "artifact_member": "outcome/heldout_predictions.csv.gz",
                "hash_mode": "sha256_of_gzip_decompressed_bytes",
                "sha256": sha(heldout),
            },
            "outcome/fold_applicability_and_scores.csv": {
                "artifact_member": "outcome/fold_applicability_and_scores.csv",
                "hash_mode": "sha256_raw_member_bytes",
                "sha256": sha(fold),
            },
            "outcome/species_summary.csv": {
                "artifact_member": "outcome/species_summary.csv",
                "hash_mode": "sha256_raw_member_bytes",
                "sha256": sha(species),
            },
            "outcome/aggregate_result.json": {
                "artifact_member": "outcome/aggregate_result.json",
                "hash_mode": "sha256_raw_member_bytes",
                "sha256": sha(aggregate),
            },
        },
        "long_term_preservation": {
            "preserved_outside_github_actions": False,
        },
    }

    receipt_path = tmp_path / "receipt.json"
    provenance_path = tmp_path / "provenance.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    provenance_full = {
        **provenance,
        "artifact_digest": f"sha256:{receipt['artifact_zip_sha256']}",
        "artifact_id": 7,
    }
    provenance_path.write_text(json.dumps(provenance_full), encoding="utf-8")
    return zip_path, receipt_path, provenance_path


def test_synthetic_authoritative_artifact_verifies(tmp_path: Path, monkeypatch):
    zip_path, receipt_path, provenance_path = build_fixture(tmp_path)
    monkeypatch.setattr(verifier, "RECEIPT", receipt_path)
    monkeypatch.setattr(verifier, "PROVENANCE", provenance_path)

    result = verifier.verify(zip_path)

    assert result["status"] == "VERIFIED"
    assert result["artifact_zip_sha256"] == verifier.sha256_file(zip_path)
    assert result["source_commit"] == "abc123"
    assert result["preserved_outside_github_actions"] is False


def test_tampered_zip_is_rejected(tmp_path: Path, monkeypatch):
    zip_path, receipt_path, provenance_path = build_fixture(tmp_path)
    monkeypatch.setattr(verifier, "RECEIPT", receipt_path)
    monkeypatch.setattr(verifier, "PROVENANCE", provenance_path)

    zip_path.write_bytes(zip_path.read_bytes() + b"tamper")

    with pytest.raises(verifier.ArtifactVerificationError, match="ZIP SHA-256 mismatch"):
        verifier.verify(zip_path)


def test_embedded_provenance_mismatch_is_rejected(tmp_path: Path, monkeypatch):
    zip_path, receipt_path, provenance_path = build_fixture(tmp_path)
    monkeypatch.setattr(verifier, "RECEIPT", receipt_path)
    monkeypatch.setattr(verifier, "PROVENANCE", provenance_path)

    with zipfile.ZipFile(zip_path, "a", compression=zipfile.ZIP_DEFLATED) as z:
        bad = {
            "git_commit": "wrong",
            "workflow_run_id": 42,
            "workflow_run_attempt": 1,
            "result_fingerprint": "f" * 64,
            "file_sha256": {
                "heldout_predictions.csv": "x",
                "fold_applicability_and_scores.csv": "x",
                "species_summary.csv": "x",
                "aggregate_result.json": "x",
            },
        }
        z.writestr("outcome/execution_provenance.json", json.dumps(bad))

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["artifact_zip_sha256"] = verifier.sha256_file(zip_path)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["artifact_digest"] = f"sha256:{receipt['artifact_zip_sha256']}"
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")

    with pytest.raises(verifier.ArtifactVerificationError, match="embedded provenance mismatch"):
        verifier.verify(zip_path)
