#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from scripts.record_mechanism_response_access_v0_7 import (  # noqa: E402
    record_access,
)

M1 = "M1_contemporary_colonization"
M2 = "M2_rescue_persistence"
M3 = "M3_historical_colonization_legacy"
M4 = "M4_environmental_proxy"
SCHEMA = "structural.mechanism_lane_score.v0_9"


class MechanismScoringError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MechanismScoringError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MechanismScoringError(f"{path} must contain a JSON object")
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
        raise MechanismScoringError(f"{label} must live inside repository") from exc
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", str(relative)],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise MechanismScoringError(f"{label} must be git-tracked before scoring")
    return str(relative)


def _binary_or_missing(value: str, *, field: str) -> int | None:
    text = value.strip()
    if text in {"", "NA", "NaN", "nan", "None"}:
        return None
    if text == "0":
        return 0
    if text == "1":
        return 1
    raise MechanismScoringError(f"{field} must be 0/1/blank/NA")


def _numeric_or_missing(value: str, *, field: str) -> float | None:
    text = value.strip()
    if text in {"", "NA", "NaN", "nan", "None"}:
        return None
    try:
        x = float(text)
    except ValueError as exc:
        raise MechanismScoringError(f"{field} must be numeric/blank/NA") from exc
    if not math.isfinite(x):
        return None
    return x


def _probability(value: str, *, field: str) -> float:
    try:
        x = float(value)
    except ValueError as exc:
        raise MechanismScoringError(f"{field} must be numeric") from exc
    if not 0.0 < x < 1.0:
        raise MechanismScoringError(f"{field} must be strictly between 0 and 1")
    return x


def _log_loss(y: int, p: float) -> float:
    return -(y * math.log(p) + (1 - y) * math.log(1.0 - p))


def _mean(values: list[float]) -> float:
    if not values:
        raise MechanismScoringError("cannot score empty value list")
    return sum(values) / len(values)


def _score_dynamic(
    scoring_csv: Path,
    response_csv: Path,
    *,
    lane: str,
) -> dict:
    scoring: dict[tuple[str, str], tuple[str, float, float]] = {}
    with scoring_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = [
            "partition_unit",
            "block",
            "unit_id",
            "p_reference",
            "p_candidate",
        ]
        if reader.fieldnames != required:
            raise MechanismScoringError("dynamic scoring input header drift")
        for row in reader:
            partition = (row["partition_unit"] or "").strip()
            block = (row["block"] or "").strip()
            unit = (row["unit_id"] or "").strip()
            key = (partition, unit)
            if key in scoring:
                raise MechanismScoringError(f"duplicate scoring key: {key}")
            scoring[key] = (
                block,
                _probability(row["p_reference"], field="p_reference"),
                _probability(row["p_candidate"], field="p_candidate"),
            )

    response: dict[tuple[str, str], tuple[str, int, int | None]] = {}
    with response_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = ["partition_unit", "block", "unit_id", "z_t", "z_t1"]
        if reader.fieldnames != required:
            raise MechanismScoringError("dynamic response header drift")
        expected_start = 0 if lane == M1 else 1
        for row in reader:
            partition = (row["partition_unit"] or "").strip()
            block = (row["block"] or "").strip()
            unit = (row["unit_id"] or "").strip()
            key = (partition, unit)
            if key in response:
                raise MechanismScoringError(f"duplicate response key: {key}")
            z_t = _binary_or_missing(row["z_t"], field="z_t")
            if z_t != expected_start:
                raise MechanismScoringError(
                    f"{lane} response start-state drift"
                )
            response[key] = (
                block,
                z_t,
                _binary_or_missing(row["z_t1"], field="z_t1"),
            )

    if set(scoring) != set(response):
        raise MechanismScoringError(
            "dynamic scoring and response unit sets must match exactly"
        )

    ref_losses: list[float] = []
    cand_losses: list[float] = []
    deltas: list[float] = []
    by_block: dict[str, list[float]] = defaultdict(list)
    missing = 0

    for key in sorted(scoring):
        s_block, p_ref, p_cand = scoring[key]
        r_block, _, z_t1 = response[key]
        if s_block != r_block:
            raise MechanismScoringError(f"block mismatch for {key}")
        if z_t1 is None:
            missing += 1
            continue
        y = z_t1 if lane == M1 else 1 - z_t1
        ref = _log_loss(y, p_ref)
        cand = _log_loss(y, p_cand)
        delta = cand - ref
        ref_losses.append(ref)
        cand_losses.append(cand)
        deltas.append(delta)
        by_block[s_block].append(delta)

    if not deltas:
        return {
            "estimable": False,
            "reason": "no_nonmissing_confirmatory_outcomes",
            "row_count": len(response),
            "nonmissing_scored_rows": 0,
            "missing_outcome_rows": missing,
        }

    return {
        "estimable": True,
        "target_event": "0_to_1" if lane == M1 else "1_to_0",
        "row_count": len(response),
        "nonmissing_scored_rows": len(deltas),
        "missing_outcome_rows": missing,
        "reference_mean_log_loss": _mean(ref_losses),
        "candidate_mean_log_loss": _mean(cand_losses),
        "candidate_minus_reference_log_loss": _mean(deltas),
        "block_candidate_minus_reference_log_loss": {
            block: _mean(values)
            for block, values in sorted(by_block.items())
        },
    }


