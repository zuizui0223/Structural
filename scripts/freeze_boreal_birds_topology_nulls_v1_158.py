#!/usr/bin/env python3
"""Freeze response-independent topology nulls for the boreal bird test v1.158."""
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
from collections import Counter
from pathlib import Path
from typing import Iterable, Mapping

from structural.boreal_dual_isolation_operator import freeze_connected_knn_operator
from structural.boreal_spatial_partition import pairwise_distances, type7_quantile


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_birds_topology_sensitivity_contract_v1_158.json"
)
DEFAULT_GEOMETRY = ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
DEFAULT_OPERATOR_FREEZE = (
    ROOT / "development/boreal_19island_source_operator_freeze_v1_01.json"
)


class BirdTopologyNullError(RuntimeError):
    pass


def canonical_sha256(value: Mapping) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def parse_number(value: object) -> float:
    text = str(value).strip()
    value_float = (
        float.fromhex(text)
        if text.lower().startswith(("0x", "+0x", "-0x"))
        else float(text)
    )
    if not math.isfinite(value_float):
        raise BirdTopologyNullError("nonfinite coordinate")
    return value_float


def load_geometry(path: Path) -> dict[str, tuple[float, float]]:
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    if len(rows) != 19:
        raise BirdTopologyNullError("expected exact 19-island geometry")
    if tuple(rows[0]) != ("Island", "Lat", "Long"):
        raise BirdTopologyNullError("unexpected geometry schema")
    out = {}
    for row in rows:
        island = str(row["Island"]).strip()
        if not island or island in out:
            raise BirdTopologyNullError("blank or duplicate island")
        out[island] = (parse_number(row["Lat"]), parse_number(row["Long"]))
    return out


def edge_pair(left: str, right: str) -> tuple[str, str]:
    if left == right:
        raise BirdTopologyNullError("self edge")
    return tuple(sorted((left, right)))


def edge_distance(
    distances: Mapping[tuple[str, str], float],
    pair: tuple[str, str],
) -> float:
    try:
        return float(distances[tuple(sorted(pair))])
    except KeyError as exc:
        raise BirdTopologyNullError(f"missing distance for edge {pair}") from exc


def adjacency(
    island_order: Iterable[str],
    edges: set[tuple[str, str]],
    distances: Mapping[tuple[str, str], float],
) -> dict[str, tuple[tuple[str, float], ...]]:
    raw = {island: [] for island in island_order}
    for left, right in sorted(edges):
        weight = edge_distance(distances, (left, right))
        raw[left].append((right, weight))
        raw[right].append((left, weight))
    return {
        island: tuple(sorted(values, key=lambda x: (x[0], x[1])))
        for island, values in raw.items()
    }


def connected(adj: Mapping[str, Iterable[tuple[str, float]]]) -> bool:
    ids = sorted(adj)
    if not ids:
        return False
    seen = {ids[0]}
    stack = [ids[0]]
    while stack:
        node = stack.pop()
        for neighbor, _ in adj[node]:
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == len(ids)


def dijkstra(
    source: str,
    adj: Mapping[str, Iterable[tuple[str, float]]],
) -> dict[str, float]:
    dist = {node: math.inf for node in adj}
    dist[source] = 0.0
    queue = [(0.0, source)]
    while queue:
        current, node = heapq.heappop(queue)
        if current > dist[node] + 1e-12:
            continue
        for neighbor, weight in adj[node]:
            candidate = current + float(weight)
            if candidate < dist[neighbor] - 1e-12:
                dist[neighbor] = candidate
                heapq.heappush(queue, (candidate, neighbor))
    if any(not math.isfinite(value) for value in dist.values()):
        raise BirdTopologyNullError("null graph disconnected")
    return dist


def degree_sequence(
    island_order: Iterable[str],
    edges: set[tuple[str, str]],
) -> dict[str, int]:
    out = {island: 0 for island in island_order}
    for left, right in edges:
        out[left] += 1
        out[right] += 1
    return out


def length_bin(distance: float, cutpoints: list[float]) -> int:
    for index, cutoff in enumerate(cutpoints):
        if distance <= cutoff + 1e-12:
            return index
    return len(cutpoints)


def deterministic_pair(
    edge_list: list[tuple[str, str]],
    *,
    null_index: int,
    attempt: int,
    salt: str,
) -> tuple[tuple[str, str], tuple[str, str], int]:
    digest = hashlib.sha256(
        f"{salt}|{null_index}|{attempt}".encode("utf-8")
    ).digest()
    n_edges = len(edge_list)
    first = int.from_bytes(digest[:8], "big") % n_edges
    second = int.from_bytes(digest[8:16], "big") % (n_edges - 1)
    if second >= first:
        second += 1
    return edge_list[first], edge_list[second], digest[16] & 1


