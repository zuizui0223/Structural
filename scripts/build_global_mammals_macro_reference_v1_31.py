#!/usr/bin/env python3
"""Freeze response-independent global mammal macro state and source operator v1.31."""
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import io
import json
import math
from pathlib import Path
from typing import Mapping, Sequence


EARTH_RADIUS_KM = 6371.0088
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/global_mammals_macro_reference_contract_v1_31.json"
)


class GlobalMammalMacroReferenceError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GlobalMammalMacroReferenceError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _number(value: object) -> float:
    text = str(value).strip()
    try:
        out = (
            float.fromhex(text)
            if text.lower().startswith(("0x", "+0x", "-0x"))
            else float(text)
        )
    except ValueError as exc:
        raise GlobalMammalMacroReferenceError(
            f"invalid numeric value: {text!r}"
        ) from exc
    if not math.isfinite(out):
        raise GlobalMammalMacroReferenceError(
            "nonfinite numeric safe covariate"
        )
    return out


def _population_mean_sd(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        raise GlobalMammalMacroReferenceError(
            "empty standardization vector"
        )
    xs = [float(x) for x in values]
    mean = math.fsum(xs) / len(xs)
    variance = math.fsum((x - mean) ** 2 for x in xs) / len(xs)
    sd = math.sqrt(variance)
    if not math.isfinite(sd) or sd <= 0.0:
        raise GlobalMammalMacroReferenceError(
            "zero/nonfinite population SD"
        )
    return mean, sd


def _type7_quantile(values: Sequence[float], p: float) -> float:
    xs = sorted(float(x) for x in values)
    if not xs:
        raise GlobalMammalMacroReferenceError("empty quantile vector")
    if not 0.0 <= p <= 1.0:
        raise GlobalMammalMacroReferenceError(
            "quantile outside [0,1]"
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


def _haversine(
    left: tuple[float, float],
    right: tuple[float, float],
) -> float:
    lat1, lon1 = map(math.radians, left)
    lat2, lon2 = map(math.radians, right)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2.0) ** 2
    )
    a = min(1.0, max(0.0, a))
    return EARTH_RADIUS_KM * (2.0 * math.asin(math.sqrt(a)))


def _spherical_mean(
    coordinates: Sequence[tuple[float, float]],
) -> tuple[float, float]:
    if not coordinates:
        raise GlobalMammalMacroReferenceError(
            "cannot form centroid of empty block"
        )
    sx = sy = sz = 0.0
    for lat_deg, lon_deg in coordinates:
        lat = math.radians(lat_deg)
        lon = math.radians(lon_deg)
        clat = math.cos(lat)
        sx += clat * math.cos(lon)
        sy += clat * math.sin(lon)
        sz += math.sin(lat)
    norm = math.sqrt(sx * sx + sy * sy + sz * sz)
    if not math.isfinite(norm) or norm <= 1e-15:
        raise GlobalMammalMacroReferenceError(
            "undefined spherical block centroid"
        )
    x, y, z = sx / norm, sy / norm, sz / norm
    lat = math.degrees(math.asin(max(-1.0, min(1.0, z))))
    lon = math.degrees(math.atan2(y, x))
    return lat, lon


def _adjacency(
    block_ids: Sequence[str],
    edges: Sequence[tuple[str, str, float]],
) -> dict[str, tuple[tuple[str, float], ...]]:
    raw = {block: [] for block in block_ids}
    for left, right, distance in edges:
        if left not in raw or right not in raw:
            raise GlobalMammalMacroReferenceError(
                "source edge references unknown block"
            )
        raw[left].append((right, float(distance)))
        raw[right].append((left, float(distance)))
    return {
        block: tuple(sorted(raw[block], key=lambda x: (x[0], x[1])))
        for block in block_ids
    }


def _connected(
    block_ids: Sequence[str],
    adjacency: Mapping[str, Sequence[tuple[str, float]]],
) -> bool:
    if not block_ids:
        return False
    seen = {block_ids[0]}
    stack = [block_ids[0]]
    while stack:
        node = stack.pop()
        for neighbor, _ in adjacency[node]:
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == len(block_ids)


