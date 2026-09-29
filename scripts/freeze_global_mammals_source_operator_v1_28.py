#!/usr/bin/env python3
"""Freeze the global 219-block response-independent source operator v1.28."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Mapping, Sequence

from structural.boreal_dual_isolation_operator import (
    BorealDualIsolationOperatorError,
    freeze_connected_knn_operator,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/global_mammals_source_operator_contract_v1_28.json"
)


class GlobalMammalOperatorError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GlobalMammalOperatorError(f"{path.name} must contain a JSON object")
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


def parse_number(value: object, *, label: str) -> float:
    text = str(value).strip()
    try:
        out = (
            float.fromhex(text)
            if text.lower().startswith(("0x", "+0x", "-0x"))
            else float(text)
        )
    except ValueError as exc:
        raise GlobalMammalOperatorError(f"invalid numeric {label}") from exc
    if not math.isfinite(out):
        raise GlobalMammalOperatorError(f"nonfinite numeric {label}")
    return out


def load_inputs(
    safe_csv: Path,
    partition_csv: Path,
) -> tuple[list[dict], list[dict]]:
    with safe_csv.open("r", encoding="utf-8", newline="") as handle:
        safe = list(csv.DictReader(handle))
    with partition_csv.open("r", encoding="utf-8", newline="") as handle:
        part = list(csv.DictReader(handle))
    if len(safe) != 5592 or len(part) != 5592:
        raise GlobalMammalOperatorError("input population is not exact 5592 rows")
    safe_ids = [str(row["ID"]).strip() for row in safe]
    part_ids = [str(row["ID"]).strip() for row in part]
    if safe_ids != part_ids:
        raise GlobalMammalOperatorError("safe/partition ID order drift")
    return safe, part


def spherical_block_centroids(
    safe_rows: Sequence[Mapping[str, str]],
    part_rows: Sequence[Mapping[str, str]],
) -> tuple[
    dict[str, tuple[float, float]],
    dict[str, dict[str, object]],
    dict[str, str],
]:
    members: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
    meta: dict[str, dict[str, object]] = {}
    island_to_block: dict[str, str] = {}

    for safe, part in zip(safe_rows, part_rows):
        island_id = str(safe["ID"]).strip()
        if island_id != str(part["ID"]).strip():
            raise GlobalMammalOperatorError("safe/partition row order drift")
        block = str(part["block_id"]).strip()
        key = str(part["block_key"]).strip()
        region = str(part["bioregion"]).strip()
        split = str(part["split"]).strip()
        if not block or not key or not region or split not in {"pilot", "confirmatory"}:
            raise GlobalMammalOperatorError("invalid block metadata")
        lat = math.radians(parse_number(safe["Latitude_centroid"], label="latitude"))
        lon = math.radians(parse_number(safe["Longitude_centroid"], label="longitude"))
        members[block].append((
            math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat),
        ))
        island_to_block[island_id] = block
        observed = {
            "block_key": key,
            "bioregion": region,
            "split": split,
        }
        prior = meta.get(block)
        if prior is not None and prior != observed:
            raise GlobalMammalOperatorError(
                "inconsistent metadata within spatial block"
            )
        meta[block] = observed

    if len(members) != 219:
        raise GlobalMammalOperatorError("block support is not exact 219")

    coordinates = {}
    for block in sorted(members):
        vectors = members[block]
        x = math.fsum(v[0] for v in vectors) / len(vectors)
        y = math.fsum(v[1] for v in vectors) / len(vectors)
        z = math.fsum(v[2] for v in vectors) / len(vectors)
        norm = math.sqrt(x * x + y * y + z * z)
        if not math.isfinite(norm) or norm <= 1e-15:
            raise GlobalMammalOperatorError(
                f"invalid spherical centroid vector: {block}"
            )
        x, y, z = x / norm, y / norm, z / norm
        lat = math.degrees(math.asin(max(-1.0, min(1.0, z))))
        lon = math.degrees(math.atan2(y, x))
        coordinates[block] = (lat, lon)
        meta[block] = {
            **meta[block],
            "island_count": len(vectors),
            "centroid_latitude_hex": float(lat).hex(),
            "centroid_longitude_hex": float(lon).hex(),
        }
    if len(set(coordinates.values())) != len(coordinates):
        raise GlobalMammalOperatorError("duplicate exact block centroid")
    return coordinates, meta, island_to_block


def freeze(
    safe_rows: Sequence[Mapping[str, str]],
    part_rows: Sequence[Mapping[str, str]],
    contract: Mapping,
) -> tuple[dict, dict, str]:
    coords, meta, island_to_block = spherical_block_centroids(
        safe_rows, part_rows
    )
    try:
        graph = freeze_connected_knn_operator(coords)
    except BorealDualIsolationOperatorError as exc:
        raise GlobalMammalOperatorError(str(exc)) from exc

    expected_audit = contract["graph"]["expected_connectivity_audit"]
    observed_audit = graph["connectivity_audit"]
    if observed_audit != expected_audit:
        raise GlobalMammalOperatorError("kNN connectivity audit drift")
    if graph["selected_k"] != contract["graph"]["expected_selected_k"]:
        raise GlobalMammalOperatorError("selected k drift")
    if len(graph["edges"]) != contract["graph"]["expected_edge_count"]:
        raise GlobalMammalOperatorError("edge count drift")
    if float(graph["kernel_scale_km"]).hex() != contract["graph"][
        "expected_kernel_scale_km_hex"
    ]:
        raise GlobalMammalOperatorError("kernel scale drift")

    cross_split = 0
    cross_region = 0
    for edge in graph["edges"]:
        left = edge["left"]
        right = edge["right"]
        if meta[left]["split"] != meta[right]["split"]:
            cross_split += 1
        if meta[left]["bioregion"] != meta[right]["bioregion"]:
            cross_region += 1
    if cross_split != contract["graph"][
        "expected_pilot_confirmatory_cross_edge_count"
    ]:
        raise GlobalMammalOperatorError("pilot-confirmatory cross-edge count drift")
    if cross_region != contract["graph"]["expected_cross_bioregion_edge_count"]:
        raise GlobalMammalOperatorError("cross-bioregion edge count drift")

    operator = {
        **graph,
        "node_unit": "v1.25_spatial_block",
        "earth_radius_km": float(contract["source_geometry"]["earth_radius_km"]),
        "block_metadata": {
            block: meta[block]
            for block in sorted(meta)
        },
    }
    fingerprint = canonical_sha256(operator)

    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow([
        "ID",
        "block_id",
        "degree_fraction_hex",
        "mean_shortest_path_km_hex",
        "closeness_per_km_hex",
    ])
    context = graph["generic_node_context"]
    for safe, part in zip(safe_rows, part_rows):
        island_id = str(safe["ID"]).strip()
        block = island_to_block[island_id]
        node = context[block]
        writer.writerow([
            island_id,
            block,
            float(node["degree_fraction"]).hex(),
            float(node["mean_shortest_path_km"]).hex(),
            float(node["closeness_per_km"]).hex(),
        ])
    context_text = out.getvalue()

    receipt = {
        "schema": "structural.global_mammals_source_operator_result.v1_28",
        "status": contract["success_ceiling"]["status"],
        "candidate_id": contract["candidate_id"],
        "analysis_route": contract["analysis_route"],
        "block_count": len(coords),
        "island_count": len(safe_rows),
        "selected_k": graph["selected_k"],
        "edge_count": len(graph["edges"]),
        "kernel_scale_km_hex": float(graph["kernel_scale_km"]).hex(),
        "pilot_confirmatory_cross_edge_count": cross_split,
        "cross_bioregion_edge_count": cross_region,
        "operator_fingerprint": fingerprint,
        "island_generic_context_sha256": hashlib.sha256(
            context_text.encode("utf-8")
        ).hexdigest(),
        "validation_block_graph_reused": False,
        "Appendix_1_reopened": False,
        "mammal_species_names_opened": False,
        "mammal_occurrence_values_opened": False,
        "response_used_to_build_operator": False,
        "counts_as_fresh_confirmation": False,
        "fresh_system_denominator_contribution": 0,
        "original_fresh_chain_restored": False,
        "macro_pilot_protocol_may_be_built": True,
        "mammal_response_access_authorized": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return operator, receipt, context_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("safe_csv", type=Path)
    parser.add_argument("partition_csv", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--operator", type=Path)
    parser.add_argument("--island-context", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.global_mammals_source_operator_contract.v1_28"
        ):
            raise GlobalMammalOperatorError("unexpected v1.28 contract schema")
        if contract.get("status") != (
            "GLOBAL_BLOCK_GRAPH_SOURCE_OPERATOR_PREDECLARED"
        ):
            raise GlobalMammalOperatorError("v1.28 contract status drift")
        if sha256_file(args.safe_csv) != (
            "b60fbfd643b8a517d3a632a50db6b2b9916f9f3f34bae123ba7b7e89665b39e8"
        ):
            raise GlobalMammalOperatorError("safe CSV SHA mismatch")
        if sha256_file(args.partition_csv) != (
            "3f85efb3b71423a8392cb1f7a5590c7b03cedef377fee0997df457a029b998bd"
        ):
            raise GlobalMammalOperatorError("partition CSV SHA mismatch")
        safe_rows, part_rows = load_inputs(args.safe_csv, args.partition_csv)
        operator, receipt, context_text = freeze(
            safe_rows, part_rows, contract
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealDualIsolationOperatorError,
        GlobalMammalOperatorError,
    ) as exc:
        operator = None
        context_text = None
        receipt = {
            "schema": "structural.global_mammals_source_operator_result.v1_28",
            "status": "HOLD_GLOBAL_SOURCE_OPERATOR_FAILED",
            "reason": str(exc),
            "Appendix_1_reopened": False,
            "mammal_species_names_opened": False,
            "mammal_occurrence_values_opened": False,
            "response_used_to_build_operator": False,
            "counts_as_fresh_confirmation": False,
            "fresh_system_denominator_contribution": 0,
            "original_fresh_chain_restored": False,
            "macro_pilot_protocol_may_be_built": False,
            "mammal_response_access_authorized": False,
        }
        code = 2
    else:
        code = 0

    if operator is not None and args.operator is not None:
        args.operator.parent.mkdir(parents=True, exist_ok=True)
        args.operator.write_text(
            json.dumps(operator, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    if context_text is not None and args.island_context is not None:
        args.island_context.parent.mkdir(parents=True, exist_ok=True)
        args.island_context.write_text(context_text, encoding="utf-8")
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