def _score_m3(scoring_csv: Path, response_csv: Path) -> dict:
    weights: dict[tuple[str, str, str], float] = {}
    with scoring_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = [
            "focal_population",
            "source_population",
            "comparison_class",
            "weight",
        ]
        if reader.fieldnames != required:
            raise MechanismScoringError("M3 scoring design header drift")
        for row in reader:
            key = (
                (row["focal_population"] or "").strip(),
                (row["source_population"] or "").strip(),
                (row["comparison_class"] or "").strip(),
            )
            if key in weights:
                raise MechanismScoringError(f"duplicate M3 scoring pair: {key}")
            weight = float(row["weight"])
            if not math.isfinite(weight) or weight <= 0:
                raise MechanismScoringError("M3 scoring weight drift")
            weights[key] = weight

    values: dict[tuple[str, str, str], float | None] = {}
    with response_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = [
            "partition_unit",
            "focal_population",
            "source_population",
            "comparison_class",
            "genetic_value",
        ]
        if reader.fieldnames != required:
            raise MechanismScoringError("M3 response header drift")
        for row in reader:
            key = (
                (row["focal_population"] or "").strip(),
                (row["source_population"] or "").strip(),
                (row["comparison_class"] or "").strip(),
            )
            if key in values:
                raise MechanismScoringError(f"duplicate M3 response pair: {key}")
            values[key] = _numeric_or_missing(
                row["genetic_value"], field="genetic_value"
            )

    if set(weights) != set(values):
        raise MechanismScoringError(
            "M3 scoring and response pair sets must match exactly"
        )

    numerator = {"graph_connected": 0.0, "alternative": 0.0}
    denominator = {"graph_connected": 0.0, "alternative": 0.0}
    count = {"graph_connected": 0, "alternative": 0}
    missing = 0

    for key in sorted(weights):
        cls = key[2]
        if cls not in numerator:
            raise MechanismScoringError(f"unexpected M3 comparison class: {cls}")
        value = values[key]
        if value is None:
            missing += 1
            continue
        weight = weights[key]
        numerator[cls] += weight * value
        denominator[cls] += weight
        count[cls] += 1

    if denominator["graph_connected"] == 0 or denominator["alternative"] == 0:
        return {
            "estimable": False,
            "reason": "one_or_more_M3_comparison_classes_have_no_nonmissing_outcome",
            "row_count": len(values),
            "missing_outcome_rows": missing,
        }

    connected = numerator["graph_connected"] / denominator["graph_connected"]
    alternative = numerator["alternative"] / denominator["alternative"]
    return {
        "estimable": True,
        "row_count": len(values),
        "nonmissing_scored_rows": sum(count.values()),
        "missing_outcome_rows": missing,
        "graph_connected_weighted_mean_genetic_value": connected,
        "alternative_weighted_mean_genetic_value": alternative,
        "graph_connected_minus_alternative_genetic_value": connected - alternative,
        "nonmissing_pairs_by_class": count,
        "weight_sum_by_class": denominator,
    }


