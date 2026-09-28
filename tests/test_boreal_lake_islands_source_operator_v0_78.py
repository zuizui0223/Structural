from __future__ import annotations

import json
from pathlib import Path

import pytest

from structural.boreal_source_operator import (
    C_FEATURES,
    R2_FEATURES,
    R3_SOURCE_FEATURES,
    BorealSourceOperatorError,
    freeze_generic_geometry_context,
    scales_from_v075_result,
    training_source_features,
    unique_scales_km,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "development/boreal_lake_islands_source_operator_contract_v0_78.json"
STATUS = ROOT / "development/current_status_v0_78.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_78.json"


def chain_geometry():
    # At the equator, 0.005 degrees longitude is about 0.556 km.
    # At radius 0.6 km, A--B--C is connected but A is not a direct neighbor of C.
    return {
        "A": (0.0, 0.000),
        "B": (0.0, 0.005),
        "C": (0.0, 0.010),
    }


def state():
    return {
        "area": {"A": 10.0, "B": 2.0, "C": 5.0},
        "mainland": {"A": 0.1, "B": 1.0, "C": 2.0},
    }


def test_unique_scales_collapse_duplicate_rounded_graphs():
    assert unique_scales_km([0.6, 0.6, 1.0, 0.8]) == (0.6, 0.8, 1.0)


def test_multihop_chain_is_connected_without_direct_source_neighbor():
    coords = chain_geometry()
    s = state()

    features = training_source_features(
        "C",
        training_islands=("A",),
        training_presence_islands=("A",),
        coordinates=coords,
        area_ha=s["area"],
        scales_km=(0.6,),
    )

    assert features["training_island_count"] == 1
    assert features["training_presence_count"] == 1
    assert features["training_global_occupied_fraction"] == 1.0
    assert features["occupied_component_frequency"] == 1.0
    assert features["direct_occupied_neighbor_frequency_diagnostic"] == 0.0
    assert features["multi_hop_only_frequency_diagnostic"] == 1.0
    assert features["nearest_training_presence_km"] > 1.0
    assert features["focal_self_excluded"] is False


def test_training_row_self_exclusion_removes_own_presence_and_denominator():
    coords = chain_geometry()
    s = state()

    features = training_source_features(
        "A",
        training_islands=("A", "B", "C"),
        training_presence_islands=("A", "C"),
        coordinates=coords,
        area_ha=s["area"],
        scales_km=(0.6, 1.2),
    )

    assert features["focal_self_excluded"] is True
    assert features["training_island_count"] == 2
    assert features["training_presence_count"] == 1
    assert features["training_global_occupied_fraction"] == 0.5
    # A cannot use itself as a zero-distance occupied source.
    assert features["nearest_training_presence_km"] > 1.0


def test_zero_effective_training_presence_is_non_estimable():
    coords = chain_geometry()
    s = state()

    with pytest.raises(
        BorealSourceOperatorError,
        match="no effective training presence",
    ):
        training_source_features(
            "A",
            training_islands=("A", "B", "C"),
            training_presence_islands=("A",),
            coordinates=coords,
            area_ha=s["area"],
            scales_km=(0.6,),
        )


def test_source_area_state_must_cover_exact_island_universe():
    coords = chain_geometry()

    with pytest.raises(
        BorealSourceOperatorError,
        match="source-area island set mismatch",
    ):
        training_source_features(
            "C",
            training_islands=("A",),
            training_presence_islands=("A",),
            coordinates=coords,
            area_ha={"A": 10.0},
            scales_km=(0.6,),
        )


def test_generic_R2_context_contains_no_species_response():
    coords = chain_geometry()
    s = state()

    frozen = freeze_generic_geometry_context(
        coords,
        area_ha=s["area"],
        mainland_distance_km=s["mainland"],
        scales_km=(0.6, 0.6, 1.2),
    )

    assert frozen["unique_scales_km"] == [0.6, 1.2]
    assert frozen["duplicate_named_scales_collapsed"] is True
    assert tuple(frozen["features"]) == R2_FEATURES
    assert set(frozen["rows"]) == {"A", "B", "C"}

    for island, row in frozen["rows"].items():
        assert set(row) == set(R2_FEATURES)
        assert row["nearest_other_island_km"] > 0
        assert 0 <= row["unanchored_component_exposure"] <= 1
        assert 0 <= row["mainland_stepping_stone_frequency"] <= 1


def test_generic_and_source_features_are_order_invariant_exactly():
    coords_a = chain_geometry()
    coords_b = dict(reversed(list(coords_a.items())))
    s = state()

    generic_a = freeze_generic_geometry_context(
        coords_a,
        area_ha=s["area"],
        mainland_distance_km=s["mainland"],
        scales_km=(1.2, 0.6, 0.6),
    )
    generic_b = freeze_generic_geometry_context(
        coords_b,
        area_ha=dict(reversed(list(s["area"].items()))),
        mainland_distance_km=dict(reversed(list(s["mainland"].items()))),
        scales_km=(0.6, 1.2),
    )
    assert generic_a == generic_b

    source_a = training_source_features(
        "C",
        training_islands=("A", "B"),
        training_presence_islands=("A", "B"),
        coordinates=coords_a,
        area_ha=s["area"],
        scales_km=(1.2, 0.6),
    )
    source_b = training_source_features(
        "C",
        training_islands=("B", "A"),
        training_presence_islands=("B", "A"),
        coordinates=coords_b,
        area_ha=dict(reversed(list(s["area"].items()))),
        scales_km=(0.6, 1.2),
    )
    assert {
        k: (float(v).hex() if isinstance(v, float) else v)
        for k, v in source_a.items()
    } == {
        k: (float(v).hex() if isinstance(v, float) else v)
        for k, v in source_b.items()
    }


def test_area_weighted_source_pressure_is_a_stronger_reference_term():
    coords = chain_geometry()
    s = state()

    features = training_source_features(
        "C",
        training_islands=("A", "B"),
        training_presence_islands=("A", "B"),
        coordinates=coords,
        area_ha=s["area"],
        scales_km=(0.6, 1.2),
    )

    assert features["area_weighted_source_pressure"] > features[
        "multi_source_pressure"
    ]


def test_v075_result_supplies_response_independent_operator_scales():
    result = {
        "schema": "structural.boreal_lake_islands_spatial_partition_result.v0_75",
        "status": "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_radii": {
            "q25": {"rounded_up_km": 0.6},
            "q50": {"rounded_up_km": 0.6},
            "q75": {"rounded_up_km": 1.2},
            "q90": {"rounded_up_km": 2.0},
        },
    }
    assert scales_from_v075_result(result) == (0.6, 1.2, 2.0)


def test_primary_model_ladder_puts_generic_and_direct_terms_before_C():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    ladder = x["reference_ladder"]

    assert tuple(ladder["R2_add"]) == R2_FEATURES
    assert tuple(ladder["R3_add"]) == R3_SOURCE_FEATURES
    assert tuple(ladder["C_add"]) == C_FEATURES
    assert ladder["C_add"] == ["occupied_component_frequency"]
    assert "area_weighted_source_pressure" in ladder["R3_add"]
    assert x["C_feature_rule"][
        "movement_probability_interpretation_authorized"
    ] is False
    assert x["C_feature_rule"][
        "colonization_probability_interpretation_authorized"
    ] is False


def test_multihop_is_diagnostic_not_posthoc_primary():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    diagnostics = x["diagnostics_not_primary_predictors"]

    assert "multi_hop_only_frequency" in diagnostics
    assert x["reference_ladder"]["C_add"] == [
        "occupied_component_frequency"
    ]
    assert "multi_hop_only_frequency" not in x["reference_ladder"]["C_add"]


def test_v078_status_keeps_denominator_zero_and_response_closed():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))

    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["source_operator_frozen_before_response"] is True
    assert boreal["stage_A_workflow_executed"] is False
    assert boreal["biological_response_values_opened"] is False
    assert boreal["v0_12_intake_authorized"] is False
    assert boreal["pilot_response_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
