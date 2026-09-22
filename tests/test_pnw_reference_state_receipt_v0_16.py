from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "development/pnw_reference_state_receipt_v0_16.json"


def load():
    return json.loads(RECEIPT.read_text())


def test_reference_state_is_frozen_before_response():
    x = load()
    assert x["status"] == "pre_response_reference_frozen"
    assert x["year"] == "2012"
    assert x["site_rows"] == 219
    assert x["evaluation_target_sites_common_with_2013"] == 150
    assert x["response_access"]["focal_species_values_opened"] is False
    assert x["response_access"]["future_target_values_opened"] is False
    assert x["model_fit_count"] == 0


def test_reference_table_identity_and_aggregation_are_frozen():
    x = load()
    assert x["derived_table"]["sha256"] == "13277413ee5d4c9c30d4d8f9cb900203a92e129ccbc5ad4b6b0593dee0bbcdfd"
    assert x["site_aggregation"]["numeric"] == "median of distinct nonmissing values within 2012 site"
    assert x["site_aggregation"]["categorical_conflicts"] == 0


def test_common_site_missingness_is_retained_not_filtered():
    x = load()
    assert x["missing_site_values"]["common_150_sites"] == {
        "elev.m": 0,
        "max.size": 0,
        "maxdepth": 1,
        "perc.wooded": 0,
        "fish": 0,
    }
    assert x["common_150_missing_detail"]["maxdepth"] == ["Deerheart.LakeMUL9"]
    assert "do not drop Deerheart.LakeMUL9" in x["next_rule"]


def test_region_universe_is_frozen_before_endpoint_classes():
    x = load()
    counts = x["evaluation_region_counts"]
    assert sum(counts.values()) == 150
    assert len(counts) == 10
    assert x["next_stage"] == "stage1_lagged_state_authorization"
