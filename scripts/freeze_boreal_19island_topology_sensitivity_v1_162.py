#!/usr/bin/env python3
"""Freeze response-independent topology nulls and configuration sensitivity.

This script reads only already committed 19-island geometry/spatial/operator
objects. It opens no bird, beetle, plant, richness, or confirmatory response.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import math
from collections import Counter
from pathlib import Path
from typing import Mapping

from structural.boreal_dual_isolation_operator import (
    freeze_connected_knn_operator,
)
from structural.boreal_spatial_partition import (
    pairwise_distances,
    type7_quantile,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GEOMETRY = ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
DEFAULT_GEOMETRY_FREEZE = ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
DEFAULT_SPATIAL = ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
DEFAULT_OPERATOR_FREEZE = ROOT / "development/boreal_19island_source_operator_freeze_v1_01.json"
DEFAULT_CONTRACT = ROOT / "development/boreal_bird_topology_sensitivity_contract_v1_162.json"


class TopologySensitivityError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TopologySensitivityError(f"{path.name} must contain an object")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def parse_number(text: str) -> float:
    s = str(text).strip()
    value = float.fromhex(s) if s.lower().startswith(("0x", "+0x", "-0x")) else float(s)
    if not math.isfinite(value):
        raise TopologySensitivityError("nonfinite geometry value")
    return value


def load_geometry(path: Path, freeze: Mapping) -> dict[str, tuple[float, float]]:
    if sha256_file(path) != freeze["geometry_sha256"]:
        raise TopologySensitivityError("geometry SHA drift")
    rows = list(csv.DictReader(path.read_text(encoding="utf-8").splitlines()))
    if len(rows) != 19 or tuple(rows[0]) != ("Island", "Lat", "Long"):
        raise TopologySensitivityError("unexpected geometry schema")
    out = {}
    for row in rows:
        island = str(row["Island"]).strip()
        if not island or island in out:
            raise TopologySensitivityError("blank/duplicate island")
        out[island] = (parse_number(row["Lat"]), parse_number(row["Long"]))
    if sorted(out) != list(freeze["island_order"]):
        raise TopologySensitivityError("geometry island identity drift")
    return out


def edge_key(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def graph_connected(ids: list[str], edges: set[tuple[str, str]]) -> bool:
    adjacency = {x: set() for x in ids}
    for left, right in edges:
        adjacency[left].add(right)
        adjacency[right].add(left)
    seen = {ids[0]}
    stack = [ids[0]]
    while stack:
        node = stack.pop()
        for neighbor in adjacency[node]:
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == len(ids)


def degree_map(ids: list[str], edges: set[tuple[str, str]]) -> dict[str, int]:
    degree = Counter()
    for left, right in edges:
        degree[left] += 1
        degree[right] += 1
    return {x: degree[x] for x in ids}


def hash_mod(seed: int, attempt: int, label: str, modulus: int) -> int:
    if modulus <= 0:
        raise TopologySensitivityError("invalid hash modulus")
    digest = hashlib.sha256(f"{seed}|{attempt}|{label}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % modulus


def edge_fingerprint(edges: set[tuple[str, str]], distance) -> str:
    payload = [
        {
            "left": left,
            "right": right,
            "distance_hex": float(distance(left, right)).hex(),
        }
        for left, right in sorted(edges)
    ]
    return canonical_sha256(payload)


def generate_null(
    *,
    actual_edges: set[tuple[str, str]],
    ids: list[str],
    distance,
    length_bin,
    seed: int,
    accepted_swaps_target: int = 80,
    max_attempts: int = 50000,
) -> tuple[set[tuple[str, str]], int, int]:
    edges = set(actual_edges)
    accepted = 0
    attempts = 0
    while attempts < max_attempts and accepted < accepted_swaps_target:
        attempts += 1
        by_bin = {idx: [] for idx in range(5)}
        for edge in sorted(edges):
            by_bin[length_bin(distance(*edge))].append(edge)
        bin_index = hash_mod(seed, attempts, "bin", 5)
        candidates = by_bin[bin_index]
        if len(candidates) < 2:
            continue
        i1 = hash_mod(seed, attempts, "i1", len(candidates))
        raw_i2 = hash_mod(seed, attempts, "i2", len(candidates) - 1)
        i2 = raw_i2 if raw_i2 < i1 else raw_i2 + 1
        e1, e2 = candidates[i1], candidates[i2]
        a, b = e1
        c, d = e2
        if len({a, b, c, d}) < 4:
            continue

        options = [
            (edge_key(a, c), edge_key(b, d)),
            (edge_key(a, d), edge_key(b, c)),
        ]
        if hash_mod(seed, attempts, "orient", 2) == 1:
            options.reverse()

        for n1, n2 in options:
            if n1 == n2 or n1 in edges or n2 in edges:
                continue
            if length_bin(distance(*n1)) != bin_index:
                continue
            if length_bin(distance(*n2)) != bin_index:
                continue
            proposed = (edges - {e1, e2}) | {n1, n2}
            if graph_connected(ids, proposed):
                edges = proposed
                accepted += 1
                break

    if accepted != accepted_swaps_target:
        raise TopologySensitivityError(
            f"null seed {seed} reached only {accepted} accepted swaps"
        )
    return edges, accepted, attempts


def adjacency(ids: list[str], edges: set[tuple[str, str]], distance):
    out = {x: [] for x in ids}
    for left, right in edges:
        weight = distance(left, right)
        out[left].append((right, weight))
        out[right].append((left, weight))
    return out


def shortest_paths(source: str, graph) -> dict[str, float]:
    values = {node: math.inf for node in graph}
    values[source] = 0.0
    queue = [(0.0, source)]
    while queue:
        current, node = heapq.heappop(queue)
        if current > values[node] + 1e-12:
            continue
        for neighbor, weight in graph[node]:
            candidate = current + weight
            if candidate < values[neighbor] - 1e-12:
                values[neighbor] = candidate
                heapq.heappush(queue, (candidate, neighbor))
    if any(not math.isfinite(x) for x in values.values()):
        raise TopologySensitivityError("disconnected graph in shortest-path calculation")
    return values


def freeze(
    *,
    geometry_path: Path,
    geometry_freeze: Mapping,
    spatial: Mapping,
    operator_freeze: Mapping,
    contract: Mapping,
) -> dict:
    if contract.get("schema") != "structural.boreal_bird_topology_sensitivity_contract.v1_162":
        raise TopologySensitivityError("unexpected protocol schema")
    if contract["response_boundary"]["bird_pilot_opened"] is not False:
        raise TopologySensitivityError("bird response boundary already open")

    coords = load_geometry(geometry_path, geometry_freeze)
    ids = sorted(coords)
    pairwise = pairwise_distances(coords)
    def distance(left: str, right: str) -> float:
        if left == right:
            return 0.0
        return float(pairwise[edge_key(left, right)])

    operator = freeze_connected_knn_operator(coords)
    if canonical_sha256(operator) != operator_freeze["operator_fingerprint"]:
        raise TopologySensitivityError("actual source-operator fingerprint drift")
    if operator["selected_k"] != 3 or len(operator["edges"]) != 35:
        raise TopologySensitivityError("unexpected actual graph structure")

    actual_edges = {
        edge_key(row["left"], row["right"]) for row in operator["edges"]
    }
    edge_lengths = sorted(distance(*edge) for edge in actual_edges)
    bounds = [type7_quantile(edge_lengths, p) for p in (0.2, 0.4, 0.6, 0.8)]
    def length_bin(value: float) -> int:
        for idx, bound in enumerate(bounds):
            if value <= bound + 1e-12:
                return idx
        return 4

    actual_bin_counts = Counter(length_bin(distance(*edge)) for edge in actual_edges)
    if [actual_bin_counts[i] for i in range(5)] != [7, 7, 7, 7, 7]:
        raise TopologySensitivityError("actual edge quintiles are not 7/7/7/7/7")
    actual_degrees = degree_map(ids, actual_edges)

    nulls = []
    fingerprints = set()
    for seed in contract["response_free_topology_surface"]["seeds"]:
        edges, accepted, attempts = generate_null(
            actual_edges=actual_edges,
            ids=ids,
            distance=distance,
            length_bin=length_bin,
            seed=int(seed),
        )
        if degree_map(ids, edges) != actual_degrees:
            raise TopologySensitivityError("null degree sequence drift")
        counts = Counter(length_bin(distance(*edge)) for edge in edges)
        if [counts[i] for i in range(5)] != [7, 7, 7, 7, 7]:
            raise TopologySensitivityError("null edge-length-bin count drift")
        if not graph_connected(ids, edges):
            raise TopologySensitivityError("null disconnected")
        fingerprint = edge_fingerprint(edges, distance)
        if fingerprint in fingerprints:
            raise TopologySensitivityError("duplicate null topology")
        fingerprints.add(fingerprint)
        nulls.append({
            "seed": int(seed),
            "accepted_swaps": accepted,
            "attempts": attempts,
            "edge_fingerprint": fingerprint,
        })

    pilot = list(spatial["pilot_islands"])
    confirmatory = list(spatial["confirmatory_islands"])
    if pilot != contract["frozen_geography"]["pilot_islands"]:
        raise TopologySensitivityError("pilot-island drift")
    if confirmatory != contract["frozen_geography"]["confirmatory_islands"]:
        raise TopologySensitivityError("confirmatory-island drift")

    graph = adjacency(ids, actual_edges, distance)
    kernel_scale = float(operator["kernel_scale_km"])
    M = len(pilot)
    sensitivity = {}
    for target in confirmatory:
        paths = shortest_paths(target, graph)
        weights = [math.exp(-paths[source] / kernel_scale) for source in pilot]
        mu = math.fsum(weights) / M
        sigma2 = math.fsum((x - mu) ** 2 for x in weights) / M
        H = sigma2 / (mu * mu)
        by_n = {}
        for n in range(2, M + 1):
            factor = (M - n) / (n * (M - 1))
            by_n[str(n)] = float(factor * H).hex()
        sensitivity[target] = {
            "mu_hex": float(mu).hex(),
            "sigma2_hex": float(sigma2).hex(),
            "heterogeneity_H_hex": float(H).hex(),
            "S_by_n_hex": by_n,
        }

    return {
        "schema": "structural.boreal_19island_topology_sensitivity_freeze.v1_162",
        "status": "RESPONSE_FREE_TOPOLOGY_NULL_AND_SENSITIVITY_SURFACE_FROZEN",
        "candidate_id": contract["candidate_id"],
        "parents": {
            "geometry_sha256": geometry_freeze["geometry_sha256"],
            "spatial_freeze_sha256": sha256_file(DEFAULT_SPATIAL),
            "source_operator_fingerprint": operator_freeze["operator_fingerprint"],
            "bird_response_sha256": contract["response_file"]["expected_sha256"],
        },
        "actual_graph": {
            "selected_k": operator["selected_k"],
            "edge_count": len(actual_edges),
            "edge_fingerprint": edge_fingerprint(actual_edges, distance),
            "kernel_scale_km_hex": kernel_scale.hex(),
            "degree_sequence": actual_degrees,
            "edge_length_quintile_bounds_km_hex": [float(x).hex() for x in bounds],
            "edge_length_bin_counts": [7, 7, 7, 7, 7],
        },
        "null_ensemble": {
            "count": len(nulls),
            "accepted_swaps_per_null": 80,
            "all_connected": True,
            "degree_sequence_exactly_preserved": True,
            "edge_length_bin_counts_exactly_preserved": True,
            "unique_topologies": len(fingerprints),
            "nulls": nulls,
        },
        "configuration_sensitivity": {
            "possible_source_count_M": M,
            "pilot_source_candidates": pilot,
            "definition": "S_i(n)=[(M-n)/(n(M-1))]*(sigma_i^2/mu_i^2)",
            "n_domain": [2, 3, 4, 5, 6],
            "targets": sensitivity,
        },
        "response_boundary": {
            "bird_values_read": 0,
            "beetle_values_reopened": 0,
            "plant_values_read": 0,
            "eBird_enabled": False,
            "counts_as_empirical_evidence": False,
        },
        "next_action": (
            "commit this response-free surface; only then may a separate bird-pilot "
            "authorization decode the six frozen pilot islands"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY)
    parser.add_argument("--geometry-freeze", type=Path, default=DEFAULT_GEOMETRY_FREEZE)
    parser.add_argument("--spatial", type=Path, default=DEFAULT_SPATIAL)
    parser.add_argument("--operator-freeze", type=Path, default=DEFAULT_OPERATOR_FREEZE)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = freeze(
        geometry_path=args.geometry,
        geometry_freeze=load_json(args.geometry_freeze),
        spatial=load_json(args.spatial),
        operator_freeze=load_json(args.operator_freeze),
        contract=load_json(args.contract),
    )
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
