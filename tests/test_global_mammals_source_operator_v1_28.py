from __future__ import annotations

import json
import math
from pathlib import Path

from scripts.freeze_global_mammals_source_operator_v1_28 import (
    spherical_block_centroids,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "development/global_mammals_source_operator_contract_v1_28.json"


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_real_contract_freezes_distinct_global_source_graph():
    x = load_contract()
    graph = x["graph"]
    assert graph["nodes"] == "219 frozen v1.25 spatial blocks"
    assert graph["validation_block_graph_reused"] is False
    assert graph["response_used_to_select_k"] is False
    assert graph["response_used_to_select_kernel_scale"] is False
    assert graph["expected_connectivity_audit"] == [
        {"k": 1, "edge_count": 152, "connected": False},
        {"k": 2, "edge_count": 280, "connected": False},
        {"k": 3, "edge_count": 409, "connected": False},
        {"k": 4, "edge_count": 542, "connected": True},
    ]
    assert graph["expected_selected_k"] == 4
    assert graph["expected_edge_count"] == 542
    assert graph["expected_kernel_scale_km_hex"] == "0x1.d9b27b6148cbep+9"
    assert graph["expected_pilot_confirmatory_cross_edge_count"] == 198
    assert graph["expected_cross_bioregion_edge_count"] == 123


def test_spherical_block_centroid_handles_dateline_without_arithmetic_lon_error():
    safe = [
        {"ID": "1", "Latitude_centroid": "0", "Longitude_centroid": "179"},
        {"ID": "2", "Latitude_centroid": "0", "Longitude_centroid": "-179"},
        {"ID": "3", "Latitude_centroid": "10", "Longitude_centroid": "0"},
    ]
    part = [
        {
            "ID": "1",
            "block_id": "A",
            "block_key": "Realm|lat09|lon35",
            "bioregion": "Realm",
            "split": "pilot",
        },
        {
            "ID": "2",
            "block_id": "A",
            "block_key": "Realm|lat09|lon35",
            "bioregion": "Realm",
            "split": "pilot",
        },
        {
            "ID": "3",
            "block_id": "B",
            "block_key": "Realm|lat10|lon18",
            "bioregion": "Realm",
            "split": "confirmatory",
        },
    ]
    coords, meta, island_to_block = spherical_block_centroids(safe, part)
    lat, lon = coords["A"]
    assert abs(lat) < 1e-12
    assert abs(abs(lon) - 180.0) < 1e-9
    assert meta["A"]["island_count"] == 2
    assert island_to_block == {"1": "A", "2": "A", "3": "B"}


def test_source_feature_rules_keep_confirmatory_response_out():
    x = load_contract()
    r3 = x["R3_direct_source_context"]
    c = x["C_graph_source_context"]
    assert "all frozen pilot islands only" in r3["confirmatory_prediction_rule"]
    assert "no confirmatory occurrence value" in r3["confirmatory_prediction_rule"]
    assert "all frozen pilot islands only" in c["confirmatory_prediction_rule"]
    assert "no confirmatory occurrence value" in c["confirmatory_prediction_rule"]
    assert x["response_boundary"]["Appendix_1_may_be_reopened"] is False
    assert x["response_boundary"]["response_used_to_build_operator"] is False
    assert x["response_boundary"]["fresh_system_denominator_contribution"] == 0
