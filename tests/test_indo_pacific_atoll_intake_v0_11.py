from __future__ import annotations

import json
from pathlib import Path

from scripts.validate_independent_system_intake_v0_11 import validate_intake_v0_11


ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "development/indo_pacific_atoll_intake_v0_11.json"
SAFE = ROOT / "development/indo_pacific_atoll_safe_schema_v0_13.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_atoll_formal_intake_passes_v011_without_response_access():
    intake = load(INTAKE)
    code, receipt = validate_intake_v0_11(intake)

    assert code == 0
    assert receipt["status"] == (
        "eligible_to_construct_v0_31_and_v0_42_pre_pilot_contracts"
    )
    assert receipt["system_id"] == "indo_pacific_atoll_native_vascular_plants_2026"
    assert receipt["v0_31_protocol_construction_authorized"] is True
    assert receipt["v0_42_quality_contract_construction_authorized"] is True
    assert receipt["pilot_response_authorized"] is False
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["predictive_denominator_contribution"] == 0


def test_atoll_static_design_uses_only_m4_mechanism_lane():
    intake = load(INTAKE)
    code, receipt = validate_intake_v0_11(intake)

    assert code == 0
    assert intake["freshness_metadata"]["temporal_replication"] == "no"
    assert intake["requested_mechanism_lanes"] == ["M4_environmental_proxy"]
    assert receipt["freshness_triage_reasons"] == [
        "non_temporal_endpoint_permitted_for_non_dynamic_lanes"
    ]
    assert receipt["response_blind_data_support"][
        "environment_predictor_metadata_available"
    ] is True
    assert receipt["response_blind_data_support"][
        "temporal_transition_metadata_available"
    ] is False
    assert receipt["response_blind_data_support"][
        "genetic_sampling_metadata_available"
    ] is False


def test_native_endpoint_semantics_are_frozen_before_response():
    intake = load(INTAKE)
    endpoint = intake["predeclared_endpoint"]

    assert endpoint["target_1"] == "plant response row has presence code N"
    assert "presence code I" in endpoint["target_0"]
    assert endpoint["introduced_occurrences_are_native_presence"] is False
    assert endpoint["heldout_response_may_not_define_graph_or_partition"] is True


def test_safe_schema_has_required_response_independent_fields():
    safe = load(SAFE)

    assert safe["response_files_opened"] == 0
    assert safe["response_value_parse_count"] == 0
    assert safe["model_fit_count"] == 0
    assert safe["required_safe_fields_present"] == {
        "spatial_unit": True,
        "archipelago_group": True,
        "latitude_longitude": True,
        "land_area": True,
        "nearest_atoll_distance": True,
        "nearest_high_island_distance": True,
        "continent_distance": True,
        "annual_precipitation": True,
    }
    assert safe["published_response_semantics"]["presence_code_N"] == "native"
    assert safe["published_response_semantics"]["presence_code_I"] == "introduced"
    assert safe["published_response_semantics"][
        "response_values_inspected_by_structural"
    ] is False