def _score_m4(scoring_csv: Path, response_csv: Path) -> dict:
    scoring: dict[tuple[str, str], tuple[str, float, float, float, float]] = {}
    with scoring_csv.open("r", encoding="utf-8-sig", newline="") as handle:
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
            raise MechanismScoringError("M4 scoring input header drift")
        for row in reader:
            partition = (row["partition_unit"] or "").strip()
            block = (row["block"] or "").strip()
            unit = (row["unit_id"] or "").strip()
            key = (partition, unit)
            if key in scoring:
                raise MechanismScoringError(f"duplicate M4 scoring unit: {key}")
            scoring[key] = (
                block,
                _probability(row["p_original_reference"], field="p_original_reference"),
                _probability(row["p_original_topology"], field="p_original_topology"),
                _probability(row["p_enriched_reference"], field="p_enriched_reference"),
                _probability(row["p_enriched_topology"], field="p_enriched_topology"),
            )

    response: dict[tuple[str, str], tuple[str, int | None]] = {}
    with response_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = ["partition_unit", "block", "unit_id", "target"]
        if reader.fieldnames != required:
            raise MechanismScoringError("M4 response header drift")
        for row in reader:
            partition = (row["partition_unit"] or "").strip()
            block = (row["block"] or "").strip()
            unit = (row["unit_id"] or "").strip()
            key = (partition, unit)
            if key in response:
                raise MechanismScoringError(f"duplicate M4 response unit: {key}")
            response[key] = (
                block,
                _binary_or_missing(row["target"], field="target"),
            )

    if set(scoring) != set(response):
        raise MechanismScoringError(
            "M4 scoring and response unit sets must match exactly"
        )

    losses = {
        "original_reference": [],
        "original_topology": [],
        "enriched_reference": [],
        "enriched_topology": [],
    }
    missing = 0
    by_block: dict[str, list[float]] = defaultdict(list)

    for key in sorted(scoring):
        s_block, p_or, p_ot, p_er, p_et = scoring[key]
        r_block, target = response[key]
        if s_block != r_block:
            raise MechanismScoringError(f"M4 block mismatch for {key}")
        if target is None:
            missing += 1
            continue
        row_losses = {
            "original_reference": _log_loss(target, p_or),
            "original_topology": _log_loss(target, p_ot),
            "enriched_reference": _log_loss(target, p_er),
            "enriched_topology": _log_loss(target, p_et),
        }
        for name, value in row_losses.items():
            losses[name].append(value)
        by_block[s_block].append(
            (row_losses["enriched_topology"] - row_losses["enriched_reference"])
            - (row_losses["original_topology"] - row_losses["original_reference"])
        )

    if not losses["original_reference"]:
        return {
            "estimable": False,
            "reason": "no_nonmissing_confirmatory_outcomes",
            "row_count": len(response),
            "nonmissing_scored_rows": 0,
            "missing_outcome_rows": missing,
        }

    means = {name: _mean(values) for name, values in losses.items()}
    original_topology_increment = (
        means["original_topology"] - means["original_reference"]
    )
    enriched_topology_increment = (
        means["enriched_topology"] - means["enriched_reference"]
    )
    enriched_reference_increment = (
        means["enriched_reference"] - means["original_reference"]
    )
    topology_increment_change = (
        enriched_topology_increment - original_topology_increment
    )
    return {
        "estimable": True,
        "row_count": len(response),
        "nonmissing_scored_rows": len(losses["original_reference"]),
        "missing_outcome_rows": missing,
        "mean_log_loss": means,
        "original_topology_increment": original_topology_increment,
        "enriched_topology_increment": enriched_topology_increment,
        "enriched_reference_minus_original_reference_log_loss":
            enriched_reference_increment,
        "enriched_minus_original_topology_increment_change":
            topology_increment_change,
        "block_topology_increment_change": {
            block: _mean(values)
            for block, values in sorted(by_block.items())
        },
    }


