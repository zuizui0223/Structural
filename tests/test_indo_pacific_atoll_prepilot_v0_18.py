from __future__ import annotations

import json
from pathlib import Path

from structural.response_quality_attrition import (
    contract_fingerprint,
    contract_from_mapping,
)
from structural.transition_pilot_protocol import (
    protocol_fingerprint,
    protocol_from_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
OLD_PROTOCOL = ROOT / "development/indo_pacific_atoll_transition_pilot_protocol_v0_31.json"
OLD_QUALITY = ROOT / "development/indo_pacific_atoll_response_quality_contract_v0_42.json"
OLD_ROUTER = ROOT / "development/indo_pacific_atoll_pilot_router_contract_v0_18.json"
GEOMETRY = ROOT / "development/indo_pacific_atoll_dual_universe_result_v0_17.json"
RETIRED = ROOT / "development/indo_pacific_atoll_retired_prepilot_protocol_v0_19.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v018_historical_protocol_identity_is_preserved():
    protocol = protocol_from_mapping(load(OLD_PROTOCOL))
    quality = contract_from_mapping(load(OLD_QUALITY))

    assert protocol_fingerprint(protocol) == (
        "c50a1b4689e41f6a40e65691ef9336eaf0a1eb3a5cdeafd1204b6a005c362653"
    )
    assert contract_fingerprint(quality) == (
        "3b8699947b8d192d5a8f5c5b5cde976a7b77547c2ee3e2d927e68846af33fcdb"
    )


def test_v018_geometry_freeze_remains_exact_and_response_blind():
    x = load(GEOMETRY)

    assert x["graph_universe_atolls"] == 310
    assert x["model_target_universe_atolls"] == 292
    assert x["frozen_graph_radii_km"] == [36, 58, 126, 233]
    assert x["selected_partition_radius_km"] == 233
    assert x["selected_block_count"] == 63
    assert x["pilot_block_count"] == 13
    assert x["confirmatory_block_count"] == 50
    assert x["major_landmass_distance_quantiles_km_model292"]["q75_primary"] == 775.3375
    assert x["model_target_design_sha256"] == (
        "237c0d5e97ab45f3d71dbed5bc799a24012da62942b296652ea0e1977f79f32b"
    )
    assert x["response_files_opened"] == 0
    assert x["response_value_parse_count"] == 0
    assert x["model_fit_count"] == 0


def test_v018_router_contract_never_authorized_response():
    router = load(OLD_ROUTER)

    assert router["pilot_response_authorized"] is False
    assert router["confirmatory_response_authorized"] is False
    assert router["confirmatory_firewall"]["confirmatory_species_values_parsed"] == 0
    assert router["confirmatory_firewall"]["confirmatory_presence_values_parsed"] == 0
    assert router["evidence_ceiling"]["effect_size"] is None
    assert router["evidence_ceiling"]["prediction_score"] is None
    assert router["evidence_ceiling"]["predictive_denominator_contribution"] == 0


def test_v018_is_retired_pre_response_not_consumed():
    retired = load(RETIRED)

    assert retired["status"] == "retired_before_any_response_access"
    assert retired["retired_protocol_fingerprint"] == (
        "c50a1b4689e41f6a40e65691ef9336eaf0a1eb3a5cdeafd1204b6a005c362653"
    )
    assert retired["response_accessed"] is False
    assert retired["pilot_consumed"] is False
    assert retired["predictive_denominator_contribution"] == 0
