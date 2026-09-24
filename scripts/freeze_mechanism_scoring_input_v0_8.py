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

from scripts.freeze_mechanism_confirmatory_protocol_v0_5 import (  # noqa: E402
    freeze as freeze_confirmatory_protocol,
)
from scripts.run_mechanism_admission_v0_4 import M1, M2, M3, M4  # noqa: E402

SCHEMA = "structural.mechanism_scoring_input_freeze_receipt.v0_8"


class MechanismScoringInputFreezeError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MechanismScoringInputFreezeError(
            f"cannot read JSON {path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        raise MechanismScoringInputFreezeError(
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
        raise MechanismScoringInputFreezeError(
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
        raise MechanismScoringInputFreezeError(
            f"{label} must be git-tracked"
        )
    return str(relative)


def _probability(value: str, *, field: str) -> float:
    try:
        x = float(value)
    except ValueError as exc:
        raise MechanismScoringInputFreezeError(
            f"{field} must be numeric"
        ) from exc
    if not (0.0 < x < 1.0):
        raise MechanismScoringInputFreezeError(
            f"{field} must be strictly between 0 and 1"
        )
    return x


def _positive_weight(value: str) -> float:
    try:
        x = float(value)
    except ValueError as exc:
        raise MechanismScoringInputFreezeError(
            "M3 weight must be numeric"
        ) from exc
    if not (x > 0.0) or x != x or x == float("inf"):
        raise MechanismScoringInputFreezeError(
            "M3 weight must be finite and >0"
        )
    return x


def _key_hash(keys: list[str]) -> str:
    payload = "\n".join(sorted(keys)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _check_partitions(seen: set[str], expected: list[str]) -> None:
    expected_set = set(expected)
    if seen != expected_set:
        raise MechanismScoringInputFreezeError(
            "scoring input partitions must equal frozen response partition exactly"
        )


def _audit_dynamic(
    path: Path,
    *,
    response_partition: list[str],
) -> dict:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = [
            "partition_unit",
            "block",
            "unit_id",
            "p_reference",
            "p_candidate",
        ]
        if reader.fieldnames != required:
            raise MechanismScoringInputFreezeError(
                "dynamic scoring input header must be exactly: "
                + ", ".join(required)
            )
        keys: list[str] = []
        seen_keys: set[tuple[str, str]] = set()
        partitions: set[str] = set()
        blocks: set[str] = set()
        for row in reader:
            partition = (row.get("partition_unit") or "").strip()
            block = (row.get("block") or "").strip()
            unit = (row.get("unit_id") or "").strip()
            if not partition or not block or not unit:
                raise MechanismScoringInputFreezeError(
                    "dynamic scoring identifiers must be non-empty"
                )
            key = (partition, unit)
            if key in seen_keys:
                raise MechanismScoringInputFreezeError(
                    f"duplicate dynamic scoring unit: {key}"
                )
            seen_keys.add(key)
            _probability(row.get("p_reference") or "", field="p_reference")
            _probability(row.get("p_candidate") or "", field="p_candidate")
            keys.append(f"{partition}\t{block}\t{unit}")
            partitions.add(partition)
            blocks.add(block)
    if not keys:
        raise MechanismScoringInputFreezeError(
            "dynamic scoring input is empty"
        )
    _check_partitions(partitions, response_partition)
    return {
        "surface": "frozen_dynamic_prediction_surface",
        "row_count": len(keys),
        "unit_count": len(seen_keys),
        "block_count": len(blocks),
        "key_set_sha256": _key_hash(keys),
    }


def _load_frozen_pairs(path: Path) -> set[tuple[str, str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = [
            "focal_population",
            "source_population",
            "comparison_class",
        ]
        if reader.fieldnames != required:
            raise MechanismScoringInputFreezeError(
                "frozen genetic pair metadata header drift"
            )
        return {
            (
                (row.get("focal_population") or "").strip(),
                (row.get("source_population") or "").strip(),
                (row.get("comparison_class") or "").strip(),
            )
            for row in reader
        }


def _audit_m3(path: Path, *, genetic_pairs_csv: Path) -> dict:
    frozen = _load_frozen_pairs(genetic_pairs_csv)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = [
            "focal_population",
            "source_population",
            "comparison_class",
            "weight",
        ]
        if reader.fieldnames != required:
            raise MechanismScoringInputFreezeError(
                "M3 scoring design header must be exactly: "
                + ", ".join(required)
            )
        seen: set[tuple[str, str, str]] = set()
        keys: list[str] = []
        total_weight = 0.0
        for row in reader:
            key = (
                (row.get("focal_population") or "").strip(),
                (row.get("source_population") or "").strip(),
                (row.get("comparison_class") or "").strip(),
            )
            if key not in frozen:
                raise MechanismScoringInputFreezeError(
                    f"M3 scoring design contains unfrozen pair: {key}"
                )
            if key in seen:
                raise MechanismScoringInputFreezeError(
                    f"duplicate M3 scoring pair: {key}"
                )
            seen.add(key)
            weight = _positive_weight(row.get("weight") or "")
            total_weight += weight
            keys.append("\t".join(key))
    if seen != frozen:
        raise MechanismScoringInputFreezeError(
            "M3 scoring design must contain the exact frozen pair set"
        )
    return {
        "surface": "frozen_genetic_scoring_design",
        "row_count": len(seen),
        "pair_count": len(seen),
        "total_weight": total_weight,
        "key_set_sha256": _key_hash(keys),
    }


def _load_environment_units(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or reader.fieldnames[:2] != [
            "unit_id",
            "block",
        ]:
            raise MechanismScoringInputFreezeError(
                "environment metadata must begin with unit_id,block"
            )
        result: dict[str, str] = {}
        for row in reader:
            unit = (row.get("unit_id") or "").strip()
            block = (row.get("block") or "").strip()
            if not unit or not block:
                raise MechanismScoringInputFreezeError(
                    "environment identifiers must be non-empty"
                )
            if unit in result:
                raise MechanismScoringInputFreezeError(
                    f"duplicate environment unit: {unit}"
                )
            result[unit] = block
    return result


def _audit_m4(
    path: Path,
    *,
    response_partition: list[str],
    environment_csv: Path,
) -> dict:
    frozen_units = _load_environment_units(environment_csv)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = [
            "partition_unit",
            "block",
            "unit_id",
            "p_original_reference",
            "p_original_topology",
            "p_enriched_reference",
            "p_enriched_topology",
        ]
        if reader.fieldnames != required:
            raise MechanismScoringInputFreezeError(
                "M4 scoring input header must be exactly: "
                + ", ".join(required)
            )
        seen_units: set[str] = set()
        partitions: set[str] = set()
        keys: list[str] = []
        blocks: set[str] = set()
        for row in reader:
            partition = (row.get("partition_unit") or "").strip()
            block = (row.get("block") or "").strip()
            unit = (row.get("unit_id") or "").strip()
            if unit not in frozen_units:
                raise MechanismScoringInputFreezeError(
                    f"M4 scoring unit not in frozen environment matrix: {unit}"
                )
            if frozen_units[unit] != block:
                raise MechanismScoringInputFreezeError(
                    f"M4 scoring block mismatch for unit {unit}"
                )
            if unit in seen_units:
                raise MechanismScoringInputFreezeError(
                    f"duplicate M4 scoring unit: {unit}"
                )
            seen_units.add(unit)
            for field in (
                "p_original_reference",
                "p_original_topology",
                "p_enriched_reference",
                "p_enriched_topology",
            ):
                _probability(row.get(field) or "", field=field)
            partitions.add(partition)
            blocks.add(block)
            keys.append(f"{partition}\t{block}\t{unit}")
    if not keys:
        raise MechanismScoringInputFreezeError(
            "M4 scoring input is empty"
        )
    _check_partitions(partitions, response_partition)
    return {
        "surface": "frozen_environmental_proxy_prediction_surface",
        "row_count": len(keys),
        "unit_count": len(seen_units),
        "block_count": len(blocks),
        "key_set_sha256": _key_hash(keys),
    }


def freeze_scoring_input(
    lane_protocol_path: Path,
    freeze_receipt_path: Path,
    scoring_input_csv: Path,
    mechanism_protocol_path: Path,
    structural_queue_path: Path,
    *,
    transition_pilot_csv: Path | None = None,
    genetic_populations_csv: Path | None = None,
    genetic_pairs_csv: Path | None = None,
    environment_csv: Path | None = None,
    allow_synthetic_structural_queue: bool = False,
    require_tracked_freeze_receipt: bool = True,
) -> tuple[int, dict]:
    tracked_freeze: str | None = None
    if require_tracked_freeze_receipt:
        try:
            tracked_freeze = require_git_tracked(
                freeze_receipt_path,
                label="v0.5 freeze receipt",
            )
        except MechanismScoringInputFreezeError as exc:
            return 2, {
                "schema": SCHEMA,
                "status": "STOP_freeze_receipt_not_committed",
                "reason": str(exc),
                "confirmatory_response_authorized": False,
                "scoring_input_frozen": False,
            }

    stored = load_json(freeze_receipt_path)
    code, recomputed = freeze_confirmatory_protocol(
        lane_protocol_path,
        mechanism_protocol_path,
        structural_queue_path,
        transition_pilot_csv=transition_pilot_csv,
        genetic_populations_csv=genetic_populations_csv,
        genetic_pairs_csv=genetic_pairs_csv,
        environment_csv=environment_csv,
        allow_synthetic_structural_queue=allow_synthetic_structural_queue,
    )
    if code != 0 or stored != recomputed:
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_freeze_receipt_not_exact_replay",
            "confirmatory_response_authorized": False,
            "scoring_input_frozen": False,
        }

    if stored.get("confirmatory_response_authorized") is not False:
        raise MechanismScoringInputFreezeError(
            "scoring inputs must freeze before response authorization"
        )

    lane = stored["mechanism_lane"]
    partitions = stored["response_partition"]
    try:
        if lane in {M1, M2}:
            audit = _audit_dynamic(
                scoring_input_csv,
                response_partition=partitions,
            )
        elif lane == M3:
            if genetic_pairs_csv is None:
                raise MechanismScoringInputFreezeError(
                    "M3 scoring input freeze requires frozen genetic pairs"
                )
            audit = _audit_m3(
                scoring_input_csv,
                genetic_pairs_csv=genetic_pairs_csv,
            )
        elif lane == M4:
            if environment_csv is None:
                raise MechanismScoringInputFreezeError(
                    "M4 scoring input freeze requires frozen environment matrix"
                )
            audit = _audit_m4(
                scoring_input_csv,
                response_partition=partitions,
                environment_csv=environment_csv,
            )
        else:
            raise MechanismScoringInputFreezeError(
                f"unknown mechanism lane: {lane}"
            )
    except MechanismScoringInputFreezeError as exc:
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_invalid_or_unauthorized_scoring_input",
            "mechanism_lane": lane,
            "reason": str(exc),
            "scoring_input_frozen": False,
            "confirmatory_response_authorized": False,
            "mechanism_claim_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "mechanism_claim_contribution": 0,
            "ttf_handoff_authorized": False,
        }

    scoring_sha = sha256_file(scoring_input_csv)
    receipt = {
        "schema": SCHEMA,
        "status": "mechanism_scoring_inputs_frozen_before_response",
        "system_id": stored["system_id"],
        "mechanism_lane": lane,
        "protocol_id": stored["protocol_id"],
        "protocol_fingerprint": stored["protocol_fingerprint"],
        "freeze_receipt_path": tracked_freeze,
        "freeze_receipt_sha256": sha256_file(freeze_receipt_path),
        "scoring_input_file_sha256": scoring_sha,
        "scoring_input_audit": audit,
        "response_partition": partitions,
        "scoring_input_frozen": True,
        "confirmatory_response_authorized": False,
        "mechanism_claim_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "mechanism_claim_contribution": 0,
        "ttf_handoff_authorized": False,
        "synthetic_ci_freeze": allow_synthetic_structural_queue,
        "counts_as_empirical_evidence": (
            False if allow_synthetic_structural_queue else None
        ),
        "next_action": "run_v0_6_response_authorization_only",
    }
    return 0, receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lane_protocol", type=Path)
    parser.add_argument("freeze_receipt", type=Path)
    parser.add_argument("scoring_input_csv", type=Path)
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
        code, payload = freeze_scoring_input(
            args.lane_protocol,
            args.freeze_receipt,
            args.scoring_input_csv,
            args.mechanism_protocol,
            args.structural_queue,
            transition_pilot_csv=args.transition_pilot,
            genetic_populations_csv=args.genetic_populations,
            genetic_pairs_csv=args.genetic_pairs,
            environment_csv=args.environment,
            allow_synthetic_structural_queue=args.allow_synthetic_structural_queue,
            require_tracked_freeze_receipt=True,
        )
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        MechanismScoringInputFreezeError,
    ) as exc:
        code, payload = 1, {
            "schema": SCHEMA,
            "status": "invalid_input",
            "reason": str(exc),
            "confirmatory_response_authorized": False,
            "scoring_input_frozen": False,
        }

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
