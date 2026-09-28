"""Deterministic confirmatory scoring for the boreal dual-isolation test."""
from __future__ import annotations

import csv
import hashlib
import io
import math
from collections import defaultdict
from typing import Mapping, Sequence


class BorealConfirmatoryScoringError(RuntimeError):
    pass


PREDICTION_HEADER = (
    "island",
    "block",
    "species",
    "p_R0_hex",
    "p_R1_hex",
    "p_R2_hex",
    "p_R3_hex",
    "p_C_hex",
)
TARGET_HEADER = ("island", "block", "species", "target")


def _parse_probability(value: str, *, label: str) -> float:
    text = str(value).strip()
    try:
        out = (
            float.fromhex(text)
            if text.lower().startswith(("0x", "+0x", "-0x"))
            else float(text)
        )
    except ValueError as exc:
        raise BorealConfirmatoryScoringError(
            f"{label} is not numeric"
        ) from exc
    if not math.isfinite(out) or not 0.0 < out < 1.0:
        raise BorealConfirmatoryScoringError(
            f"{label} must be finite and strictly inside (0,1)"
        )
    return out


def parse_prediction_surface(text: str) -> dict[tuple[str, str, str], dict[str, float]]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or tuple(reader.fieldnames) != PREDICTION_HEADER:
        raise BorealConfirmatoryScoringError(
            "unexpected frozen prediction-surface header"
        )
    out = {}
    for row in reader:
        key = (
            str(row["island"]).strip(),
            str(row["block"]).strip(),
            str(row["species"]).strip(),
        )
        if any(not x for x in key):
            raise BorealConfirmatoryScoringError(
                "blank prediction key field"
            )
        if key in out:
            raise BorealConfirmatoryScoringError(
                f"duplicate prediction key: {key}"
            )
        out[key] = {
            name: _parse_probability(
                row[f"p_{name}_hex"],
                label=f"{key}.{name}",
            )
            for name in ("R0", "R1", "R2", "R3", "C")
        }
    if not out:
        raise BorealConfirmatoryScoringError(
            "empty frozen prediction surface"
        )
    return out


def parse_target_surface(text: str) -> dict[tuple[str, str, str], int]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or tuple(reader.fieldnames) != TARGET_HEADER:
        raise BorealConfirmatoryScoringError(
            "unexpected confirmatory target-surface header"
        )
    out = {}
    for row in reader:
        key = (
            str(row["island"]).strip(),
            str(row["block"]).strip(),
            str(row["species"]).strip(),
        )
        if any(not x for x in key):
            raise BorealConfirmatoryScoringError(
                "blank target key field"
            )
        if key in out:
            raise BorealConfirmatoryScoringError(
                f"duplicate target key: {key}"
            )
        raw = str(row["target"]).strip()
        if raw not in {"0", "1"}:
            raise BorealConfirmatoryScoringError(
                f"nonbinary confirmatory target: {raw!r}"
            )
        out[key] = int(raw)
    if not out:
        raise BorealConfirmatoryScoringError(
            "empty confirmatory target surface"
        )
    return out


def binary_log_loss(target: int, probability: float) -> float:
    if target not in (0, 1):
        raise BorealConfirmatoryScoringError(
            "binary log loss target must be 0/1"
        )
    if not 0.0 < probability < 1.0:
        raise BorealConfirmatoryScoringError(
            "binary log loss probability outside (0,1)"
        )
    return -math.log(probability) if target == 1 else -math.log1p(-probability)


def linear_quantile(values: Sequence[float], p: float) -> float:
    if not 0.0 <= p <= 1.0:
        raise BorealConfirmatoryScoringError(
            "quantile probability outside [0,1]"
        )
    xs = sorted(float(x) for x in values)
    if not xs:
        raise BorealConfirmatoryScoringError(
            "empty quantile vector"
        )
    if len(xs) == 1:
        return xs[0]
    h = (len(xs) - 1) * p
    lo = int(math.floor(h))
    hi = int(math.ceil(h))
    if lo == hi:
        return xs[lo]
    frac = h - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


