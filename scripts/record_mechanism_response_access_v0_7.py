#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.authorize_mechanism_response_v0_6 import (  # noqa: E402
    authorize as authorize_response,
)

M1 = "M1_contemporary_colonization"
M2 = "M2_rescue_persistence"
M3 = "M3_historical_colonization_legacy"
M4 = "M4_environmental_proxy"
SCHEMA = "structural.mechanism_response_access_receipt.v0_7"


class MechanismResponseAccessError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MechanismResponseAccessError(
            f"cannot read JSON {path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise MechanismResponseAccessError(
            f"{path} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def require_git_tracked(path: Path, *, label: str) -> str:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise MechanismResponseAccessError(
            f"{label} must live inside repository"
        ) from exc
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", str(relative)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise MechanismResponseAccessError(
            f"{label} must be git-tracked before response access"
        )
    return str(relative)


def _parse_binary_or_missing(value: str, *, field: str) -> int | None:
    text = value.strip()
    if text in {"", "NA", "NaN", "nan", "None"}:
        return None
    if text == "0":
        return 0
    if text == "1":
        return 1
    raise MechanismResponseAccessError(
        f"{field} must be 0/1/blank/NA, got {value!r}"
    )


def _parse_numeric_or_missing(value: str, *, field: str) -> float | None:
    text = value.strip()
    if text in {"", "NA", "NaN", "nan", "None"}:
        return None
    try:
        number = float(text)
    except ValueError as exc:
        raise MechanismResponseAccessError(
            f"{field} must be numeric/blank/NA, got {value!r}"
        ) from exc
    if number != number or number in {float("inf"), float("-inf")}:
        return None
    return number


def _check_partitions(
    seen: set[str],
    allowed: list[str],
) -> None:
    allowed_set = set(allowed)
    extra = sorted(seen - allowed_set)
    missing = sorted(allowed_set - seen)
    if extra:
        raise MechanismResponseAccessError(
            "response contains unauthorized partition units: "
            + ", ".join(extra)
        )
    if missing:
        raise MechanismResponseAccessError(
            "response is missing authorized partition units: "
            + ", ".join(missing)
        )


def _audit_dynamic_response(
    path: Path,
    *,
    lane: str,
    allowed_partitions: list[str],
) -> dict:
    expected_start = 0 if lane == M1 else 1
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = ["partition_unit", "block", "unit_id", "z_t", "z_t1"]
        if reader.fieldnames != required:
            raise MechanismResponseAccessError(
                "dynamic response CSV header must be exactly: "
                + ", ".join(required)
            )
        row_count = 0
        outcome_nonmissing = 0
        seen_units: set[tuple[str, str]] = set()
        partitions: set[str] = set()
        blocks: set[str] = set()
        for row in reader:
            partition = (row.get("partition_unit") or "").strip()
            block = (row.get("block") or "").strip()
            unit = (row.get("unit_id") or "").strip()
            if not partition or not block or not unit:
                raise MechanismResponseAccessError(
                    "dynamic response identifiers must be non-empty"
                )
            key = (partition, unit)
            if key in seen_units:
                raise MechanismResponseAccessError(
                    f"duplicate dynamic response unit: {key}"
                )
            seen_units.add(key)
            z_t = _parse_binary_or_missing(
                row.get("z_t") or "", field="z_t"
            )
            if z_t != expected_start:
                raise MechanismResponseAccessError(
                    f"{lane} response may contain only z_t={expected_start} rows"
                )
            z_t1 = _parse_binary_or_missing(
                row.get("z_t1") or "", field="z_t1"
            )
            outcome_nonmissing += int(z_t1 is not None)
            row_count += 1
            partitions.add(partition)
            blocks.add(block)
    if row_count == 0:
        raise MechanismResponseAccessError("dynamic response file is empty")
    _check_partitions(partitions, allowed_partitions)
    return {
        "surface": "dynamic_transition_response",
        "row_count": row_count,
        "outcome_nonmissing_rows": outcome_nonmissing,
        "outcome_missing_rows": row_count - outcome_nonmissing,
        "blocks": len(blocks),
        "units": len(seen_units),
        "eligible_start_state": expected_start,
    }


