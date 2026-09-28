from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_boreal_19island_prepilot_v1_02.py"
CONTRACT = ROOT / "development/boreal_19island_prepilot_builder_contract_v1_02.json"
REQUEST = ROOT / "development/boreal_19island_prepilot_request_v1_02.json"
WORKFLOW = ROOT / ".github/workflows/boreal-19island-prepilot-v1_02.yml"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal19_prepilot_v102", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_world(module):
    return module.build(
        contract=module._load(module.DEFAULT_CONTRACT),
        header_freeze=module._load(module.DEFAULT_HEADER_FREEZE),
        geometry_freeze=module._load(module.DEFAULT_GEOMETRY_FREEZE),
        spatial_freeze=module._load(module.DEFAULT_SPATIAL_FREEZE),
        state_freeze=module._load(module.DEFAULT_STATE_FREEZE),
        operator_freeze=module._load(module.DEFAULT_OPERATOR_FREEZE),
        operator_contract=module._load(module.DEFAULT_OPERATOR_CONTRACT),
        legacy_operator=module._load(module.DEFAULT_LEGACY_OPERATOR),
        metadata=module._load(module.DEFAULT_METADATA),
        preintake=module._load(module.DEFAULT_PREINTAKE),
        geometry_path=module.DEFAULT_GEOMETRY,
        state_path=module.DEFAULT_STATE,
        geometry_freeze_path=module.DEFAULT_GEOMETRY_FREEZE,
        spatial_freeze_path=module.DEFAULT_SPATIAL_FREEZE,
        state_freeze_path=module.DEFAULT_STATE_FREEZE,
        operator_freeze_path=module.DEFAULT_OPERATOR_FREEZE,
    )


def test_v102_builds_validator_clean_response_sealed_bundle():
    module = load_script()
    intake, intake_receipt, protocol, quality, receipt = build_world(module)

    assert intake["system_id"] == "lac_la_ronge_boreal_19island_beetles_2026"
    assert intake["response_firewall_state"] == "response_sealed"
    assert intake["response_values_accessed"] is False
    assert intake["analysis_population"]["count"] == 19
    assert intake["analysis_population"]["outcome_selected"] is False
    assert len(intake["analysis_population"]["island_order"]) == 19
    assert intake["response_contract"]["parent_matrix_island_rows"] == 42
    assert intake["response_contract"]["required_response_domain"] == ["0", "1"]
    assert intake["response_contract"]["domain_verified_now"] is False

    response = [
        row for row in intake["source_files"] if row["role"] == "response"
    ]
    assert len(response) == 1
    assert response[0]["opened"] is False
    assert response[0]["sha256"] == (
        "01eef34863bfd49fdc68dfae0aec58766a6fcdd1234751a9c75824df9f038be0"
    )

    assert intake_receipt["status"] == (
        "eligible_to_construct_v0_31_and_v0_42_pre_pilot_contracts"
    )
    assert intake_receipt["pilot_response_authorized"] is False
    assert protocol["pilot_partition"] == [
        "SC_7d7dc2dd44ae",
        "SC_1d9ef1dca674",
        "SC_0318f99b7680",
    ]
    assert len(protocol["confirmatory_partition"]) == 7
    assert quality["parent_protocol_fingerprint"] == receipt["protocol_fingerprint"]
    assert receipt["status"] == "V012_V031_V042_FROZEN_RESPONSE_REMAINS_SEALED"
    assert receipt["pilot_block_count"] == 3
    assert receipt["confirmatory_block_count"] == 7
    assert receipt["pilot_island_count"] == 6
    assert receipt["confirmatory_island_count"] == 13
    assert receipt["out_of_population_rows_must_remain_opaque"] == 23
    assert receipt["response_domain_frozen"] == ["0", "1"]
    assert receipt["response_domain_verified_now"] is False
    assert receipt["pilot_response_authorized"] is False
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["predictive_denominator_contribution"] == 0
    assert receipt["counts_as_empirical_evidence"] is False


def test_v102_fails_if_population_selection_is_relabelled_as_response_based():
    module = load_script()
    contract = module._load(module.DEFAULT_CONTRACT)
    contract["analysis_population"]["selection_basis"] = "beetle response direction"
    with pytest.raises(module.Boreal19PrepilotError, match="selection basis drift"):
        module.build(
            contract=contract,
            header_freeze=module._load(module.DEFAULT_HEADER_FREEZE),
            geometry_freeze=module._load(module.DEFAULT_GEOMETRY_FREEZE),
            spatial_freeze=module._load(module.DEFAULT_SPATIAL_FREEZE),
            state_freeze=module._load(module.DEFAULT_STATE_FREEZE),
            operator_freeze=module._load(module.DEFAULT_OPERATOR_FREEZE),
            operator_contract=module._load(module.DEFAULT_OPERATOR_CONTRACT),
            legacy_operator=module._load(module.DEFAULT_LEGACY_OPERATOR),
            metadata=module._load(module.DEFAULT_METADATA),
            preintake=module._load(module.DEFAULT_PREINTAKE),
            geometry_path=module.DEFAULT_GEOMETRY,
            state_path=module.DEFAULT_STATE,
            geometry_freeze_path=module.DEFAULT_GEOMETRY_FREEZE,
            spatial_freeze_path=module.DEFAULT_SPATIAL_FREEZE,
            state_freeze_path=module.DEFAULT_STATE_FREEZE,
            operator_freeze_path=module.DEFAULT_OPERATOR_FREEZE,
        )


def test_v102_request_and_workflow_never_access_response():
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    assert request["response_file_download_authorized"] is False
    assert request["response_header_access_authorized"] is False
    assert request["response_value_access_authorized"] is False
    assert request["pilot_response_authorized"] is False

    text = WORKFLOW.read_text(encoding="utf-8")
    assert "beetles_speciesmatrix_presenceabsence.csv" not in text
    assert "DRYAD_CLIENT_ID" not in text
    assert "DRYAD_TOKEN" not in text
    assert "build_boreal_19island_prepilot_v1_02.py" in text
