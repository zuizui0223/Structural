#!/usr/bin/env python3
"""Verify the frozen v1.13 fresh result without reopening response data."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Mapping

from structural.boreal_confirmatory_scoring import (
    deterministic_block_bootstrap,
    linear_quantile,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULT = (
    ROOT / "development/boreal_19island_confirmatory_scoring_result_v1_14.json"
)
DEFAULT_FREEZE = (
    ROOT / "development/boreal_19island_confirmatory_result_freeze_v1_14.json"
)
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class Boreal19ResultVerificationError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19ResultVerificationError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Mapping) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA64.fullmatch(value):
        raise Boreal19ResultVerificationError(
            f"invalid SHA-256: {label}"
        )
    return value


def verify(
    result: Mapping,
    freeze: Mapping,
    *,
    result_file_sha256: str,
) -> dict:
    if freeze.get("schema") != (
        "structural.boreal_19island_confirmatory_result_freeze.v1_14"
    ):
        raise Boreal19ResultVerificationError("unexpected v1.14 freeze schema")
    if freeze.get("status") != (
        "FRESH_CONFIRMATORY_RESULT_COMMITTED_PRIMARY_NOT_SUPPORTED"
    ):
        raise Boreal19ResultVerificationError("v1.14 freeze status drift")
    if result.get("schema") != (
        "structural.boreal_19island_confirmatory_scoring_result.v1_13"
    ):
        raise Boreal19ResultVerificationError("unexpected scoring-result schema")
    if result.get("status") != (
        "PRIMARY_NOT_SUPPORTED_INTERNAL_SOURCE_ISOLATION_NONREDUNDANT"
    ):
        raise Boreal19ResultVerificationError("source result status drift")

    source_files = freeze.get("source_artifact_files")
    if not isinstance(source_files, dict):
        raise Boreal19ResultVerificationError("source artifact hashes missing")
    if result_file_sha256 != _sha(
        source_files.get("committed_canonical_json_plus_newline_sha256"),
        "committed canonical result",
    ):
        raise Boreal19ResultVerificationError(
            "committed result file SHA mismatch"
        )
    if canonical_sha256(dict(result)) != _sha(
        source_files.get("scoring_result_canonical_json_sha256"),
        "source canonical result",
    ):
        raise Boreal19ResultVerificationError(
            "canonical result fingerprint mismatch"
        )

    parent = freeze.get("frozen_parent_identity")
    if not isinstance(parent, dict):
        raise Boreal19ResultVerificationError("parent identities missing")
    for result_key, freeze_key in (
        ("authorization_fingerprint", "authorization_fingerprint"),
        ("prediction_surface_sha256", "prediction_surface_sha256"),
        ("models_fingerprint", "models_fingerprint"),
        ("response_file_sha256", "response_file_sha256"),
        ("confirmatory_target_surface_sha256", "confirmatory_target_surface_sha256"),
    ):
        if result.get(result_key) != parent.get(freeze_key):
            raise Boreal19ResultVerificationError(
                f"frozen parent identity mismatch: {result_key}"
            )

    for key, expected in (
        ("authorization_consumed", True),
        ("confirmatory_response_opened", True),
        ("confirmatory_response_authorized_after_completion", False),
        ("confirmatory_target_values_parsed", 1287),
        ("pilot_target_values_parsed", 0),
        ("excluded_target_values_parsed", 0),
        ("nonfocal_confirmatory_target_values_parsed", 0),
        ("fixed_species_count", 99),
        ("confirmatory_island_count", 13),
        ("excluded_island_count", 23),
        ("confirmatory_block_count", 7),
        ("counts_as_fresh_confirmatory_evidence", True),
        ("counts_as_primary_confirmatory_evidence", True),
        ("fresh_system_denominator_contribution", 1),
        ("primary_supported", False),
        ("rerun_authorized", False),
        ("secondary_analysis_may_change_primary_status", False),
        ("mechanism_claim_authorized", False),
    ):
        if result.get(key) != expected:
            raise Boreal19ResultVerificationError(
                f"result boundary/accounting mismatch: {key}"
            )

    primary = result.get("primary")
    frozen_primary = freeze.get("primary")
    if not isinstance(primary, dict) or not isinstance(frozen_primary, dict):
        raise Boreal19ResultVerificationError("primary result missing")
    blocks = primary.get("block_summaries")
    if not isinstance(blocks, list) or len(blocks) != 7:
        raise Boreal19ResultVerificationError(
            "primary block summaries are not exact seven-block support"
        )
    block_names = [str(row.get("block", "")) for row in blocks]
    if any(not name for name in block_names) or len(set(block_names)) != 7:
        raise Boreal19ResultVerificationError("invalid primary block identities")

    rows = 0
    positives = 0
    deltas = {}
    ordered_deltas = []
    for row in blocks:
        if not isinstance(row, dict):
            raise Boreal19ResultVerificationError("invalid block summary")
        block = str(row["block"])
        n = int(row["rows"])
        pos = int(row["positive_targets"])
        delta = float.fromhex(str(row["mean_C_minus_R3_hex"]))
        r3 = float.fromhex(str(row["mean_R3_log_loss_hex"]))
        c = float.fromhex(str(row["mean_C_log_loss_hex"]))
        if n < 1 or pos < 0 or pos > n:
            raise Boreal19ResultVerificationError("invalid block target counts")
        if not all(math.isfinite(x) for x in (delta, r3, c)):
            raise Boreal19ResultVerificationError("nonfinite block metric")
        if float(c - r3).hex() != float(delta).hex():
            # Means are frozen independently and may differ by final rounding;
            # require numerical equality at a strict floating tolerance instead.
            if not math.isclose(c - r3, delta, rel_tol=0.0, abs_tol=2e-16):
                raise Boreal19ResultVerificationError(
                    f"block C-minus-R3 inconsistency: {block}"
                )
        rows += n
        positives += pos
        deltas[block] = delta
        ordered_deltas.append(delta)

    if rows != primary.get("row_count") or rows != 1287:
        raise Boreal19ResultVerificationError("primary row total drift")
    if positives != primary.get("positive_targets") or positives != 534:
        raise Boreal19ResultVerificationError("primary positive total drift")

    point = math.fsum(ordered_deltas) / len(ordered_deltas)
    bootstrap = deterministic_block_bootstrap(
        deltas,
        replicates=int(primary["bootstrap_replicates"]),
        seed=int(primary["bootstrap_seed"]),
    )
    lower = linear_quantile(bootstrap, 0.025)
    upper = linear_quantile(bootstrap, 0.975)

    if float(point).hex() != primary.get("point_estimate_hex"):
        raise Boreal19ResultVerificationError("primary point estimate replay drift")
    if float(lower).hex() != primary.get("ci95_lower_hex"):
        raise Boreal19ResultVerificationError("primary lower CI replay drift")
    if float(upper).hex() != primary.get("ci95_upper_hex"):
        raise Boreal19ResultVerificationError("primary upper CI replay drift")

    supported = point < 0.0 and upper < 0.0
    if supported is not False or primary.get("primary_supported") is not False:
        raise Boreal19ResultVerificationError(
            "primary support decision replay drift"
        )
    if not (point > 0.0 and lower > 0.0 and upper > 0.0):
        raise Boreal19ResultVerificationError(
            "frozen not-supported direction no longer strictly positive"
        )

    for key in (
        "point_estimate_hex",
        "ci95_lower_hex",
        "ci95_upper_hex",
        "bootstrap_replicates",
        "bootstrap_seed",
        "quantile_method",
        "primary_supported",
    ):
        if primary.get(key) != frozen_primary.get(key):
            raise Boreal19ResultVerificationError(
                f"freeze/result primary mismatch: {key}"
            )

    return {
        "schema": (
            "structural.boreal_19island_confirmatory_result_verification.v1_14"
        ),
        "status": "VERIFIED_FRESH_RESULT_PRIMARY_NOT_SUPPORTED",
        "candidate_id": result["candidate_id"],
        "source_result_status": result["status"],
        "primary_supported": False,
        "point_estimate_hex": primary["point_estimate_hex"],
        "ci95_lower_hex": primary["ci95_lower_hex"],
        "ci95_upper_hex": primary["ci95_upper_hex"],
        "confirmatory_block_count": 7,
        "confirmatory_target_count": 1287,
        "fresh_system_denominator_contribution": 1,
        "counts_as_fresh_confirmatory_evidence": True,
        "mechanism_claim_authorized": False,
        "secondary_analysis_may_change_primary_status": False,
        "rerun_authorized": False,
        "raw_response_reopened_by_verifier": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = verify(
            _load(args.result),
            _load(args.freeze),
            result_file_sha256=sha256_file(args.result),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        Boreal19ResultVerificationError,
    ) as exc:
        result = {
            "schema": (
                "structural.boreal_19island_confirmatory_result_verification.v1_14"
            ),
            "status": "STOP",
            "reason": str(exc),
            "fresh_system_denominator_contribution": 0,
            "counts_as_fresh_confirmatory_evidence": False,
            "mechanism_claim_authorized": False,
            "rerun_authorized": False,
            "raw_response_reopened_by_verifier": False,
        }
        code = 2
    else:
        code = 0

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
