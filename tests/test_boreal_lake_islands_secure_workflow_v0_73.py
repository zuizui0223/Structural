from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
from urllib.parse import parse_qs

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/prepare_dryad_token_v0_73.py"
CONTRACT = ROOT / "development/boreal_lake_islands_secure_workflow_contract_v0_73.json"
WORKFLOW = ROOT / ".github/workflows/boreal-lake-islands-stage-a-v0_73.yml"
STATUS = ROOT / "development/current_status_v0_73.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_73.json"


def load_script():
    spec = importlib.util.spec_from_file_location("dryad_token_v073", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeOpener:
    def __init__(self, payload: dict):
        self.payload = payload
        self.requests = []

    def open(self, request, timeout=None):
        self.requests.append(request)
        return FakeResponse(self.payload)


def test_mint_token_uses_client_credentials_and_returns_only_token_in_memory():
    module = load_script()
    opener = FakeOpener({
        "access_token": "SHORT_LIVED_SECRET_TOKEN",
        "token_type": "Bearer",
        "expires_in": 36000,
    })

    token, expires = module.mint_token(
        "client-id-value",
        "client-secret-value",
        opener=opener,
    )

    assert token == "SHORT_LIVED_SECRET_TOKEN"
    assert expires == 36000
    assert len(opener.requests) == 1
    request = opener.requests[0]
    assert request.full_url == "https://datadryad.org/oauth/token"
    assert request.get_method() == "POST"
    body = parse_qs(request.data.decode("utf-8"))
    assert body == {
        "client_id": ["client-id-value"],
        "client_secret": ["client-secret-value"],
        "grant_type": ["client_credentials"],
    }


def test_prepare_token_writes_runner_env_but_receipt_contains_no_secret(tmp_path: Path):
    module = load_script()
    opener = FakeOpener({
        "access_token": "TOKEN_NEVER_IN_RECEIPT",
        "token_type": "Bearer",
        "expires_in": 35999,
    })
    github_env = tmp_path / "github_env"

    receipt = module.prepare_token(
        client_id="CLIENT_NEVER_IN_RECEIPT",
        client_secret="SECRET_NEVER_IN_RECEIPT",
        fallback_token="",
        github_env=github_env,
        opener=opener,
    )

    assert github_env.read_text(encoding="utf-8") == (
        "DRYAD_TOKEN=TOKEN_NEVER_IN_RECEIPT\n"
    )
    serialized = json.dumps(receipt)
    assert "TOKEN_NEVER_IN_RECEIPT" not in serialized
    assert "CLIENT_NEVER_IN_RECEIPT" not in serialized
    assert "SECRET_NEVER_IN_RECEIPT" not in serialized
    assert receipt["mode"] == "client_credentials_minted_token"
    assert receipt["token_persisted_in_receipt"] is False
    assert receipt["client_credentials_persisted_in_receipt"] is False


def test_fallback_token_can_be_installed_without_client_credentials(tmp_path: Path):
    module = load_script()
    github_env = tmp_path / "github_env"

    receipt = module.prepare_token(
        client_id="",
        client_secret="",
        fallback_token="FALLBACK_SHORT_TOKEN",
        github_env=github_env,
    )

    assert receipt["mode"] == "preexisting_short_lived_token"
    assert receipt["expires_in_seconds"] is None
    assert "FALLBACK_SHORT_TOKEN" not in json.dumps(receipt)
    assert "DRYAD_TOKEN=FALLBACK_SHORT_TOKEN" in github_env.read_text(
        encoding="utf-8"
    )


def test_partial_client_credentials_fail_closed(tmp_path: Path):
    module = load_script()
    with pytest.raises(module.DryadTokenError, match="supplied together"):
        module.prepare_token(
            client_id="only-id",
            client_secret="",
            fallback_token="",
            github_env=tmp_path / "github_env",
        )


def test_token_request_error_does_not_surface_secret_or_remote_message():
    module = load_script()

    class SecretErrorOpener:
        def open(self, request, timeout=None):
            raise RuntimeError(
                "client_secret=DO_NOT_LEAK&redirect=https://private.example"
            )

    with pytest.raises(
        module.DryadTokenError,
        match=r"token request failed: RuntimeError$",
    ) as caught:
        module.mint_token(
            "CLIENT_DO_NOT_LEAK",
            "SECRET_DO_NOT_LEAK",
            opener=SecretErrorOpener(),
        )

    message = str(caught.value)
    assert "DO_NOT_LEAK" not in message
    assert "private.example" not in message


def test_v073_contract_is_manual_only_and_json_artifact_only():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert x["trigger"] == "workflow_dispatch_only"
    assert x["permissions"] == {"contents": "read"}
    assert x["artifact_policy"]["raw_csv_upload_forbidden"] is True
    assert x["artifact_policy"]["token_or_client_secret_upload_forbidden"] is True
    assert x["artifact_policy"]["row_value_upload_forbidden"] is True
    assert x["evidence_boundary"]["safe_row_values_may_be_opened"] is False
    assert x["evidence_boundary"]["protected_response_values_may_be_opened"] is False
    assert x["evidence_boundary"]["counts_as_empirical_evidence"] is False
    assert x["evidence_boundary"]["v0_11_intake_authorized"] is False
    assert x["workflow_execution_authorized_by_this_revision"] is False


def test_workflow_has_no_automatic_trigger_and_no_raw_artifact_path():
    text = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in text
    assert "\n  push:" not in text
    assert "\n  pull_request:" not in text
    assert "\n  schedule:" not in text
    assert "permissions:\n  contents: read" in text
    assert "persist-credentials: false" in text

    assert "secrets.DRYAD_CLIENT_ID" in text
    assert "secrets.DRYAD_CLIENT_SECRET" in text
    assert "secrets.DRYAD_TOKEN" in text
    assert "--github-env \"$GITHUB_ENV\"" in text

    assert "rm -rf build/boreal_v073/raw" in text
    upload = text.split("Upload Stage A receipts only", 1)[1]
    assert "build/boreal_v073/raw" not in upload
    assert "token_receipt.json" in upload
    assert "transport_receipt.json" in upload
    assert "header_audit.json" in upload
    assert "retention-days: 7" in upload


def test_v073_status_keeps_denominator_zero_and_execution_false():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))

    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["secure_manual_stage_A_route_frozen"] is True
    assert boreal["stage_A_workflow_executed"] is False
    assert boreal["header_sha_frozen"] is False
    assert boreal["safe_row_values_opened"] is False
    assert boreal["biological_response_values_opened"] is False
    assert boreal["v0_11_intake_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
