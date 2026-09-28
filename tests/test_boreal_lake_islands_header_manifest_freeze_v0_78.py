from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/freeze_boreal_header_manifests_v0_78.py"
PROJECTION_SCRIPT = ROOT / "scripts/project_boreal_safe_rows_v0_74.py"
CONTRACT = ROOT / "development/boreal_lake_islands_header_manifest_freeze_contract_v0_78.json"
V071 = ROOT / "development/boreal_lake_islands_header_freeze_contract_v0_71.json"
WORKFLOW = ROOT / ".github/workflows/boreal-lake-islands-stage-a-v0_78.yml"
STATUS = ROOT / "development/current_status_v0_78.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_78.json"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stage_a_objects():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    v071 = json.loads(V071.read_text(encoding="utf-8"))
    repo = contract["workflow_requirements"]["repository"]
    ref = contract["workflow_requirements"]["ref"]
    workflow = contract["workflow"]
    context = {
        "schema": "structural.boreal_stage_a_execution_context.v0_78",
        "status": "manual_main_stage_a_execution",
        "repository": repo,
        "head_sha": "a" * 40,
        "ref": ref,
        "run_id": 123456,
        "run_attempt": 1,
        "workflow": "Boreal lake islands Stage A v0.78",
        "workflow_ref": f"{repo}/{workflow}@{ref}",
        "raw_csv_artifact_authorized": False,
        "counts_as_empirical_evidence": False,
    }
    token = {
        "schema": "structural.dryad_token_prepare_result.v0_73",
        "status": "token_installed_in_runner_environment",
        "mode": "client_credentials_minted_token",
        "expires_in_seconds": 36000,
        "token_persisted_in_receipt": False,
        "client_credentials_persisted_in_receipt": False,
        "counts_as_empirical_evidence": False,
    }

    transport_files = {}
    audit_files = {}
    for name, prior in v071["files"].items():
        header_sha = ("1" if name.startswith("alpha") else "2") * 64
        transport_files[name] = {
            "file_id": prior["dryad_file_id"],
            "size_bytes": prior["expected_size_bytes"],
            "sha256": prior["expected_sha256"],
            "transport": "downloaded_and_verified",
        }
        audit_files[name] = {
            "file_sha256": prior["expected_sha256"],
            "header_sha256": header_sha,
            "header": (
                prior["safe_pre_response_columns"]
                + prior["protected_response_columns"]
                + ["closed.extra"]
            ),
            "declared_safe_columns": prior["safe_pre_response_columns"],
            "declared_protected_columns": prior["protected_response_columns"],
            "present_safe_columns": prior["safe_pre_response_columns"],
            "missing_safe_columns": [],
            "present_protected_columns": prior["protected_response_columns"],
            "missing_protected_columns": [],
            "closed_unclassified_columns": ["closed.extra"],
            "qualified_to_freeze_manifest": True,
            "reasons": [],
            "candidate_manifest": {
                "file_sha256": prior["expected_sha256"],
                "header_sha256": header_sha,
                "safe_pre_response_columns": prior["safe_pre_response_columns"],
                "protected_response_columns": prior["protected_response_columns"],
            },
        }

    transport = {
        "schema": "structural.boreal_lake_islands_exact_transport_result.v0_72",
        "status": "exact_mixed_file_bytes_verified",
        "candidate_id": contract["candidate_id"],
        "files": transport_files,
        "header_decoded": False,
        "data_rows_semantically_opened": 0,
        "safe_row_values_opened": False,
        "biological_response_values_opened": False,
        "model_fit_count": 0,
        "counts_as_empirical_evidence": False,
        "safe_row_projection_authorized": False,
        "v0_11_intake_authorized": False,
    }
    audit = {
        "schema": "structural.boreal_lake_islands_header_audit_result.v0_71",
        "status": "qualified_to_freeze_header_manifests_only",
        "candidate_id": contract["candidate_id"],
        "files": audit_files,
        "data_rows_semantically_opened": 0,
        "safe_row_values_opened": False,
        "protected_response_values_opened": False,
        "model_fit_count": 0,
        "counts_as_empirical_evidence": False,
        "safe_row_projection_authorized": False,
        "v0_11_intake_authorized": False,
    }
    return contract, v071, context, token, transport, audit


