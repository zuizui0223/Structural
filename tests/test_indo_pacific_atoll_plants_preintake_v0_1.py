from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRE = ROOT / "development/indo_pacific_atoll_plants_preintake_v0_1.json"
STATUS = ROOT / "development/current_status_v0_42.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_atoll_plants_remain_preintake_and_response_sealed():
    x = load(PRE)

    assert x["status"].startswith("HOLD_")
    assert x["source_identity"]["response_package_downloaded_by_structural"] is False
    assert x["source_identity"]["vascular_plant_response_values_opened_by_structural"] is False
    assert x["v0_11_intake_authorized"] is False
    assert x["pilot_response_authorized"] is False
    assert x["confirmatory_response_authorized"] is False
    assert x["counts_as_empirical_evidence"] is False


def test_focal_response_is_native_complete_atoll_inventory():
    x = load(PRE)
    focal = x["focal_response"]
    meta = x["metadata_only_basis"]

    assert focal["guild"] == "vascular_plants"
    assert focal["taxon_scope"] == "native_only"
    assert focal["unit"] == "atoll"
    assert focal["introduced_species_excluded_before_response_access"] is True
    assert meta["plant_inventory_rule"].startswith("only complete")
    assert meta["individual_islets_not_used_as_response_units"] is True


def test_source_pool_handoff_primary_remains_q75_and_no_rescue():
    x = load(PRE)

    iso = x["response_independent_isolation"]
    assert iso["primary_extreme_rule"].startswith("upper 25%")
    assert iso["robustness_quantiles"] == [0.70, 0.80]
    assert iso["robustness_may_not_rescue_primary"] is True
    assert x["strong_reference_template"]["primary_predictive_contrast"] == (
        "C_minus_R3 heldout log loss"
    )
    assert x["strong_reference_template"]["favourable_direction"] == "negative"


def test_graph_and_split_are_response_independent():
    x = load(PRE)

    graph = x["response_independent_graph_rule"]
    split = x["spatial_validation_template"]

    assert "before response access" in graph["radii_rule"]
    assert graph["source_conditioned_connectivity"].startswith(
        "fraction of the same frozen radii"
    )
    assert split["species_and_atoll_response_values_forbidden_during_partition_construction"] is True
    assert split["if_minimum_not_met"] == "STOP_before_response"


def test_current_status_registers_hold_without_promoting_candidate():
    status = load(STATUS)
    pre = status["hypothesis_driven_preintake_candidate"]

    assert status["active_empirical_candidates"] == []
    assert status["live_confirmatory_queue"]["expected_entry_count"] == 0
    assert pre["candidate_id"] == "indo_pacific_atoll_native_vascular_plants_2026"
    assert pre["status"].startswith("HOLD_")
    assert pre["response_values_opened"] is False
    assert pre["counts_as_active_empirical_candidate"] is False
    assert pre["counts_as_confirmatory_evidence"] is False
