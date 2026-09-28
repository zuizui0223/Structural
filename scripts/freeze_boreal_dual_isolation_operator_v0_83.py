#!/usr/bin/env python3
"""Freeze the response-independent boreal dual-isolation source operator."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Mapping

from scripts.freeze_boreal_spatial_partition_v0_75 import (
    load_geometry,
    load_universe,
)
from structural.boreal_dual_isolation_operator import (
    BorealDualIsolationOperatorError,
    freeze_connected_knn_operator,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_dual_isolation_operator_contract_v0_83.json"
)


class BorealDualIsolationFreezeError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BorealDualIsolationFreezeError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha256(value: Mapping) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def freeze(
    geometry_csv: Path,
    projection_receipt: Mapping,
    spatial_receipt: Mapping,
    *,
    spatial_receipt_sha256: str,
    contract: Mapping,
) -> tuple[dict, dict]:
    candidate = contract["candidate_id"]
    if projection_receipt.get("schema") != (
        "structural.boreal_lake_islands_safe_projection_result.v0_74"
    ):
        raise BorealDualIsolationFreezeError(
            "unexpected v0.74 projection receipt"
        )
    if projection_receipt.get("status") != (
        "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED"
    ):
        raise BorealDualIsolationFreezeError(
            "v0.74 safe projection did not qualify"
        )
    if projection_receipt.get("candidate_id") != candidate:
        raise BorealDualIsolationFreezeError(
            "v0.74 candidate identity mismatch"
        )
    if projection_receipt.get("protected_response_values_opened") is not False:
        raise BorealDualIsolationFreezeError(
            "v0.74 protected response boundary violated"
        )
    if projection_receipt.get("counts_as_empirical_evidence") is not False:
        raise BorealDualIsolationFreezeError(
            "v0.74 evidence boundary violated"
        )

    geometry = projection_receipt.get("geometry")
    if not isinstance(geometry, dict):
        raise BorealDualIsolationFreezeError(
            "v0.74 geometry receipt missing"
        )
    expected_geometry_sha = geometry.get("sha256")
    if not isinstance(expected_geometry_sha, str):
        raise BorealDualIsolationFreezeError(
            "v0.74 geometry SHA missing"
        )

    universe = load_universe()
    coordinates = load_geometry(
        geometry_csv,
        expected_sha256=expected_geometry_sha,
        universe=universe,
    )

    if spatial_receipt.get("schema") != (
        "structural.boreal_lake_islands_spatial_partition_result.v0_75"
    ):
        raise BorealDualIsolationFreezeError(
            "unexpected v0.75 spatial receipt"
        )
    if spatial_receipt.get("status") != (
        "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY"
    ):
        raise BorealDualIsolationFreezeError(
            "v0.75 spatial partition did not qualify"
        )
    if spatial_receipt.get("candidate_id") != candidate:
        raise BorealDualIsolationFreezeError(
            "v0.75 candidate identity mismatch"
        )
    if spatial_receipt.get("source_geometry_sha256") != expected_geometry_sha:
        raise BorealDualIsolationFreezeError(
            "v0.75 geometry binding differs from v0.74"
        )
    for key in (
        "species_occurrence_used",
        "richness_used",
        "habitat_values_used",
        "counts_as_empirical_evidence",
        "pilot_response_authorized",
        "confirmatory_response_authorized",
    ):
        if spatial_receipt.get(key) is not False:
            raise BorealDualIsolationFreezeError(
                f"v0.75 response/evidence boundary violated: {key}"
            )

    island_to_block = spatial_receipt.get("island_to_block")
    if not isinstance(island_to_block, dict):
        raise BorealDualIsolationFreezeError(
            "v0.75 island-to-block map missing"
        )
    if set(island_to_block) != set(universe):
        raise BorealDualIsolationFreezeError(
            "v0.75 island-to-block universe mismatch"
        )

    try:
        operator = freeze_connected_knn_operator(coordinates)
    except BorealDualIsolationOperatorError as exc:
        raise BorealDualIsolationFreezeError(str(exc)) from exc

    cross_block_edges = []
    for row in operator["edges"]:
        left = row["left"]
        right = row["right"]
        if island_to_block[left] != island_to_block[right]:
            cross_block_edges.append({
                "left": left,
                "right": right,
                "left_block": island_to_block[left],
                "right_block": island_to_block[right],
                "distance_km": row["distance_km"],
            })

    minimum_cross = contract[
        "required_cross_partition_support"
    ]["minimum_cross_block_edges"]
    if len(cross_block_edges) < minimum_cross:
        raise BorealDualIsolationFreezeError(
            "source operator has no usable cross-validation-block edge"
        )

    operator_fingerprint = canonical_sha256(operator)
    receipt = {
        "schema": "structural.boreal_dual_isolation_operator_result.v0_83",
        "status": "DUAL_ISOLATION_OPERATOR_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": candidate,
        "source_geometry_sha256": expected_geometry_sha,
        "source_spatial_receipt_sha256": spatial_receipt_sha256,
        "operator_fingerprint": operator_fingerprint,
        "selected_k": operator["selected_k"],
        "kernel_scale_km_hex": float(
            operator["kernel_scale_km"]
        ).hex(),
        "edge_count": len(operator["edges"]),
        "cross_v075_block_edge_count": len(cross_block_edges),
        "cross_v075_block_edges": cross_block_edges,
        "validation_radius_reused": False,
        "species_occurrence_used_to_build_operator": False,
        "pilot_response_used_to_build_operator": False,
        "confirmatory_response_used_to_build_operator": False,
        "counts_as_empirical_evidence": False,
        "confirmatory_response_authorized": False,
        "next_action": (
            "after a qualified v0.82 pilot, freeze the full confirmatory "
            "R0-R3-C scoring protocol using this exact operator fingerprint "
            "before any confirmatory occurrence cell is opened"
        ),
    }
    return operator, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geometry_csv", type=Path)
    parser.add_argument("projection_receipt", type=Path)
    parser.add_argument("spatial_receipt", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-operator", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_dual_isolation_operator_contract.v0_83"
        ):
            raise BorealDualIsolationFreezeError(
                "unexpected v0.83 contract schema"
            )
        operator, receipt = freeze(
            args.geometry_csv,
            _load(args.projection_receipt),
            _load(args.spatial_receipt),
            spatial_receipt_sha256=sha256_file(args.spatial_receipt),
            contract=contract,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealDualIsolationOperatorError,
        BorealDualIsolationFreezeError,
    ) as exc:
        operator = None
        receipt = {
            "schema": "structural.boreal_dual_isolation_operator_result.v0_83",
            "status": "STOP",
            "reason": str(exc),
            "species_occurrence_used_to_build_operator": False,
            "pilot_response_used_to_build_operator": False,
            "confirmatory_response_used_to_build_operator": False,
            "counts_as_empirical_evidence": False,
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

    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