def test_successful_freeze_is_directly_accepted_by_v074_projection_gate():
    freezer = load_module(SCRIPT, "boreal_manifest_freezer_v078")
    projection = load_module(PROJECTION_SCRIPT, "boreal_projection_v074")
    contract, v071, context, token, transport, audit = stage_a_objects()

    result = freezer.freeze(
        context,
        token,
        transport,
        audit,
        contract=contract,
        v071=v071,
        input_sha256={
            "execution_context": "a" * 64,
            "token_receipt": "b" * 64,
            "transport_receipt": "c" * 64,
            "header_audit": "d" * 64,
        },
    )

    assert result["schema"] == (
        "structural.boreal_lake_islands_header_manifest_freeze.v0_74"
    )
    assert result["status"] == "header_manifests_frozen_before_row_projection"
    assert result["safe_row_projection_authorized"] is True
    assert result["row_values_opened_by_freezer"] == 0
    assert result["biological_response_values_opened_by_freezer"] is False
    assert result["counts_as_empirical_evidence"] is False
    assert result["v0_12_intake_authorized"] is False

    projection_contract = json.loads(
        (
            ROOT
            / "development/boreal_lake_islands_safe_projection_contract_v0_74.json"
        ).read_text(encoding="utf-8")
    )
    manifests = projection.validate_manifest_freeze(
        result,
        contract=projection_contract,
        v071=v071,
    )
    assert set(manifests) == {
        "alpha_diversity_ALL_islands.csv",
        "RDA_environmental_variables.csv",
    }


def test_non_main_stage_a_is_rejected():
    freezer = load_module(SCRIPT, "boreal_manifest_freezer_v078_nonmain")
    contract, v071, context, token, transport, audit = stage_a_objects()
    context["ref"] = "refs/heads/research/test"

    with pytest.raises(
        freezer.BorealManifestFreezeError,
        match="not run from main",
    ):
        freezer.freeze(
            context, token, transport, audit, contract=contract, v071=v071
        )


def test_wrong_workflow_identity_is_rejected():
    freezer = load_module(SCRIPT, "boreal_manifest_freezer_v078_wrongwf")
    contract, v071, context, token, transport, audit = stage_a_objects()
    context["workflow_ref"] = (
        "zuizui0223/Structural/.github/workflows/other.yml@refs/heads/main"
    )

    with pytest.raises(
        freezer.BorealManifestFreezeError,
        match="workflow identity mismatch",
    ):
        freezer.freeze(
            context, token, transport, audit, contract=contract, v071=v071
        )


def test_transport_size_or_file_identity_drift_is_rejected():
    freezer = load_module(SCRIPT, "boreal_manifest_freezer_v078_transport")
    contract, v071, context, token, transport, audit = stage_a_objects()
    name = "alpha_diversity_ALL_islands.csv"
    transport["files"][name]["size_bytes"] += 1

    with pytest.raises(
        freezer.BorealManifestFreezeError,
        match="transport size mismatch",
    ):
        freezer.freeze(
            context, token, transport, audit, contract=contract, v071=v071
        )


def test_safe_declaration_drift_is_rejected():
    freezer = load_module(SCRIPT, "boreal_manifest_freezer_v078_safe")
    contract, v071, context, token, transport, audit = stage_a_objects()
    name = "RDA_environmental_variables.csv"
    audit["files"][name]["candidate_manifest"][
        "safe_pre_response_columns"
    ] = ["Island"]

    with pytest.raises(
        freezer.BorealManifestFreezeError,
        match="safe-column declaration drift",
    ):
        freezer.freeze(
            context, token, transport, audit, contract=contract, v071=v071
        )


def test_any_stage_a_semantic_row_access_is_terminal():
    freezer = load_module(SCRIPT, "boreal_manifest_freezer_v078_rows")
    contract, v071, context, token, transport, audit = stage_a_objects()
    audit["data_rows_semantically_opened"] = 1

    with pytest.raises(
        freezer.BorealManifestFreezeError,
        match="header audit boundary mismatch",
    ):
        freezer.freeze(
            context, token, transport, audit, contract=contract, v071=v071
        )


def test_workflow_is_manual_main_only_and_uploads_four_jsons_only():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "\n  push:" not in text
    assert "\n  pull_request:" not in text
    assert "\n  schedule:" not in text
    assert 'test "$GITHUB_REF" = "refs/heads/main"' in text
    assert "persist-credentials: false" in text
    assert "execution_context.json" in text
    assert "rm -rf build/boreal_v078/raw" in text

    upload = text.split("Upload Stage A receipts only", 1)[1]
    assert "build/boreal_v078/raw" not in upload
    for filename in (
        "execution_context.json",
        "token_receipt.json",
        "transport_receipt.json",
        "header_audit.json",
    ):
        assert filename in upload
    assert "retention-days: 7" in upload


def test_v078_status_preserves_zero_fresh_denominator():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))
    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["stage_A_workflow_executed"] is False
    assert boreal["header_manifest_freeze_exists"] is False
    assert boreal["safe_row_projection_executed"] is False
    assert boreal["biological_response_values_opened"] is False
    assert boreal["v0_12_intake_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
