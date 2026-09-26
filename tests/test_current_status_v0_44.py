from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "development/current_status_v0_44.json"
REGISTRY = ROOT / "development/connectivity_candidate_registry_v0_44.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_44.json"
GEOMETRY = ROOT / "development/indo_pacific_atoll_dual_universe_result_v0_17.json"
PROTOCOL = ROOT / "development/indo_pacific_atoll_transition_pilot_protocol_v0_31b.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v044_has_one_corrected_response_sealed_system_and_empty_queue():
    status = load(STATUS)
    registry = load(REGISTRY)
    queue = load(ROOT / status["live_confirmatory_queue"]["path"])

    assert status["status"] == "canonical_current_status"
    assert registry["status"] == (
        "one_active_response_sealed_empirical_system_corrected_prepilot"
    )
    assert [x["candidate_id"] for x in registry["active_empirical_candidates"]] == [
        "indo_pacific_atoll_native_vascular_plants_2026"
    ]
    active = registry["active_empirical_candidates"][0]
    assert active["pilot_response_accessed"] is False
    assert active["confirmatory_response_accessed"] is False
    assert active["counts_as_empirical_evidence"] is False
    assert active["confirmatory_eligible"] is False

    assert queue["entry_count"] == 0
    assert queue["confirmatory_response_authorized"] is False
    assert status["confirmatory_eligible_systems"] == []
    assert status["confirmatory_eligible_count"] == 0


def test_v044_corrected_protocol_matches_frozen_geometry_partitions():
    geometry = load(GEOMETRY)
    protocol = load(PROTOCOL)

    assert protocol["pilot_partition"] == geometry["pilot_block_ids"]
    assert protocol["confirmatory_partition"] == geometry["confirmatory_block_ids"]
    assert len(protocol["pilot_partition"]) == 13
    assert len(protocol["confirmatory_partition"]) == 50
    assert geometry["selected_partition_radius_km"] == 233
    assert geometry["major_landmass_distance_quantiles_km_model292"][
        "q75_primary"
    ] == 775.3375


def test_v044_fingerprints_and_fixed_species_rule_are_canonical():
    active = load(STATUS)["active_empirical_system"]

    assert active["v0_31_protocol_fingerprint"] == (
        "ee8cccc38fb8f4602e05e97d9d875c5ad8773280460c0dafca36ac03fe5871f5"
    )
    assert active["v0_42_quality_contract_fingerprint"] == (
        "1b3ad5da960ceac60e594b3ed664a39835e2f49ba1f7d70bfd32ee1c54e28fc6"
    )
    assert active["fixed_pilot_species_rule"] == (
        "native N in at least two distinct pilot spatial blocks"
    )
    assert active["pilot_response_accessed"] is False
    assert active["confirmatory_response_accessed"] is False


def test_v044_retired_design_was_never_consumed():
    status = load(STATUS)
    retired = load(ROOT / status["retired_pre_response_design"]["path"])

    assert retired["status"] == "retired_before_any_response_access"
    assert retired["response_accessed"] is False
    assert retired["pilot_consumed"] is False
    assert retired["predictive_denominator_contribution"] == 0


def test_v044_priority_forbids_rescue_or_confirmatory_opening():
    priority = load(PRIORITY)

    assert priority["status"] == "active_corrected_atoll_burned_pilot"
    assert priority["current_confirmatory_eligible_count"] == 0
    rules = priority["priority_rules"]
    assert rules["candidate_hunting"] is False
    assert rules["change_partitions_after_pilot"] is False
    assert rules["change_species_support_rule_after_pilot"] is False
    assert rules["lower_estimability_or_quality_thresholds"] is False
    assert rules["decode_confirmatory_species_or_presence"] is False
    assert rules["use_pilot_for_effect_or_predictive_score"] is False
    assert rules["rerun_consumed_pilot"] is False