def rewire_one(
    *,
    null_index: int,
    actual_edges: set[tuple[str, str]],
    island_order: list[str],
    distances: Mapping[tuple[str, str], float],
    cutpoints: list[float],
    target_swaps: int,
    salt: str,
    max_attempts: int = 100_000,
) -> tuple[set[tuple[str, str]], int]:
    edges = set(actual_edges)
    accepted = 0
    for attempt in range(max_attempts):
        if accepted >= target_swaps:
            return edges, attempt
        edge_list = sorted(edges)
        first, second, orientation = deterministic_pair(
            edge_list,
            null_index=null_index,
            attempt=attempt,
            salt=salt,
        )
        a, b = first
        c, d = second
        if len({a, b, c, d}) < 4:
            continue

        proposals = [
            (edge_pair(a, c), edge_pair(b, d)),
            (edge_pair(a, d), edge_pair(b, c)),
        ]
        if orientation:
            proposals.reverse()

        old_bins = sorted(
            [
                length_bin(edge_distance(distances, first), cutpoints),
                length_bin(edge_distance(distances, second), cutpoints),
            ]
        )
        for new_first, new_second in proposals:
            if new_first == new_second:
                continue
            if new_first in edges or new_second in edges:
                continue
            new_bins = sorted(
                [
                    length_bin(edge_distance(distances, new_first), cutpoints),
                    length_bin(edge_distance(distances, new_second), cutpoints),
                ]
            )
            if new_bins != old_bins:
                continue
            candidate = (edges - {first, second}) | {new_first, new_second}
            if not connected(adjacency(island_order, candidate, distances)):
                continue
            edges = candidate
            accepted += 1
            break
    raise BirdTopologyNullError(
        f"null {null_index} reached only {accepted}/{target_swaps} accepted swaps"
    )


def sensitivity_surface(
    *,
    actual_edges: set[tuple[str, str]],
    island_order: list[str],
    distances: Mapping[tuple[str, str], float],
    pilot_islands: list[str],
    confirmatory_islands: list[str],
    kernel_scale: float,
) -> list[dict]:
    adj = adjacency(island_order, actual_edges, distances)
    shortest = {target: dijkstra(target, adj) for target in confirmatory_islands}
    rows = []
    m = len(pilot_islands)
    for target in confirmatory_islands:
        weights = [
            math.exp(-shortest[target][source] / kernel_scale)
            for source in pilot_islands
        ]
        mean = math.fsum(weights) / m
        variance = math.fsum((value - mean) ** 2 for value in weights) / m
        h_value = variance / (mean * mean)
        rows.append(
            {
                "Island": target,
                "M": m,
                "mu_hex": float(mean).hex(),
                "variance_hex": float(variance).hex(),
                "H_hex": float(h_value).hex(),
                "H": h_value,
                "nearest_possible_source_km_hex": float(
                    min(shortest[target][source] for source in pilot_islands)
                ).hex(),
                "furthest_possible_source_km_hex": float(
                    max(shortest[target][source] for source in pilot_islands)
                ).hex(),
            }
        )
    return rows


