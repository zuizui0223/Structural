from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "development/current_status_v0_47.json"
STRESS = ROOT / "development/independent_stress_test_registry_v0_47.json"
FRESH = ROOT / "development/connectivity_candidate_registry_v0_45.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v047_keeps_fresh_denominator_empty():
    status = load(STATUS)
    fresh = load(FRESH)
    queue = load(ROOT / status["live_confirmatory_queue"]["path"])

    assert fresh["active_empirical_candidates"] == []
    assert status["fresh_confirmatory_eligible_systems"] == []
    assert status["fresh_confirmatory_eligible_count"] == 0
    assert queue["entry_count"] == 0
    assert queue["confirmatory_response_authorized"] is False


def test_pristine_5592_mammal_lane_remains_separate_hold():
    x = load(STATUS)["pristine_preintake_hold"]

    assert x["candidate_id"] == "global_island_native_mammals_barreto_2024"
    assert x["raw_presence_absence_response_opened"] is False
    assert x["counts_as_active_empirical_candidate"] is False
    assert x["counts_as_confirmatory_evidence"] is False
    assert x["status"].startswith("HOLD_")


def test_318_mammal_lane_is_stress_only():
    status = load(STATUS)["independent_stress_test"]
    registry = load(STRESS)
    lane = registry["stress_tests"][0]

    assert registry["fresh_confirmatory_denominator_count"] == 0
    assert status["candidate_id"] == lane["candidate_id"]
    assert lane["evidence_class"] == (
        "design_frozen_response_summary_exposed_independent_stress_test"
    )
    assert status["design_was_frozen_before_summary_exposure"] is True
    assert status["raw_species_occurrence_matrix_opened"] is False
    assert lane["counts_as_fresh_confirmation"] is False
    assert status["counts_as_fresh_confirmation"] is False
    assert status["counts_as_primary_confirmatory_evidence"] is False


def test_318_stress_frozen_numbers_are_exact():
    x = load(STATUS)["independent_stress_test"]

    assert x["pilot_islands"] == 65
    assert x["heldout_islands"] == 244
    assert x["q75_dContinent_km"] == 1124.41
    assert x["pilot_protocol_fingerprint"] == (
        "98dd81e471f165303503f88fc02ce6b22c624ea9c2b9a72a635869d047fdba9f"
    )
    assert x["quality_contract_fingerprint"] == (
        "9b6b61c927ae6e5246821781bb842edcf98dd8dd57d5b63246ba5aeb98f57c2a"
    )


def test_atoll_terminal_boundary_is_unchanged():
    x = load(STATUS)["terminal_atoll_system"]

    assert x["failure_class"] == "endpoint_value_domain_mismatch"
    assert x["pilot_response_accessed"] is True
    assert x["confirmatory_response_accessed"] is False
    assert x["source_pool_handoff_scored"] is False
    assert x["rerun_authorized"] is False
