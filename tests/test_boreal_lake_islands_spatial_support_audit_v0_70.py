from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "development/boreal_lake_islands_spatial_support_audit_v0_70.json"
STATUS = ROOT / "development/current_status_v0_70.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_70.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_lake_only_route_is_rejected_by_frozen_spatial_support():
    x = load(AUDIT)
    c = x["audited_constraints"]

    assert x["status"] == "lake_only_coordinate_free_route_rejected_before_response_access"
    assert c["study_lakes"] == 6
    assert c["system_specific_minimum_pilot_spatial_blocks"] == 3
    assert c["system_specific_minimum_confirmatory_spatial_blocks"] == 6
    assert c["minimum_disjoint_spatial_blocks_needed"] == 9
    assert c["lake_level_spatial_blocks_available"] == 6
    assert c["lake_level_block_shortfall"] == 3
    assert x["deduction"]["lake_membership_alone_can_replace_exact_coordinates"] is False


def test_stricter_system_specific_contract_remains_binding():
    x = load(AUDIT)
    p = x["contract_precedence"]

    assert "does not weaken" in p["generic_v0_31"]
    assert "3 pilot spatial blocks and 6 confirmatory spatial blocks" in p["system_specific_v0_65"]
    assert "spatial transfer" in p["v0_55"]
    assert "stricter" in p["decision"]


def test_no_gate_lowering_or_response_defined_fallback():
    x = load(AUDIT)
    forbidden = "\n".join(x["required_spatial_resolution_before_v0_11"]["forbidden_alternatives"])

    assert "lower the 3-pilot or 6-confirmatory block requirements" in forbidden
    assert "biological response values" in forbidden
    assert "digitize approximate coordinates by eye" in forbidden


def test_habitat_blocker_remains_in_force():
    x = load(AUDIT)
    h = x["other_preintake_blocker"]

    assert h["safe_local_habitat_reference"] == "still unresolved"
    assert "STOP before biological response" in h["rule"]


def test_response_firewall_and_fresh_denominator_remain_zero():
    x = load(AUDIT)
    fw = x["response_firewall"]
    d = x["fresh_denominator"]

    assert fw["beetle_matrix_opened"] is False
    assert fw["bird_matrix_opened"] is False
    assert fw["plant_matrix_opened"] is False
    assert fw["pilot_response_authorized"] is False
    assert fw["confirmatory_response_authorized"] is False
    assert fw["counts_as_empirical_evidence"] is False
    assert d == {
        "active_fresh_systems": 0,
        "confirmatory_eligible_systems": 0,
        "live_confirmatory_queue_entries": 0,
    }


def test_v070_status_and_priority_match_audit():
    s = load(STATUS)
    p = load(PRIORITY)

    assert s["fresh_empirical_state"]["active_candidates"] == []
    assert s["fresh_empirical_state"]["confirmatory_eligible_count"] == 0
    b = s["boreal_lake_island_preintake"]
    assert b["known_lake_count"] == 6
    assert b["lake_only_route_sufficient"] is False
    assert b["minimum_disjoint_spatial_units_required_by_system_contract"] == 9
    assert b["v0_11_intake_authorized"] is False
    assert b["biological_response_opened"] is False

    assert p["fresh_active_empirical_candidate"] is None
    assert p["fresh_confirmatory_eligible_count"] == 0
    assert "exact sampling-plot coordinates" in p["active_goal"]
