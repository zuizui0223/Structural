from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYNTHESIS = ROOT / "development/aislands_source_pool_handoff_v0_1.json"
PROSPECTIVE = ROOT / "development/prospective_source_pool_handoff_hypothesis_v0_1.json"
PARENT = ROOT / "development/prospective_extreme_isolation_topology_hypothesis_v0_3.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_aislands_source_pool_handoff_is_synthesis_not_new_confirmation():
    x = load(SYNTHESIS)

    assert x["status"] == "ecological_synthesis_from_frozen_exploratory_outputs"
    assert x["changes_frozen_structural_primary"] is False
    assert x["counts_as_confirmatory_evidence"] is False
    assert x["adds_new_same_data_search"] is False
    assert x["next_test"] == (
        "development/prospective_source_pool_handoff_hypothesis_v0_1.json"
    )


def test_source_pool_handoff_preserves_frozen_extreme_isolation_primary():
    future = load(PROSPECTIVE)
    parent = load(PARENT)

    assert future["discovery_sources_may_not_count_as_confirmation"] is True
    assert future["same_data_retuning_forbidden"] is True
    assert future["primary_prediction"]["inherits_exactly_from"] == (
        "development/prospective_extreme_isolation_topology_hypothesis_v0_3.json"
    )
    assert future["primary_prediction"]["extreme_isolation_rule"] == (
        parent["primary_hypothesis"]["extreme_isolation_rule"]
    )
    assert future["primary_prediction"]["favourable_direction"] == (
        parent["primary_hypothesis"]["favourable_direction"]
    )
    assert future["primary_prediction"]["threshold_retuning_after_response"] is False
    assert future["confirmatory_response_authorized"] is False


def test_mechanistic_secondaries_cannot_rescue_primary():
    future = load(PROSPECTIVE)
    secondaries = future["secondary_predictions"]

    assert secondaries["remote_but_linked_vs_remote_unlinked"][
        "may_rescue_failed_primary"
    ] is False
    assert secondaries["multihop_continuity"]["may_rescue_failed_primary"] is False
    assert future["independent_biological_discrimination"][
        "no_mechanism_may_rescue_failed_structural_primary"
    ] is True
