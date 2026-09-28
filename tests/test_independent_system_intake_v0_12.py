from __future__ import annotations

import importlib.util
import json
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V012 = ROOT / "scripts/validate_independent_system_intake_v0_12.py"
V011 = ROOT / "scripts/validate_independent_system_intake_v0_11.py"
FIXTURE = ROOT / "tests/fixtures/independent_system_intake_v0_12/valid_static_dual_isolation.json"
CONTRACT = ROOT / "development/independent_system_intake_contract_v0_12.json"
STATUS = ROOT / "development/current_status_v0_77.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_77.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_v012_accepts_static_v055_without_temporal_mechanism_lanes():
    module = load_module(V012, "intake_v012")
    x = fixture()

    code, receipt = module.validate_intake_v0_12(x)

    assert code == 0
    assert receipt["status"] == (
        "eligible_to_construct_v0_31_and_v0_42_pre_pilot_contracts"
    )
    assert receipt["analysis_bindings"]["ecological_hypothesis"] == (
        "development/prospective_dual_isolation_source_pool_hypothesis_v0_55.json"
    )
    assert receipt["endpoint_design"]["mode"] == "static_cross_sectional_occurrence"
    assert receipt["response_blind_data_support"][
        "temporal_transition_metadata_available"
    ] is False
    assert receipt["response_blind_data_support"][
        "genetic_sampling_metadata_available"
    ] is False
    assert receipt["requested_mechanism_lanes"] == []
    assert receipt["mechanism_claim_requested"] is False
    assert receipt["v0_31_protocol_construction_authorized"] is True
    assert receipt["v0_42_quality_contract_construction_authorized"] is True
    assert receipt["pilot_response_authorized"] is False
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["mechanism_response_authorized"] is False
    assert receipt["mechanism_claim_authorized"] is False
    assert receipt["predictive_denominator_contribution"] == 0


def test_legacy_v011_cannot_truthfully_accept_v055_binding():
    legacy = load_module(V011, "intake_v011")
    x = fixture()

    # Re-express the same future system in the legacy v0.10/v0.11 schema.
    legacy_intake = {
        "schema": "structural.independent_system_intake.v0_10",
        "status": "response_sealed_intake_draft",
        "system_id": x["system_id"],
        "source_id": x["source_id"],
        "source_version": x["source_version"],
        "source_fingerprint": x["source_fingerprint"],
        "origin": x["origin"],
        "is_prior_closed_system": False,
        "response_firewall_state": "response_sealed",
        "response_values_accessed": False,
        "source_files": deepcopy(x["source_files"]),
        "freshness_metadata": deepcopy(x["freshness_metadata"]),
        "selection_firewall": deepcopy(x["selection_firewall"]),
        "requested_mechanism_lanes": ["M4_environmental_proxy"],
        "response_blind_data_support": {
            "temporal_transition_metadata_available": False,
            "genetic_sampling_metadata_available": False,
            "environment_predictor_metadata_available": True,
        },
        "hypothesis_bindings": {
            "structural_partition_contract":
                "development/transition_pilot_protocol_contract_v0_31.json",
            "ecological_hypothesis":
                "development/prospective_dual_isolation_source_pool_hypothesis_v0_55.json",
            "mechanism_framework":
                "development/prospective_mechanism_discrimination_v0_1.json",
        },
    }

    code, receipt = legacy.validate_intake_v0_11(legacy_intake)

    assert code != 0
    assert receipt["status"] == "invalid_intake_schema"
    assert "hypothesis binding drift" in receipt["reason"]
    assert receipt["v0_31_protocol_construction_authorized"] is False
    assert receipt["v0_42_quality_contract_construction_authorized"] is False


def test_v012_rejects_superseded_v03_hypothesis_binding():
    module = load_module(V012, "intake_v012_v03")
    x = fixture()
    x["analysis_bindings"]["ecological_hypothesis"] = (
        "development/prospective_extreme_isolation_topology_hypothesis_v0_3.json"
    )

    code, receipt = module.validate_intake_v0_12(x)

    assert code == 1
    assert receipt["status"] == "invalid_intake_schema"
    assert "dual-isolation analysis binding drift" in receipt["reason"]
    assert receipt["pilot_response_authorized"] is False


def test_v012_rejects_temporal_mechanism_lane_smuggling():
    module = load_module(V012, "intake_v012_lanes")
    x = fixture()
    x["requested_mechanism_lanes"] = ["M1_contemporary_colonization"]

    code, receipt = module.validate_intake_v0_12(x)

    assert code == 1
    assert receipt["status"] == "invalid_intake_schema"
    assert "must be an empty list" in receipt["reason"]
    assert receipt["mechanism_claim_authorized"] is False


def test_v012_rejects_missing_preintake_support():
    module = load_module(V012, "intake_v012_support")
    x = fixture()
    x["response_blind_data_support"]["spatial_partition_frozen"] = False

    code, receipt = module.validate_intake_v0_12(x)

    assert code == 1
    assert receipt["status"] == "invalid_intake_schema"
    assert "spatial_partition_frozen" in receipt["reason"]
    assert receipt["v0_31_protocol_construction_authorized"] is False


def test_v012_rejects_opened_response_file():
    module = load_module(V012, "intake_v012_response")
    x = fixture()
    x["source_files"][-1]["opened"] = True

    code, receipt = module.validate_intake_v0_12(x)

    assert code == 1
    assert receipt["status"] == "invalid_intake_schema"
    assert "response/unknown file was opened" in receipt["reason"]
    assert receipt["pilot_response_authorized"] is False


def test_v012_requires_exact_preintake_receipt_hash_keys():
    module = load_module(V012, "intake_v012_hashes")
    x = fixture()
    x["response_blind_data_support"]["preintake_receipt_sha256"][
        "extra"
    ] = "2" * 64

    code, receipt = module.validate_intake_v0_12(x)

    assert code == 1
    assert receipt["status"] == "invalid_intake_schema"
    assert "receipt SHA keys must be exact" in receipt["reason"]


def test_v012_contract_preserves_response_ceiling():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert x["historical_v0_10_modified"] is False
    assert x["historical_v0_11_modified"] is False
    assert x["required_analysis_bindings"]["ecological_hypothesis"] == (
        "development/prospective_dual_isolation_source_pool_hypothesis_v0_55.json"
    )
    assert x["mechanism_boundary"]["mechanism_claim_requested"] is False
    assert x["mechanism_boundary"]["requested_mechanism_lanes"] == []
    ceiling = x["successful_output_ceiling"]
    assert ceiling["v0_31_protocol_construction_authorized"] is True
    assert ceiling["v0_42_quality_contract_construction_authorized"] is True
    assert ceiling["pilot_response_authorized"] is False
    assert ceiling["confirmatory_response_authorized"] is False
    assert ceiling["mechanism_claim_authorized"] is False
    assert ceiling["predictive_denominator_contribution"] == 0


def test_v077_status_keeps_fresh_denominator_zero():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))

    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    assert status["future_intake"]["dual_isolation_contract"].endswith(
        "independent_system_intake_contract_v0_12.json"
    )
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["stage_A_workflow_executed"] is False
    assert boreal["v0_12_intake_authorized"] is False
    assert boreal["pilot_response_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
