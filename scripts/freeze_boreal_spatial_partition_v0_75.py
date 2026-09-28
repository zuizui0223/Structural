#!/usr/bin/env python3
"""Freeze the boreal spatial graph and disjoint pilot/confirmatory blocks."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

from structural.boreal_spatial_partition import (
    BorealSpatialPartitionError,
    freeze_spatial_partition,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_lake_islands_spatial_partition_contract_v0_75.json"
)
DEFAULT_UNIVERSE = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)


class BorealSpatialFreezeError(RuntimeError):
    pass


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_universe(path: Path = DEFAULT_UNIVERSE) -> tuple[str, ...]:
    x = json.loads(path.read_text(encoding="utf-8"))
    codes = tuple(x["current_study_island_universe"]["codes"])
    if len(codes) != 42 or len(set(codes)) != 42:
        raise BorealSpatialFreezeError(
            "expected exact frozen 42-island universe"
        )
    return codes


def parse_float(value: str) -> float:
    text = str(value).strip()
    if text.lower().startswith(("0x", "+0x", "-0x")):
        value_float = float.fromhex(text)
    else:
        value_float = float(text)
    if not math.isfinite(value_float):
        raise BorealSpatialFreezeError("nonfinite geometry value")
    return value_float


def load_geometry(
    path: Path,
    *,
    expected_sha256: str,
    universe: tuple[str, ...],
) -> dict[str, tuple[float, float]]:
    text = path.read_text(encoding="utf-8")
    if sha256_text(text) != expected_sha256:
        raise BorealSpatialFreezeError("safe geometry SHA mismatch")
    rows = list(csv.DictReader(text.splitlines()))
    if not rows or tuple(rows[0].keys()) != ("Island", "Lat", "Long"):
        raise BorealSpatialFreezeError("unexpected safe geometry schema")
    if len(rows) != len(universe):
        raise BorealSpatialFreezeError("safe geometry row count mismatch")
    coords = {}
    for row in rows:
        island = row["Island"].strip()
        if not island or island in coords:
            raise BorealSpatialFreezeError("blank/duplicate island geometry")
        coords[island] = (
            parse_float(row["Lat"]),
            parse_float(row["Long"]),
        )
    if set(coords) != set(universe):
        raise BorealSpatialFreezeError("safe geometry island-set mismatch")
    return coords


def run(
    geometry_csv: Path,
    projection_receipt: dict,
    *,
    contract: dict,
    universe: tuple[str, ...],
) -> dict:
    if projection_receipt.get("schema") != (
        "structural.boreal_lake_islands_safe_projection_result.v0_74"
    ):
        raise BorealSpatialFreezeError("unexpected v0.74 projection receipt")
    if projection_receipt.get("status") != (
        "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED"
    ):
        raise BorealSpatialFreezeError("safe projection did not qualify")
    if projection_receipt.get("protected_response_values_opened") is not False:
        raise BorealSpatialFreezeError("protected response boundary violated")
    geometry = projection_receipt.get("geometry", {})
    expected_sha = geometry.get("sha256")
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise BorealSpatialFreezeError("projection receipt geometry SHA missing")

    coords = load_geometry(
        geometry_csv,
        expected_sha256=expected_sha,
        universe=universe,
    )
    rule = contract["partition_rule"]
    result = freeze_spatial_partition(
        coords,
        minimum_total_blocks=rule["minimum_total_blocks"],
        minimum_pilot_blocks=rule["minimum_pilot_blocks"],
        minimum_confirmatory_blocks=rule["minimum_confirmatory_blocks"],
        pilot_fraction=rule["pilot_fraction"],
        ranking_salt="boreal-v0.75-pilot-split",
    )
    return {
        "schema": "structural.boreal_lake_islands_spatial_partition_result.v0_75",
        "candidate_id": contract["candidate_id"],
        **result,
        "source_geometry_sha256": expected_sha,
        "species_occurrence_used": False,
        "richness_used": False,
        "habitat_values_used": False,
        "counts_as_empirical_evidence": False,
        "v0_11_intake_authorized": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "next_action": (
            "freeze the response-independent local habitat reference; only "
            "after both spatial and habitat gates are complete may v0.11 be considered"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geometry_csv", type=Path)
    parser.add_argument("projection_receipt", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        if contract.get("schema") != (
            "structural.boreal_lake_islands_spatial_partition_contract.v0_75"
        ):
            raise BorealSpatialFreezeError("unexpected v0.75 contract schema")
        receipt = json.loads(
            args.projection_receipt.read_text(encoding="utf-8")
        )
        result = run(
            args.geometry_csv,
            receipt,
            contract=contract,
            universe=load_universe(),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealSpatialPartitionError,
        BorealSpatialFreezeError,
    ) as exc:
        result = {
            "schema": "structural.boreal_lake_islands_spatial_partition_result.v0_75",
            "status": "STOP",
            "reason": str(exc),
            "counts_as_empirical_evidence": False,
            "v0_11_intake_authorized": False,
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
