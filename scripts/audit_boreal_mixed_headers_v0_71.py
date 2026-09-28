#!/usr/bin/env python3
"""Header-only audit for the boreal mixed geometry/habitat CSV files.

This stage verifies exact frozen bytes and decodes only the first physical CSV
record. It never projects or summarizes data rows. A successful run authorizes
only a separate repository revision that freezes the resulting header hashes
and manifests.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from structural.mixed_csv_firewall import (
    MixedCSVFirewallError,
    inspect_mixed_csv_header_for_freeze,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_lake_islands_header_freeze_contract_v0_71.json"
)


class BorealHeaderAuditError(RuntimeError):
    pass


def load_contract(path: Path = DEFAULT_CONTRACT) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != (
        "structural.boreal_lake_islands_header_freeze_contract.v0_71"
    ):
        raise BorealHeaderAuditError("unexpected v0.71 contract schema")
    return data


def _audit_one(path: Path, spec: dict) -> dict:
    if not path.is_file():
        raise BorealHeaderAuditError(f"missing local file: {path}")
    expected_size = spec["expected_size_bytes"]
    observed_size = path.stat().st_size
    if observed_size != expected_size:
        raise BorealHeaderAuditError(
            f"{path.name} byte-size mismatch: expected {expected_size}, "
            f"observed {observed_size}"
        )

    audit = inspect_mixed_csv_header_for_freeze(
        path,
        expected_file_sha256=spec["expected_sha256"],
        safe_pre_response_columns=tuple(spec["safe_pre_response_columns"]),
        protected_response_columns=tuple(spec["protected_response_columns"]),
    )
    payload = asdict(audit)
    payload["header"] = list(audit.header)
    for key in (
        "declared_safe_columns",
        "declared_protected_columns",
        "present_safe_columns",
        "missing_safe_columns",
        "present_protected_columns",
        "missing_protected_columns",
        "closed_unclassified_columns",
        "reasons",
    ):
        payload[key] = list(payload[key])

    if audit.qualified_to_freeze_manifest:
        payload["candidate_manifest"] = {
            "file_sha256": audit.file_sha256,
            "header_sha256": audit.header_sha256,
            "safe_pre_response_columns": list(audit.declared_safe_columns),
            "protected_response_columns": list(
                audit.declared_protected_columns
            ),
        }
    else:
        payload["candidate_manifest"] = None
    return payload


def audit(
    alpha_path: Path,
    rda_path: Path,
    *,
    contract: dict | None = None,
) -> dict:
    contract = load_contract() if contract is None else contract
    specs = contract["files"]
    inputs = {
        "alpha_diversity_ALL_islands.csv": alpha_path,
        "RDA_environmental_variables.csv": rda_path,
    }

    results = {}
    for name, path in inputs.items():
        results[name] = _audit_one(path, specs[name])

    qualified = all(
        result["qualified_to_freeze_manifest"] for result in results.values()
    )
    return {
        "schema": "structural.boreal_lake_islands_header_audit_result.v0_71",
        "status": (
            "qualified_to_freeze_header_manifests_only"
            if qualified
            else "STOP_header_classification_mismatch"
        ),
        "candidate_id": contract["candidate_id"],
        "files": results,
        "data_rows_semantically_opened": 0,
        "safe_row_values_opened": False,
        "protected_response_values_opened": False,
        "model_fit_count": 0,
        "counts_as_empirical_evidence": False,
        "safe_row_projection_authorized": False,
        "v0_11_intake_authorized": False,
        "next_action": (
            "commit exact Stage-A header hashes and candidate manifests in a "
            "separate pre-row revision; only that later frozen revision may "
            "authorize safe-row projection"
            if qualified
            else "STOP before data rows; reconcile header declarations only "
            "from response-independent documentation"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("alpha_csv", type=Path)
    parser.add_argument("rda_csv", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        contract = load_contract(args.contract)
        result = audit(args.alpha_csv, args.rda_csv, contract=contract)
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        MixedCSVFirewallError,
        BorealHeaderAuditError,
    ) as exc:
        result = {
            "schema": "structural.boreal_lake_islands_header_audit_result.v0_71",
            "status": "STOP",
            "reason": str(exc),
            "data_rows_semantically_opened": 0,
            "safe_row_values_opened": False,
            "protected_response_values_opened": False,
            "counts_as_empirical_evidence": False,
            "safe_row_projection_authorized": False,
            "v0_11_intake_authorized": False,
        }
        code = 2
    else:
        code = 0 if result["status"].startswith("qualified_") else 2

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
