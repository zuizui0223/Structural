from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE = (
    ROOT / "development/boreal_19island_pilot_authorization_freeze_v1_06.json"
)
AUTH = (
    ROOT / "development/boreal_19island_pilot_response_authorization_v1_05.json"
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: dict) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def test_v106_freezes_exact_v105_authorization_bytes_and_fingerprint():
    freeze = load(FREEZE)
    auth = load(AUTH)

    assert freeze["status"] == (
        "ONE_SHOT_PILOT_AUTHORIZATION_COMMITTED_RESPONSE_UNOPENED"
    )
    assert sha(AUTH) == freeze["authorization"]["file_sha256"]
    assert sha(AUTH) == (
        "b32613cad3c2ca4055c581b2540db349b312641e5d94ccd4dee5ec5e6c21978b"
    )

    fingerprint = auth.pop("authorization_fingerprint")
    assert fingerprint == freeze["authorization"]["authorization_fingerprint"]
    assert canonical_sha256(auth) == fingerprint
    assert fingerprint == (
        "2942d3d76d118bcf04c71d721d8f37f5531abb964713828dc375f610d08fab97"
    )


def test_v106_preserves_exact_semantic_ceiling():
    freeze = load(FREEZE)
    auth = load(AUTH)

    assert len(auth["full_source_island_order"]) == 42
    assert len(auth["pilot_islands"]) == 6
    assert len(auth["confirmatory_islands"]) == 13
    assert len(auth["excluded_islands"]) == 23

    access = auth["allowed_semantic_access"]
    assert access == {
        "analysis_confirmatory_occurrence_cells": False,
        "excluded_23_island_occurrence_cells": False,
        "pilot_island_occurrence_cells": True,
        "routing_island_field_all_42_rows": True,
        "species_header_names": True,
    }
    assert freeze["semantic_ceiling"] == {
        "routing_island_fields_may_be_decoded": 42,
        "species_header_names_may_be_decoded": 466,
        "pilot_island_occurrence_rows_may_be_decoded": 6,
        "confirmatory_island_occurrence_rows_may_be_decoded": 0,
        "excluded_island_occurrence_rows_may_be_decoded": 0,
    }


def test_v106_authorized_is_not_opened_or_consumed():
    freeze = load(FREEZE)
    auth = load(AUTH)

    assert auth["pilot_response_authorized"] is True
    assert auth["authorization_consumed"] is False
    assert auth["response_values_opened_by_authorization"] is False
    assert auth["confirmatory_response_authorized"] is False
    assert auth["predictive_denominator_contribution"] == 0
    assert auth["counts_as_empirical_evidence"] is False

    assert freeze["response_boundary"] == {
        "pilot_response_authorized": True,
        "pilot_response_opened": False,
        "authorization_consumed": False,
        "confirmatory_response_authorized": False,
        "confirmatory_response_opened": False,
        "counts_as_empirical_evidence": False,
        "predictive_denominator_contribution": 0,
    }
    assert freeze["pilot_executor_may_be_built"] is True
    assert freeze["pilot_executor_may_run_in_this_revision"] is False
