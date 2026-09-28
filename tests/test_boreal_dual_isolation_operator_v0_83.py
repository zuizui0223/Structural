from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import pytest

from structural.boreal_dual_isolation_operator import (
    BorealDualIsolationOperatorError,
    freeze_connected_knn_operator,
    source_features,
)
from structural.boreal_spatial_partition import connected_components


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/freeze_boreal_dual_isolation_operator_v0_83.py"
CONTRACT = ROOT / "development/boreal_dual_isolation_operator_contract_v0_83.json"
UNIVERSE = ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
STATUS = ROOT / "development/current_status_v0_83.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_83.json"


def load_script():
    spec = importlib.util.spec_from_file_location(
        "boreal_dual_isolation_freeze_v083",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_source_operator_is_distinct_from_disconnected_validation_graph():
    coordinates = {
        "A": (50.000, -105.000),
        "B": (50.005, -105.000),
        "C": (50.500, -105.000),
        "D": (50.505, -105.000),
    }

    components = connected_components(coordinates, radius_km=2.0)
    assert len(components) == 2

    operator = freeze_connected_knn_operator(coordinates)
    assert operator["operator"] == "minimal_connected_symmetrized_knn"
    assert operator["selected_k"] == 2
    assert operator["kernel_scale_km"] > 0
    assert operator["connectivity_audit"][0]["connected"] is False
    assert operator["connectivity_audit"][-1]["connected"] is True

    cross_cluster = [
        row
        for row in operator["edges"]
        if {row["left"], row["right"]} in (
            {"A", "C"}, {"A", "D"}, {"B", "C"}, {"B", "D"}
        )
    ]
    assert cross_cluster


def test_operator_is_deterministic_under_coordinate_mapping_order():
    a = {
        "A": (50.0, -105.0),
        "B": (50.1, -105.0),
        "C": (50.2, -105.0),
        "D": (50.3, -105.0),
    }
    b = dict(reversed(list(a.items())))

    assert freeze_connected_knn_operator(a) == freeze_connected_knn_operator(b)


def test_graph_source_features_are_nonredundant_but_geometrically_constrained():
    coordinates = {
        "A": (50.0, -105.0),
        "B": (50.05, -105.0),
        "C": (50.10, -105.0),
        "D": (50.15, -105.0),
    }
    operator = freeze_connected_knn_operator(coordinates)

    features = source_features(
        target="A",
        occupied_sources=("C", "D"),
        coordinates=coordinates,
        operator=operator,
    )

    assert features.nearest_euclidean_km > 0
    assert features.nearest_graph_path_km >= (
        features.nearest_euclidean_km - 1e-9
    )
    assert features.euclidean_source_pressure > 0
    assert features.graph_source_pressure > 0
    assert features.graph_source_pressure <= (
        features.euclidean_source_pressure + 1e-12
    )


def test_focal_island_is_defensively_excluded_from_occupied_sources():
    coordinates = {
        "A": (50.0, -105.0),
        "B": (50.1, -105.0),
        "C": (50.2, -105.0),
    }
    operator = freeze_connected_knn_operator(coordinates)

    with pytest.raises(
        BorealDualIsolationOperatorError,
        match="no occupied training source",
    ):
        source_features(
            target="A",
            occupied_sources=("A",),
            coordinates=coordinates,
            operator=operator,
        )


def test_real_freezer_requires_cross_v075_block_support(tmp_path: Path):
    module = load_script()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    universe_obj = json.loads(UNIVERSE.read_text(encoding="utf-8"))
    islands = universe_obj["current_study_island_universe"]["codes"]
    assert len(islands) == 42

    geometry_path = tmp_path / "safe_geometry.csv"
    rows = []
    for i, island in enumerate(islands):
        rows.append((island, 50.0 + i * 0.01, -105.0))

    with geometry_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["Island", "Lat", "Long"])
        for island, lat, lon in rows:
            writer.writerow([island, float(lat).hex(), float(lon).hex()])

    geometry_text = geometry_path.read_text(encoding="utf-8")
    geometry_sha = sha256_text(geometry_text)

    projection = {
        "schema": "structural.boreal_lake_islands_safe_projection_result.v0_74",
        "status": "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED",
        "candidate_id": contract["candidate_id"],
        "geometry": {
            "row_count": 42,
            "unique_island_count": 42,
            "sha256": geometry_sha,
        },
        "protected_response_values_opened": False,
        "counts_as_empirical_evidence": False,
    }

    island_to_block = {}
    for i, island in enumerate(islands):
        island_to_block[island] = "LEFT" if i < 21 else "RIGHT"

    spatial = {
        "schema": "structural.boreal_lake_islands_spatial_partition_result.v0_75",
        "status": "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": contract["candidate_id"],
        "source_geometry_sha256": geometry_sha,
        "island_to_block": island_to_block,
        "species_occurrence_used": False,
        "richness_used": False,
        "habitat_values_used": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
    }

    operator, receipt = module.freeze(
        geometry_path,
        projection,
        spatial,
        spatial_receipt_sha256="a" * 64,
        contract=contract,
    )

    assert receipt["status"] == (
        "DUAL_ISOLATION_OPERATOR_FROZEN_RESPONSE_INDEPENDENTLY"
    )
    assert receipt["cross_v075_block_edge_count"] >= 1
    assert receipt["validation_radius_reused"] is False
    assert receipt["species_occurrence_used_to_build_operator"] is False
    assert receipt["confirmatory_response_used_to_build_operator"] is False
    assert receipt["counts_as_empirical_evidence"] is False
    assert receipt["confirmatory_response_authorized"] is False
    assert len(receipt["operator_fingerprint"]) == 64
    assert operator["selected_k"] >= 1


def test_contract_binds_v055_and_forbids_tail_rescue():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["operator"]["response_used_to_select_k"] is False
    assert contract["operator"]["response_used_to_select_kernel_scale"] is False
    assert contract["operator"]["validation_radius_reused"] is False
    assert contract["required_cross_partition_support"][
        "source_graph_must_cross_v075_spatial_blocks"
    ] is True
    primary = contract["primary_hypothesis_binding"]
    assert "v0_55" in primary["hypothesis"]
    assert primary["favourable_direction"] == "negative"
    assert primary["external_isolation_interaction_required"] is False
    assert primary["extreme_isolation_tail_may_rescue_primary"] is False


def test_v083_status_keeps_fresh_denominator_zero():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))

    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["pilot_response_consumed"] is False
    assert boreal["dual_isolation_operator_executed"] is False
    assert boreal["confirmatory_response_values_opened"] is False
    assert boreal["confirmatory_protocol_freeze_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
