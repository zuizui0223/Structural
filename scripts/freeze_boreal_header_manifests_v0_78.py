#!/usr/bin/env python3
"""Freeze boreal Stage-A header manifests from JSON-only workflow evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_lake_islands_header_manifest_freeze_contract_v0_78.json"
)
DEFAULT_V071 = (
    ROOT / "development/boreal_lake_islands_header_freeze_contract_v0_71.json"
)
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class BorealManifestFreezeError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BorealManifestFreezeError(f"{path.name} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expect_schema(value: Mapping, schema: str, label: str) -> None:
    if value.get("schema") != schema:
        raise BorealManifestFreezeError(f"unexpected {label} schema")


def freeze(
    execution_context: Mapping,
    token_receipt: Mapping,
    transport_receipt: Mapping,
    header_audit: Mapping,
    *,
    contract: Mapping,
    v071: Mapping,
    input_sha256: Mapping[str, str] | None = None,
) -> dict:
    req = contract["required_input_schemas"]
    _expect_schema(execution_context, req["execution_context"], "execution context")
    _expect_schema(token_receipt, req["token_receipt"], "token receipt")
    _expect_schema(transport_receipt, req["transport_receipt"], "transport receipt")
    _expect_schema(header_audit, req["header_audit"], "header audit")

    wf = contract["workflow_requirements"]
    if execution_context.get("status") != "manual_main_stage_a_execution":
        raise BorealManifestFreezeError("Stage A execution context did not qualify")
    if execution_context.get("repository") != wf["repository"]:
        raise BorealManifestFreezeError("Stage A repository identity mismatch")
    if execution_context.get("ref") != wf["ref"]:
        raise BorealManifestFreezeError("Stage A was not run from main")
    expected_workflow_ref = (
        wf["repository"] + "/" + contract["workflow"] + "@" + wf["ref"]
    )
    if execution_context.get("workflow_ref") != expected_workflow_ref:
        raise BorealManifestFreezeError("Stage A workflow identity mismatch")
    head_sha = execution_context.get("head_sha")
    if not isinstance(head_sha, str) or not SHA40.fullmatch(head_sha):
        raise BorealManifestFreezeError("invalid Stage A head SHA")
    if not isinstance(execution_context.get("run_id"), int) or execution_context["run_id"] < 1:
        raise BorealManifestFreezeError("invalid Stage A run id")
    if not isinstance(execution_context.get("run_attempt"), int) or execution_context["run_attempt"] < 1:
        raise BorealManifestFreezeError("invalid Stage A run attempt")
    if execution_context.get("raw_csv_artifact_authorized") is not False:
        raise BorealManifestFreezeError("raw CSV artifact boundary violated")
    if execution_context.get("counts_as_empirical_evidence") is not False:
        raise BorealManifestFreezeError("execution context evidence boundary violated")

    if token_receipt.get("status") != "token_installed_in_runner_environment":
        raise BorealManifestFreezeError("Dryad token preparation did not qualify")
    if token_receipt.get("token_persisted_in_receipt") is not False:
        raise BorealManifestFreezeError("token receipt secrecy boundary violated")
    if token_receipt.get("client_credentials_persisted_in_receipt") is not False:
        raise BorealManifestFreezeError("client credential secrecy boundary violated")
    if token_receipt.get("counts_as_empirical_evidence") is not False:
        raise BorealManifestFreezeError("token receipt evidence boundary violated")

    if transport_receipt.get("status") != "exact_mixed_file_bytes_verified":
        raise BorealManifestFreezeError("exact transport did not qualify")
    if transport_receipt.get("candidate_id") != contract["candidate_id"]:
        raise BorealManifestFreezeError("transport candidate identity mismatch")
    for key, expected in (
        ("header_decoded", False),
        ("data_rows_semantically_opened", 0),
        ("safe_row_values_opened", False),
        ("biological_response_values_opened", False),
        ("counts_as_empirical_evidence", False),
        ("safe_row_projection_authorized", False),
        ("v0_11_intake_authorized", False),
    ):
        if transport_receipt.get(key) != expected:
            raise BorealManifestFreezeError(
                f"transport boundary mismatch: {key}"
            )

    if header_audit.get("status") != "qualified_to_freeze_header_manifests_only":
        raise BorealManifestFreezeError("header audit did not qualify")
    if header_audit.get("candidate_id") != contract["candidate_id"]:
        raise BorealManifestFreezeError("header-audit candidate identity mismatch")
    for key, expected in (
        ("data_rows_semantically_opened", 0),
        ("safe_row_values_opened", False),
        ("protected_response_values_opened", False),
        ("counts_as_empirical_evidence", False),
        ("safe_row_projection_authorized", False),
        ("v0_11_intake_authorized", False),
    ):
        if header_audit.get(key) != expected:
            raise BorealManifestFreezeError(
                f"header audit boundary mismatch: {key}"
            )

    transport_files = transport_receipt.get("files")
    audit_files = header_audit.get("files")
    if not isinstance(transport_files, dict) or not isinstance(audit_files, dict):
        raise BorealManifestFreezeError("Stage A file evidence missing")

    frozen_files = {}
    for name in contract["file_requirements"]:
        prior = v071["files"].get(name)
        transport = transport_files.get(name)
        audit = audit_files.get(name)
        if not isinstance(prior, dict) or not isinstance(transport, dict) or not isinstance(audit, dict):
            raise BorealManifestFreezeError(f"missing Stage A evidence for {name}")

        expected_sha = prior["expected_sha256"]
        if transport.get("file_id") != prior["dryad_file_id"]:
            raise BorealManifestFreezeError(f"{name} Dryad file ID mismatch")
        if transport.get("size_bytes") != prior["expected_size_bytes"]:
            raise BorealManifestFreezeError(f"{name} transport size mismatch")
        if transport.get("sha256") != expected_sha:
            raise BorealManifestFreezeError(f"{name} transport SHA mismatch")
        if audit.get("file_sha256") != expected_sha:
            raise BorealManifestFreezeError(f"{name} audit file SHA mismatch")

        candidate = audit.get("candidate_manifest")
        if not isinstance(candidate, dict):
            raise BorealManifestFreezeError(f"{name} candidate manifest missing")
        if candidate.get("file_sha256") != expected_sha:
            raise BorealManifestFreezeError(f"{name} candidate file SHA mismatch")
        header_sha = candidate.get("header_sha256")
        if not isinstance(header_sha, str) or not SHA64.fullmatch(header_sha):
            raise BorealManifestFreezeError(f"{name} header SHA invalid")
        if candidate.get("safe_pre_response_columns") != prior["safe_pre_response_columns"]:
            raise BorealManifestFreezeError(f"{name} safe-column declaration drift")
        if candidate.get("protected_response_columns") != prior["protected_response_columns"]:
            raise BorealManifestFreezeError(f"{name} protected-column declaration drift")
        if audit.get("header_sha256") != header_sha:
            raise BorealManifestFreezeError(f"{name} header SHA disagreement")
        if audit.get("missing_safe_columns") not in ([], ()):
            raise BorealManifestFreezeError(f"{name} safe columns missing")
        if audit.get("missing_protected_columns") not in ([], ()):
            raise BorealManifestFreezeError(f"{name} protected columns missing")
        if audit.get("qualified_to_freeze_manifest") is not True:
            raise BorealManifestFreezeError(f"{name} audit not qualified")

        frozen_files[name] = {
            "file_sha256": expected_sha,
            "header_sha256": header_sha,
            "safe_pre_response_columns": list(prior["safe_pre_response_columns"]),
            "protected_response_columns": list(prior["protected_response_columns"]),
            "closed_unclassified_columns": list(
                audit.get("closed_unclassified_columns", [])
            ),
        }

    output = contract["freeze_output"]
    receipt_hashes = dict(input_sha256 or {})
    return {
        "schema": output["schema"],
        "status": output["status"],
        "candidate_id": contract["candidate_id"],
        "stage_a_execution": {
            "repository": execution_context["repository"],
            "head_sha": head_sha,
            "ref": execution_context["ref"],
            "run_id": execution_context["run_id"],
            "run_attempt": execution_context["run_attempt"],
            "workflow": execution_context.get("workflow"),
            "workflow_ref": execution_context.get("workflow_ref"),
        },
        "source_receipt_sha256": receipt_hashes,
        "files": frozen_files,
        "safe_row_projection_authorized": True,
        "row_values_opened_by_freezer": 0,
        "biological_response_values_opened_by_freezer": False,
        "counts_as_empirical_evidence": False,
        "v0_12_intake_authorized": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "next_action": (
            "run v0.74 safe geometry/habitat projection against the exact "
            "Stage-A files in a controlled local execution; v0.12 remains closed"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("execution_context", type=Path)
    parser.add_argument("token_receipt", type=Path)
    parser.add_argument("transport_receipt", type=Path)
    parser.add_argument("header_audit", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--v071", type=Path, default=DEFAULT_V071)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    paths = {
        "execution_context": args.execution_context,
        "token_receipt": args.token_receipt,
        "transport_receipt": args.transport_receipt,
        "header_audit": args.header_audit,
    }
    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_lake_islands_header_manifest_freeze_contract.v0_78"
        ):
            raise BorealManifestFreezeError("unexpected v0.78 contract schema")
        v071 = _load(args.v071)
        result = freeze(
            _load(args.execution_context),
            _load(args.token_receipt),
            _load(args.transport_receipt),
            _load(args.header_audit),
            contract=contract,
            v071=v071,
            input_sha256={name: sha256_file(path) for name, path in paths.items()},
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealManifestFreezeError,
    ) as exc:
        result = {
            "schema": "structural.boreal_lake_islands_header_manifest_freeze.v0_74",
            "status": "STOP",
            "reason": str(exc),
            "safe_row_projection_authorized": False,
            "row_values_opened_by_freezer": 0,
            "biological_response_values_opened_by_freezer": False,
            "counts_as_empirical_evidence": False,
            "v0_12_intake_authorized": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
        }
        code = 2
    else:
        code = 0

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
