from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from scripts.validate_mechanism_protocol_v0_1 import (
    MechanismProtocolError,
    validate_framework,
    validate_future_protocol,
)


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = ROOT / "development/prospective_mechanism_discrimination_v0_1.json"
FIXTURE = ROOT / "tests/fixtures/mechanism_protocol_v0_1/valid_protocol.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_prospective_mechanism_framework_is_valid_and_inactive():
    result = validate_framework(load(FRAMEWORK))

    assert result["status"] == "VALID_PROSPECTIVE_FRAMEWORK"
    assert result["current_system_count"] == 0
    assert result["confirmatory_response_authorized"] is False
    assert result["mechanism_claim_authorized"] is False
    assert result["mechanism_lanes"] == [
        "M1_contemporary_colonization",
        "M2_rescue_persistence",
        "M3_historical_colonization_legacy",
        "M4_environmental_proxy",
    ]


def test_framework_keeps_colonization_and_persistence_as_separate_estimands():
    x = load(FRAMEWORK)

    assert x["mechanism_lanes"]["M1_contemporary_colonization"][
        "target_transition"
    ] == "0_to_1"
    assert x["mechanism_lanes"]["M2_rescue_persistence"][
        "target_transition"
    ] == "1_to_0 or equivalently 1_to_1 persistence"

    dynamic = x["dynamic_separation_contract"]
    assert dynamic["colonization_and_extinction_are_separate_estimands"] is True
    assert (
        dynamic[
            "pooling_0_to_1_and_1_to_0_into_one_binary_endpoint_for_mechanism_claims"
        ]
        is False
    )
    assert (
        dynamic["non_estimable_transition_lane_counts_as_neither_support_nor_refutation"]
        is True
    )


def test_valid_future_protocol_starts_response_sealed():
    result = validate_future_protocol(load(FIXTURE))

    assert result["status"] == "VALID_RESPONSE_SEALED_PROTOCOL"
    assert result["response_access_authorized"] is False
    assert set(result["mechanism_lanes_authorized"]) == {
        "M1_contemporary_colonization",
        "M2_rescue_persistence",
        "M3_historical_colonization_legacy",
        "M4_environmental_proxy",
    }


def test_future_protocol_cannot_start_with_response_access():
    x = load(FIXTURE)
    x["response_access_authorized"] = True

    with pytest.raises(MechanismProtocolError, match="response-sealed"):
        validate_future_protocol(x)


def test_dynamic_lanes_require_both_transition_event_minima():
    x = load(FIXTURE)
    del x["transition_event_minima_if_dynamic"]["minimum_1_to_0"]

    with pytest.raises(MechanismProtocolError, match="both transition event minima"):
        validate_future_protocol(x)


def test_historical_lane_requires_genetic_estimand_and_null():
    x = load(FIXTURE)
    del x["genetic_estimand_and_null_if_M3"]

    with pytest.raises(MechanismProtocolError, match="M3 requires"):
        validate_future_protocol(x)


def test_environmental_proxy_lane_requires_frozen_environment_enrichment():
    x = load(FIXTURE)
    del x["enriched_environment_predictors_if_M4"]

    with pytest.raises(MechanismProtocolError, match="M4 requires"):
        validate_future_protocol(x)


def test_mechanism_lanes_cannot_rescue_structural_primary():
    x = load(FRAMEWORK)

    assert x["entry_conditions"]["mechanism_result_may_not_change_structural_primary"] is True
    assert (
        "do not use any mechanism lane to rescue a failed Structural extreme-isolation primary"
        in x["anti_selection"]
    )


def test_environmental_proxy_must_be_response_blind_not_iterative_erasure():
    x = load(FRAMEWORK)
    lane = x["mechanism_lanes"]["M4_environmental_proxy"]

    assert "response-blind enriched habitat/environment predictors" in lane["minimum_data"]
    assert "may not be expanded iteratively" in lane["negative_control"]


def test_interpretation_matrix_allows_mixed_or_unresolved_mechanisms():
    x = load(FRAMEWORK)

    assert "mixed_or_unresolved" in x["interpretation_matrix"]
    assert "no forced single-winner label" in x["interpretation_matrix"]["mixed_or_unresolved"]
