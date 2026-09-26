from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "development/current_status_v0_45.json"
REGISTRY = ROOT / "development/connectivity_candidate_registry_v0_45.json"
TERMINAL = ROOT / "development/indo_pacific_atoll_terminal_burned_pilot_v0_22.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_45.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v045_has_no_active_or_confirmatory_eligible_system():
    status = load(STATUS)
    registry = load(REGISTRY)
    queue = load(ROOT / status["live_confirmatory_queue"]["path"])

    assert registry["status"] == (
        "no_active_empirical_candidate_after_atoll_terminal_endpoint_domain_stop"
    )
    assert registry["active_empirical_candidates"] == []
    assert status["confirmatory_eligible_systems"] == []
    assert status["confirmatory_eligible_count"] == 0
    assert queue["entry_count"] == 0
    assert queue["confirmatory_response_authorized"] is False


def test_atoll_terminal_stop_is_after_pilot_access_but_before_scoring():
    x = load(TERMINAL)

    assert x["status"] == (
        "terminal_endpoint_value_domain_mismatch_after_pilot_response_access"
    )
    assert x["observed_terminal_event"]["pilot_response_accessed"] is True
    assert x["observed_terminal_event"]["observed_code_outside_frozen_domain"] == "U"
    assert x["observed_terminal_event"]["frozen_allowed_presence_codes"] == ["N", "I"]
    assert x["firewall_outcome"]["confirmatory_response_accessed"] is False
    assert x["firewall_outcome"]["confirmatory_species_values_parsed"] == 0
    assert x["firewall_outcome"]["confirmatory_presence_values_parsed"] == 0
    assert x["firewall_outcome"]["effect_size"] is None
    assert x["firewall_outcome"]["prediction_score"] is None
    assert x["firewall_outcome"]["predictive_denominator_contribution"] == 0


def test_atoll_did_not_complete_estimability_or_quality_gates():
    x = load(TERMINAL)
    incomplete = x["incomplete_outputs"]

    assert incomplete["fixed_pilot_species_universe_completed"] is False
    assert incomplete["exact_three_column_pilot_surface_completed"] is False
    assert incomplete["v0_32_estimability_completed"] is False
    assert incomplete["v0_42_response_quality_completed"] is False
    assert incomplete["confirmatory_admission_evaluated"] is False
    assert x["scientific_interpretation"]["source_pool_handoff_direction_scored"] is False
    assert x["scientific_interpretation"]["favourable_or_adverse_ecological_evidence"] == "none"


def test_consumed_atoll_protocol_cannot_be_rescued_or_rerun():
    x = load(TERMINAL)
    priority = load(PRIORITY)

    assert x["rerun_authorized"] is False
    assert x["replacement_protocol_on_same_response_authorized"] is False
    assert x["confirmatory_response_authorized"] is False
    assert priority["active_empirical_system"] is None
    assert any("rerun" in rule.lower() for rule in x["terminal_rules"])
    assert any("reinterpret" in rule.lower() for rule in x["terminal_rules"])


def test_current_status_classifies_failure_as_domain_mismatch_not_ecological_result():
    status = load(STATUS)
    terminal = status["terminal_atoll_system"]

    assert terminal["failure_class"] == "endpoint_value_domain_mismatch"
    assert terminal["observed_unfrozen_code"] == "U"
    assert terminal["v0_32_completed"] is False
    assert terminal["v0_42_completed"] is False
    assert terminal["source_pool_handoff_scored"] is False
    assert terminal["rerun_authorized"] is False
