from __future__ import annotations

import json
from pathlib import Path

from structural.mixed_csv_firewall import header_sha256


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "development/boreal_19island_header_projection_freeze_v0_95.json"


def test_v095_freezes_exact_header_and_geometry_only_before_rows():
    x = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert x["status"] == "HEADER_AND_SAFE_GEOMETRY_COLUMNS_FROZEN_BEFORE_ROW_ACCESS"
    assert x["candidate_id"] == "lac_la_ronge_boreal_19island_beetles_2026"
    assert len(x["file"]["header"]) == 19
    assert header_sha256(tuple(x["file"]["header"])) == (
        x["file"]["header_canonical_sha256"]
    )
    m = x["projection_manifest"]
    assert m["safe_pre_response_columns"] == ["Island", "Lat", "Long"]
    assert set(m["safe_pre_response_columns"]).isdisjoint(
        m["protected_response_columns"]
    )
    assert set(m["safe_pre_response_columns"]).isdisjoint(
        m["closed_unclassified_columns"]
    )
    assert sorted(
        m["safe_pre_response_columns"]
        + m["protected_response_columns"]
        + m["closed_unclassified_columns"]
    ) == sorted(x["file"]["header"])
    assert x["row_values_opened_by_freezer"] == 0
    assert x["biological_response_values_opened_by_freezer"] is False
    assert x["safe_geometry_projection_authorized_for_later_revision"] is True
    assert x["non_geometry_projection_authorized"] is False


def test_v095_subset_rule_is_response_independent():
    x = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert x["scope"]["island_count_expected"] == 19
    assert x["scope"]["source_defined_selection_rule"] == (
        "islands that burned between 1995 and 2021"
    )
    assert x["scope"]["selection_basis"] == (
        "fire-history and Landsat availability, not beetle response"
    )
