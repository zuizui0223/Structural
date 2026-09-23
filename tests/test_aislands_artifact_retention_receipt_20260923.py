from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIR = ROOT / "validation/aislands_isolation_adequacy_20260812"
RECEIPT = DIR / "artifact_retention_receipt_20260923.json"
PROVENANCE = DIR / "authoritative_execution_provenance.json"
OUTCOME = DIR / "authoritative_outcome.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_retention_receipt_matches_committed_authoritative_provenance():
    receipt = load(RECEIPT)
    provenance = load(PROVENANCE)

    assert receipt["status"] == "VERIFIED_OUTSIDE_ACTIONS_BACKUP_FINAL_ARCHIVE_PENDING"
    assert receipt["source_repository"] == "zuizui0223/eog"
    assert receipt["source_commit"] == provenance["git_commit"]
    assert receipt["workflow_run_id"] == provenance["workflow_run_id"]
    assert receipt["workflow_run_attempt"] == provenance["workflow_run_attempt"]
    assert receipt["artifact_id"] == provenance["artifact_id"]
    assert receipt["artifact_name"] == provenance["artifact_name"]
    assert (
        f"sha256:{receipt['artifact_zip_sha256']}"
        == provenance["artifact_digest"]
    )
    assert receipt["result_fingerprint"] == provenance["result_fingerprint"]


def test_retention_member_hashes_match_provenance_and_outcome():
    receipt = load(RECEIPT)
    provenance = load(PROVENANCE)
    outcome = load(OUTCOME)

    expected = provenance["file_sha256"]
    members = receipt["verified_member_hashes"]

    assert members["outcome/heldout_predictions.csv"]["sha256"] == expected[
        "heldout_predictions.csv"
    ]
    assert members["outcome/fold_applicability_and_scores.csv"]["sha256"] == expected[
        "fold_applicability_and_scores.csv"
    ]
    assert members["outcome/species_summary.csv"]["sha256"] == expected[
        "species_summary.csv"
    ]
    assert members["outcome/aggregate_result.json"]["sha256"] == expected[
        "aggregate_result.json"
    ]

    assert outcome["output_sha256"]["heldout_predictions"] == expected[
        "heldout_predictions.csv"
    ]
    assert outcome["output_sha256"]["fold_applicability_and_scores"] == expected[
        "fold_applicability_and_scores.csv"
    ]
    assert outcome["output_sha256"]["species_summary"] == expected[
        "species_summary.csv"
    ]


def test_retention_deadline_is_explicit_and_not_claimed_complete():
    receipt = load(RECEIPT)
    retention = receipt["long_term_preservation"]

    assert receipt["artifact_expired_at_verification"] is False
    assert receipt["artifact_expires_at"] == "2026-11-10T04:42:52Z"
    assert retention["preserved_outside_github_actions"] is True
    assert retention["actions_expiry_risk_mitigated"] is True
    assert retention["backup_provider"] == "Google Drive"
    assert retention["backup_size_bytes"] == receipt["artifact_size_bytes"]
    assert retention["backup_redownload_sha256"] == receipt["artifact_zip_sha256"]
    assert retention["final_doi_archive_contains_verified_artifact"] is False
    assert retention["actions_artifact_expires_at"] == receipt["artifact_expires_at"]
    assert (
        retention["final_release_must_not_claim_raw_authoritative_artifact_archived_until_verified"]
        is True
    )