def freeze(
    *,
    contract: Mapping,
    geometry: Mapping[str, tuple[float, float]],
    operator_freeze: Mapping,
) -> tuple[dict, list[dict]]:
    if contract.get("schema") != (
        "structural.boreal_19island_birds_topology_sensitivity_contract.v1_158"
    ):
        raise BirdTopologyNullError("unexpected v1.158 contract schema")
    if contract["response_boundary"]["bird_pilot_response_opened"] is not False:
        raise BirdTopologyNullError("bird response boundary already violated")

    operator = freeze_connected_knn_operator(geometry)
    observed_fingerprint = canonical_sha256(operator)
    expected_fingerprint = contract["actual_topology"]["operator_fingerprint"]
    if observed_fingerprint != expected_fingerprint:
        raise BirdTopologyNullError("actual topology fingerprint mismatch")
    if operator_freeze.get("operator_fingerprint") != expected_fingerprint:
        raise BirdTopologyNullError("parent operator freeze mismatch")

    island_order = list(operator["island_order"])
    distances = pairwise_distances(geometry)
    actual_edges = {
        edge_pair(row["left"], row["right"])
        for row in operator["edges"]
    }
    actual_lengths = [
        edge_distance(distances, pair) for pair in sorted(actual_edges)
    ]
    cutpoints = [
        type7_quantile(actual_lengths, p)
        for p in (0.20, 0.40, 0.60, 0.80)
    ]

    degree_target = degree_sequence(island_order, actual_edges)
    bin_target = Counter(
        length_bin(edge_distance(distances, edge), cutpoints)
        for edge in actual_edges
    )
    null_rule = contract["matched_topology_null"]
    nulls = []
    signatures = set()
    for index in range(int(null_rule["null_count"])):
        edges, attempts = rewire_one(
            null_index=index,
            actual_edges=actual_edges,
            island_order=island_order,
            distances=distances,
            cutpoints=cutpoints,
            target_swaps=int(null_rule["accepted_double_edge_swaps_per_null"]),
            salt=str(null_rule["scheduler_salt"]),
        )
        signature = tuple(sorted(edges))
        if signature == tuple(sorted(actual_edges)):
            raise BirdTopologyNullError("null equals actual topology")
        if signature in signatures:
            raise BirdTopologyNullError("duplicate null topology")
        signatures.add(signature)
        if degree_sequence(island_order, edges) != degree_target:
            raise BirdTopologyNullError("degree sequence drift")
        bins = Counter(
            length_bin(edge_distance(distances, edge), cutpoints)
            for edge in edges
        )
        if bins != bin_target:
            raise BirdTopologyNullError("edge-length-bin drift")
        if not connected(adjacency(island_order, edges, distances)):
            raise BirdTopologyNullError("null lost connectedness")
        nulls.append(
            {
                "null_index": index + 1,
                "accepted_swaps": int(
                    null_rule["accepted_double_edge_swaps_per_null"]
                ),
                "attempts": attempts,
                "edges": [
                    {
                        "left": left,
                        "right": right,
                        "distance_km_hex": float(
                            edge_distance(distances, (left, right))
                        ).hex(),
                        "length_bin": (
                            length_bin(
                                edge_distance(distances, (left, right)),
                                cutpoints,
                            )
                            + 1
                        ),
                    }
                    for left, right in sorted(edges)
                ],
            }
        )

    surface = sensitivity_surface(
        actual_edges=actual_edges,
        island_order=island_order,
        distances=distances,
        pilot_islands=list(contract["frozen_geography"]["pilot_islands"]),
        confirmatory_islands=list(
            contract["frozen_geography"]["confirmatory_islands"]
        ),
        kernel_scale=float(operator["kernel_scale_km"]),
    )

    freeze_object = {
        "schema": "structural.boreal_19island_birds_topology_null_freeze.v1_158",
        "status": "RESPONSE_INDEPENDENT_TOPOLOGY_NULLS_FROZEN",
        "candidate_id": contract["candidate_id"],
        "actual_operator_fingerprint": observed_fingerprint,
        "actual_edge_count": len(actual_edges),
        "actual_degree_sequence": degree_target,
        "edge_length_cutpoints_km_hex": [float(x).hex() for x in cutpoints],
        "edge_length_bin_counts": {
            str(index + 1): int(bin_target[index])
            for index in range(5)
        },
        "kernel_scale_km_hex": float(operator["kernel_scale_km"]).hex(),
        "null_count": len(nulls),
        "nulls": nulls,
        "bird_response_values_opened": 0,
        "counts_as_empirical_evidence": False,
    }
    return freeze_object, surface


def write_surface(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "Island",
        "M",
        "mu_hex",
        "variance_hex",
        "H_hex",
        "nearest_possible_source_km_hex",
        "furthest_possible_source_km_hex",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row[field] for field in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY)
    parser.add_argument(
        "--operator-freeze", type=Path, default=DEFAULT_OPERATOR_FREEZE
    )
    parser.add_argument("--output-nulls", type=Path, required=True)
    parser.add_argument("--output-surface", type=Path, required=True)
    args = parser.parse_args()

    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        operator_freeze = json.loads(
            args.operator_freeze.read_text(encoding="utf-8")
        )
        nulls, surface = freeze(
            contract=contract,
            geometry=load_geometry(args.geometry),
            operator_freeze=operator_freeze,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BirdTopologyNullError,
    ) as exc:
        print(
            json.dumps(
                {
                    "schema": (
                        "structural.boreal_19island_birds_topology_null_freeze.v1_158"
                    ),
                    "status": "STOP",
                    "reason": str(exc),
                    "bird_response_values_opened": 0,
                    "counts_as_empirical_evidence": False,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    args.output_nulls.parent.mkdir(parents=True, exist_ok=True)
    args.output_nulls.write_text(
        json.dumps(nulls, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_surface(args.output_surface, surface)
    summary = {
        "status": nulls["status"],
        "null_count": nulls["null_count"],
        "surface_rows": len(surface),
        "H_min": min(row["H"] for row in surface),
        "H_max": max(row["H"] for row in surface),
        "bird_response_values_opened": 0,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
