from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import scripts.verify_release_candidate_v0_2 as verifier
from scripts.verify_release_candidate_v0_2 import (
    AUTHOR_METADATA,
    PREFLIGHT,
    _archive_blockers,
    _human_policy_blockers,
    evaluate,
)


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_current_repository_evaluates_to_human_policy_hold_without_package():
    receipt = evaluate(None)

    assert receipt["stage"] == "HOLD_HUMAN_POLICY_GATES"
    assert receipt["release_actions_authorized"] is False
    assert receipt["scientific_state_changed"] is False
    assert receipt["package_verified"] is False
    assert receipt["human_policy_blockers"]


def test_current_author_template_exposes_expected_unresolved_gates():
    metadata = load(AUTHOR_METADATA)
    blockers = set(_human_policy_blockers(metadata))

    assert "author_list_or_roles_incomplete" in blockers
    assert "affiliations_incomplete" in blockers
    assert "corresponding_author_incomplete" in blockers
    assert "funding_statement_incomplete" in blockers
    assert "generative_ai_disclosure_not_approved" in blockers
    assert "journal_specific_guide_not_checked" in blockers
    assert "creator_order_not_confirmed" in blockers


def test_fully_approved_synthetic_metadata_has_no_human_policy_blockers():
    metadata = load(AUTHOR_METADATA)
    approved = deepcopy(metadata)

    approved["authors"] = [
        {
            "name": "Approved Author",
            "orcid": "",
            "affiliation_ids": ["aff1"],
            "credit_roles": ["Conceptualization"],
            "corresponding_author": True,
        }
    ]
    approved["affiliations"] = [
        {
            "id": "aff1",
            "institution": "Approved Institution",
            "department": "",
            "city": "Approved City",
            "country": "Approved Country",
        }
    ]
    approved["corresponding_author"] = {
        "name": "Approved Author",
        "email": "approved@example.org",
        "postal_address": "Approved address",
    }
    approved["funding"] = [
        {"funder": "None", "grant_number": "", "recipient": ""}
    ]
    approved["competing_interests"] = {
        "confirmed_by_all_authors": True,
        "statement": "No competing interests.",
    }
    approved["ethics_and_permits"] = {
        "review_completed": True,
        "statement": "Not applicable.",
    }
    approved["originality_and_submission"] = {
        "approved_by_all_authors": True,
        "not_published_previously_confirmed": True,
        "not_under_consideration_elsewhere_confirmed": True,
    }
    approved["generative_ai_disclosure"].update(
        {
            "reviewed_by_all_authors": True,
            "live_journal_policy_checked": True,
            "journal_specific_guide_checked": True,
            "final_statement": "Approved disclosure.",
        }
    )
    approved["release_metadata"] = {
        "creator_order_confirmed": True,
        "software_citation_metadata_approved": True,
    }

    assert _human_policy_blockers(approved) == []


def test_preflight_still_forbids_final_release():
    preflight = load(PREFLIGHT)

    assert preflight["status"] == "HOLD_HUMAN_POLICY_GATES"
    assert all(
        value is False
        for value in preflight["release_actions_authorized"].values()
    )

def test_current_repository_exposes_authoritative_artifact_archive_blocker():
    blockers = _archive_blockers()

    assert blockers == ["authoritative_raw_artifact_not_preserved_durably"]


def test_archive_gate_blocks_identifier_stage_after_human_gates_clear(monkeypatch):
    monkeypatch.setattr(verifier, "_human_policy_blockers", lambda metadata: [])

    receipt = verifier.evaluate(None)

    assert receipt["stage"] == "HOLD_ARCHIVE_CONTENT_GATES"
    assert receipt["archive_content_blockers"] == [
        "authoritative_raw_artifact_not_preserved_durably"
    ]


def test_identifier_stage_requires_both_human_and_archive_gates_clear(monkeypatch):
    monkeypatch.setattr(verifier, "_human_policy_blockers", lambda metadata: [])
    monkeypatch.setattr(verifier, "_archive_blockers", lambda: [])

    receipt = verifier.evaluate(None)

    assert receipt["stage"] == "READY_FOR_IDENTIFIER_RESERVATION_AND_IDENTIFIER_ONLY_PR"
    assert receipt["human_policy_blockers"] == []
    assert receipt["archive_content_blockers"] == []
    assert receipt["unresolved_identifier_placeholders"]

