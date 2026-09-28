from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_boreal_19island_header_v0_94.py"
CONTRACT = ROOT / "development/boreal_19island_header_audit_contract_v0_94.json"
FREEZE = ROOT / "development/boreal_19island_geometry_identity_freeze_v0_93.json"
WORKFLOW = ROOT / ".github/workflows/boreal-19island-header-audit-v0_94.yml"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal19_header_v094", SCRIPT)
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

    def open(self, request, timeout=None):
        return FakeResponse(self.payload)


def test_v094_contract_is_header_only_after_exact_v093_identity():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert contract["target"]["expected_size_bytes"] == freeze["file"]["size_bytes"]
    assert contract["target"]["expected_sha256"] == freeze["file"]["sha256"]
    assert contract["success_does_not_authorize_row_projection"] is True
    assert freeze["access_state_at_freeze"]["header_decoded"] is False


def test_header_audit_decodes_only_first_physical_record(tmp_path: Path):
    module = load_script()
    payload = b"island,Lat,Long,beetle.richness\nAA,55,-105,999\n"
    digest = hashlib.sha256(payload).hexdigest()

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    contract["target"]["expected_size_bytes"] = len(payload)
    contract["target"]["expected_sha256"] = digest
    freeze["file"]["size_bytes"] = len(payload)
    freeze["file"]["sha256"] = digest

    result = module.audit_header(
        tmp_path / "candidate.csv",
        contract=contract,
        freeze=freeze,
        token="TEST_TOKEN",
        opener=FakeOpener(payload),
    )

    assert result["status"] == "HEADER_ONLY_AUDIT_COMPLETE_ROWS_REMAIN_SEALED"
    assert result["header"] == ["island", "Lat", "Long", "beetle.richness"]
    assert result["header_decoded"] is True
    assert result["data_rows_semantically_opened"] == 0
    assert result["safe_row_values_opened"] is False
    assert result["biological_response_values_opened"] is False
    assert result["all_header_columns_closed_until_next_revision"] is True
    assert result["safe_row_projection_authorized"] is False


def test_v094_workflow_uploads_json_receipts_not_raw_csv():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "boreal_19island_geometry_identity_freeze_v0_93.json" in text
    assert "audit_boreal_19island_header_v0_94.py" in text
    assert "rm -rf build/boreal_v094/raw" in text
    upload = text.split("Upload header receipts only", 1)[1]
    assert "header_receipt.json" in upload
    assert "token_receipt.json" in upload
    assert "raw/alpha_diversity_model_selection_19islands.csv" not in upload