def deterministic_block_bootstrap(
    block_values: Mapping[str, float],
    *,
    replicates: int,
    seed: int,
) -> tuple[float, ...]:
    if replicates < 1:
        raise BorealConfirmatoryScoringError(
            "bootstrap replicates must be >=1"
        )
    blocks = tuple(sorted(block_values))
    if not blocks:
        raise BorealConfirmatoryScoringError(
            "bootstrap requires at least one block"
        )
    values = tuple(float(block_values[b]) for b in blocks)
    n = len(blocks)
    out = []
    for rep in range(replicates):
        sample = []
        for draw in range(n):
            digest = hashlib.sha256(
                f"{seed}|{rep}|{draw}".encode("utf-8")
            ).digest()
            index = int.from_bytes(digest[:8], "big") % n
            sample.append(values[index])
        out.append(math.fsum(sample) / n)
    return tuple(out)


def score_primary(
    predictions_text: str,
    targets_text: str,
    *,
    expected_blocks: Sequence[str],
    bootstrap_replicates: int,
    bootstrap_seed: int,
) -> dict:
    predictions = parse_prediction_surface(predictions_text)
    targets = parse_target_surface(targets_text)

    if set(predictions) != set(targets):
        missing_target = sorted(set(predictions) - set(targets))
        extra_target = sorted(set(targets) - set(predictions))
        raise BorealConfirmatoryScoringError(
            "prediction/target key mismatch "
            f"missing_target={missing_target[:5]} "
            f"extra_target={extra_target[:5]}"
        )

    expected = tuple(expected_blocks)
    if not expected or len(expected) != len(set(expected)):
        raise BorealConfirmatoryScoringError(
            "expected confirmatory blocks invalid"
        )

    rows_by_block: dict[str, list[float]] = defaultdict(list)
    r3_loss_by_block: dict[str, list[float]] = defaultdict(list)
    c_loss_by_block: dict[str, list[float]] = defaultdict(list)
    positives_by_block: dict[str, int] = defaultdict(int)

    for key in sorted(predictions):
        island, block, species = key
        if block not in set(expected):
            raise BorealConfirmatoryScoringError(
                f"prediction row outside frozen confirmatory blocks: {block}"
            )
        target = targets[key]
        p = predictions[key]
        r3 = binary_log_loss(target, p["R3"])
        c = binary_log_loss(target, p["C"])
        rows_by_block[block].append(c - r3)
        r3_loss_by_block[block].append(r3)
        c_loss_by_block[block].append(c)
        positives_by_block[block] += target

    if set(rows_by_block) != set(expected):
        missing = sorted(set(expected) - set(rows_by_block))
        raise BorealConfirmatoryScoringError(
            "confirmatory blocks missing scored rows: " + ", ".join(missing)
        )

    block_delta = {
        block: math.fsum(rows_by_block[block]) / len(rows_by_block[block])
        for block in expected
    }
    block_r3 = {
        block: math.fsum(r3_loss_by_block[block]) / len(r3_loss_by_block[block])
        for block in expected
    }
    block_c = {
        block: math.fsum(c_loss_by_block[block]) / len(c_loss_by_block[block])
        for block in expected
    }
    point = math.fsum(block_delta[b] for b in expected) / len(expected)

    bootstrap = deterministic_block_bootstrap(
        block_delta,
        replicates=bootstrap_replicates,
        seed=bootstrap_seed,
    )
    lower = linear_quantile(bootstrap, 0.025)
    upper = linear_quantile(bootstrap, 0.975)
    supported = point < 0.0 and upper < 0.0

    block_rows = []
    for block in expected:
        n = len(rows_by_block[block])
        block_rows.append({
            "block": block,
            "rows": n,
            "positive_targets": positives_by_block[block],
            "target_prevalence_hex": float(
                positives_by_block[block] / n
            ).hex(),
            "mean_R3_log_loss_hex": float(block_r3[block]).hex(),
            "mean_C_log_loss_hex": float(block_c[block]).hex(),
            "mean_C_minus_R3_hex": float(block_delta[block]).hex(),
        })

    total_rows = len(targets)
    total_positive = sum(targets.values())
    return {
        "row_count": total_rows,
        "positive_targets": total_positive,
        "target_prevalence_hex": float(
            total_positive / total_rows
        ).hex(),
        "confirmatory_block_count": len(expected),
        "block_summaries": block_rows,
        "point_estimate_hex": float(point).hex(),
        "ci95_lower_hex": float(lower).hex(),
        "ci95_upper_hex": float(upper).hex(),
        "bootstrap_replicates": bootstrap_replicates,
        "bootstrap_seed": bootstrap_seed,
        "bootstrap_algorithm": (
            "SHA256(seed|replicate|draw) first-8-byte integer modulo n_blocks"
        ),
        "quantile_method": "linear_type7",
        "favourable_direction": "negative",
        "primary_supported": supported,
    }