def _load_frozen_genetic_pairs(path: Path) -> set[tuple[str, str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = [
            "focal_population",
            "source_population",
            "comparison_class",
        ]
        if reader.fieldnames != required:
            raise MechanismResponseAccessError(
                "genetic pair metadata header drift"
            )
        return {
            (
                (row.get("focal_population") or "").strip(),
                (row.get("source_population") or "").strip(),
                (row.get("comparison_class") or "").strip(),
            )
            for row in reader
        }


def _audit_genetic_response(
    path: Path,
    *,
    allowed_partitions: list[str],
    genetic_pairs_csv: Path,
) -> dict:
    allowed_pairs = _load_frozen_genetic_pairs(genetic_pairs_csv)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = [
            "partition_unit",
            "focal_population",
            "source_population",
            "comparison_class",
            "genetic_value",
        ]
        if reader.fieldnames != required:
            raise MechanismResponseAccessError(
                "M3 response CSV header must be exactly: "
                + ", ".join(required)
            )
        row_count = 0
        nonmissing = 0
        partitions: set[str] = set()
        seen: set[tuple[str, str, str]] = set()
        comparison_counts = {
            "graph_connected": 0,
            "alternative": 0,
        }
        for row in reader:
            partition = (row.get("partition_unit") or "").strip()
            pair = (
                (row.get("focal_population") or "").strip(),
                (row.get("source_population") or "").strip(),
                (row.get("comparison_class") or "").strip(),
            )
            if pair not in allowed_pairs:
                raise MechanismResponseAccessError(
                    f"M3 response contains pair not frozen at qualification: {pair}"
                )
            if pair in seen:
                raise MechanismResponseAccessError(
                    f"duplicate M3 response pair: {pair}"
                )
            seen.add(pair)
            value = _parse_numeric_or_missing(
                row.get("genetic_value") or "",
                field="genetic_value",
            )
            nonmissing += int(value is not None)
            row_count += 1
            partitions.add(partition)
            comparison_counts[pair[2]] += 1
    if row_count == 0:
        raise MechanismResponseAccessError("M3 response file is empty")
    _check_partitions(partitions, allowed_partitions)
    return {
        "surface": "genetic_source_affinity_response",
        "row_count": row_count,
        "outcome_nonmissing_rows": nonmissing,
        "outcome_missing_rows": row_count - nonmissing,
        "unique_pairs": len(seen),
        "comparison_counts": comparison_counts,
    }


def _load_environment_units(
    path: Path,
) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or reader.fieldnames[:2] != [
            "unit_id",
            "block",
        ]:
            raise MechanismResponseAccessError(
                "environment metadata must begin with unit_id,block"
            )
        result: dict[str, str] = {}
        for row in reader:
            unit = (row.get("unit_id") or "").strip()
            block = (row.get("block") or "").strip()
            if not unit or not block:
                raise MechanismResponseAccessError(
                    "environment metadata identifiers must be non-empty"
                )
            if unit in result:
                raise MechanismResponseAccessError(
                    f"duplicate environment unit_id: {unit}"
                )
            result[unit] = block
    return result


def _audit_environment_response(
    path: Path,
    *,
    allowed_partitions: list[str],
    environment_csv: Path,
) -> dict:
    frozen_units = _load_environment_units(environment_csv)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = ["partition_unit", "block", "unit_id", "target"]
        if reader.fieldnames != required:
            raise MechanismResponseAccessError(
                "M4 response CSV header must be exactly: "
                + ", ".join(required)
            )
        row_count = 0
        nonmissing = 0
        partitions: set[str] = set()
        seen: set[str] = set()
        blocks: set[str] = set()
        for row in reader:
            partition = (row.get("partition_unit") or "").strip()
            block = (row.get("block") or "").strip()
            unit = (row.get("unit_id") or "").strip()
            if unit not in frozen_units:
                raise MechanismResponseAccessError(
                    f"M4 response unit not in frozen environment matrix: {unit}"
                )
            if frozen_units[unit] != block:
                raise MechanismResponseAccessError(
                    f"M4 block mismatch for unit {unit}"
                )
            if unit in seen:
                raise MechanismResponseAccessError(
                    f"duplicate M4 response unit: {unit}"
                )
            seen.add(unit)
            target = _parse_binary_or_missing(
                row.get("target") or "", field="target"
            )
            nonmissing += int(target is not None)
            row_count += 1
            partitions.add(partition)
            blocks.add(block)
    if row_count == 0:
        raise MechanismResponseAccessError("M4 response file is empty")
    _check_partitions(partitions, allowed_partitions)
    return {
        "surface": "environmental_proxy_ecological_response",
        "row_count": row_count,
        "outcome_nonmissing_rows": nonmissing,
        "outcome_missing_rows": row_count - nonmissing,
        "units": len(seen),
        "blocks": len(blocks),
    }


def access_id(
    *,
    authorization_id: str,
    response_sha256: str,
    protocol_fingerprint: str,
) -> str:
    payload = json.dumps(
        {
            "authorization_id": authorization_id,
            "response_sha256": response_sha256,
            "protocol_fingerprint": protocol_fingerprint,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def record_access(
    lane_protocol_path: Path,
    authorization_receipt_path: Path,
    scoring_receipt_path: Path,
    scoring_input_csv: Path,
    response_csv: Path,
    mechanism_protocol_path: Path,
    structural_queue_path: Path,
    *,
    transition_pilot_csv: Path | None = None,
    genetic_populations_csv: Path | None = None,
    genetic_pairs_csv: Path | None = None,
    environment_csv: Path | None = None,
    allow_synthetic_structural_queue: bool = False,
    require_tracked_authorization: bool = True,
) -> tuple[int, dict]:
    tracked_authorization: str | None = None
    if require_tracked_authorization:
        try:
            tracked_authorization = require_git_tracked(
                authorization_receipt_path,
                label="v0.6 authorization receipt",
            )
        except MechanismResponseAccessError as exc:
            return 2, {
                "schema": SCHEMA,
                "status": "STOP_authorization_receipt_not_committed",
                "reason": str(exc),
                "scoring_authorized": False,
                "mechanism_claim_authorized": False,
            }

    stored = load_json(authorization_receipt_path)
    freeze_path_text = stored.get("freeze_receipt_path")
    if not isinstance(freeze_path_text, str) or not freeze_path_text.strip():
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_authorization_receipt_missing_freeze_binding",
            "scoring_authorized": False,
            "mechanism_claim_authorized": False,
        }
    freeze_path = ROOT / freeze_path_text

    auth_code, recomputed = authorize_response(
        lane_protocol_path,
        freeze_path,
        scoring_receipt_path,
        scoring_input_csv,
        mechanism_protocol_path,
        structural_queue_path,
        transition_pilot_csv=transition_pilot_csv,
        genetic_populations_csv=genetic_populations_csv,
        genetic_pairs_csv=genetic_pairs_csv,
        environment_csv=environment_csv,
        allow_synthetic_structural_queue=allow_synthetic_structural_queue,
        require_tracked_receipt=True,
        require_tracked_scoring_receipt=True,
    )
    if auth_code != 0:
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_authorization_no_longer_replays",
            "authorization_status": recomputed.get("status"),
            "scoring_authorized": False,
            "mechanism_claim_authorized": False,
        }
    if stored != recomputed:
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_committed_authorization_not_exact_replay",
            "scoring_authorized": False,
            "mechanism_claim_authorized": False,
        }

    if stored.get("single_use") is not True:
        raise MechanismResponseAccessError(
            "authorization must be single-use"
        )
    if stored.get("response_access_consumed") is not False:
        raise MechanismResponseAccessError(
            "authorization already marked consumed"
        )
    if stored.get("confirmatory_response_authorized") is not True:
        raise MechanismResponseAccessError(
            "authorization does not permit response access"
        )
    if stored.get("mechanism_claim_authorized") is not False:
        raise MechanismResponseAccessError(
            "authorization may not already authorize mechanism claim"
        )

    lane = stored.get("mechanism_lane")
    partitions = stored.get("response_partition")
    if not isinstance(partitions, list) or not partitions:
        raise MechanismResponseAccessError(
            "authorization response partition missing"
        )

    try:
        if lane in {M1, M2}:
            audit = _audit_dynamic_response(
                response_csv,
                lane=lane,
                allowed_partitions=partitions,
            )
        elif lane == M3:
            if genetic_pairs_csv is None:
                raise MechanismResponseAccessError(
                    "M3 access requires frozen genetic pair metadata"
                )
            audit = _audit_genetic_response(
                response_csv,
                allowed_partitions=partitions,
                genetic_pairs_csv=genetic_pairs_csv,
            )
        elif lane == M4:
            if environment_csv is None:
                raise MechanismResponseAccessError(
                    "M4 access requires frozen environment metadata"
                )
            audit = _audit_environment_response(
                response_csv,
                allowed_partitions=partitions,
                environment_csv=environment_csv,
            )
        else:
            raise MechanismResponseAccessError(
                f"unknown mechanism lane in authorization: {lane}"
            )
    except MechanismResponseAccessError as exc:
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_invalid_or_unauthorized_response_surface",
            "mechanism_lane": lane,
            "authorization_id": stored.get("authorization_id"),
            "reason": str(exc),
            "response_access_consumed": False,
            "confirmatory_response_authorized": False,
            "scoring_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "mechanism_claim_contribution": 0,
            "ttf_handoff_authorized": False,
        }

    response_sha = sha256_file(response_csv)
    receipt = {
        "schema": SCHEMA,
        "status": "confirmatory_mechanism_response_access_recorded",
        "system_id": stored["system_id"],
        "mechanism_lane": lane,
        "protocol_id": stored["protocol_id"],
        "protocol_fingerprint": stored["protocol_fingerprint"],
        "authorization_id": stored["authorization_id"],
        "authorization_receipt_path": tracked_authorization,
        "authorization_receipt_sha256": sha256_file(
            authorization_receipt_path
        ),
        "scoring_receipt_path": stored["scoring_receipt_path"],
        "scoring_receipt_sha256": stored["scoring_receipt_sha256"],
        "scoring_input_file_sha256": stored["scoring_input_file_sha256"],
        "scoring_input_key_set_sha256": stored["scoring_input_key_set_sha256"],
        "response_partition": partitions,
        "response_file_sha256": response_sha,
        "response_audit": audit,
        "response_access_consumed": True,
        "confirmatory_response_authorized": False,
        "scoring_authorized": True,
        "mechanism_claim_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "mechanism_claim_contribution": 0,
        "ttf_handoff_authorized": False,
        "synthetic_ci_access": stored.get(
            "synthetic_ci_authorization"
        ) is True,
        "counts_as_empirical_evidence": (
            False
            if stored.get("synthetic_ci_authorization") is True
            else None
        ),
        "access_id": access_id(
            authorization_id=stored["authorization_id"],
            response_sha256=response_sha,
            protocol_fingerprint=stored["protocol_fingerprint"],
        ),
        "next_action": "run_frozen_lane_scoring_only",
    }
    return 0, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lane_protocol", type=Path)
    parser.add_argument("authorization_receipt", type=Path)
    parser.add_argument("scoring_receipt", type=Path)
    parser.add_argument("scoring_input_csv", type=Path)
    parser.add_argument("response_csv", type=Path)
    parser.add_argument("mechanism_protocol", type=Path)
    parser.add_argument("structural_queue", type=Path)
    parser.add_argument("--transition-pilot", type=Path)
    parser.add_argument("--genetic-populations", type=Path)
    parser.add_argument("--genetic-pairs", type=Path)
    parser.add_argument("--environment", type=Path)
    parser.add_argument("--allow-synthetic-structural-queue", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        code, payload = record_access(
            args.lane_protocol,
            args.authorization_receipt,
            args.scoring_receipt,
            args.scoring_input_csv,
            args.response_csv,
            args.mechanism_protocol,
            args.structural_queue,
            transition_pilot_csv=args.transition_pilot,
            genetic_populations_csv=args.genetic_populations,
            genetic_pairs_csv=args.genetic_pairs,
            environment_csv=args.environment,
            allow_synthetic_structural_queue=args.allow_synthetic_structural_queue,
            require_tracked_authorization=True,
        )
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        MechanismResponseAccessError,
    ) as exc:
        code, payload = 1, {
            "schema": SCHEMA,
            "status": "invalid_input",
            "reason": str(exc),
            "scoring_authorized": False,
            "mechanism_claim_authorized": False,
        }

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
