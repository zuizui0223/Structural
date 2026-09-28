from __future__ import annotations

import hashlib
import importlib.util
import io
import json
from pathlib import Path
from urllib.request import Request

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "development/boreal_lake_islands_exact_transport_contract_v0_72.json"
METADATA_V065 = ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
HEADER_V071 = ROOT / "development/boreal_lake_islands_header_freeze_contract_v0_71.json"
STATUS = ROOT / "development/current_status_v0_72.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_72.json"
SCRIPT = ROOT / "scripts/fetch_boreal_mixed_files_v0_72.py"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal_transport_v072", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FakeResponse:
    def __init__(self, payload: bytes):
        self._stream = io.BytesIO(payload)

    def read(self, n: int = -1) -> bytes:
        return self._stream.read(n)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeOpener:
    def __init__(self, payloads: dict[str, bytes]):
        self.payloads = payloads
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append(request)
        return FakeResponse(self.payloads[request.full_url])


class ExplodingOpener:
    def open(self, request, timeout=None):
        raise AssertionError("network must not be used")


def synthetic_contract(alpha: bytes, rda: bytes) -> dict:
    return {
        "schema": "structural.boreal_lake_islands_exact_transport_contract.v0_72",
        "candidate_id": "synthetic-boreal-transport",
        "targets": {
            "alpha_diversity_ALL_islands.csv": {
                "dryad_file_id": 1,
                "download_url": "https://datadryad.org/api/v2/files/1/download",
                "expected_size_bytes": len(alpha),
                "expected_sha256": digest(alpha),
            },
            "RDA_environmental_variables.csv": {
                "dryad_file_id": 2,
                "download_url": "https://datadryad.org/api/v2/files/2/download",
                "expected_size_bytes": len(rda),
                "expected_sha256": digest(rda),
            },
        },
    }


def test_v072_targets_are_exactly_bound_to_v065_and_v071():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    metadata = json.loads(METADATA_V065.read_text(encoding="utf-8"))
    header = json.loads(HEADER_V071.read_text(encoding="utf-8"))

    assert set(x["targets"]) == {
        "alpha_diversity_ALL_islands.csv",
        "RDA_environmental_variables.csv",
    }
    for name, target in x["targets"].items():
        meta = metadata["focal_files"][name]
        prior = header["files"][name]
        assert target["dryad_file_id"] == meta["file_id"]
        assert target["expected_size_bytes"] == meta["size"]
        assert target["expected_sha256"] == meta["sha256"]
        assert target["expected_size_bytes"] == prior["expected_size_bytes"]
        assert target["expected_sha256"] == prior["expected_sha256"]


def test_v072_contract_keeps_transport_semantically_closed():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    auth = x["authentication"]
    receipt = x["success_receipt"]

    assert auth["token_source"] == "DRYAD_TOKEN environment variable only"
    assert auth["token_on_command_line_forbidden"] is True
    assert auth["token_in_receipt_forbidden"] is True
    assert auth["cross_host_redirect_authorization_forwarding_forbidden"] is True
    assert receipt["header_decoded"] is False
    assert receipt["data_rows_semantically_opened"] == 0
    assert receipt["safe_row_values_opened"] is False
    assert receipt["biological_response_values_opened"] is False
    assert receipt["counts_as_empirical_evidence"] is False
    assert receipt["safe_row_projection_authorized"] is False
    assert receipt["v0_11_intake_authorized"] is False


def test_cross_origin_redirect_drops_authorization():
    module = load_script()
    handler = module.StripAuthorizationOnCrossOriginRedirect()
    request = Request(
        "https://datadryad.org/api/v2/files/1/download",
        headers={"Authorization": "Bearer SECRET", "Accept": "application/octet-stream"},
    )

    redirected = handler.redirect_request(
        request,
        None,
        302,
        "Found",
        {},
        "https://storage.example.org/object?signature=secret",
    )

    assert redirected is not None
    assert redirected.get_header("Authorization") is None
    assert redirected.get_header("Accept") == "application/octet-stream"


