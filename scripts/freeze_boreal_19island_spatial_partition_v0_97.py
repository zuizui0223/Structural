#!/usr/bin/env python3
"""Freeze the 19-island spatial pilot/confirmatory split with the unchanged v0.75 rule."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

from structural.boreal_spatial_partition import (
    BorealSpatialPartitionError,
    freeze_spatial_partition,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GEOMETRY = ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
DEFAULT_FREEZE = ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
DEFAULT_CONTRACT = ROOT / "development/boreal_19island_spatial_partition_contract_v0_97.json"
DEFAULT_LEGACY = ROOT / "development/boreal_lake_islands_spatial_partition_contract_v0_75.json"


class Boreal19SpatialError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19SpatialError(f"{path.name} must contain a JSON object")
    return value


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_float(value: str) -> float:
    text = str(value).strip()
    if text.lower().startswith(("0x", "+0x", "-0x")):
        out = float.fromhex(text)
    else:
        out = float(text)
    if not math.isfinite(out):
        raise Boreal19SpatialError("nonfinite coordinate")
    return out


def _validate_legacy_rule(contract: Mapping, legacy: Mapping) -> None:
    if legacy.get("schema") != (
        "structural.boreal_lake_islands_spatial_partition_contract.v0_75"
    ):
        raise Boreal19SpatialError("unexpected legacy v0.75 contract schema")
    if contract.get("legacy_rule_source", {}).get(
        "rule_changed_after_19island_geometry_seen"
    ) is not False:
        raise Boreal19SpatialError("v0.97 must not tune the legacy rule")

    old_radius = legacy["radius_rule"]
    new_radius = contract["radius_rule"]
    for key in (
        "quantiles",
        "quantile_definition",
        "rounding",
        "graph",
        "candidate_selection_order",
    ):
        if new_radius.get(key) != old_radius.get(key):
            raise Boreal19SpatialError(f"legacy radius rule drift: {key}")

    old_part = legacy["partition_rule"]
    new_part = contract["partition_rule"]
    for key in (
        "minimum_total_blocks",
        "minimum_pilot_blocks",
        "minimum_confirmatory_blocks",
        "pilot_fraction",
        "ranking_salt",
    ):
        expected = (
            old_part.get(key)
            if key != "ranking_salt"
            else "boreal-v0.75-pilot-split"
        )
        if new_part.get(key) != expected:
            raise Boreal19SpatialError(f"legacy partition rule drift: {key}")


def load_geometry(
    path: Path,
    *,
    freeze: Mapping,
    contract: Mapping,
) -> dict[str, tuple[float, float]]:
    text = path.read_text(encoding="utf-8")
    observed_sha = _sha256_text(text)
    expected_sha = contract["input"]["geometry_sha256"]
    if observed_sha != expected_sha:
        raise Boreal19SpatialError("committed safe geometry SHA mismatch")
    if freeze.get("geometry_sha256") != expected_sha:
        raise Boreal19SpatialError("v0.97 geometry-freeze SHA drift")
    if freeze.get("status") != "SAFE_GEOMETRY_COMMITTED_RESPONSE_INDEPENDENTLY":
        raise Boreal19SpatialError("safe geometry freeze did not qualify")
    if freeze.get("biological_response_values_opened") is not False:
        raise Boreal19SpatialError("biological response boundary violated")
    if freeze.get("spatial_partition_may_be_frozen_from_this_geometry") is not True:
        raise Boreal19SpatialError("geometry freeze does not authorize spatial partition")

    rows = list(csv.DictReader(text.splitlines()))
    if len(rows) != int(contract["input"]["island_count"]):
        raise Boreal19SpatialError("19-island geometry row count drift")
    if not rows or tuple(rows[0].keys()) != ("Island", "Lat", "Long"):
        raise Boreal19SpatialError("unexpected safe geometry schema")

    coords: dict[str, tuple[float, float]] = {}
    for row in rows:
        island = str(row["Island"]).strip()
        if not island or island in coords:
            raise Boreal19SpatialError("blank or duplicate island geometry")
        coords[island] = (
            _parse_float(row["Lat"]),
            _parse_float(row["Long"]),
        )

    expected_order = tuple(freeze["island_order"])
    if tuple(sorted(coords)) != expected_order:
        raise Boreal19SpatialError("safe geometry island identity drift")
    return coords


def run(
    geometry_path: Path,
    *,
    freeze: Mapping,
    contract: Mapping,
    legacy: Mapping,
) -> dict:
    if contract.get("schema") != (
        "structural.boreal_19island_spatial_partition_contract.v0_97"
    ):
        raise Boreal19SpatialError("unexpected v0.97 contract schema")
    if contract.get("candidate_id") != freeze.get("candidate_id"):
        raise Boreal19SpatialError("candidate identity drift")
    _validate_legacy_rule(contract, legacy)
    coords = load_geometry(geometry_path, freeze=freeze, contract=contract)

    rule = contract["partition_rule"]
    frozen = freeze_spatial_partition(
        coords,
        minimum_total_blocks=int(rule["minimum_total_blocks"]),
        minimum_pilot_blocks=int(rule["minimum_pilot_blocks"]),
        minimum_confirmatory_blocks=int(rule["minimum_confirmatory_blocks"]),
        pilot_fraction=float(rule["pilot_fraction"]),
        ranking_salt=str(rule["ranking_salt"]),
    )
    return {
        "schema": "structural.boreal_19island_spatial_partition_result.v0_97",
        "candidate_id": contract["candidate_id"],
        **frozen,
        "source_geometry_sha256": contract["input"]["geometry_sha256"],
        "legacy_v075_rule_reused_without_tuning": True,
        "species_occurrence_used": False,
        "richness_used": False,
        "habitat_values_used": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "next_action": (
            "freeze a response-independent habitat/external-state reference for "
            "these exact 19 islands, then construct the response-sealed intake"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY)
    parser.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--legacy-contract", type=Path, default=DEFAULT_LEGACY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        result = run(
            args.geometry,
            freeze=_load(args.freeze),
            contract=_load(args.contract),
            legacy=_load(args.legacy_contract),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealSpatialPartitionError,
        Boreal19SpatialError,
    ) as exc:
        result = {
            "schema": "structural.boreal_19island_spatial_partition_result.v0_97",
            "status": "STOP",
            "reason": str(exc),
            "species_occurrence_used": False,
            "counts_as_empirical_evidence": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
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