def _dijkstra(
    source: str,
    adjacency: Mapping[str, Sequence[tuple[str, float]]],
) -> dict[str, float]:
    distances = {node: math.inf for node in adjacency}
    distances[source] = 0.0
    queue = [(0.0, source)]
    while queue:
        current, node = heapq.heappop(queue)
        if current > distances[node] + 1e-12:
            continue
        for neighbor, weight in adjacency[node]:
            candidate = current + float(weight)
            if candidate < distances[neighbor] - 1e-12:
                distances[neighbor] = candidate
                heapq.heappush(queue, (candidate, neighbor))
    if any(not math.isfinite(x) for x in distances.values()):
        raise GlobalMammalMacroReferenceError(
            "selected source graph is disconnected"
        )
    return distances


def _freeze_source_graph(
    block_centroids: Mapping[str, tuple[float, float]],
    block_bioregion: Mapping[str, str],
) -> dict:
    block_ids = tuple(sorted(block_centroids))
    if len(block_ids) < 2:
        raise GlobalMammalMacroReferenceError(
            "at least two source blocks required"
        )

    pair_distance: dict[tuple[str, str], float] = {}
    neighbor_rank: dict[str, list[tuple[float, str]]] = {
        block: [] for block in block_ids
    }
    for i, left in enumerate(block_ids):
        for right in block_ids[i + 1:]:
            distance = _haversine(
                block_centroids[left],
                block_centroids[right],
            )
            pair_distance[(left, right)] = distance
            neighbor_rank[left].append((distance, right))
            neighbor_rank[right].append((distance, left))
    for block in block_ids:
        neighbor_rank[block].sort(key=lambda x: (x[0], x[1]))

    selected_k = None
    selected_edges = None
    selected_adjacency = None
    connectivity_audit = []
    for k in range(1, len(block_ids)):
        edge_map: dict[tuple[str, str], float] = {}
        for block in block_ids:
            for distance, other in neighbor_rank[block][:k]:
                pair = tuple(sorted((block, other)))
                edge_map[pair] = float(distance)
        edges = tuple(
            (left, right, edge_map[(left, right)])
            for left, right in sorted(edge_map)
        )
        adjacency = _adjacency(block_ids, edges)
        connected = _connected(block_ids, adjacency)
        connectivity_audit.append({
            "k": k,
            "edge_count": len(edges),
            "connected": connected,
        })
        if connected:
            selected_k = k
            selected_edges = edges
            selected_adjacency = adjacency
            break

    if (
        selected_k is None
        or selected_edges is None
        or selected_adjacency is None
    ):
        raise GlobalMammalMacroReferenceError(
            "no connected block kNN graph found"
        )

    positive = [d for _, _, d in selected_edges if d > 0.0]
    kernel_scale = _type7_quantile(positive, 0.5)
    if not math.isfinite(kernel_scale) or kernel_scale <= 0.0:
        raise GlobalMammalMacroReferenceError(
            "invalid source-graph kernel scale"
        )

    all_paths = {
        block: _dijkstra(block, selected_adjacency)
        for block in block_ids
    }
    edge_set = {
        tuple(sorted((left, right)))
        for left, right, _ in selected_edges
    }

    generic = {}
    for block in block_ids:
        neighbors = tuple(
            neighbor for neighbor, _ in selected_adjacency[block]
        )
        path_values = [
            all_paths[block][other]
            for other in block_ids
            if other != block
        ]
        total = math.fsum(path_values)
        degree = len(neighbors)
        possible_pairs = degree * (degree - 1) // 2
        neighbor_edges = 0
        if possible_pairs:
            for i, left in enumerate(neighbors):
                for right in neighbors[i + 1:]:
                    if tuple(sorted((left, right))) in edge_set:
                        neighbor_edges += 1
        clustering = (
            neighbor_edges / possible_pairs
            if possible_pairs
            else 0.0
        )
        generic[block] = {
            "degree_fraction": degree / (len(block_ids) - 1),
            "mean_shortest_path_km": total / (len(block_ids) - 1),
            "closeness_per_km": (len(block_ids) - 1) / total,
            "local_clustering_coefficient": clustering,
        }

    cross_bioregion = sum(
        block_bioregion[left] != block_bioregion[right]
        for left, right, _ in selected_edges
    )
    shortest_rows = []
    for i, left in enumerate(block_ids):
        for right in block_ids[i + 1:]:
            shortest_rows.append({
                "left": left,
                "right": right,
                "distance_km_hex": float(
                    all_paths[left][right]
                ).hex(),
            })

    return {
        "schema": "structural.global_mammals_source_block_operator.v1_31",
        "operator": "minimal_connected_symmetrized_knn_over_frozen_block_centroids",
        "block_order": list(block_ids),
        "selected_k": selected_k,
        "kernel_scale_rule": (
            "Hyndman-Fan type-7 median of positive selected graph edge lengths"
        ),
        "kernel_scale_km_hex": float(kernel_scale).hex(),
        "block_centroids": {
            block: {
                "latitude_hex": float(block_centroids[block][0]).hex(),
                "longitude_hex": float(block_centroids[block][1]).hex(),
                "bioregion": block_bioregion[block],
            }
            for block in block_ids
        },
        "connectivity_audit": connectivity_audit,
        "edges": [
            {
                "left": left,
                "right": right,
                "distance_km_hex": float(distance).hex(),
            }
            for left, right, distance in selected_edges
        ],
        "generic_block_context": {
            block: {
                key: float(value).hex()
                for key, value in generic[block].items()
            }
            for block in block_ids
        },
        "all_pairs_shortest_paths": shortest_rows,
        "edge_count": len(selected_edges),
        "cross_bioregion_edge_count": cross_bioregion,
        "validation_tile_adjacency_reused": False,
        "response_used_to_build_operator": False,
    }


