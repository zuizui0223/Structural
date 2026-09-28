from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from structural.response_quality_attrition import (
    canonical_contract_mapping,
    contract_fingerprint,
    contract_from_mapping,
)
from structural.transition_pilot_protocol import (
    canonical_protocol_mapping,
    protocol_fingerprint,
    protocol_from_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "scripts/run_boreal_19island_pilot_v1_07.py"
FETCHER = ROOT / "scripts/fetch_boreal_19island_beetle_response_v1_07.py"
CONTRACT_PATH = (
    ROOT / "development/boreal_19island_one_shot_pilot_contract_v1_07.json"
)
WORKFLOW = ROOT / ".github/workflows/boreal-19island-pilot-execution-v1_07.yml"


def load_script(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_inputs():
    full = tuple(f"I{i:02d}" for i in range(1, 43))
    analysis = full[:19]
    pilot_islands = analysis[:6]
    confirmatory_islands = analysis[6:]
    excluded = full[19:]
    pilot_blocks = ("P1", "P2", "P3")
    confirmatory_blocks = ("C1", "C2", "C3", "C4", "C5", "C6", "C7")

    mapping = {}
    for i, island in enumerate(pilot_islands):
        mapping[island] = pilot_blocks[i // 2]
    for i, island in enumerate(confirmatory_islands):
        mapping[island] = confirmatory_blocks[i % len(confirmatory_blocks)]

    protocol = protocol_from_mapping({
        "protocol_id": "synthetic-19-v107",
        "system_id": "synthetic-19",
        "partition_axis": "synthetic-spatial",
        "pilot_partition": list(pilot_blocks),
        "confirmatory_partition": list(confirmatory_blocks),
        "endpoint_id": "synthetic-fixed-universe",
        "endpoint_semantics": "synthetic exact binary targets",
        "heldout_design_id": "synthetic-loso",
        "minimum_test_rows": 3,
        "minimum_train_positive": 5,
        "minimum_train_negative": 5,
        "minimum_estimable_blocks": 3,
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
        "pilot_used_for_effect_estimation": False,
    })
    protocol_map = canonical_protocol_mapping(protocol)
    pfp = protocol_fingerprint(protocol)

    quality = contract_from_mapping({
        "contract_id": "synthetic-19-quality-v107",
        "system_id": "synthetic-19",
        "parent_protocol_fingerprint": pfp,
        "minimum_response_qualified_blocks": 3,
        "response_quality_semantics": "synthetic response quality",
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
    })
    quality_map = canonical_contract_mapping(quality)
    qfp = contract_fingerprint(quality)

    pilot_patterns = (
        b"1,0,1,0",
        b"0,1,0,1",
        b"1,0,1,0",
        b"0,1,0,1",
        b"1,0,1,0",
        b"0,1,0,1",
    )
    lines = [b"Island,sp1,sp2,sp3,sp4\n"]
    pi = 0
    for island in full:
        if island in pilot_islands:
            payload = pilot_patterns[pi]
            pi += 1
        else:
            # Non-UTF8 proves confirmatory/excluded targets remain opaque.
            payload = b"\xff,\xfe,\xff,\xfe"
        lines.append(island.encode("utf-8") + b"," + payload + b"\n")
    response = b"".join(lines)
    response_sha = hashlib.sha256(response).hexdigest()

    auth_core = {
        "schema": "structural.boreal_19island_pilot_response_authorization.v1_05",
        "status": "AUTHORIZED_ONE_SHOT_19ISLAND_BURNED_PILOT_RESPONSE",
        "candidate_id": "synthetic-19",
        "parent_intake_fingerprint": "1" * 64,
        "source_operator_fingerprint": "2" * 64,
        "protocol_fingerprint": pfp,
        "quality_contract_fingerprint": qfp,
        "response_file": {
            "name": "beetles_speciesmatrix_presenceabsence.csv",
            "dryad_file_id": 4569032,
            "size_bytes": len(response),
            "sha256": response_sha,
            "expected_species_columns": 4,
        },
        "full_source_island_order": list(full),
        "analysis_island_order": list(analysis),
        "pilot_islands": list(pilot_islands),
        "confirmatory_islands": list(confirmatory_islands),
        "excluded_islands": list(excluded),
        "island_to_block": mapping,
        "pilot_block_ids": list(pilot_blocks),
        "confirmatory_block_ids": list(confirmatory_blocks),
        "allowed_semantic_access": {
            "species_header_names": True,
            "routing_island_field_all_42_rows": True,
            "pilot_island_occurrence_cells": True,
            "analysis_confirmatory_occurrence_cells": False,
            "excluded_23_island_occurrence_cells": False,
        },
        "router": {
            "implementation": (
                "src/structural/boreal_19island_beetle_pilot_router.py"
            ),
            "confirmatory_target_values_parsed_must_equal": 0,
            "excluded_target_values_parsed_must_equal": 0,
        },
        "pilot_response_authorized": True,
        "confirmatory_response_authorized": False,
        "authorization_consumed": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "response_values_opened_by_authorization": False,
        "next_action": "synthetic",
    }
    executor = load_script(EXECUTOR, "boreal19_exec_v107")
    auth = {
        **auth_core,
        "authorization_fingerprint": executor.canonical_sha256(auth_core),
    }
    auth_raw = (json.dumps(auth, indent=2, sort_keys=True) + "\n").encode("utf-8")
    auth_sha = hashlib.sha256(auth_raw).hexdigest()

    contract = {
        "schema": "structural.boreal_19island_one_shot_pilot_contract.v1_07",
        "candidate_id": "synthetic-19",
        "authorization": {
            "schema": auth["schema"],
            "status": auth["status"],
            "expected_fingerprint": auth["authorization_fingerprint"],
            "expected_json_sha256": auth_sha,
        },
        "response_file": {
            "name": auth["response_file"]["name"],
            "dryad_file_id": 4569032,
            "download_url": "https://example.invalid/download",
            "expected_size_bytes": len(response),
            "expected_sha256": response_sha,
            "expected_species_columns": 4,
            "expected_full_source_island_rows": 42,
        },
        "population": {
            "full_source_island_count": 42,
            "analysis_island_count": 19,
            "pilot_island_count": 6,
            "confirmatory_island_count": 13,
            "excluded_island_count": 23,
            "pilot_block_count": 3,
            "confirmatory_block_count": 7,
        },
        "semantic_access": {
            "router": (
                "src/structural/boreal_19island_beetle_pilot_router.py"
            ),
            "expected_pilot_target_values_parsed": 24,
            "required_confirmatory_target_values_parsed": 0,
            "required_excluded_target_values_parsed": 0,
        },
        "qualified_ceiling": {
            "status": (
                "QUALIFIED_TO_FREEZE_19ISLAND_CONFIRMATORY_MODEL_WITH_PILOT_SNAPSHOT"
            ),
            "eligible_action": (
                "freeze_19island_confirmatory_model_and_predictions_only"
            ),
        },
    }
    return executor, auth, auth_raw, auth_sha, protocol_map, quality_map, response, contract


def test_synthetic_v107_qualifies_and_never_parses_nonpilot_occurrences():
    (
        executor,
        auth,
        _,
        auth_sha,
        protocol,
        quality,
        response,
        contract,
    ) = synthetic_inputs()

    result, snapshot = executor.execute(
        auth,
        protocol,
        quality,
        response,
        authorization_file_sha256=auth_sha,
        contract=contract,
    )

    assert result["status"] == (
        "QUALIFIED_TO_FREEZE_19ISLAND_CONFIRMATORY_MODEL_WITH_PILOT_SNAPSHOT"
    )
    assert result["authorization_consumed"] is True
    assert result["pilot_response_opened"] is True
    assert result["source_response_rows_seen"] == 42
    assert result["routing_island_fields_decoded"] == 42
    assert result["pilot_island_rows_semantically_parsed"] == 6
    assert result["pilot_target_values_parsed"] == 24
    assert result["confirmatory_target_values_parsed"] == 0
    assert result["excluded_target_values_parsed"] == 0
    assert result["pilot_species_universe_count"] == 4
    assert result["model_snapshot_frozen"] is True
    assert result["v0_32_exit_code"] == 0
    assert result["effect_size"] is None
    assert result["prediction_score"] is None
    assert result["predictive_denominator_contribution"] == 0
    assert result["counts_as_empirical_evidence"] is False
    assert result["confirmatory_response_authorized"] is False

    assert snapshot is not None
    assert snapshot["pilot_island_count"] == 6
    assert snapshot["confirmatory_island_count"] == 13
    assert snapshot["excluded_island_count"] == 23
    assert snapshot["confirmatory_target_values_parsed"] == 0
    assert snapshot["excluded_target_values_parsed"] == 0
    assert snapshot["confirmatory_occurrence_values_stored"] is False
    assert snapshot["excluded_occurrence_values_stored"] is False
    assert snapshot["pilot_species_universe"] == ["sp1", "sp2", "sp3", "sp4"]
    assert len(snapshot["targets_hex_by_island"]) == 6
    assert snapshot["qualified_for_confirmatory_model_freeze"] is True


def test_response_identity_failure_is_preaccess_and_does_not_consume():
    (
        executor,
        auth,
        _,
        auth_sha,
        protocol,
        quality,
        response,
        contract,
    ) = synthetic_inputs()

    tampered = response[:-1] + (b"\\r" if response[-1:] != b"\\r" else b"\\n")
    assert len(tampered) == len(response)
    assert tampered != response

    with pytest.raises(executor.Boreal19PilotExecutionError, match="response SHA"):
        executor.execute(
            auth,
            protocol,
            quality,
            tampered,
            authorization_file_sha256=auth_sha,
            contract=contract,
        )


def test_pilot_domain_failure_is_terminal_and_consumes_authorization():
    (
        executor,
        auth,
        _,
        auth_sha,
        protocol,
        quality,
        response,
        contract,
    ) = synthetic_inputs()
    broken = response.replace(b"I01,1,0,1,0", b"I01,x,0,1,0")
    contract = json.loads(json.dumps(contract))
    contract["response_file"]["expected_size_bytes"] = len(broken)
    contract["response_file"]["expected_sha256"] = hashlib.sha256(broken).hexdigest()
    auth = json.loads(json.dumps(auth))
    auth["response_file"]["size_bytes"] = len(broken)
    auth["response_file"]["sha256"] = contract["response_file"]["expected_sha256"]
    auth.pop("authorization_fingerprint")
    core = dict(auth)
    auth["authorization_fingerprint"] = executor.canonical_sha256(core)
    contract["authorization"]["expected_fingerprint"] = auth["authorization_fingerprint"]
    raw = (json.dumps(auth, indent=2, sort_keys=True) + "\n").encode("utf-8")
    auth_sha = hashlib.sha256(raw).hexdigest()
    contract["authorization"]["expected_json_sha256"] = auth_sha

    result, snapshot = executor.execute(
        auth,
        protocol,
        quality,
        broken,
        authorization_file_sha256=auth_sha,
        contract=contract,
    )
    assert result["status"] == "TERMINAL_PILOT_ROUTER_STOP"
    assert result["authorization_consumed"] is True
    assert result["pilot_response_opened"] is True
    assert result["confirmatory_response_authorized"] is False
    assert snapshot is None


class FakeResponse:
    def __init__(self, payload: bytes):
        self.payload = payload
        self.pos = 0

    def read(self, n=-1):
        if self.pos >= len(self.payload):
            return b""
        if n < 0:
            n = len(self.payload) - self.pos
        chunk = self.payload[self.pos:self.pos + n]
        self.pos += len(chunk)
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeOpener:
    def __init__(self, payload: bytes):
        self.payload = payload

    def open(self, request, timeout=None):
        return FakeResponse(self.payload)


def test_transport_verifies_bytes_without_semantic_open(tmp_path: Path):
    fetcher = load_script(FETCHER, "boreal19_fetch_v107")
    (
        _,
        auth,
        auth_raw,
        auth_sha,
        _,
        _,
        response,
        contract,
    ) = synthetic_inputs()
    destination = tmp_path / "response.csv"

    receipt = fetcher.fetch(
        auth,
        destination,
        authorization_file_sha256=auth_sha,
        contract=contract,
        token="TOKEN",
        opener=FakeOpener(response),
    )
    assert destination.read_bytes() == response
    assert receipt["status"] == "EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED"
    assert receipt["response_semantics_opened"] is False
    assert receipt["authorization_consumed"] is False
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["counts_as_empirical_evidence"] is False
    assert hashlib.sha256(auth_raw).hexdigest() == auth_sha


def test_real_contract_preserves_one_shot_response_ceiling():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["authorization"]["expected_fingerprint"] == (
        "2942d3d76d118bcf04c71d721d8f37f5531abb964713828dc375f610d08fab97"
    )
    assert contract["authorization"]["expected_json_sha256"] == (
        "b32613cad3c2ca4055c581b2540db349b312641e5d94ccd4dee5ec5e6c21978b"
    )
    assert contract["semantic_access"]["expected_pilot_target_values_parsed"] == 2796
    assert contract["semantic_access"]["required_confirmatory_target_values_parsed"] == 0
    assert contract["semantic_access"]["required_excluded_target_values_parsed"] == 0
    assert contract["qualified_ceiling"]["confirmatory_response_authorized"] is False
    assert contract["qualified_ceiling"]["counts_as_empirical_evidence"] is False


def test_workflow_is_retry_closed_and_never_uploads_raw_response():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'test "$GITHUB_RUN_ATTEMPT" = "1"' in text
    assert "git rev-list --count HEAD --" in text
    assert "prepare_dryad_token_v0_73.py" in text
    assert "fetch_boreal_19island_beetle_response_v1_07.py" in text
    assert "run_boreal_19island_pilot_v1_07.py" in text
    assert "rm -rf build/boreal_v107/raw" in text
    upload = text.split("Upload consumed pilot audit bundle", 1)[1]
    assert "raw/" not in upload
    assert "training_snapshot.json" in upload
    assert "execution_receipt.json" in upload
