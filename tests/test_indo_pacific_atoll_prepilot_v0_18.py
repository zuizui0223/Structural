from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from structural.atoll_pilot_router import (
    AtollPilotRouterError,
    build_atoll_burned_pilot_surface,
)
from structural.response_quality_attrition import (
    contract_fingerprint,
    contract_from_mapping,
    evaluate_response_quality_contract,
    ResponseQualityContractStatus,
)
from structural.transition_pilot_protocol import (
    PilotProtocolStatus,
    evaluate_transition_pilot_protocol,
    protocol_fingerprint,
    protocol_from_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "development/indo_pacific_atoll_transition_pilot_protocol_v0_31.json"
QUALITY = ROOT / "development/indo_pacific_atoll_response_quality_contract_v0_42.json"
GEOMETRY = ROOT / "development/indo_pacific_atoll_dual_universe_result_v0_17.json"
ROUTER = ROOT / "development/indo_pacific_atoll_pilot_router_contract_v0_18.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_atoll_v031_and_v042_are_bound_before_response():
    protocol = protocol_from_mapping(load(PROTOCOL))
    quality = contract_from_mapping(load(QUALITY))

    p = evaluate_transition_pilot_protocol(protocol)
    q = evaluate_response_quality_contract(protocol=protocol, contract=quality)

    assert p.status is PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT
    assert p.protocol_fingerprint == (
        "c50a1b4689e41f6a40e65691ef9336eaf0a1eb3a5cdeafd1204b6a005c362653"
    )
    assert protocol_fingerprint(protocol) == p.protocol_fingerprint
    assert q.status is ResponseQualityContractStatus.QUALIFIED_TO_OPEN_PILOT
    assert contract_fingerprint(quality) == (
        "3b8699947b8d192d5a8f5c5b5cde976a7b77547c2ee3e2d927e68846af33fcdb"
    )

    geometry = load(GEOMETRY)
    assert list(protocol.pilot_partition) == geometry["pilot_block_ids"]
    assert list(protocol.confirmatory_partition) == geometry["confirmatory_block_ids"]
    assert len(protocol.pilot_partition) == 13
    assert len(protocol.confirmatory_partition) == 50
    assert set(protocol.pilot_partition).isdisjoint(protocol.confirmatory_partition)
    assert protocol.minimum_test_rows == 3
    assert protocol.minimum_train_positive == 5
    assert protocol.minimum_train_negative == 5
    assert protocol.minimum_estimable_blocks == 3
    assert quality.minimum_response_qualified_blocks == 3


def test_atoll_geometry_freeze_is_response_blind_and_exact():
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
    assert x["counts_as_empirical_evidence"] is False


def test_router_contract_keeps_confirmatory_semantics_closed():
    x = load(ROUTER)

    assert x["pilot_response_authorized"] is False
    assert x["confirmatory_response_authorized"] is False
    assert x["confirmatory_firewall"]["confirmatory_species_values_parsed"] == 0
    assert x["confirmatory_firewall"]["confirmatory_presence_values_parsed"] == 0
    assert x["pilot_surface_rule"]["raw_columns"] == [
        "partition_unit", "block", "target"
    ]
    assert x["pilot_surface_rule"]["species_identifiers_may_appear_in_raw_surface"] is False


def test_confirmatory_species_and_presence_bytes_are_never_decoded():
    # C and X deliberately contain invalid UTF-8 in species/presence fields.
    raw = (
        b"atoll,species,presence\n"
        b"A,sp1,N\n"
        b"A,sp2,I\n"
        b"B,sp1,N\n"
        b"B,sp3,N\n"
        b"C,\xff,\xfe\n"
        b"X,\xff,\xfe\n"
    )
    routed = build_atoll_burned_pilot_surface(
        response_csv_bytes=raw,
        atoll_to_block={"A": "P1", "B": "P2", "C": "C1"},
        excluded_model_target_atolls={"X"},
        pilot_partition=["P1", "P2"],
        confirmatory_partition=["C1"],
    )

    assert routed.confirmatory_species_values_parsed == 0
    assert routed.confirmatory_presence_values_parsed == 0
    assert routed.excluded_species_values_parsed == 0
    assert routed.excluded_presence_values_parsed == 0
    assert routed.pilot_response_rows_semantically_parsed == 4

    assert routed.csv_text == (
        "partition_unit,block,target\n"
        "P1,P1,1\n"
        "P1,P1,0\n"
        "P2,P2,1\n"
    )
    assert routed.raw_surface_sha256 == hashlib.sha256(
        routed.csv_text.encode("utf-8")
    ).hexdigest()


def test_empty_pilot_block_gets_nonestimable_sentinel():
    raw = b"atoll,species,presence\nA,sp1,N\n"
    routed = build_atoll_burned_pilot_surface(
        response_csv_bytes=raw,
        atoll_to_block={"A": "P1", "B": "P2", "C": "C1"},
        excluded_model_target_atolls=set(),
        pilot_partition=["P1", "P2"],
        confirmatory_partition=["C1"],
    )

    assert routed.blank_sentinel_blocks == ("P1", "P2")
    assert routed.csv_text == (
        "partition_unit,block,target\n"
        "P1,P1,\n"
        "P2,P2,\n"
    )


def test_duplicate_opened_pilot_species_row_fails_closed():
    raw = (
        b"atoll,species,presence\n"
        b"A,sp1,N\n"
        b"A,sp1,N\n"
    )
    with pytest.raises(AtollPilotRouterError, match="duplicate pilot"):
        build_atoll_burned_pilot_surface(
            response_csv_bytes=raw,
            atoll_to_block={"A": "P1", "B": "P2", "C": "C1"},
            excluded_model_target_atolls=set(),
            pilot_partition=["P1", "P2"],
            confirmatory_partition=["C1"],
        )
