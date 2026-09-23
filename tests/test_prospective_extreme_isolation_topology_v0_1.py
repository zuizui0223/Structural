from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
H = ROOT / "development/prospective_extreme_isolation_topology_hypothesis_v0_1.json"


def load() -> dict:
    return json.loads(H.read_text(encoding="utf-8"))


def test_fresh_hypothesis_does_not_reuse_discovery_as_confirmation():
    x = load()

    assert x["status"] == "fresh_hypothesis_frozen_from_post_outcome_discovery_not_yet_tested"
    assert x["discovery_sources_may_not_count_as_confirmation"] is True
    assert x["candidate_selection_by_discovery_effect_direction"] is False
    assert x["current_confirmatory_systems"] == []
    assert x["confirmatory_response_authorized"] is False


def test_extreme_isolation_rule_is_response_independent_and_immutable():
    x = load()
    h = x["primary_hypothesis"]

    assert "upper 25%" in h["extreme_isolation_rule"]
    assert "predictor-only data before response access" in h["extreme_isolation_rule"]
    assert h["threshold_retuning_after_response"] is False
    assert h["favourable_direction"] == "negative"


def test_cross_origin_claim_requires_spatial_transfer_not_only_local_support():
    x = load()
    transfer = x["transfer_design"]

    assert transfer["local_only_support_cannot_establish_cross_origin_portability"] is True
    assert "same direction under spatial transfer" in transfer["cross_origin_claim_rule"]


def test_presence_absence_asymmetry_is_secondary_only():
    x = load()
    d = x["secondary_diagnostics"]["presence_absence_asymmetry"]

    assert d["role"] == "secondary_mechanism_diagnostic_not_primary_success_gate"
    assert d["favourable_subgroup_selection_forbidden"] is True