def _score_id(
    *,
    access_receipt_sha256: str,
    scoring_input_sha256: str,
    response_sha256: str,
    metric_payload: dict,
) -> str:
    payload = json.dumps(
        {
            "access_receipt_sha256": access_receipt_sha256,
            "scoring_input_sha256": scoring_input_sha256,
            "response_sha256": response_sha256,
            "metric_payload": metric_payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def score_lane(
    lane_protocol_path: Path,
    access_receipt_path: Path,
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
) -> tuple[int, dict]:
    try:
        tracked_access = require_git_tracked(
            access_receipt_path,
            label="v0.7 response-access receipt",
        )
    except MechanismScoringError as exc:
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_access_receipt_not_committed",
            "reason": str(exc),
            "mechanism_claim_authorized": False,
        }

    stored = load_json(access_receipt_path)
    auth_path_text = stored.get("authorization_receipt_path")
    if not isinstance(auth_path_text, str) or not auth_path_text.strip():
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_access_receipt_missing_authorization_binding",
            "mechanism_claim_authorized": False,
        }
    auth_path = ROOT / auth_path_text

    access_code, recomputed = record_access(
        lane_protocol_path,
        auth_path,
        scoring_receipt_path,
        scoring_input_csv,
        response_csv,
        mechanism_protocol_path,
        structural_queue_path,
        transition_pilot_csv=transition_pilot_csv,
        genetic_populations_csv=genetic_populations_csv,
        genetic_pairs_csv=genetic_pairs_csv,
        environment_csv=environment_csv,
        allow_synthetic_structural_queue=allow_synthetic_structural_queue,
        require_tracked_authorization=True,
    )
    if access_code != 0 or stored != recomputed:
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_access_receipt_not_exact_replay",
            "replayed_status": recomputed.get("status"),
            "mechanism_claim_authorized": False,
        }

    if stored.get("scoring_authorized") is not True:
        raise MechanismScoringError("v0.7 receipt does not authorize scoring")
    if stored.get("response_access_consumed") is not True:
        raise MechanismScoringError("response access has not been consumed")
    if stored.get("mechanism_claim_authorized") is not False:
        raise MechanismScoringError("mechanism claim unexpectedly pre-authorized")

    if sha256_file(scoring_input_csv) != stored.get("scoring_input_file_sha256"):
        raise MechanismScoringError("scoring input SHA mismatch")
    if sha256_file(response_csv) != stored.get("response_file_sha256"):
        raise MechanismScoringError("response SHA mismatch")

    lane = stored["mechanism_lane"]
    try:
        if lane in {M1, M2}:
            metric = _score_dynamic(scoring_input_csv, response_csv, lane=lane)
            primary_metric_name = "candidate_minus_reference_log_loss"
            primary_metric = (
                metric.get("candidate_minus_reference_log_loss")
                if metric.get("estimable")
                else None
            )
            effect_size = None
            prediction_score = primary_metric
            adjudication_blockers = ["separate_spatial_transfer_not_combined"]
        elif lane == M3:
            metric = _score_m3(scoring_input_csv, response_csv)
            primary_metric_name = (
                "graph_connected_minus_alternative_genetic_value"
            )
            primary_metric = (
                metric.get("graph_connected_minus_alternative_genetic_value")
                if metric.get("estimable")
                else None
            )
            effect_size = primary_metric
            prediction_score = None
            adjudication_blockers = [
                "predeclared_geographic_spatial_null_adjudication_not_combined"
            ]
        elif lane == M4:
            metric = _score_m4(scoring_input_csv, response_csv)
            primary_metric_name = (
                "enriched_minus_original_topology_increment_change"
            )
            primary_metric = (
                metric.get("enriched_minus_original_topology_increment_change")
                if metric.get("estimable")
                else None
            )
            effect_size = primary_metric
            prediction_score = None
            adjudication_blockers = [
                "practical_null_interval_not_machine_frozen",
                "separate_spatial_transfer_not_combined",
            ]
        else:
            raise MechanismScoringError(f"unknown mechanism lane: {lane}")
    except MechanismScoringError as exc:
        return 2, {
            "schema": SCHEMA,
            "status": "STOP_scoring_surface_or_join_violation",
            "mechanism_lane": lane,
            "reason": str(exc),
            "mechanism_claim_authorized": False,
        }

    estimable = metric.get("estimable") is True
    access_sha = sha256_file(access_receipt_path)
    score_id = _score_id(
        access_receipt_sha256=access_sha,
        scoring_input_sha256=stored["scoring_input_file_sha256"],
        response_sha256=stored["response_file_sha256"],
        metric_payload=metric,
    )

    return 0, {
        "schema": SCHEMA,
        "status": (
            "scored_confirmatory_mechanism_lane_no_claim_adjudication"
            if estimable
            else "confirmatory_mechanism_lane_non_estimable_after_response"
        ),
        "system_id": stored["system_id"],
        "mechanism_lane": lane,
        "protocol_id": stored["protocol_id"],
        "protocol_fingerprint": stored["protocol_fingerprint"],
        "access_id": stored["access_id"],
        "access_receipt_path": tracked_access,
        "access_receipt_sha256": access_sha,
        "scoring_input_file_sha256": stored["scoring_input_file_sha256"],
        "response_file_sha256": stored["response_file_sha256"],
        "primary_metric_name": primary_metric_name,
        "primary_metric": primary_metric,
        "metric_details": metric,
        "effect_size": effect_size,
        "prediction_score": prediction_score,
        "scored_lane_contribution": 1 if estimable else 0,
        "mechanism_claim_contribution": 0,
        "mechanism_claim_authorized": False,
        "ttf_handoff_authorized": False,
        "counts_as_empirical_evidence": (
            False if stored.get("synthetic_ci_access") is True else None
        ),
        "synthetic_ci_score": stored.get("synthetic_ci_access") is True,
        "adjudication_blockers": adjudication_blockers,
        "score_id": score_id,
        "next_action": (
            "combine_with_predeclared_transfer_or_null_evidence_then_adjudicate_claim"
            if estimable
            else "record_non_estimable_lane_without_mechanism_claim"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("lane_protocol", type=Path)
    parser.add_argument("access_receipt", type=Path)
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
        code, payload = score_lane(
            args.lane_protocol,
            args.access_receipt,
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
        )
    except (OSError, ValueError, json.JSONDecodeError, MechanismScoringError) as exc:
        code, payload = 1, {
            "schema": SCHEMA,
            "status": "invalid_input",
            "reason": str(exc),
            "mechanism_claim_authorized": False,
        }

    text = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
