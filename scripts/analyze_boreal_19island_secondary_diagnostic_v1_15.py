#!/usr/bin/env python3
"""Post-hoc, non-rescuing diagnostic for the completed boreal fresh result."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_secondary_diagnostic_contract_v1_15.json"
)
DEFAULT_RESULT = (
    ROOT / "development/boreal_19island_confirmatory_scoring_result_v1_14.json"
)
DEFAULT_PRIMARY_FREEZE = (
    ROOT / "development/boreal_19island_confirmatory_result_freeze_v1_14.json"
)
DEFAULT_PREDICTIONS = (
    ROOT / "development/boreal_19island_confirmatory_predictions_v1_10.csv"
)
DEFAULT_PRECONFIRMATORY_FREEZE = (
    ROOT / "development/boreal_19island_preconfirmatory_freeze_v1_10.json"
)
DEFAULT_STATE = (
    ROOT / "development/boreal_19island_state_reference_v0_99.csv"
)
DEFAULT_STATE_FREEZE = (
    ROOT / "development/boreal_19island_state_reference_freeze_v0_99.json"
)
DEFAULT_SPATIAL = (
    ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
)


class Boreal19SecondaryDiagnosticError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19SecondaryDiagnosticError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _number(value: object) -> float:
    text = str(value).strip()
    try:
        out = (
            float.fromhex(text)
            if text.lower().startswith(("0x", "+0x", "-0x"))
            else float(text)
        )
    except ValueError as exc:
        raise Boreal19SecondaryDiagnosticError(
            f"invalid numeric value: {text!r}"
        ) from exc
    if not math.isfinite(out):
        raise Boreal19SecondaryDiagnosticError("nonfinite numeric value")
    return out


def _mean(values: Sequence[float]) -> float:
    if not values:
        raise Boreal19SecondaryDiagnosticError("empty mean vector")
    return math.fsum(values) / len(values)


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        raise Boreal19SecondaryDiagnosticError(
            "invalid descriptive correlation vectors"
        )
    mx = _mean(xs)
    my = _mean(ys)
    dx = [x - mx for x in xs]
    dy = [y - my for y in ys]
    denom_x = math.fsum(x * x for x in dx)
    denom_y = math.fsum(y * y for y in dy)
    if denom_x <= 0.0 or denom_y <= 0.0:
        raise Boreal19SecondaryDiagnosticError(
            "zero-variance descriptive correlation vector"
        )
    return math.fsum(x * y for x, y in zip(dx, dy)) / math.sqrt(
        denom_x * denom_y
    )


def _parse_predictions(
    path: Path,
    freeze: Mapping,
) -> list[dict[str, object]]:
    expected = freeze.get("files", {}).get(
        "confirmatory_predictions", {}
    ).get("sha256")
    if sha256_file(path) != expected:
        raise Boreal19SecondaryDiagnosticError(
            "frozen prediction file SHA mismatch"
        )
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_header = (
            "island",
            "block",
            "species",
            "p_R0_hex",
            "p_R1_hex",
            "p_R2_hex",
            "p_R3_hex",
            "p_C_hex",
        )
        if tuple(reader.fieldnames or ()) != expected_header:
            raise Boreal19SecondaryDiagnosticError(
                "prediction header drift"
            )
        rows = []
        for row in reader:
            rows.append({
                "island": str(row["island"]).strip(),
                "block": str(row["block"]).strip(),
                "species": str(row["species"]).strip(),
                "p_R3": _number(row["p_R3_hex"]),
                "p_C": _number(row["p_C_hex"]),
            })
    if len(rows) != 1287:
        raise Boreal19SecondaryDiagnosticError(
            "prediction row count is not 1287"
        )
    return rows


def _parse_state(
    path: Path,
    freeze: Mapping,
) -> tuple[tuple[str, ...], dict[str, dict[str, float]]]:
    expected_sha = freeze.get("state_reference_sha256")
    if sha256_file(path) != expected_sha:
        raise Boreal19SecondaryDiagnosticError(
            "state reference SHA mismatch"
        )
    expected_order = tuple(freeze.get("island_order") or ())
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_header = (
            "Island",
            "PC1",
            "PC2",
            "PC3",
            "TSF_Z",
            "LOG_AREA_Z",
            "LOG_MAINLAND_DISTANCE_Z",
        )
        if tuple(reader.fieldnames or ()) != expected_header:
            raise Boreal19SecondaryDiagnosticError("state header drift")
        rows = list(reader)
    order = tuple(str(row["Island"]).strip() for row in rows)
    if order != expected_order:
        raise Boreal19SecondaryDiagnosticError("state island order drift")
    values = {
        str(row["Island"]).strip(): {
            key: _number(row[key])
            for key in expected_header
            if key != "Island"
        }
        for row in rows
    }
    return order, values


def analyze(
    *,
    result: Mapping,
    primary_freeze: Mapping,
    predictions_path: Path,
    preconfirmatory_freeze: Mapping,
    state_path: Path,
    state_freeze: Mapping,
    spatial: Mapping,
    contract: Mapping,
    result_file_sha256: str,
) -> dict:
    if contract.get("schema") != (
        "structural.boreal_19island_secondary_diagnostic_contract.v1_15"
    ):
        raise Boreal19SecondaryDiagnosticError(
            "unexpected v1.15 contract schema"
        )
    if result.get("schema") != (
        "structural.boreal_19island_confirmatory_scoring_result.v1_13"
    ):
        raise Boreal19SecondaryDiagnosticError(
            "unexpected primary result schema"
        )
    if result.get("primary_supported") is not False:
        raise Boreal19SecondaryDiagnosticError(
            "secondary diagnostic requires locked primary not supported"
        )
    if result.get("fresh_system_denominator_contribution") != 1:
        raise Boreal19SecondaryDiagnosticError(
            "fresh evidence accounting drift"
        )
    if result.get("secondary_analysis_may_change_primary_status") is not False:
        raise Boreal19SecondaryDiagnosticError(
            "primary rescue boundary drift"
        )
    if result.get("rerun_authorized") is not False:
        raise Boreal19SecondaryDiagnosticError("rerun boundary drift")

    source_hash = primary_freeze.get("source_artifact_files", {}).get(
        "committed_canonical_json_plus_newline_sha256"
    )
    if result_file_sha256 != source_hash:
        raise Boreal19SecondaryDiagnosticError(
            "committed primary result SHA drift"
        )
    if primary_freeze.get("primary", {}).get("primary_supported") is not False:
        raise Boreal19SecondaryDiagnosticError(
            "primary freeze support status drift"
        )

    predictions = _parse_predictions(
        predictions_path,
        preconfirmatory_freeze,
    )
    state_order, state = _parse_state(state_path, state_freeze)

    if spatial.get("schema") != (
        "structural.boreal_19island_spatial_partition_freeze.v1_00"
    ):
        raise Boreal19SecondaryDiagnosticError(
            "unexpected spatial freeze schema"
        )
    blocks = tuple(spatial.get("confirmatory_block_ids") or ())
    if len(blocks) != 7 or len(set(blocks)) != 7:
        raise Boreal19SecondaryDiagnosticError(
            "confirmatory block support is not exact seven"
        )
    confirmatory = set(spatial.get("confirmatory_islands") or ())
    if len(confirmatory) != 13:
        raise Boreal19SecondaryDiagnosticError(
            "confirmatory island support is not exact thirteen"
        )
    if {str(row["island"]) for row in predictions} != confirmatory:
        raise Boreal19SecondaryDiagnosticError(
            "prediction population drift"
        )

    result_blocks = result.get("primary", {}).get("block_summaries")
    if not isinstance(result_blocks, list):
        raise Boreal19SecondaryDiagnosticError(
            "primary block summaries missing"
        )
    primary_by_block = {
        str(row["block"]): {
            "loss_delta": _number(row["mean_C_minus_R3_hex"]),
            "prevalence": _number(row["target_prevalence_hex"]),
            "rows": int(row["rows"]),
            "positive_targets": int(row["positive_targets"]),
        }
        for row in result_blocks
    }
    if set(primary_by_block) != set(blocks):
        raise Boreal19SecondaryDiagnosticError(
            "primary/spatial block identity drift"
        )

    pred_by_block: dict[str, list[float]] = {block: [] for block in blocks}
    for row in predictions:
        block = str(row["block"])
        if block not in pred_by_block:
            raise Boreal19SecondaryDiagnosticError(
                f"prediction outside confirmatory block: {block}"
            )
        shift = float(row["p_C"]) - float(row["p_R3"])
        pred_by_block[block].append(shift)

    state_keys = (
        "PC1",
        "PC2",
        "PC3",
        "TSF_Z",
        "LOG_AREA_Z",
        "LOG_MAINLAND_DISTANCE_Z",
    )
    block_rows = []
    metrics: dict[str, dict[str, float]] = {}
    for block in blocks:
        islands = tuple(
            island
            for island in state_order
            if spatial["island_to_block"].get(island) == block
        )
        if not islands or not set(islands) <= confirmatory:
            raise Boreal19SecondaryDiagnosticError(
                f"invalid confirmatory block island support: {block}"
            )
        shifts = pred_by_block[block]
        if len(shifts) != len(islands) * 99:
            raise Boreal19SecondaryDiagnosticError(
                f"prediction count drift in block: {block}"
            )
        signed = _mean(shifts)
        absolute = _mean([abs(x) for x in shifts])
        rms = math.sqrt(_mean([x * x for x in shifts]))
        fraction_higher = sum(x > 0.0 for x in shifts) / len(shifts)
        state_means = {
            key: _mean([state[island][key] for island in islands])
            for key in state_keys
        }
        p = primary_by_block[block]
        row = {
            "block": block,
            "islands": list(islands),
            "island_count": len(islands),
            "prediction_count": len(shifts),
            "loss_C_minus_R3_hex": float(p["loss_delta"]).hex(),
            "target_prevalence_hex": float(p["prevalence"]).hex(),
            "mean_probability_C_minus_R3_hex": float(signed).hex(),
            "mean_absolute_probability_shift_hex": float(absolute).hex(),
            "rms_probability_shift_hex": float(rms).hex(),
            "fraction_C_probability_higher_hex": float(
                fraction_higher
            ).hex(),
            "state_mean_hex": {
                key: float(value).hex()
                for key, value in state_means.items()
            },
        }
        block_rows.append(row)
        metrics[block] = {
            "loss_delta": p["loss_delta"],
            "prevalence": p["prevalence"],
            "mean_probability_shift": signed,
            "mean_absolute_probability_shift": absolute,
            "rms_probability_shift": rms,
            "fraction_C_probability_higher": fraction_higher,
            **state_means,
        }

    y = [metrics[block]["loss_delta"] for block in blocks]
    diagnostic_keys = (
        "mean_probability_shift",
        "mean_absolute_probability_shift",
        "rms_probability_shift",
        "fraction_C_probability_higher",
        "PC1",
        "PC2",
        "PC3",
        "TSF_Z",
        "LOG_AREA_Z",
        "LOG_MAINLAND_DISTANCE_Z",
        "prevalence",
    )
    correlations = {
        key: _pearson(
            [metrics[block][key] for block in blocks],
            y,
        )
        for key in diagnostic_keys
    }

    worsening = [
        block for block in blocks
        if metrics[block]["loss_delta"] > 0.0
    ]
    improving = [
        block for block in blocks
        if metrics[block]["loss_delta"] < 0.0
    ]
    worsening_higher_fractions = [
        metrics[block]["fraction_C_probability_higher"]
        for block in worsening
    ]
    improving_higher_fractions = [
        metrics[block]["fraction_C_probability_higher"]
        for block in improving
    ]

    return {
        "schema": (
            "structural.boreal_19island_secondary_diagnostic_result.v1_15"
        ),
        "status": contract["success_ceiling"]["status"],
        "candidate_id": contract["candidate_id"],
        "primary_status_locked": (
            "PRIMARY_NOT_SUPPORTED_INTERNAL_SOURCE_ISOLATION_NONREDUNDANT"
        ),
        "primary_supported": False,
        "fresh_system_denominator_contribution": 0,
        "raw_confirmatory_response_reopened": False,
        "row_level_confirmatory_targets_used": False,
        "block_count": 7,
        "block_diagnostics": block_rows,
        "pattern_summary": {
            "worsening_block_count": len(worsening),
            "improving_block_count": len(improving),
            "worsening_blocks": worsening,
            "improving_blocks": improving,
            "all_worsening_blocks_C_probability_higher_fraction_min_hex": (
                float(min(worsening_higher_fractions)).hex()
            ),
            "improving_blocks_C_probability_higher_fraction_range_hex": [
                float(min(improving_higher_fractions)).hex(),
                float(max(improving_higher_fractions)).hex(),
            ],
            "correlation_loss_with_signed_probability_shift_hex": float(
                correlations["mean_probability_shift"]
            ).hex(),
            "correlation_loss_with_absolute_probability_shift_hex": float(
                correlations["mean_absolute_probability_shift"]
            ).hex(),
            "correlation_loss_with_rms_probability_shift_hex": float(
                correlations["rms_probability_shift"]
            ).hex(),
            "correlation_loss_with_log_area_z_hex": float(
                correlations["LOG_AREA_Z"]
            ).hex(),
            "correlation_loss_with_log_mainland_distance_z_hex": float(
                correlations["LOG_MAINLAND_DISTANCE_Z"]
            ).hex(),
        },
        "all_descriptive_correlations_hex": {
            key: float(value).hex()
            for key, value in correlations.items()
        },
        "descriptive_interpretation": {
            "dominant_pattern": (
                "C usually shifted occurrence probabilities upward relative "
                "to R3 in blocks where heldout log loss worsened; larger "
                "C-minus-R3 probability shifts coincided with larger loss "
                "penalties across the seven frozen blocks"
            ),
            "consistent_with": (
                "graph-path source continuity acting mainly as redundant "
                "or over-adjusting source signal after global occupancy and "
                "direct/diffuse Euclidean source context were already in R3"
            ),
            "not_authorized": (
                "this post-hoc seven-block pattern does not identify a "
                "dispersal mechanism, prove direct over-water movement, or "
                "rescue/reverse the primary not-supported result"
            ),
        },
        "secondary_analysis_may_change_primary_status": False,
        "mechanism_claim_authorized": False,
        "causal_dispersal_claim_authorized": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--result", type=Path, default=DEFAULT_RESULT)
    parser.add_argument(
        "--primary-freeze", type=Path, default=DEFAULT_PRIMARY_FREEZE
    )
    parser.add_argument(
        "--predictions", type=Path, default=DEFAULT_PREDICTIONS
    )
    parser.add_argument(
        "--preconfirmatory-freeze",
        type=Path,
        default=DEFAULT_PRECONFIRMATORY_FREEZE,
    )
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument(
        "--state-freeze", type=Path, default=DEFAULT_STATE_FREEZE
    )
    parser.add_argument("--spatial", type=Path, default=DEFAULT_SPATIAL)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        contract = _load(args.contract)
        result = analyze(
            result=_load(args.result),
            primary_freeze=_load(args.primary_freeze),
            predictions_path=args.predictions,
            preconfirmatory_freeze=_load(args.preconfirmatory_freeze),
            state_path=args.state,
            state_freeze=_load(args.state_freeze),
            spatial=_load(args.spatial),
            contract=contract,
            result_file_sha256=sha256_file(args.result),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        Boreal19SecondaryDiagnosticError,
    ) as exc:
        result = {
            "schema": (
                "structural.boreal_19island_secondary_diagnostic_result.v1_15"
            ),
            "status": "STOP",
            "reason": str(exc),
            "primary_supported": False,
            "fresh_system_denominator_contribution": 0,
            "raw_confirmatory_response_reopened": False,
            "secondary_analysis_may_change_primary_status": False,
            "mechanism_claim_authorized": False,
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
