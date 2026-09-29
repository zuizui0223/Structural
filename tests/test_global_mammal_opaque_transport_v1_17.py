from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/fetch_global_mammal_response_opaque_v1_17.py"
CONTRACT = (
    ROOT / "development/global_mammals_credentialed_opaque_transport_contract_v1_17.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("global_mammals_v117", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


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
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append(request)
        return FakeResponse(self.payload)


def synthetic_contract(payload: bytes):
    x = load_contract()
    x["target"] = dict(x["target"])
    x["target"]["download_url"] = "https://datadryad.org/api/v2/files/3242161/download"
    x["target"]["expected_size_bytes"] = len(payload)
    x["target"]["expected_sha256"] = hashlib.sha256(payload).hexdigest()
    return x


def test_real_contract_changes_transport_only_and_keeps_response_sealed():
    x = load_contract()
    sup = x["operational_supersession"]
    assert sup["scientific_hypothesis_changed"] is False
    assert sup["endpoint_changed"] is False
    assert sup["population_changed"] is False
    assert sup["crosswalk_rule_changed"] is False
    assert sup["response_domain_changed"] is False
    assert sup["isolation_reference_changed"] is False

    target = x["target"]
    assert target["dryad_file_id"] == 3242161
    assert target["expected_size_bytes"] == 60486843
    assert target["expected_sha256"] == (
        "32bf3f077af7e66ddcbf05fc675d6c51656f59111c27cd37129e14c658430fa6"
    )
    assert target["source_reported_island_rows"] == 5592

    attempt = x["attempt_policy"]
    assert attempt["credentialed_attempt_limit"] == 1
    assert attempt["blind_endpoint_retry_authorized"] is False
    assert attempt["alternate_file_id_retry_authorized"] is False

    firewall = x["semantic_firewall"]
    assert firewall["header_decoded"] is False
    assert firewall["routing_ids_decoded"] == 0
    assert firewall["species_header_fields_decoded"] == 0
    assert firewall["occurrence_values_decoded"] == 0
    assert firewall["biological_response_values_opened"] is False


def test_transport_hashes_opaque_bytes_without_semantic_decode(tmp_path: Path):
    module = load_module()
    payload = (
        b"ID,species_a,species_b\n"
        b"123,1,0\n"
        b"456,0,1\n"
    )
    opener = FakeOpener(payload)
    output = tmp_path / "Appendix_1_presence_absence.csv"

    result = module.transport(
        output,
        contract=synthetic_contract(payload),
        token="SHORT_LIVED_TEST_TOKEN",
        opener=opener,
    )

    assert output.read_bytes() == payload
    assert result["status"] == "EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED"
    assert result["response_bytes_read_as_opaque"] == len(payload)
    assert result["header_decoded"] is False
    assert result["routing_ids_decoded"] == 0
    assert result["species_header_fields_decoded"] == 0
    assert result["occurrence_values_decoded"] == 0
    assert result["biological_response_values_opened"] is False
    assert result["raw_response_artifact_authorized"] is False
    assert result["semantic_crosswalk_authorized_in_same_revision"] is False
    assert result["credentialed_attempt_consumed"] is True
    assert result["fresh_system_denominator_contribution"] == 0
    assert len(opener.requests) == 1
    assert opener.requests[0].full_url.endswith(
        "/api/v2/files/3242161/download"
    )


def test_identity_mismatch_deletes_partial_and_fails_closed(tmp_path: Path):
    module = load_module()
    payload = b"opaque bytes"
    contract = synthetic_contract(payload)
    contract["target"]["expected_sha256"] = "0" * 64
    output = tmp_path / "response.csv"

    with pytest.raises(
        module.GlobalMammalTransportError,
        match="exact byte identity verification failed",
    ):
        module.transport(
            output,
            contract=contract,
            token="TEST_TOKEN",
            opener=FakeOpener(payload),
        )

    assert not output.exists()
    assert not output.with_name(".response.csv.part").exists()


def test_empty_or_malformed_token_fails_before_network(tmp_path: Path):
    module = load_module()
    payload = b"x"
    opener = FakeOpener(payload)
    for token in ("", "bad\ntoken", "bad\rtoken"):
        with pytest.raises(
            module.GlobalMammalTransportError,
            match="missing or malformed",
        ):
            module.transport(
                tmp_path / f"out-{len(token)}.csv",
                contract=synthetic_contract(payload),
                token=token,
                opener=opener,
            )
    assert opener.requests == []
