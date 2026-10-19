from __future__ import annotations

import importlib.util
import io
import json
import math
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/freeze_global_mammals_macro_state_operator_v1_27.py"
CONTRACT = ROOT / "development/global_mammals_macro_state_operator_contract_v1_27.json"


def load_module():
    spec = importlib.util.spec_from_file_location(
        "global_mammals_v127", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def synthetic_rows():
    return [
        {
            "ID": str(i + 1),
            "Longitude_centroid": float(i),
            "Latitude_centroid": 0.0,
            "Area": float(i + 1),
            "Current_isolation": float(i) / 10.0,
            "Past_isolation": float(i % 2),
            "Climate_velocity": float(i + 2),
            "Temperature_mean": float(10 + i),
            "Temperature_sd": float(1 + i),
            "Precipitation_mean": float(100 + 5 * i),
            "Precipitation_sd": float(10 + i),
            "Elevation_sd": float(2 + i),
            "bioregion": (
                "Afrotropical" if i < 2 else
                "Australian" if i < 4 else
                "Paleartic"
            ),
        }
        for i in range(6)
    ]


def test_real_contract_keeps_macro_only_response_boundary():
    x = load_contract()
    assert x["analysis_route"] == "contaminated_macro_analysis_only"
    assert x["safe_artifact"]["safe_row_count"] == 5592
    assert x["spatial_artifact"]["total_block_count"] == 219

    state = x["state_reference"]
    assert state["categorical_reference"]["reference_level"] == "Afrotropical"
    assert state["transform_rules"]["Area"] == (
        "log10(Area + 1.0) before population z-score"
    )
    assert state["R0_numeric_source_columns"] == [
        "Temperature_mean",
        "Temperature_sd",
        "Precipitation_mean",
        "Precipitation_sd",
        "Elevation_sd",
    ]
    assert state["R1_add_source_columns"] == [
        "Area",
        "Current_isolation",
        "Past_isolation",
        "Climate_velocity",
    ]

    op = x["source_operator"]
    assert op["validation_blocks_reused_as_source_components"] is False
    assert op["response_used_to_choose_k"] is False
    assert op["response_used_to_choose_kernel_scale"] is False
    assert op["audit_expectations_from_response_independent_geometry"] == {
        "selected_k": 36,
        "edge_count": 124733,
        "cross_validation_block_edge_count": 37235,
        "kernel_scale_km_hex": "0x1.0329e68e17975p+7",
    }

    boundary = x["response_boundary"]
    assert boundary["Appendix_1_reopened"] is False
    assert boundary["mammal_species_names_opened"] is False
    assert boundary["mammal_occurrence_values_opened"] is False
    assert boundary["counts_as_fresh_confirmation"] is False
    assert boundary["fresh_system_denominator_contribution"] == 0
    assert boundary["original_fresh_chain_restored"] is False


def test_state_reference_freezes_realm_dummies_and_population_z_scores():
    module = load_module()
    contract = load_contract()
    text, receipt = module.freeze_state_reference(
        synthetic_rows(),
        contract=contract,
    )
    header = text.splitlines()[0].split(",")
    assert header[:2] == ["ID", "bioregion"]
    assert "REALM_Australian" in header
    assert "REALM_Paleartic" in header
    assert "REALM_Afrotropical" not in header
    assert "Z_Temperature_mean" in header
    assert "Z_LOG10_AREA_PLUS1" in header
    assert "Z_Current_isolation" in header
    assert "Z_Past_isolation" in header
    assert "Z_Climate_velocity" in header

    assert receipt["bioregion_reference_level"] == "Afrotropical"
    assert receipt["state_reference_row_count"] == 6
    assert len(receipt["R0_columns"]) == 7
    assert receipt["R1_add_columns"] == [
        "Z_LOG10_AREA_PLUS1",
        "Z_Current_isolation",
        "Z_Past_isolation",
        "Z_Climate_velocity",
    ]
    assert len(receipt["state_reference_sha256"]) == 64


def test_small_source_operator_uses_distinct_graph_and_crosses_blocks():
    module = load_module()
    rows = synthetic_rows()[:4]
    partition = {
        "1": {"block_id": "A"},
        "2": {"block_id": "A"},
        "3": {"block_id": "B"},
        "4": {"block_id": "B"},
    }
    contract = load_contract()
    contract["source_operator"] = json.loads(
        json.dumps(contract["source_operator"])
    )
    contract["source_operator"]["search_max_k"] = 3

    one_degree = module._haversine_km(0.0, 0.0, 0.0, 1.0)
    contract["source_operator"][
        "audit_expectations_from_response_independent_geometry"
    ] = {
        "selected_k": 1,
        "edge_count": 3,
        "cross_validation_block_edge_count": 1,
        "kernel_scale_km_hex": float(one_degree).hex(),
    }
    operator, receipt = module.freeze_source_operator(
        rows,
        partition,
        contract=contract,
    )

    assert operator["selected_k"] == 1
    assert operator["edge_count"] == 3
    assert operator["cross_validation_block_edge_count"] == 1
    assert operator["validation_blocks_reused_as_source_components"] is False
    assert operator["response_used_to_choose_k"] is False
    assert operator["response_used_to_choose_kernel_scale"] is False
    assert len(operator["operator_fingerprint"]) == 64
    assert receipt["selected_k"] == 1
    assert receipt["edge_count"] == 3
    assert receipt["cross_validation_block_edge_count"] == 1
    assert receipt["connectivity_audit"][0]["connected"] is True
    assert set(operator["generic_node_context"]) == {"1", "2", "3", "4"}


def test_source_operator_fails_closed_if_audit_drifts():
    module = load_module()
    rows = synthetic_rows()[:4]
    partition = {
        str(i + 1): {"block_id": "A" if i < 2 else "B"}
        for i in range(4)
    }
    contract = load_contract()
    contract["source_operator"] = json.loads(
        json.dumps(contract["source_operator"])
    )
    contract["source_operator"]["search_max_k"] = 3
    contract["source_operator"][
        "audit_expectations_from_response_independent_geometry"
    ] = {
        "selected_k": 2,
        "edge_count": 999,
        "cross_validation_block_edge_count": 999,
        "kernel_scale_km_hex": "0x1.0p+0",
    }
    with pytest.raises(
        module.GlobalMammalStateOperatorError,
        match="source-graph audit drift",
    ):
        module.freeze_source_operator(
            rows,
            partition,
            contract=contract,
        )


def test_area_transform_is_log10_plus_one_not_raw_log():
    module = load_module()
    rows = synthetic_rows()
    _, receipt = module.freeze_state_reference(
        rows,
        contract=load_contract(),
    )
    constants = receipt["standardization_constants_hex"]
    mean = float.fromhex(constants["LOG10_AREA_PLUS1"]["mean_hex"])
    expected = sum(
        math.log10(float(row["Area"]) + 1.0)
        for row in rows
    ) / len(rows)
    assert math.isclose(mean, expected, rel_tol=0.0, abs_tol=1e-15)
