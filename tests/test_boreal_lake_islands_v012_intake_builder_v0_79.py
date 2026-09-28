from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from scripts.validate_independent_system_intake_v0_12 import validate_intake_v0_12


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_boreal_v012_intake_v0_79.py"
CONTRACT = ROOT / "development/boreal_lake_islands_v012_intake_builder_contract_v0_79.json"
PREINTAKE = ROOT / "development/boreal_lake_islands_preintake_v0_65.json"
METADATA = ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
STATUS = ROOT / "development/current_status_v0_79.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_79.json"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal_v012_builder_v079", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def receipts():
    candidate = "lac_la_ronge_boreal_island_beetles_2026"
    geometry_sha = "a" * 64
    habitat_sha = "b" * 64
    reference_sha = "c" * 64
    projection = {
        "schema": "structural.boreal_lake_islands_safe_projection_result.v0_74",
        "status": "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED",
        "candidate_id": candidate,
        "geometry": {
            "row_count": 42,
            "unique_island_count": 42,
            "sha256": geometry_sha,
        },
        "habitat": {
            "row_count": 42,
            "eligible_columns": ["Basal.area"],
            "sha256": habitat_sha,
        },
        "protected_response_values_opened": False,
        "unclassified_values_returned": False,
        "counts_as_empirical_evidence": False,
        "v0_11_intake_authorized": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
    }
    pilot = [f"I{i:02d}" for i in range(12)]
    confirmatory = [f"I{i:02d}" for i in range(12, 42)]
    spatial = {
        "schema": "structural.boreal_lake_islands_spatial_partition_result.v0_75",
        "status": "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": candidate,
        "source_geometry_sha256": geometry_sha,
        "spatial_block_count": 9,
        "pilot_block_count": 3,
        "confirmatory_block_count": 6,
        "pilot_islands": pilot,
        "confirmatory_islands": confirmatory,
        "species_occurrence_used": False,
        "richness_used": False,
        "habitat_values_used": False,
        "counts_as_empirical_evidence": False,
        "v0_11_intake_authorized": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
    }
    habitat = {
        "schema": "structural.boreal_lake_islands_habitat_reference_result.v0_76",
        "status": "HABITAT_REFERENCE_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": candidate,
        "source_habitat_sha256": habitat_sha,
        "eligible_columns": ["Basal.area"],
        "reference_sha256": reference_sha,
        "species_occurrence_used": False,
        "richness_used": False,
        "protected_response_values_opened": False,
        "counts_as_empirical_evidence": False,
        "v0_11_intake_authorized": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
    }
    return projection, spatial, habitat


def build_with(receipt_hashes=None):
    module = load_script()
    projection, spatial, habitat = receipts()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    preintake = json.loads(PREINTAKE.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    if receipt_hashes is None:
        receipt_hashes = {
            "safe_projection_v0_74": "d" * 64,
            "spatial_partition_v0_75": "e" * 64,
            "habitat_reference_v0_76": "f" * 64,
        }
    intake = module.build_intake(
        projection,
        spatial,
        habitat,
        contract=contract,
        preintake=preintake,
        metadata=metadata,
        receipt_sha256=receipt_hashes,
    )
    return module, intake, projection, spatial, habitat


def test_generated_boreal_intake_passes_v012_validator_exactly():
    module, intake, projection, spatial, habitat = build_with()
    code, receipt = validate_intake_v0_12(intake)

    assert code == 0
    assert receipt["status"] == (
        "eligible_to_construct_v0_31_and_v0_42_pre_pilot_contracts"
    )
    assert receipt["system_id"] == "lac_la_ronge_boreal_island_beetles_2026"
    assert receipt["v0_31_protocol_construction_authorized"] is True
    assert receipt["v0_42_quality_contract_construction_authorized"] is True
    assert receipt["pilot_response_authorized"] is False
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["mechanism_response_authorized"] is False
    assert receipt["predictive_denominator_contribution"] == 0

    assert intake["endpoint_design"]["mode"] == "static_cross_sectional_occurrence"
    assert intake["requested_mechanism_lanes"] == []
    assert intake["mechanism_claim_requested"] is False


def test_generated_source_files_keep_original_beetle_response_sealed():
    _, intake, *_ = build_with()
    files = {row["file_id"]: row for row in intake["source_files"]}

    assert set(files) == {
        "safe_geometry.csv",
        "habitat_reference.csv",
        "beetles_speciesmatrix_presenceabsence.csv",
    }
    assert files["safe_geometry.csv"] == {
        "file_id": "safe_geometry.csv",
        "sha256": "a" * 64,
        "role": "geometry",
        "opened": True,
    }
    assert files["habitat_reference.csv"] == {
        "file_id": "habitat_reference.csv",
        "sha256": "c" * 64,
        "role": "safe_metadata",
        "opened": True,
    }
    response = files["beetles_speciesmatrix_presenceabsence.csv"]
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    assert response["sha256"] == metadata["focal_files"][
        "beetles_speciesmatrix_presenceabsence.csv"
    ]["sha256"]
    assert response["role"] == "response"
    assert response["opened"] is False
    assert intake["response_firewall_state"] == "response_sealed"
    assert intake["response_values_accessed"] is False


def test_source_fingerprint_depends_only_on_frozen_source_identity():
    module, intake, *_ = build_with()
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))
    preintake = json.loads(PREINTAKE.read_text(encoding="utf-8"))
    response = metadata["focal_files"]["beetles_speciesmatrix_presenceabsence.csv"]
    expected = module.canonical_sha256({
        "dryad_identifier": metadata["dryad_identifier"],
        "dryad_version_id": metadata["selected_version_id"],
        "dryad_version_number": metadata["selected_version_number"],
        "source_article_doi": preintake["source_identity"]["source_article_doi"],
        "primary_response_file_id": response["file_id"],
        "primary_response_file_sha256": response["sha256"],
    })
    assert intake["source_fingerprint"] == expected

    _, altered_receipt_intake, *_ = build_with({
        "safe_projection_v0_74": "1" * 64,
        "spatial_partition_v0_75": "2" * 64,
        "habitat_reference_v0_76": "3" * 64,
    })
    assert altered_receipt_intake["source_fingerprint"] == expected


