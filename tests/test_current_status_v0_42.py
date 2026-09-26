from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "development/current_status_v0_42.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v042_status_keeps_queue_empty_and_base_freeze_historical():
    status = load(STATUS)

    registry_cfg = status["authoritative_empirical_registry"]
    registry = load(ROOT / registry_cfg["path"])
    assert registry["status"] == registry_cfg["expected_status"]
    assert registry["active_empirical_candidates"] == []
    assert status["active_empirical_candidates"] == []

    queue_cfg = status["live_confirmatory_queue"]
    queue = load(ROOT / queue_cfg["path"])
    assert queue["entry_count"] == queue_cfg["expected_entry_count"] == 0
    assert queue["entries"] == []
    assert queue["confirmatory_response_authorized"] is False

    base = status["base_admission_infrastructure"]
    frozen = load(ROOT / base["path"])
    assert frozen["status"] == base["expected_status"]
    assert base["frozen_through"] == "v0.40"
    assert base["historical_chain_modified"] is False


def test_v042_is_future_only_and_does_not_rescue_landfrag():
    status = load(STATUS)
    ext = status["future_only_admission_extension"]
    landfrag = status["closed_fragmentation_stress_test"]

    assert ext["status"] == "future_only_additive_admission_gate"
    assert ext["applies_to_historical_systems"] is False
    assert ext["changes_v0_31_v0_40_historical_results"] is False
    assert ext["confirmatory_response_authorized"] is False

    assert landfrag["response_qualified_independent_geographies"] == 29
    assert landfrag["frozen_minimum_geographies"] == 30
    assert landfrag["H1_scored"] is False
    assert landfrag["H1_estimate"] is None
    assert landfrag["H1_ci"] is None
    assert landfrag["used_to_revise_its_own_threshold"] is False
    assert landfrag["rerun_authorized"] is False


def test_failure_modes_are_explicitly_separated():
    status = load(STATUS)
    modes = status["failure_mode_separation"]

    assert "held-out blocks" in modes["response_quality_attrition"]
    assert "training positive/negative" in modes["endpoint_class_collapse"]
    assert modes["one_may_rescue_the_other"] is False

    sequence = status["future_admission_sequence"]
    assert sequence.index("v0.42 response-quality attrition contract freeze") < sequence.index(
        "v0.32 pilot-only execution"
    )
    assert sequence.index("v0.42 response-quality survival audit") > sequence.index(
        "v0.32 pilot-only execution"
    )


def test_ttf_boundary_is_unchanged():
    ttf = load(STATUS)["ttf_boundary"]

    assert ttf["status"] == "later_independent_transferability_layer"
    assert ttf["may_select_structural_candidates"] is False
    assert ttf["may_rescue_failed_structural_systems"] is False
    assert ttf["may_count_burned_pilot_as_transfer_evidence"] is False
    assert ttf["empirical_denominator_shared_with_structural"] is False


def test_current_status_points_to_v011_intake_and_v042_priority():
    status = load(STATUS)

    intake_cfg = status["independent_system_intake"]
    intake = load(ROOT / intake_cfg["path"])
    assert intake["status"] == intake_cfg["status"] == "future_only_bridge_to_v0_42"
    assert intake_cfg["successful_action"] == (
        "construct_v0_31_protocol_then_bind_v0_42_quality_contract_only"
    )
    assert intake_cfg["pilot_response_authorized"] is False
    assert intake_cfg["confirmatory_response_authorized"] is False

    priority_cfg = status["active_priority"]
    priority = load(ROOT / priority_cfg["path"])
    assert priority["status"] == priority_cfg["status"] == "active_mainline_lock"
    assert priority["canonical_current_status"] == (
        "development/current_status_v0_42.json"
    )
    assert priority["live_confirmatory_queue"] == (
        "development/confirmatory_admission_queue_v0_42.json"
    )
    assert priority["independent_system_intake"] == (
        "development/independent_system_intake_contract_v0_11.json"
    )
