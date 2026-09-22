from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "development/pnw_stage1_result_v0_18.json"


def test_stage1_result_is_frozen_before_2013_target():
    x = json.loads(RECEIPT.read_text())
    assert x["status"] == "stage1_complete_with_normalization_adjudication"
    assert x["response_access"]["2012_lagged_state_opened"] is True
    assert x["response_access"]["2013_target_opened"] is False
    assert x["response_access"]["2013_target_values_summarized"] is False
    assert x["response_access"]["model_fit_count"] == 0


def test_stage1_source_and_feature_counts_are_frozen():
    x = json.loads(RECEIPT.read_text())
    assert x["site_state"]["sites_total"] == 219
    assert x["site_state"]["positive"] == 134
    assert x["site_state"]["negative"] == 19
    assert x["site_state"]["non_estimable"] == 66
    assert x["connectivity"]["occupied_source_sites"] == 134
    assert x["feature_table"]["rows"] == 150


def test_stage1_fingerprints_are_frozen():
    x = json.loads(RECEIPT.read_text())
    assert x["site_state"]["state_table_sha256"] ==         "bbf407503d1db9f911989d27717bb44e80d4028b65647c7b588d23f5bf87b440"
    assert x["feature_table"]["sha256"] ==         "f2e85764d736ee069c5805e6a808b7e434bbb2930cfa0808e7ff723927af4ce6"


def test_normalization_adjudication_is_explicit():
    x = json.loads(RECEIPT.read_text())
    n = x["normalization"]
    assert n["valid_survey_types"] == ["full", "partial"]
    assert "dry" in n["excluded_survey_types"]
    assert "zero-fill RACA" in n["missing_species_row_rule"]
    assert x["counts_as_pristine_fresh_evidence"] is False