def test_preintake_receipt_hashes_are_bound_exactly():
    _, intake, *_ = build_with()
    hashes = intake["response_blind_data_support"]["preintake_receipt_sha256"]
    assert hashes == {
        "safe_projection_v0_74": "d" * 64,
        "spatial_partition_v0_75": "e" * 64,
        "habitat_reference_v0_76": "f" * 64,
    }


def test_spatial_shortfall_stops_before_intake():
    module = load_script()
    projection, spatial, habitat = receipts()
    spatial["confirmatory_block_count"] = 5
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    preintake = json.loads(PREINTAKE.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))

    with pytest.raises(
        module.BorealIntakeBuilderError,
        match="fewer than six confirmatory blocks",
    ):
        module.build_intake(
            projection,
            spatial,
            habitat,
            contract=contract,
            preintake=preintake,
            metadata=metadata,
            receipt_sha256={
                "safe_projection_v0_74": "d" * 64,
                "spatial_partition_v0_75": "e" * 64,
                "habitat_reference_v0_76": "f" * 64,
            },
        )


def test_any_projection_response_or_unclassified_boundary_drift_stops():
    module = load_script()
    projection, spatial, habitat = receipts()
    projection["unclassified_values_returned"] = True
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    preintake = json.loads(PREINTAKE.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))

    with pytest.raises(
        module.BorealIntakeBuilderError,
        match="unclassified-value boundary",
    ):
        module.build_intake(
            projection,
            spatial,
            habitat,
            contract=contract,
            preintake=preintake,
            metadata=metadata,
            receipt_sha256={
                "safe_projection_v0_74": "d" * 64,
                "spatial_partition_v0_75": "e" * 64,
                "habitat_reference_v0_76": "f" * 64,
            },
        )


def test_habitat_column_drift_between_v074_and_v076_stops():
    module = load_script()
    projection, spatial, habitat = receipts()
    habitat["eligible_columns"] = ["other"]
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    preintake = json.loads(PREINTAKE.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA.read_text(encoding="utf-8"))

    with pytest.raises(
        module.BorealIntakeBuilderError,
        match="eligible habitat columns drift",
    ):
        module.build_intake(
            projection,
            spatial,
            habitat,
            contract=contract,
            preintake=preintake,
            metadata=metadata,
            receipt_sha256={
                "safe_projection_v0_74": "d" * 64,
                "spatial_partition_v0_75": "e" * 64,
                "habitat_reference_v0_76": "f" * 64,
            },
        )


def test_v079_contract_and_status_keep_static_nonmechanistic_boundary():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))

    assert contract["endpoint_design"]["mode"] == "static_cross_sectional_occurrence"
    assert contract["endpoint_design"]["temporal_transition_required"] is False
    assert contract["mechanism_claim_requested"] is False
    assert contract["requested_mechanism_lanes"] == []
    assert contract["successful_output_ceiling"]["pilot_response_authorized"] is False
    assert contract["successful_output_ceiling"]["confirmatory_response_authorized"] is False

    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["v0_12_intake_built"] is False
    assert boreal["biological_response_values_opened"] is False
    assert boreal["pilot_response_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