def test_exact_download_verifies_bytes_without_semantic_opening(tmp_path: Path):
    module = load_script()
    alpha = b"opaque-alpha-bytes\n"
    rda = b"opaque-rda-bytes\n"
    contract = synthetic_contract(alpha, rda)
    opener = FakeOpener({
        contract["targets"]["alpha_diversity_ALL_islands.csv"]["download_url"]: alpha,
        contract["targets"]["RDA_environmental_variables.csv"]["download_url"]: rda,
    })
    token = "TOKEN_MUST_NEVER_APPEAR_IN_RECEIPT"

    result = module.transport(
        tmp_path,
        contract=contract,
        token=token,
        opener=opener,
    )

    assert result["status"] == "exact_mixed_file_bytes_verified"
    assert result["header_decoded"] is False
    assert result["data_rows_semantically_opened"] == 0
    assert result["safe_row_values_opened"] is False
    assert result["biological_response_values_opened"] is False
    assert result["safe_row_projection_authorized"] is False
    assert result["v0_11_intake_authorized"] is False
    assert token not in json.dumps(result)

    assert (tmp_path / "alpha_diversity_ALL_islands.csv").read_bytes() == alpha
    assert (tmp_path / "RDA_environmental_variables.csv").read_bytes() == rda
    assert not list(tmp_path.glob(".*.part"))
    assert len(opener.requests) == 2
    for request in opener.requests:
        assert request.get_header("Authorization") == f"Bearer {token}"


def test_sha_mismatch_deletes_partial_and_never_installs_destination(tmp_path: Path):
    module = load_script()
    expected = b"expected"
    observed = b"tampered"
    spec = {
        "dryad_file_id": 1,
        "download_url": "https://datadryad.org/api/v2/files/1/download",
        "expected_size_bytes": len(observed),
        "expected_sha256": digest(expected),
    }
    opener = FakeOpener({spec["download_url"]: observed})

    with pytest.raises(module.BorealTransportError, match="verification failed"):
        module._download_one(
            "alpha_diversity_ALL_islands.csv",
            spec,
            tmp_path,
            "token",
            opener=opener,
        )

    assert not (tmp_path / "alpha_diversity_ALL_islands.csv").exists()
    assert not (tmp_path / ".alpha_diversity_ALL_islands.csv.part").exists()


def test_network_error_is_sanitized_and_partial_is_deleted(tmp_path: Path):
    module = load_script()

    class SecretErrorOpener:
        def open(self, request, timeout=None):
            raise RuntimeError(
                "https://object.example/private?signature=DO_NOT_LEAK"
            )

    spec = {
        "dryad_file_id": 1,
        "download_url": "https://datadryad.org/api/v2/files/1/download",
        "expected_size_bytes": 1,
        "expected_sha256": "0" * 64,
    }

    with pytest.raises(
        module.BorealTransportError,
        match=r"transport failed: RuntimeError$",
    ) as caught:
        module._download_one(
            "alpha_diversity_ALL_islands.csv",
            spec,
            tmp_path,
            "token",
            opener=SecretErrorOpener(),
        )

    assert "DO_NOT_LEAK" not in str(caught.value)
    assert "object.example" not in str(caught.value)
    assert not (tmp_path / ".alpha_diversity_ALL_islands.csv.part").exists()


def test_existing_exact_file_is_reused_without_network_or_token(tmp_path: Path):
    module = load_script()
    payload = b"already-exact"
    destination = tmp_path / "alpha_diversity_ALL_islands.csv"
    destination.write_bytes(payload)
    spec = {
        "dryad_file_id": 1,
        "download_url": "https://datadryad.org/api/v2/files/1/download",
        "expected_size_bytes": len(payload),
        "expected_sha256": digest(payload),
    }

    result = module._download_one(
        destination.name,
        spec,
        tmp_path,
        "",
        opener=ExplodingOpener(),
    )

    assert result["transport"] == "reused_existing_exact_file"
    assert destination.read_bytes() == payload


def test_existing_wrong_file_fails_closed_without_overwrite(tmp_path: Path):
    module = load_script()
    destination = tmp_path / "alpha_diversity_ALL_islands.csv"
    destination.write_bytes(b"wrong")
    original = destination.read_bytes()
    spec = {
        "dryad_file_id": 1,
        "download_url": "https://datadryad.org/api/v2/files/1/download",
        "expected_size_bytes": len(b"right"),
        "expected_sha256": digest(b"right"),
    }

    with pytest.raises(module.BorealTransportError, match="wrong"):
        module._download_one(
            destination.name,
            spec,
            tmp_path,
            "token",
            opener=ExplodingOpener(),
        )

    assert destination.read_bytes() == original


def test_v072_status_remains_zero_and_not_executed():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))

    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["exact_file_transport_route_frozen"] is True
    assert boreal["exact_file_transport_executed"] is False
    assert boreal["header_sha_frozen"] is False
    assert boreal["safe_row_values_opened"] is False
    assert boreal["biological_response_values_opened"] is False
    assert boreal["v0_11_intake_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
