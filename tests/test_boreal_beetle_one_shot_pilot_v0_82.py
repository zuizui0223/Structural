from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path

import pytest

from structural.response_quality_attrition import (
    ResponseQualityAttritionContract,
    canonical_contract_mapping,
    contract_fingerprint,
)
from structural.transition_pilot_protocol import (
    TransitionPilotProtocol,
    canonical_protocol_mapping,
    protocol_fingerprint,
)


ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "scripts/run_boreal_beetle_pilot_v0_82.py"
FETCHER = ROOT / "scripts/fetch_boreal_beetle_response_v0_82.py"
CONTRACT = ROOT / "development/boreal_beetle_one_shot_pilot_contract_v0_82.json"
STATUS = ROOT / "development/current_status_v0_82.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_82.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def make_world(*, collapsed: bool = False, invalid_pilot: bool = False):
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    candidate = contract["candidate_id"]
    pilot_blocks = ("P1", "P2", "P3")
    confirmatory_blocks = ("C1", "C2", "C3", "C4", "C5", "C6")

    islands = tuple(f"I{i:02d}" for i in range(1, 43))
    island_to_block = {}
    for idx, island in enumerate(islands[:15]):
        island_to_block[island] = pilot_blocks[idx // 5]
    remaining = islands[15:]
    sizes = (5, 5, 5, 4, 4, 4)
    cursor = 0
    for block, size in zip(confirmatory_blocks, sizes):
        for island in remaining[cursor:cursor + size]:
            island_to_block[island] = block
        cursor += size

    protocol = TransitionPilotProtocol(
        protocol_id="synthetic-boreal-v082",
        system_id=candidate,
        partition_axis="response_independent_spatial_components_v075",
        pilot_partition=pilot_blocks,
        confirmatory_partition=confirmatory_blocks,
        endpoint_id="fixed_pilot_supported_beetle_plot_occurrence",
        endpoint_semantics="synthetic fixed common pilot universe",
        heldout_design_id=(
            "leave_one_spatial_component_out_fixed_pilot_supported_species_universe"
        ),
        minimum_test_rows=3,
        minimum_train_positive=5,
        minimum_train_negative=5,
        minimum_estimable_blocks=3,
        pilot_response_accessed=False,
        confirmatory_response_accessed=False,
        pilot_used_for_effect_estimation=False,
    )
    pmap = canonical_protocol_mapping(protocol)
    pfp = protocol_fingerprint(protocol)
    quality = ResponseQualityAttritionContract(
        contract_id="synthetic-boreal-quality-v082",
        system_id=candidate,
        parent_protocol_fingerprint=pfp,
        minimum_response_qualified_blocks=3,
        response_quality_semantics="synthetic response quality",
        pilot_response_accessed=False,
        confirmatory_response_accessed=False,
    )
    qmap = canonical_contract_mapping(quality)
    qfp = contract_fingerprint(quality)

    species = [f"sp{j:03d}" for j in range(1, 467)]
    header = ("Island," + ",".join(species) + "\n").encode("utf-8")
    rows = [header]
    for idx, island in enumerate(islands):
        block = island_to_block[island]
        if block in pilot_blocks:
            vals = []
            for j in range(466):
                if j < 20:
                    if collapsed:
                        value = "1"
                    else:
                        value = str((idx + j) % 2)
                else:
                    value = "0"
                vals.append(value)
            if invalid_pilot and island == islands[0]:
                vals[0] = "X"
            rows.append(
                (island + "," + ",".join(vals) + "\n").encode("utf-8")
            )
        else:
            # Confirmatory cells are deliberately invalid UTF-8. A successful
            # pilot proves they were never semantically decoded.
            rows.append(
                island.encode("utf-8")
                + b","
                + b",".join([b"\xff"] * 466)
                + b"\n"
            )
    raw = b"".join(rows)

    synthetic_contract = json.loads(json.dumps(contract))
    synthetic_contract["response_file"]["expected_size_bytes"] = len(raw)
    synthetic_contract["response_file"]["expected_sha256"] = sha(raw)
    synthetic_contract["response_file"]["dryad_file_id"] = 999
    synthetic_contract["response_file"]["download_url"] = (
        "https://datadryad.org/api/v2/files/999/download"
    )

    spatial_sha = "a" * 64
    spatial = {
        "schema": "structural.boreal_lake_islands_spatial_partition_result.v0_75",
        "status": "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": candidate,
        "island_to_block": island_to_block,
        "pilot_block_ids": list(pilot_blocks),
        "confirmatory_block_ids": list(confirmatory_blocks),
        "species_occurrence_used": False,
        "richness_used": False,
        "habitat_values_used": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
    }
    auth = {
        "schema": "structural.boreal_beetle_pilot_response_authorization.v0_81",
        "status": "AUTHORIZED_ONE_SHOT_BURNED_PILOT_RESPONSE",
        "candidate_id": candidate,
        "protocol_fingerprint": pfp,
        "quality_contract_fingerprint": qfp,
        "source_spatial_receipt_sha256": spatial_sha,
        "response_file": {
            "name": synthetic_contract["response_file"]["name"],
            "dryad_file_id": 999,
            "size_bytes": len(raw),
            "sha256": sha(raw),
        },
        "allowed_semantic_access": {
            "header_species_names": True,
            "routing_island_field_all_rows": True,
            "pilot_island_occurrence_cells": True,
            "confirmatory_island_occurrence_cells": False,
        },
        "router": {
            "confirmatory_target_values_parsed_must_equal": 0,
        },
        "pilot_response_authorized": True,
        "confirmatory_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "authorization_consumed": False,
    }
    return (
        synthetic_contract,
        auth,
        pmap,
        qmap,
        spatial,
        spatial_sha,
        raw,
        islands,
    )


def test_one_shot_executor_qualifies_without_decoding_confirmatory_cells():
    module = load_module(EXECUTOR, "boreal_pilot_v082_success")
    contract, auth, pmap, qmap, spatial, spatial_sha, raw, islands = make_world()

    result = module.execute(
        auth,
        pmap,
        qmap,
        spatial,
        raw,
        contract=contract,
        spatial_receipt_sha256=spatial_sha,
        expected_islands=islands,
    )

    assert result["status"] == "QUALIFIED_TO_FREEZE_CONFIRMATORY_PROTOCOL_ONLY"
    assert result["authorization_consumed"] is True
    assert result["pilot_response_opened"] is True
    assert result["source_response_rows_seen"] == 42
    assert result["routing_island_fields_decoded"] == 42
    assert result["pilot_island_rows_semantically_parsed"] == 15
    assert result["confirmatory_target_values_parsed"] == 0
    assert result["pilot_species_universe_count"] == 20
    assert result["v0_32_exit_code"] == 0
    assert result["pilot_result"]["status"] == (
        "qualified_for_new_confirmatory_protocol"
    )
    future = result["future_admission_receipt"]
    assert future["status"] == "admitted_to_confirmatory_protocol_queue_v0_42"
    assert future["eligible_action"] == "freeze_confirmatory_protocol_only"
    assert future["confirmatory_response_authorized"] is False
    assert result["eligible_action"] == "freeze_confirmatory_protocol_only"
    assert result["effect_size"] is None
    assert result["prediction_score"] is None
    assert result["predictive_denominator_contribution"] == 0
    assert result["counts_as_empirical_evidence"] is False


def test_response_identity_failure_is_pre_access_and_does_not_consume():
    module = load_module(EXECUTOR, "boreal_pilot_v082_preaccess")
    contract, auth, pmap, qmap, spatial, spatial_sha, raw, islands = make_world()
    tampered = raw + b"x"

    with pytest.raises(
        module.BorealPilotExecutionError,
        match="response byte size mismatch",
    ):
        module.execute(
            auth,
            pmap,
            qmap,
            spatial,
            tampered,
            contract=contract,
            spatial_receipt_sha256=spatial_sha,
            expected_islands=islands,
        )


def test_pilot_domain_failure_is_terminal_and_consumes_authorization():
    module = load_module(EXECUTOR, "boreal_pilot_v082_domain")
    contract, auth, pmap, qmap, spatial, spatial_sha, raw, islands = make_world(
        invalid_pilot=True
    )

    result = module.execute(
        auth,
        pmap,
        qmap,
        spatial,
        raw,
        contract=contract,
        spatial_receipt_sha256=spatial_sha,
        expected_islands=islands,
    )

    assert result["status"] == "TERMINAL_PILOT_ROUTER_STOP"
    assert result["authorization_consumed"] is True
    assert result["pilot_response_opened"] is True
    assert result["confirmatory_target_values_parsed"] == 0
    assert "unexpected pilot occurrence value" in result["reason"]
    assert result["effect_size"] is None
    assert result["prediction_score"] is None
    assert result["eligible_action"] is None


def test_endpoint_class_collapse_is_terminal_after_access():
    module = load_module(EXECUTOR, "boreal_pilot_v082_collapse")
    contract, auth, pmap, qmap, spatial, spatial_sha, raw, islands = make_world(
        collapsed=True
    )

    result = module.execute(
        auth,
        pmap,
        qmap,
        spatial,
        raw,
        contract=contract,
        spatial_receipt_sha256=spatial_sha,
        expected_islands=islands,
    )

    assert result["status"] == "TERMINAL_PILOT_GATE_STOP"
    assert result["authorization_consumed"] is True
    assert result["confirmatory_target_values_parsed"] == 0
    assert result["pilot_result"]["status"] == "stop_endpoint_variation"
    assert result["future_admission_receipt"]["status"] == "stop"
    assert result["eligible_action"] is None
    assert result["effect_size"] is None
    assert result["prediction_score"] is None


def test_consumed_authorization_stops_before_semantic_access():
    module = load_module(EXECUTOR, "boreal_pilot_v082_consumed")
    contract, auth, pmap, qmap, spatial, spatial_sha, raw, islands = make_world()
    auth["authorization_consumed"] = True

    with pytest.raises(
        module.BorealPilotExecutionError,
        match="authorization already consumed",
    ):
        module.execute(
            auth,
            pmap,
            qmap,
            spatial,
            raw,
            contract=contract,
            spatial_receipt_sha256=spatial_sha,
            expected_islands=islands,
        )


def test_spatial_evidence_boundary_is_rechecked_pre_access():
    module = load_module(EXECUTOR, "boreal_pilot_v082_spatial")
    contract, auth, pmap, qmap, spatial, spatial_sha, raw, islands = make_world()
    spatial["species_occurrence_used"] = True

    with pytest.raises(
        module.BorealPilotExecutionError,
        match="evidence/response boundary violated",
    ):
        module.execute(
            auth,
            pmap,
            qmap,
            spatial,
            raw,
            contract=contract,
            spatial_receipt_sha256=spatial_sha,
            expected_islands=islands,
        )


class FakeResponse:
    def __init__(self, payload: bytes):
        self.stream = io.BytesIO(payload)

    def read(self, n=-1):
        return self.stream.read(n)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeOpener:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.calls = 0

    def open(self, request, timeout=None):
        self.calls += 1
        return FakeResponse(self.payload)


def test_exact_response_fetch_is_pre_semantic_and_unconsumed(tmp_path: Path):
    module = load_module(FETCHER, "boreal_fetch_v082_success")
    contract, auth, _, _, _, _, raw, _ = make_world()
    opener = FakeOpener(raw)
    destination = tmp_path / "beetles.csv"

    result = module.fetch(
        auth,
        destination,
        contract=contract,
        token="SECRET_TOKEN",
        opener=opener,
    )

    assert opener.calls == 1
    assert destination.read_bytes() == raw
    assert result["status"] == "EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED"
    assert result["response_semantics_opened"] is False
    assert result["authorization_consumed"] is False
    assert result["pilot_response_authorized"] is True
    assert result["confirmatory_response_authorized"] is False
    assert result["counts_as_empirical_evidence"] is False
    assert "SECRET_TOKEN" not in json.dumps(result)


def test_response_fetch_sha_mismatch_deletes_partial(tmp_path: Path):
    module = load_module(FETCHER, "boreal_fetch_v082_badsha")
    contract, auth, _, _, _, _, raw, _ = make_world()
    observed = raw[:-1] + b"z"
    opener = FakeOpener(observed)
    destination = tmp_path / "beetles.csv"

    with pytest.raises(
        module.BorealBeetleResponseTransportError,
        match="verification failed",
    ):
        module.fetch(
            auth,
            destination,
            contract=contract,
            token="SECRET_TOKEN",
            opener=opener,
        )

    assert not destination.exists()
    assert not (tmp_path / ".beetles.csv.part").exists()


def test_response_fetch_refuses_consumed_authorization_without_network(
    tmp_path: Path,
):
    module = load_module(FETCHER, "boreal_fetch_v082_consumed")
    contract, auth, _, _, _, _, raw, _ = make_world()
    auth["authorization_consumed"] = True
    opener = FakeOpener(raw)

    with pytest.raises(
        module.BorealBeetleResponseTransportError,
        match="already consumed",
    ):
        module.fetch(
            auth,
            tmp_path / "beetles.csv",
            contract=contract,
            token="SECRET_TOKEN",
            opener=opener,
        )

    assert opener.calls == 0


def test_v082_contract_and_status_keep_real_execution_unstarted():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))

    assert contract["execution_authorized_now"] is False
    assert contract["pre_access"][
        "transport_or_identity_failure_consumes_authorization"
    ] is False
    assert contract["semantic_access"][
        "confirmatory_target_values_parsed_required"
    ] == 0
    assert contract["pilot_execution"]["effect_size"] is None
    assert contract["pilot_execution"]["prediction_score"] is None

    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["pilot_response_authorization_issued"] is False
    assert boreal["pilot_response_consumed"] is False
    assert boreal["confirmatory_response_values_opened"] is False
    assert boreal["confirmatory_protocol_freeze_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
