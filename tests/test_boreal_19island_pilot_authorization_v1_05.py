from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from structural.boreal_19island_beetle_pilot_router import (
    Boreal19BeetlePilotRouterError,
    build_boreal_19island_beetle_pilot_surface,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/authorize_boreal_19island_pilot_response_v1_05.py"
CONTRACT = (
    ROOT / "development/boreal_19island_pilot_response_authorization_contract_v1_05.json"
)
INTAKE = ROOT / "development/boreal_19island_response_sealed_intake_v1_02.json"
INTAKE_RECEIPT = (
    ROOT / "development/boreal_19island_response_sealed_intake_receipt_v1_02.json"
)
FREEZE = ROOT / "development/boreal_19island_prepilot_freeze_v1_04.json"
PROTOCOL = ROOT / "development/boreal_19island_v031_protocol_v1_03.json"
QUALITY = ROOT / "development/boreal_19island_v042_quality_contract_v1_03.json"
PREPILOT_RECEIPT = (
    ROOT / "development/boreal_19island_prepilot_receipt_v1_03.json"
)
METADATA = ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
FULL_UNIVERSE = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("boreal19_auth_v105", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_real_authorization():
    module = load_module()
    return module.authorize(
        load(INTAKE),
        load(INTAKE_RECEIPT),
        load(FREEZE),
        load(PROTOCOL),
        load(QUALITY),
        load(PREPILOT_RECEIPT),
        load(METADATA),
        load(FULL_UNIVERSE),
        contract=load(CONTRACT),
        observed_file_sha256={
            "protocol": sha(PROTOCOL),
            "quality_contract": sha(QUALITY),
            "prepilot_receipt": sha(PREPILOT_RECEIPT),
        },
    )


def test_real_frozen_chain_authorizes_only_one_future_19island_pilot_opening():
    auth = build_real_authorization()

    assert auth["status"] == "AUTHORIZED_ONE_SHOT_19ISLAND_BURNED_PILOT_RESPONSE"
    assert auth["candidate_id"] == "lac_la_ronge_boreal_19island_beetles_2026"
    assert auth["parent_intake_fingerprint"] == (
        "87df95481c96d710190174175254b4437459714f637f1d0a99aa37c078fa8cb2"
    )
    assert auth["protocol_fingerprint"] == (
        "3a4bd6698780049918c634a5253ff1846c84e8d1c3281e26e2014d766ab90314"
    )
    assert auth["quality_contract_fingerprint"] == (
        "8ac0fe95901caae988673b3d8079b123fdac00573f749049eec3264b89906b58"
    )
    assert len(auth["full_source_island_order"]) == 42
    assert len(auth["analysis_island_order"]) == 19
    assert len(auth["pilot_islands"]) == 6
    assert len(auth["confirmatory_islands"]) == 13
    assert len(auth["excluded_islands"]) == 23
    assert set(auth["pilot_islands"]).isdisjoint(auth["confirmatory_islands"])
    assert set(auth["analysis_island_order"]) == (
        set(auth["pilot_islands"]) | set(auth["confirmatory_islands"])
    )
    assert set(auth["excluded_islands"]).isdisjoint(auth["analysis_island_order"])
    assert set(auth["full_source_island_order"]) == (
        set(auth["analysis_island_order"]) | set(auth["excluded_islands"])
    )

    access = auth["allowed_semantic_access"]
    assert access["species_header_names"] is True
    assert access["routing_island_field_all_42_rows"] is True
    assert access["pilot_island_occurrence_cells"] is True
    assert access["analysis_confirmatory_occurrence_cells"] is False
    assert access["excluded_23_island_occurrence_cells"] is False

    assert auth["pilot_response_authorized"] is True
    assert auth["confirmatory_response_authorized"] is False
    assert auth["authorization_consumed"] is False
    assert auth["response_values_opened_by_authorization"] is False
    assert auth["effect_size"] is None
    assert auth["prediction_score"] is None
    assert auth["predictive_denominator_contribution"] == 0
    assert auth["counts_as_empirical_evidence"] is False
    assert len(auth["authorization_fingerprint"]) == 64


def test_real_authorization_is_bound_to_exact_committed_prepilot_files():
    contract = load(CONTRACT)
    expected = contract["required_parent_identity"]
    assert sha(PROTOCOL) == expected["protocol_file_sha256"]
    assert sha(QUALITY) == expected["quality_contract_file_sha256"]
    assert sha(PREPILOT_RECEIPT) == expected["prepilot_receipt_file_sha256"]


def test_protocol_file_sha_tamper_fails_closed():
    module = load_module()
    with pytest.raises(module.Boreal19PilotAuthorizationError, match="file SHA"):
        module.authorize(
            load(INTAKE),
            load(INTAKE_RECEIPT),
            load(FREEZE),
            load(PROTOCOL),
            load(QUALITY),
            load(PREPILOT_RECEIPT),
            load(METADATA),
            load(FULL_UNIVERSE),
            contract=load(CONTRACT),
            observed_file_sha256={
                "protocol": "0" * 64,
                "quality_contract": sha(QUALITY),
                "prepilot_receipt": sha(PREPILOT_RECEIPT),
            },
        )


def test_opened_response_fails_closed():
    module = load_module()
    intake = load(INTAKE)
    intake["response_values_accessed"] = True
    with pytest.raises(module.Boreal19PilotAuthorizationError, match="response already"):
        module.authorize(
            intake,
            load(INTAKE_RECEIPT),
            load(FREEZE),
            load(PROTOCOL),
            load(QUALITY),
            load(PREPILOT_RECEIPT),
            load(METADATA),
            load(FULL_UNIVERSE),
            contract=load(CONTRACT),
            observed_file_sha256={
                "protocol": sha(PROTOCOL),
                "quality_contract": sha(QUALITY),
                "prepilot_receipt": sha(PREPILOT_RECEIPT),
            },
        )


def synthetic_router_inputs():
    full = tuple(f"I{i:02d}" for i in range(1, 43))
    analysis = full[:19]
    pilot = analysis[:6]
    confirmatory = analysis[6:]
    pilot_blocks = ("P1", "P2", "P3")
    confirmatory_blocks = ("C1", "C2", "C3", "C4", "C5", "C6", "C7")

    mapping = {}
    for i, island in enumerate(pilot):
        mapping[island] = pilot_blocks[i // 2]
    for i, island in enumerate(confirmatory):
        mapping[island] = confirmatory_blocks[i % len(confirmatory_blocks)]

    lines = [b"Island,sp1,sp2,sp3,sp4\n"]
    for i, island in enumerate(full):
        if island in pilot:
            payload = b"1,0,1,0" if i % 2 == 0 else b"0,1,1,0"
        else:
            # Invalid UTF-8 proves confirmatory/excluded occurrence bytes are opaque.
            payload = b"\xff,\xfe,\xff,\xfe"
        lines.append(island.encode("utf-8") + b"," + payload + b"\n")

    return (
        b"".join(lines),
        full,
        analysis,
        mapping,
        pilot_blocks,
        confirmatory_blocks,
    )


def test_router_parses_only_six_pilot_rows_and_leaves_36_other_rows_opaque():
    (
        raw,
        full,
        analysis,
        mapping,
        pilot_blocks,
        confirmatory_blocks,
    ) = synthetic_router_inputs()

    routed = build_boreal_19island_beetle_pilot_surface(
        response_csv_bytes=raw,
        full_expected_islands=full,
        analysis_expected_islands=analysis,
        analysis_island_to_block=mapping,
        pilot_partition=pilot_blocks,
        confirmatory_partition=confirmatory_blocks,
        expected_species_count=4,
    )

    assert routed.source_response_rows_seen == 42
    assert routed.routing_island_fields_decoded == 42
    assert routed.pilot_island_rows_semantically_parsed == 6
    assert routed.pilot_target_values_parsed == 24
    assert routed.confirmatory_target_values_parsed == 0
    assert routed.excluded_target_values_parsed == 0
    assert routed.pilot_island_count == 6
    assert routed.confirmatory_island_count == 13
    assert routed.excluded_island_count == 23
    assert routed.pilot_block_count == 3
    assert routed.pilot_species_universe == ("sp1", "sp2", "sp3")
    assert len(routed.pilot_targets_hex_by_island) == 6


def test_router_rejects_invalid_pilot_occurrence_even_while_other_rows_stay_opaque():
    (
        raw,
        full,
        analysis,
        mapping,
        pilot_blocks,
        confirmatory_blocks,
    ) = synthetic_router_inputs()
    raw = raw.replace(b"I01,1,0,1,0", b"I01,x,0,1,0")

    with pytest.raises(
        Boreal19BeetlePilotRouterError,
        match="unexpected pilot occurrence",
    ):
        build_boreal_19island_beetle_pilot_surface(
            response_csv_bytes=raw,
            full_expected_islands=full,
            analysis_expected_islands=analysis,
            analysis_island_to_block=mapping,
            pilot_partition=pilot_blocks,
            confirmatory_partition=confirmatory_blocks,
            expected_species_count=4,
        )
