from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRE = ROOT / "development/zenodo_318_island_mammals_preintake_v0_1.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_zenodo_318_mammals_is_preintake_and_response_sealed():
    x = load(PRE)

    assert x["status"].startswith("HOLD_")
    assert x["source_identity"]["structural_prior_use_found"] is False
    assert x["source_identity"]["response_file_downloaded_by_structural"] is False
    assert x["source_identity"]["response_values_opened_by_structural"] is False
    assert x["v0_11_intake_authorized"] is False
    assert x["pilot_response_authorized"] is False
    assert x["confirmatory_response_authorized"] is False
    assert x["counts_as_empirical_evidence"] is False


def test_primary_is_source_pool_handoff_not_graph_metric_reuse():
    x = load(PRE)

    assert x["ecological_hypothesis"]["name"] == (
        "archipelago_source_pool_handoff_mammals"
    )
    assert x["source_pool_operator"]["candidate"].startswith(
        "fraction of other training islands"
    )
    assert x["proposed_reference_ladder"]["primary_predictive_contrast"] == (
        "C_minus_R3 heldout log loss"
    )
    assert x["proposed_reference_ladder"]["favourable_direction"] == "negative"
    assert x["primary_regime_prediction"]["primary_extreme_rule"].startswith(
        "upper 25%"
    )
    assert x["primary_regime_prediction"][
        "q70_q80_sensitivity_may_not_rescue_primary"
    ] is True


def test_mixed_file_firewall_is_declared_before_rows_open():
    x = load(PRE)
    fw = x["mixed_file_firewall_intent"]

    assert fw["column_firewall_must_be_frozen_before_any_data_row_is_opened"] is True
    assert "ID" in fw["safe_columns"]
    assert "dContinent_km" in fw["safe_columns"]
    assert "distance_biggerLandmass" in fw["safe_columns"]
    assert "SppRich" in fw["forbidden_response_derived_columns"]
    assert "Island_FRic" in fw["forbidden_response_derived_columns"]


def test_response_domain_must_be_frozen_before_pilot():
    x = load(PRE)

    requirements = x["response_schema_requirements"]
    assert any("value domain" in s for s in requirements)
    assert any("unexpected categorical response code" in s for s in requirements)
    assert x["source_pool_operator"]["fixed_species_universe_rule"].startswith(
        "must be frozen"
    )
