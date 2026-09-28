from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/fetch_boreal_19island_geometry_candidate_v0_92.py"
CONTRACT = ROOT / "development/boreal_19island_geometry_identity_contract_v0_92.json"
WORKFLOW = ROOT / ".github/workflows/boreal-19island-geometry-identity-v0_92.yml"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal19_v092", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_contract_freezes_file_id_before_header_access():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert x["source"]["file_name"] == (
        "alpha_diversity_model_selection_19islands.csv"
    )
    assert x["source"]["dryad_file_id"] == 4569035
    assert x["response_firewall"]["header_decoded"] is False
    assert x["response_firewall"]["data_rows_semantically_opened"] == 0
    assert x["response_firewall"]["biological_response_values_opened"] is False
    assert x["response_firewall"]["counts_as_empirical_evidence"] is False
    assert "expected_sha256" not in x["source"]


def test_transport_hashes_opaque_bytes_without_semantic_access(tmp_path: Path):
    module = load_script()
    payload = (
        b"island,Lat,Long,beetle.richness\n"
        b"AA,55.0,-105.0,999\n"
    )
    opener = FakeOpener(payload)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    output = tmp_path / "candidate.csv"

    receipt = module.discover_identity(
        output,
        contract=contract,
        token="TEST_TOKEN",
        opener=opener,
    )

    assert output.read_bytes() == payload
    assert receipt["status"] == "OPAQUE_BYTE_IDENTITY_DISCOVERED"
    assert receipt["size_bytes"] == len(payload)
    assert receipt["sha256"] == hashlib.sha256(payload).hexdigest()
    assert receipt["header_decoded"] is False
    assert receipt["data_rows_semantically_opened"] == 0
    assert receipt["safe_row_values_opened"] is False
    assert receipt["biological_response_values_opened"] is False
    assert receipt["counts_as_empirical_evidence"] is False
    assert len(opener.requests) == 1
    assert opener.requests[0].full_url.endswith("/api/v2/files/4569035/download")


def test_workflow_never_uploads_raw_candidate_csv():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "prepare_dryad_token_v0_73.py" in text
    assert "fetch_boreal_19island_geometry_candidate_v0_92.py" in text
    assert "rm -rf build/boreal_v092/raw" in text
    upload = text.split("Upload identity receipts only", 1)[1]
    assert "raw/alpha_diversity_model_selection_19islands.csv" not in upload
    assert "identity_receipt.json" in upload
    assert "token_receipt.json" in upload