def build(
    *,
    safe_csv: Path,
    island_partition_csv: Path,
    block_table_csv: Path,
    contract: Mapping,
) -> tuple[str, str, dict]:
    safe_spec = contract["safe_covariate_artifact"]
    spatial_spec = contract["spatial_artifact"]
    if sha256_file(safe_csv) != safe_spec["safe_csv_sha256"]:
        raise GlobalMammalMacroReferenceError(
            "safe covariate CSV SHA mismatch"
        )
    if sha256_file(island_partition_csv) != spatial_spec[
        "island_partition_sha256"
    ]:
        raise GlobalMammalMacroReferenceError(
            "island partition CSV SHA mismatch"
        )
    if sha256_file(block_table_csv) != spatial_spec[
        "block_table_sha256"
    ]:
        raise GlobalMammalMacroReferenceError(
            "block table CSV SHA mismatch"
        )

    with safe_csv.open("r", encoding="utf-8", newline="") as handle:
        safe_reader = csv.DictReader(handle)
        safe_rows = list(safe_reader)
    with island_partition_csv.open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        partition_reader = csv.DictReader(handle)
        partition_rows = list(partition_reader)
    with block_table_csv.open(
        "r", encoding="utf-8", newline=""
    ) as handle:
        block_reader = csv.DictReader(handle)
        block_rows = list(block_reader)

    if len(safe_rows) != safe_spec["safe_row_count"]:
        raise GlobalMammalMacroReferenceError(
            "safe row count drift"
        )
    if len(partition_rows) != spatial_spec["island_count"]:
        raise GlobalMammalMacroReferenceError(
            "partition row count drift"
        )
    if len(block_rows) != spatial_spec["block_count"]:
        raise GlobalMammalMacroReferenceError(
            "block count drift"
        )

    safe_ids = [str(row["ID"]).strip() for row in safe_rows]
    partition_ids = [str(row["ID"]).strip() for row in partition_rows]
    if len(set(safe_ids)) != len(safe_ids):
        raise GlobalMammalMacroReferenceError(
            "duplicate safe IDs"
        )
    if set(safe_ids) != set(partition_ids):
        raise GlobalMammalMacroReferenceError(
            "safe/partition ID universe mismatch"
        )
    by_partition = {
        str(row["ID"]).strip(): row
        for row in partition_rows
    }

    safe_by_id = {}
    raw_features = {}
    coordinates = {}
    bioregions = []
    for row in safe_rows:
        island_id = str(row["ID"]).strip()
        bioregion = str(row["bioregion"]).strip()
        if not island_id or not bioregion:
            raise GlobalMammalMacroReferenceError(
                "blank ID or bioregion"
            )
        area = _number(row["Area"])
        if area <= 0.0:
            raise GlobalMammalMacroReferenceError(
                "Area must be strictly positive"
            )
        safe_by_id[island_id] = row
        bioregions.append(bioregion)
        coordinates[island_id] = (
            _number(row["Latitude_centroid"]),
            _number(row["Longitude_centroid"]),
        )
        raw_features[island_id] = {
            "Temperature_mean": _number(row["Temperature_mean"]),
            "Temperature_sd": _number(row["Temperature_sd"]),
            "Precipitation_mean": _number(row["Precipitation_mean"]),
            "Precipitation_sd": _number(row["Precipitation_sd"]),
            "Elevation_sd": _number(row["Elevation_sd"]),
            "LOG_AREA": math.log(area),
            "Current_isolation": _number(row["Current_isolation"]),
            "Past_isolation": _number(row["Past_isolation"]),
            "Climate_velocity": _number(row["Climate_velocity"]),
        }

    levels = tuple(sorted(set(bioregions)))
    if len(levels) != 12:
        raise GlobalMammalMacroReferenceError(
            "bioregion level count drift"
        )
    baseline = levels[0]
    if baseline != "Afrotropical":
        raise GlobalMammalMacroReferenceError(
            "fixed bioregion baseline drift"
        )

    raw_names = (
        "Temperature_mean",
        "Temperature_sd",
        "Precipitation_mean",
        "Precipitation_sd",
        "Elevation_sd",
        "LOG_AREA",
        "Current_isolation",
        "Past_isolation",
        "Climate_velocity",
    )
    output_names = (
        "TEMP_MEAN_Z",
        "TEMP_SD_Z",
        "PREC_MEAN_Z",
        "PREC_SD_Z",
        "ELEV_SD_Z",
        "LOG_AREA_Z",
        "CURRENT_ISOLATION_Z",
        "PAST_ISOLATION_Z",
        "CLIMATE_VELOCITY_Z",
    )
    constants = {}
    for raw_name in raw_names:
        mean, sd = _population_mean_sd([
            raw_features[island_id][raw_name]
            for island_id in safe_ids
        ])
        constants[raw_name] = {
            "mean": mean,
            "sd": sd,
        }

    state_out = io.StringIO(newline="")
    state_writer = csv.writer(state_out, lineterminator="\n")
    state_writer.writerow([
        "ID",
        "bioregion",
        "block_id",
        "split",
        "extreme_current_isolation",
        *output_names,
    ])
    for island_id in safe_ids:
        partition = by_partition[island_id]
        if str(partition["bioregion"]).strip() != str(
            safe_by_id[island_id]["bioregion"]
        ).strip():
            raise GlobalMammalMacroReferenceError(
                "safe/partition bioregion mismatch"
            )
        z_values = []
        for raw_name in raw_names:
            c = constants[raw_name]
            z = (
                raw_features[island_id][raw_name] - c["mean"]
            ) / c["sd"]
            z_values.append(float(z).hex())
        state_writer.writerow([
            island_id,
            str(safe_by_id[island_id]["bioregion"]).strip(),
            str(partition["block_id"]).strip(),
            str(partition["split"]).strip(),
            str(partition["extreme_current_isolation"]).strip(),
            *z_values,
        ])
    state_text = state_out.getvalue()

    block_members: dict[str, list[str]] = {}
    block_bioregion: dict[str, str] = {}
    for row in block_rows:
        block = str(row["block_id"]).strip()
        region = str(row["bioregion"]).strip()
        block_members[block] = []
        block_bioregion[block] = region
    for island_id in safe_ids:
        block = str(by_partition[island_id]["block_id"]).strip()
        if block not in block_members:
            raise GlobalMammalMacroReferenceError(
                "partition references unknown block"
            )
        block_members[block].append(island_id)
    for row in block_rows:
        block = str(row["block_id"]).strip()
        if len(block_members[block]) != int(row["island_count"]):
            raise GlobalMammalMacroReferenceError(
                "block island count drift"
            )
        if any(
            str(safe_by_id[island]["bioregion"]).strip()
            != block_bioregion[block]
            for island in block_members[block]
        ):
            raise GlobalMammalMacroReferenceError(
                "block spans multiple bioregions"
            )

    block_centroids = {
        block: _spherical_mean([
            coordinates[island]
            for island in block_members[block]
        ])
        for block in sorted(block_members)
    }
    operator = _freeze_source_graph(
        block_centroids,
        block_bioregion,
    )
    operator_text = (
        json.dumps(operator, indent=2, sort_keys=True) + "\n"
    )

    split_counts = {
        "pilot_blocks": sum(
            str(row["split"]).strip() == "pilot"
            for row in block_rows
        ),
        "confirmatory_blocks": sum(
            str(row["split"]).strip() == "confirmatory"
            for row in block_rows
        ),
        "pilot_islands": sum(
            str(row["split"]).strip() == "pilot"
            for row in partition_rows
        ),
        "confirmatory_islands": sum(
            str(row["split"]).strip() == "confirmatory"
            for row in partition_rows
        ),
    }
    if split_counts != {
        "pilot_blocks": spatial_spec["pilot_block_count"],
        "confirmatory_blocks": spatial_spec["confirmatory_block_count"],
        "pilot_islands": 1307,
        "confirmatory_islands": 4285,
    }:
        raise GlobalMammalMacroReferenceError(
            "frozen pilot/confirmatory support drift"
        )

    receipt = {
        "schema": "structural.global_mammals_macro_reference_result.v1_31",
        "status": contract["success_ceiling"]["status"],
        "candidate_id": contract["candidate_id"],
        "analysis_route": contract["analysis_route"],
        "island_count": len(safe_ids),
        "block_count": len(block_rows),
        "pilot_block_count": split_counts["pilot_blocks"],
        "confirmatory_block_count": split_counts[
            "confirmatory_blocks"
        ],
        "pilot_island_count": split_counts["pilot_islands"],
        "confirmatory_island_count": split_counts[
            "confirmatory_islands"
        ],
        "bioregion_levels": list(levels),
        "bioregion_baseline": baseline,
        "state_numeric_standardization": {
            raw_name: {
                "mean_hex": float(constants[raw_name]["mean"]).hex(),
                "sd_hex": float(constants[raw_name]["sd"]).hex(),
            }
            for raw_name in raw_names
        },
        "state_reference_sha256": sha256_text(state_text),
        "source_operator_sha256": sha256_text(operator_text),
        "source_operator": {
            "source_unit": "frozen validation block",
            "selected_k": operator["selected_k"],
            "edge_count": operator["edge_count"],
            "cross_bioregion_edge_count": operator[
                "cross_bioregion_edge_count"
            ],
            "kernel_scale_km_hex": operator[
                "kernel_scale_km_hex"
            ],
            "shortest_path_pair_count": len(
                operator["all_pairs_shortest_paths"]
            ),
            "validation_tile_adjacency_reused": False,
        },
        "later_R3_requirements": list(
            contract["later_training_only_source_semantics"][
                "R3_must_include"
            ]
        ),
        "later_C_adds_only": list(
            contract["later_training_only_source_semantics"][
                "C_adds_only"
            ]
        ),
        "Appendix_1_reopened": False,
        "mammal_species_names_opened": False,
        "mammal_occurrence_values_opened": False,
        "counts_as_fresh_confirmation": False,
        "fresh_system_denominator_contribution": 0,
        "original_fresh_chain_restored": False,
        "mechanism_claim_authorized": False,
        "contaminated_macro_protocol_may_be_built": True,
        "Appendix_1_response_access_authorized": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return state_text, operator_text, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--safe-csv", type=Path, required=True)
    parser.add_argument("--island-partition", type=Path, required=True)
    parser.add_argument("--block-table", type=Path, required=True)
    parser.add_argument("--state-output", type=Path)
    parser.add_argument("--operator-output", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.global_mammals_macro_reference_contract.v1_31"
        ):
            raise GlobalMammalMacroReferenceError(
                "unexpected v1.31 contract schema"
            )
        state_text, operator_text, receipt = build(
            safe_csv=args.safe_csv,
            island_partition_csv=args.island_partition,
            block_table_csv=args.block_table,
            contract=contract,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        GlobalMammalMacroReferenceError,
    ) as exc:
        state_text = None
        operator_text = None
        receipt = {
            "schema": "structural.global_mammals_macro_reference_result.v1_31",
            "status": "STOP",
            "reason": str(exc),
            "Appendix_1_reopened": False,
            "mammal_species_names_opened": False,
            "mammal_occurrence_values_opened": False,
            "counts_as_fresh_confirmation": False,
            "fresh_system_denominator_contribution": 0,
            "original_fresh_chain_restored": False,
            "mechanism_claim_authorized": False,
            "contaminated_macro_protocol_may_be_built": False,
            "Appendix_1_response_access_authorized": False,
        }
        code = 2
    else:
        code = 0

    if state_text is not None and args.state_output is not None:
        args.state_output.parent.mkdir(parents=True, exist_ok=True)
        args.state_output.write_text(state_text, encoding="utf-8")
    if operator_text is not None and args.operator_output is not None:
        args.operator_output.parent.mkdir(
            parents=True, exist_ok=True
        )
        args.operator_output.write_text(
            operator_text, encoding="utf-8"
        )
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
