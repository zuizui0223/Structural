from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "development/current_status_v0_43.json"
REGISTRY = ROOT / "development/connectivity_candidate_registry_v0_43.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v043_has_one_active_response_sealed_system_and_empty_queue():
    status = load(STATUS)
    registry = load(REGISTRY)
    queue = load(ROOT / status["live_confirmatory_queue"]["path"])

    assert registry["status"] == (
        "one_active_response_sealed_empirical_system_pre_pilot"
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


def test_v043_atoll_spatial_design_matches_frozen_geometry():
    status = load(STATUS)
    active = status["active_empirical_system"]

    assert active["graph_universe_atolls"] == 310
    assert active["model_target_atolls"] == 292
    assert active["response_blind_excluded_target_atolls"] == 18
    assert active["frozen_graph_radii_km"] == [36, 58, 126, 233]
    assert active["selected_spatial_partition_radius_km"] == 233
    assert active["burned_pilot_blocks"] == 13
    assert active["confirmatory_blocks"] == 50
    assert active["q75_major_landmass_isolation_km"] == 775.3375


def test_v043_protocol_fingerprints_are_frozen_before_pilot():
    active = load(STATUS)["active_empirical_system"]

    assert active["v0_31_protocol_fingerprint"] == (
        "c50a1b4689e41f6a40e65691ef9336eaf0a1eb3a5cdeafd1204b6a005c362653"
    )
    assert active["v0_42_quality_contract_fingerprint"] == (
        "3b8699947b8d192d5a8f5c5b5cde976a7b77547c2ee3e2d927e68846af33fcdb"
    )
    assert active["pilot_response_accessed"] is False
    assert active["confirmatory_response_accessed"] is False
    assert active["counts_as_confirmatory_evidence"] is False


def test_v043_preserves_closed_system_boundaries():
    status = load(STATUS)
    registry = load(REGISTRY)

    assert status["closed_dynamic_systems"] == [
        "PNW_terminal_non_estimable_endpoint_class_collapse",
        "RMNP_terminal_non_estimable_endpoint_class_collapse",
    ]
    assert status["closed_fragmentation_stress_test"]["H1_scored"] is False
    assert status["closed_fragmentation_stress_test"]["rerun_authorized"] is False

    invariants = registry["invariants"]
    assert any("A-Islands does not count as confirmation" in x for x in invariants)
    assert any("burned pilot contributes zero predictive evidence" in x for x in invariants)
