"""Frozen confirmatory scoring for the boreal dual-isolation test."""
from __future__ import annotations

import csv
import io
import math
import random
from dataclasses import dataclass
from typing import Sequence

from .boreal_spatial_partition import type7_quantile


class BorealConfirmatoryScoringError(RuntimeError):
    pass


@dataclass(frozen=True)
class PredictionRow:
    island: str
    block: str
    species: str
    p_r0: float
    p_r1: float
    p_r2: float
    p_r3: float
    p_c: float


@dataclass(frozen=True)
class TargetRow:
    island: str
    block: str
    species: str
    target: int


def _parse_probability(value: str) -> float:
    text = str(value).strip()
    try:
        if text.lower().startswith(("0x", "+0x", "-0x")):
            probability = float.fromhex(text)
        else:
            probability = float(text)
    except ValueError as exc:
        raise BorealConfirmatoryScoringError(
            "invalid frozen probability"
        ) from exc
    if not math.isfinite(probability) or not 0.0 < probability < 1.0:
        raise BorealConfirmatoryScoringError(
            "frozen probability outside (0,1)"
        )
    return probability


def parse_prediction_surface(text: str) -> tuple[PredictionRow, ...]:
    reader = csv.DictReader(io.StringIO(text))
    required = [
        "island",
        "block",
        "species",
        "p_R0_hex",
        "p_R1_hex",
        "p_R2_hex",
        "p_R3_hex",
        "p_C_hex",
    ]
    if reader.fieldnames != required:
        raise BorealConfirmatoryScoringError(
            "unexpected prediction-surface schema"
        )
    rows = []
    seen = set()
    for raw in reader:
        island = str(raw["island"]).strip()
        block = str(raw["block"]).strip()
        species = str(raw["species"]).strip()
        if not island or not block or not species:
            raise BorealConfirmatoryScoringError(
                "blank prediction key"
            )
        key = (island, block, species)
        if key in seen:
            raise BorealConfirmatoryScoringError(
                "duplicate prediction key"
            )
        seen.add(key)
        rows.append(PredictionRow(
            island=island,
            block=block,
            species=species,
            p_r0=_parse_probability(raw["p_R0_hex"]),
            p_r1=_parse_probability(raw["p_R1_hex"]),
            p_r2=_parse_probability(raw["p_R2_hex"]),
            p_r3=_parse_probability(raw["p_R3_hex"]),
            p_c=_parse_probability(raw["p_C_hex"]),
        ))
    if not rows:
        raise BorealConfirmatoryScoringError(
            "empty prediction surface"
        )
    return tuple(rows)


def parse_target_surface(text: str) -> tuple[TargetRow, ...]:
    reader = csv.DictReader(io.StringIO(text))
    required = ["island", "block", "species", "target"]
    if reader.fieldnames != required:
        raise BorealConfirmatoryScoringError(
            "unexpected target-surface schema"
        )
    rows = []
    seen = set()
    for raw in reader:
        island = str(raw["island"]).strip()
        block = str(raw["block"]).strip()
        species = str(raw["species"]).strip()
        value = str(raw["target"]).strip()
        if not island or not block or not species:
            raise BorealConfirmatoryScoringError(
                "blank target key"
            )
        if value not in {"0", "1"}:
            raise BorealConfirmatoryScoringError(
                "confirmatory target is not binary"
            )
        key = (island, block, species)
        if key in seen:
            raise BorealConfirmatoryScoringError(
                "duplicate target key"
            )
        seen.add(key)
        rows.append(TargetRow(
            island=island,
            block=block,
            species=species,
            target=int(value),
        ))
    if not rows:
        raise BorealConfirmatoryScoringError(
            "empty target surface"
        )
    return tuple(rows)


def frozen_species_order(
    predictions: Sequence[PredictionRow],
) -> tuple[str, ...]:
    first_island = predictions[0].island
    order = tuple(
        row.species
        for row in predictions
        if row.island == first_island
    )
    if not order or len(order) != len(set(order)):
        raise BorealConfirmatoryScoringError(
            "invalid frozen species order"
        )

    by_island: dict[str, list[str]] = {}
    for row in predictions:
        by_island.setdefault(row.island, []).append(row.species)
    for island, species in by_island.items():
        if tuple(species) != order:
            raise BorealConfirmatoryScoringError(
                f"species order drift on island: {island}"
            )
    return order


