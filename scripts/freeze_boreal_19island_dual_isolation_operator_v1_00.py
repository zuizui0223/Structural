#!/usr/bin/env python3
"""Freeze the 19-island dual-isolation source operator with exact spatial replay."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

from structural.boreal_dual_isolation_operator import (
    BorealDualIsolationOperatorError,
    freeze_connected_knn_operator,
)
from structural.boreal_spatial_partition import (
    BorealSpatialPartitionError,
    freeze_spatial_partition,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GEOMETRY = ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
DEFAULT_GEOMETRY_FREEZE = (
    ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
)
DEFAULT_SPATIAL_FREEZE = (
    ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
)
DEFAULT_STATE_FREEZE = (
    ROOT / "development/boreal_19island_state_reference_freeze_v0_99.json"
)
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_dual_isolation_operator_contract_v1_00.json"
)
DEFAULT_LEGACY = ROOT / "development/boreal_dual_isolation_operator_contract_v0_83.json"


class Boreal19OperatorError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19OperatorError(f"{path.name} must contain a JSON object")
    return value


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: Mapping) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _parse_number(value: object) -> float:
    text = str(value).strip()
    if text.lower().startswith(("0x", "+0x", "-0x")):
        out = float.fromhex(text)
    else:
        out = float(text)
    if not math.isfinite(out):
        raise Boreal19OperatorError("nonfinite geometry value")
    return out


def _load_geometry(
    geometry_path: Path,
    geometry_freeze: Mapping,
) -> dict[str, tuple[float, float]]:
    if geometry_freeze.get("schema") != (
        "structural.boreal_19island_safe_geometry_freeze.v0_97"
    ):
        raise Boreal19OperatorError("unexpected geometry freeze schema")
    if geometry_freeze.get("status") != (
        "SAFE_GEOMETRY_COMMITTED_RESPONSE_INDEPENDENTLY"
    ):
        raise Boreal19OperatorError("geometry freeze did not qualify")
    expected_sha = geometry_freeze.get("geometry_sha256")
    if _sha256_file(geometry_path) != expected_sha:
        raise Boreal19OperatorError("committed geometry SHA mismatch")
    if geometry_freeze.get("biological_response_values_opened") is not False:
        raise Boreal19OperatorError("geometry response boundary violated")

    rows = list(csv.DictReader(geometry_path.read_text(encoding="utf-8").splitlines()))
    if len(rows) != 19 or not rows:
        raise Boreal19OperatorError("unexpected 19-island geometry support")
    if tuple(rows[0].keys()) != ("Island", "Lat", "Long"):
        raise Boreal19OperatorError("unexpected geometry schema")
    coords: dict[str, tuple[float, float]] = {}
    for row in rows:
        island = str(row["Island"]).strip()
        if not island or island in coords:
            raise Boreal19OperatorError("blank/duplicate geometry island")
        coords[island] = (
            _parse_number(row["Lat"]),
            _parse_number(row["Long"]),
        )
    expected_order = tuple(geometry_freeze["island_order"])
    if tuple(sorted(coords)) != expected_order:
        raise Boreal19OperatorError("geometry island identity drift")
    return coords


def _validate_legacy_rule(contract: Mapping, legacy: Mapping) -> None:
    if legacy.get("schema") != "structural.boreal_dual_isolation_operator_contract.v0_83":
        raise Boreal19OperatorError("unexpected legacy v0.83 operator contract")
    if contract.get("legacy_rule_source", {}).get(
        "rule_changed_after_19island_geometry_seen"
    ) is not False:
        raise Boreal19OperatorError("source operator rule was post-geometry tuned")

    old = legacy["operator"]
    new = contract["operator"]
    for key in (
        "neighbor_tie_rule",
        "edge_weight",
        "kernel_scale_rule",
        "response_used_to_select_k",
        "response_used_to_select_kernel_scale",
        "validation_radius_reused",
    ):
        if new.get(key) != old.get(key):
            raise Boreal19OperatorError(f"legacy v0.83 operator rule drift: {key}")


def _replay_spatial(
    coordinates: Mapping[str, tuple[float, float]],
    spatial_freeze: Mapping,
    contract: Mapping,
) -> dict:
    if spatial_freeze.get("schema") != (
        "structural.boreal_19island_spatial_partition_freeze.v1_00"
    ):
        raise Boreal19OperatorError("unexpected committed spatial freeze schema")
    if spatial_freeze.get("status") != (
        "SPATIAL_PARTITION_COMMITTED_RESPONSE_INDEPENDENTLY"
    ):
        raise Boreal19OperatorError("committed spatial freeze did not qualify")
    for key in (
        "species_occurrence_used",
        "richness_used",
        "habitat_values_used",
        "counts_as_empirical_evidence",
        "pilot_response_authorized",
        "confirmatory_response_authorized",
    ):
        if spatial_freeze.get(key) is not False:
            raise Boreal19OperatorError(f"spatial response boundary violated: {key}")

    rule = contract["spatial_replay"]
    replay = freeze_spatial_partition(
        coordinates,
        minimum_total_blocks=int(rule["minimum_total_blocks"]),
        minimum_pilot_blocks=int(rule["minimum_pilot_blocks"]),
        minimum_confirmatory_blocks=int(rule["minimum_confirmatory_blocks"]),
        pilot_fraction=float(rule["pilot_fraction"]),
        ranking_salt=str(rule["ranking_salt"]),
    )
    comparisons = {
        "selected_quantile": replay["selected_quantile"],
        "selected_radius_km": replay["selected_radius_km"],
        "spatial_block_count": replay["spatial_block_count"],
        "pilot_block_ids": replay["pilot_block_ids"],
        "confirmatory_block_ids": replay["confirmatory_block_ids"],
        "pilot_islands": replay["pilot_islands"],
        "confirmatory_islands": replay["confirmatory_islands"],
        "island_to_block": replay["island_to_block"],
    }
    for key, observed in comparisons.items():
        if observed != spatial_freeze.get(key):
            raise Boreal19OperatorError(f"v0.97 spatial replay mismatch: {key}")
    return replay


def freeze(
    geometry_path: Path,
    *,
    geometry_freeze: Mapping,
    spatial_freeze: Mapping,
    state_freeze: Mapping,
    contract: Mapping,
    legacy: Mapping,
    spatial_freeze_sha256: str,
    state_freeze_sha256: str,
) -> tuple[dict, dict]:
    if contract.get("schema") != (
        "structural.boreal_19island_dual_isolation_operator_contract.v1_00"
    ):
        raise Boreal19OperatorError("unexpected v1.00 operator contract")
    candidate = contract["candidate_id"]
    if geometry_freeze.get("candidate_id") != candidate:
        raise Boreal19OperatorError("geometry candidate identity drift")
    if spatial_freeze.get("candidate_id") != candidate:
        raise Boreal19OperatorError("spatial candidate identity drift")
    if state_freeze.get("candidate_id") != candidate:
        raise Boreal19OperatorError("state candidate identity drift")
    if state_freeze.get("status") != (
        "STATE_REFERENCE_COMMITTED_RESPONSE_INDEPENDENTLY"
    ):
        raise Boreal19OperatorError("state reference freeze did not qualify")
    if state_freeze.get("source_operator_may_be_frozen") is not True:
        raise Boreal19OperatorError("state freeze does not authorize source operator")

    _validate_legacy_rule(contract, legacy)
    coordinates = _load_geometry(geometry_path, geometry_freeze)
    if spatial_freeze.get("source_geometry_sha256") != geometry_freeze.get(
        "geometry_sha256"
    ):
        raise Boreal19OperatorError("spatial/geometry SHA binding drift")
    _replay_spatial(coordinates, spatial_freeze, contract)

    try:
        operator = freeze_connected_knn_operator(coordinates)
    except BorealDualIsolationOperatorError as exc:
        raise Boreal19OperatorError(str(exc)) from exc

    island_to_block = spatial_freeze["island_to_block"]
    cross_edges = []
    for edge in operator["edges"]:
        left = edge["left"]
        right = edge["right"]
        if island_to_block[left] != island_to_block[right]:
            cross_edges.append({
                "left": left,
                "right": right,
                "left_block": island_to_block[left],
                "right_block": island_to_block[right],
                "distance_km": edge["distance_km"],
            })

    minimum_cross = int(
        contract["required_cross_partition_support"]["minimum_cross_block_edges"]
    )
    if len(cross_edges) < minimum_cross:
        raise Boreal19OperatorError(
            "source operator lacks required cross-validation-block support"
        )

    receipt = {
        "schema": "structural.boreal_19island_dual_isolation_operator_result.v1_00",
        "status": "DUAL_ISOLATION_OPERATOR_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": candidate,
        "source_geometry_sha256": geometry_freeze["geometry_sha256"],
        "source_spatial_freeze_sha256": spatial_freeze_sha256,
        "source_state_freeze_sha256": state_freeze_sha256,
        "operator_fingerprint": _canonical_sha256(operator),
        "selected_k": operator["selected_k"],
        "kernel_scale_km_hex": float(operator["kernel_scale_km"]).hex(),
        "edge_count": len(operator["edges"]),
        "cross_validation_block_edge_count": len(cross_edges),
        "cross_validation_block_edges": cross_edges,
        "validation_radius_reused": False,
        "legacy_v083_rule_reused_without_tuning": True,
        "species_occurrence_used_to_build_operator": False,
        "pilot_response_used_to_build_operator": False,
        "confirmatory_response_used_to_build_operator": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return operator, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY)
    parser.add_argument(
        "--geometry-freeze", type=Path, default=DEFAULT_GEOMETRY_FREEZE
    )
    parser.add_argument(
        "--spatial-freeze", type=Path, default=DEFAULT_SPATIAL_FREEZE
    )
    parser.add_argument("--state-freeze", type=Path, default=DEFAULT_STATE_FREEZE)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--legacy-contract", type=Path, default=DEFAULT_LEGACY)
    parser.add_argument("--output-operator", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        spatial_freeze = _load(args.spatial_freeze)
        state_freeze = _load(args.state_freeze)
        operator, receipt = freeze(
            args.geometry,
            geometry_freeze=_load(args.geometry_freeze),
            spatial_freeze=spatial_freeze,
            state_freeze=state_freeze,
            contract=_load(args.contract),
            legacy=_load(args.legacy_contract),
            spatial_freeze_sha256=_sha256_file(args.spatial_freeze),
            state_freeze_sha256=_sha256_file(args.state_freeze),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealSpatialPartitionError,
        BorealDualIsolationOperatorError,
        Boreal19OperatorError,
    ) as exc:
        operator = None
        receipt = {
            "schema": "structural.boreal_19island_dual_isolation_operator_result.v1_00",
            "status": "STOP",
            "reason": str(exc),
            "species_occurrence_used_to_build_operator": False,
            "pilot_response_used_to_build_operator": False,
            "confirmatory_response_used_to_build_operator": False,
            "counts_as_empirical_evidence": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
        }
        code = 2
    else:
        code = 0

    if operator is not None and args.output_operator is not None:
        args.output_operator.parent.mkdir(parents=True, exist_ok=True)
        args.output_operator.write_text(
            json.dumps(operator, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