def _log_loss(target: int, probability: float) -> float:
    if target == 1:
        return -math.log(probability)
    return -math.log1p(-probability)


def score_frozen_surfaces(
    predictions_text: str,
    targets_text: str,
    *,
    bootstrap_replicates: int,
    bootstrap_seed: int,
) -> dict:
    if bootstrap_replicates < 1:
        raise BorealConfirmatoryScoringError(
            "bootstrap_replicates must be positive"
        )

    predictions = parse_prediction_surface(predictions_text)
    targets = parse_target_surface(targets_text)
    species_order = frozen_species_order(predictions)

    prediction_by_key = {
        (row.island, row.block, row.species): row
        for row in predictions
    }
    target_by_key = {
        (row.island, row.block, row.species): row.target
        for row in targets
    }
    if set(prediction_by_key) != set(target_by_key):
        missing = sorted(set(prediction_by_key) - set(target_by_key))
        extra = sorted(set(target_by_key) - set(prediction_by_key))
        raise BorealConfirmatoryScoringError(
            f"prediction/target key mismatch missing={missing} extra={extra}"
        )

    block_deltas: dict[str, list[float]] = {}
    block_r3: dict[str, list[float]] = {}
    block_c: dict[str, list[float]] = {}
    for key, prediction in prediction_by_key.items():
        target = target_by_key[key]
        loss_r3 = _log_loss(target, prediction.p_r3)
        loss_c = _log_loss(target, prediction.p_c)
        block_deltas.setdefault(prediction.block, []).append(
            loss_c - loss_r3
        )
        block_r3.setdefault(prediction.block, []).append(loss_r3)
        block_c.setdefault(prediction.block, []).append(loss_c)

    blocks = tuple(sorted(block_deltas))
    if not blocks:
        raise BorealConfirmatoryScoringError(
            "no confirmatory blocks in score"
        )

    block_mean_delta = {
        block: math.fsum(block_deltas[block]) / len(block_deltas[block])
        for block in blocks
    }
    block_mean_r3 = {
        block: math.fsum(block_r3[block]) / len(block_r3[block])
        for block in blocks
    }
    block_mean_c = {
        block: math.fsum(block_c[block]) / len(block_c[block])
        for block in blocks
    }

    primary = math.fsum(
        block_mean_delta[block] for block in blocks
    ) / len(blocks)
    mean_r3 = math.fsum(
        block_mean_r3[block] for block in blocks
    ) / len(blocks)
    mean_c = math.fsum(
        block_mean_c[block] for block in blocks
    ) / len(blocks)

    rng = random.Random(int(bootstrap_seed))
    bootstrap = []
    n_blocks = len(blocks)
    for _ in range(bootstrap_replicates):
        sampled = [
            blocks[rng.randrange(n_blocks)]
            for _ in range(n_blocks)
        ]
        bootstrap.append(
            math.fsum(block_mean_delta[block] for block in sampled)
            / n_blocks
        )

    ci_low = type7_quantile(bootstrap, 0.025)
    ci_high = type7_quantile(bootstrap, 0.975)
    supported = primary < 0.0 and ci_high < 0.0

    return {
        "row_count": len(predictions),
        "species_count": len(species_order),
        "species_order": list(species_order),
        "block_count": len(blocks),
        "block_order": list(blocks),
        "block_mean_c_minus_r3": {
            block: block_mean_delta[block]
            for block in blocks
        },
        "block_mean_r3_log_loss": {
            block: block_mean_r3[block]
            for block in blocks
        },
        "block_mean_c_log_loss": {
            block: block_mean_c[block]
            for block in blocks
        },
        "primary_c_minus_r3": primary,
        "cluster_weighted_r3_log_loss": mean_r3,
        "cluster_weighted_c_log_loss": mean_c,
        "ci95_low": ci_low,
        "ci95_high": ci_high,
        "bootstrap_replicates": bootstrap_replicates,
        "bootstrap_seed": bootstrap_seed,
        "primary_supported": supported,
    }
