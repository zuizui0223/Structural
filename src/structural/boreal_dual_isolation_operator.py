"""Response-independent source-connectivity operator for boreal lake islands.

The heldout partition and the source operator are intentionally distinct.

v0.75 defines heldout blocks as connected components under a sparse radius
chosen to leave enough disjoint spatial units. Reusing that same graph for
source continuity would make every source outside a heldout component
unreachable by construction. This module instead freezes a second,
response-independent graph from the same exact coordinates: the smallest
symmetrized k-nearest-neighbor graph that connects all 42 islands.

No biological response is used to choose k or the source-decay scale.
"""
from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from typing import Mapping, Sequence

from .boreal_spatial_partition import (
    BorealSpatialPartitionError,
    pairwise_distances,
    type7_quantile,
)


class BorealDualIsolationOperatorError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceFeatures:
    nearest_euclidean_km: float
    euclidean_source_pressure: float
    nearest_graph_path_km: float
    graph_source_pressure: float


def _distance(
    distances: Mapping[tuple[str, str], float],
    left: str,
    right: str,
) -> float:
    if left == right:
        return 0.0
    key = tuple(sorted((left, right)))
    try:
        return float(distances[key])
    except KeyError as exc:
        raise BorealDualIsolationOperatorError(
            f"missing pairwise distance: {left}, {right}"
        ) from exc


def _symmetrized_knn_edges(
    ids: Sequence[str],
    distances: Mapping[tuple[str, str], float],
    k: int,
) -> tuple[tuple[str, str, float], ...]:
    if k < 1 or k >= len(ids):
        raise BorealDualIsolationOperatorError("k outside valid range")

    edges: dict[tuple[str, str], float] = {}
    for island in ids:
        ranked = sorted(
            (
                (_distance(distances, island, other), other)
                for other in ids
                if other != island
            ),
            key=lambda item: (item[0], item[1]),
        )
        for distance, other in ranked[:k]:
            pair = tuple(sorted((island, other)))
            edges[pair] = float(distance)

    return tuple(
        (left, right, edges[(left, right)])
        for left, right in sorted(edges)
    )


def _adjacency(
    ids: Sequence[str],
    edges: Sequence[tuple[str, str, float]],
) -> dict[str, tuple[tuple[str, float], ...]]:
    raw: dict[str, list[tuple[str, float]]] = {
        island: [] for island in ids
    }
    for left, right, distance in edges:
        if left not in raw or right not in raw:
            raise BorealDualIsolationOperatorError(
                "edge references island outside frozen graph"
            )
        if not math.isfinite(distance) or distance < 0.0:
            raise BorealDualIsolationOperatorError(
                "invalid edge distance"
            )
        raw[left].append((right, float(distance)))
        raw[right].append((left, float(distance)))

    return {
        island: tuple(
            sorted(raw[island], key=lambda item: (item[0], item[1]))
        )
        for island in ids
    }


def _connected(
    ids: Sequence[str],
    adjacency: Mapping[str, Sequence[tuple[str, float]]],
) -> bool:
    if not ids:
        return False
    seen = {ids[0]}
    stack = [ids[0]]
    while stack:
        node = stack.pop()
        for neighbor, _ in adjacency[node]:
            if neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return len(seen) == len(ids)


def _dijkstra(
    source: str,
    adjacency: Mapping[str, Sequence[tuple[str, float]]],
) -> dict[str, float]:
    if source not in adjacency:
        raise BorealDualIsolationOperatorError(
            f"source outside graph: {source}"
        )

    distances = {node: math.inf for node in adjacency}
    distances[source] = 0.0
    queue: list[tuple[float, str]] = [(0.0, source)]

    while queue:
        current, node = heapq.heappop(queue)
        if current > distances[node] + 1e-12:
            continue
        for neighbor, weight in adjacency[node]:
            candidate = current + float(weight)
            if candidate < distances[neighbor] - 1e-12:
                distances[neighbor] = candidate
                heapq.heappush(queue, (candidate, neighbor))

    if any(not math.isfinite(value) for value in distances.values()):
        raise BorealDualIsolationOperatorError(
            "source graph is not connected"
        )
    return distances


def freeze_connected_knn_operator(
    coordinates: Mapping[str, tuple[float, float]],
) -> dict:
    """Freeze the smallest response-independent connected symmetrized kNN graph."""

    if len(coordinates) < 2:
        raise BorealDualIsolationOperatorError(
            "at least two islands required"
        )
    ids = tuple(sorted(str(island) for island in coordinates))
    if len(ids) != len(set(ids)) or set(ids) != set(coordinates):
        raise BorealDualIsolationOperatorError(
            "invalid island identity set"
        )

    try:
        euclidean = pairwise_distances(coordinates)
    except BorealSpatialPartitionError as exc:
        raise BorealDualIsolationOperatorError(str(exc)) from exc

    connectivity_audit = []
    selected_k = None
    selected_edges = None
    selected_adjacency = None

    for k in range(1, len(ids)):
        edges = _symmetrized_knn_edges(ids, euclidean, k)
        adjacency = _adjacency(ids, edges)
        connected = _connected(ids, adjacency)
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
        raise BorealDualIsolationOperatorError(
            "no connected kNN graph found"
        )

    positive_edge_lengths = [
        distance
        for _, _, distance in selected_edges
        if distance > 0.0
    ]
    if not positive_edge_lengths:
        raise BorealDualIsolationOperatorError(
            "connected graph has no positive edge length"
        )
    kernel_scale = type7_quantile(positive_edge_lengths, 0.50)
    if not math.isfinite(kernel_scale) or kernel_scale <= 0.0:
        raise BorealDualIsolationOperatorError(
            "invalid response-independent kernel scale"
        )

    shortest = {
        island: _dijkstra(island, selected_adjacency)
        for island in ids
    }

    generic_context = {}
    for island in ids:
        path_values = [
            shortest[island][other]
            for other in ids
            if other != island
        ]
        total = math.fsum(path_values)
        if total <= 0.0:
            raise BorealDualIsolationOperatorError(
                "invalid graph path total"
            )
        generic_context[island] = {
            "degree_fraction": (
                len(selected_adjacency[island]) / (len(ids) - 1)
            ),
            "mean_shortest_path_km": total / (len(ids) - 1),
            "closeness_per_km": (len(ids) - 1) / total,
        }

    return {
        "operator": "minimal_connected_symmetrized_knn",
        "selected_k": selected_k,
        "kernel_scale_rule": (
            "type7 median of positive selected-kNN edge lengths"
        ),
        "kernel_scale_km": float(kernel_scale),
        "island_order": list(ids),
        "connectivity_audit": connectivity_audit,
        "edges": [
            {
                "left": left,
                "right": right,
                "distance_km": float(distance),
            }
            for left, right, distance in selected_edges
        ],
        "generic_node_context": generic_context,
    }


def adjacency_from_operator(
    operator: Mapping,
) -> dict[str, tuple[tuple[str, float], ...]]:
    ids = tuple(operator.get("island_order") or ())
    if len(ids) < 2 or len(ids) != len(set(ids)):
        raise BorealDualIsolationOperatorError(
            "invalid operator island order"
        )
    raw_edges = operator.get("edges")
    if not isinstance(raw_edges, list):
        raise BorealDualIsolationOperatorError("operator edges missing")

    edges = []
    for row in raw_edges:
        if not isinstance(row, dict):
            raise BorealDualIsolationOperatorError(
                "invalid operator edge"
            )
        left = str(row.get("left", ""))
        right = str(row.get("right", ""))
        try:
            distance = float(row.get("distance_km"))
        except (TypeError, ValueError) as exc:
            raise BorealDualIsolationOperatorError(
                "invalid operator edge distance"
            ) from exc
        edges.append((left, right, distance))
    adjacency = _adjacency(ids, edges)
    if not _connected(ids, adjacency):
        raise BorealDualIsolationOperatorError(
            "frozen operator is not connected"
        )
    return adjacency


def source_features(
    *,
    target: str,
    occupied_sources: Sequence[str],
    coordinates: Mapping[str, tuple[float, float]],
    operator: Mapping,
) -> SourceFeatures:
    """Compute R3 Euclidean and C graph-path source features.

    occupied_sources must be training-only. The target itself is removed
    defensively if present, so a training row cannot predict itself from its
    own occurrence.
    """

    ids = tuple(operator.get("island_order") or ())
    graph_set = set(ids)
    if target not in graph_set:
        raise BorealDualIsolationOperatorError(
            f"target outside frozen graph: {target}"
        )
    if set(coordinates) != graph_set:
        raise BorealDualIsolationOperatorError(
            "coordinate universe differs from frozen operator"
        )

    sources = tuple(sorted({
        str(source)
        for source in occupied_sources
        if str(source) != target
    }))
    if not sources:
        raise BorealDualIsolationOperatorError(
            "no occupied training source after focal exclusion"
        )
    if not set(sources) <= graph_set:
        raise BorealDualIsolationOperatorError(
            "occupied source outside frozen graph"
        )

    try:
        euclidean = pairwise_distances(coordinates)
    except BorealSpatialPartitionError as exc:
        raise BorealDualIsolationOperatorError(str(exc)) from exc

    adjacency = adjacency_from_operator(operator)
    graph_paths = _dijkstra(target, adjacency)

    scale = float(operator.get("kernel_scale_km"))
    if not math.isfinite(scale) or scale <= 0.0:
        raise BorealDualIsolationOperatorError(
            "invalid frozen kernel scale"
        )

    euclidean_distances = [
        _distance(euclidean, target, source)
        for source in sources
    ]
    graph_distances = [
        graph_paths[source]
        for source in sources
    ]

    nearest_euclidean = min(euclidean_distances)
    nearest_graph = min(graph_distances)
    euclidean_pressure = math.fsum(
        math.exp(-distance / scale)
        for distance in euclidean_distances
    )
    graph_pressure = math.fsum(
        math.exp(-distance / scale)
        for distance in graph_distances
    )

    return SourceFeatures(
        nearest_euclidean_km=float(nearest_euclidean),
        euclidean_source_pressure=float(euclidean_pressure),
        nearest_graph_path_km=float(nearest_graph),
        graph_source_pressure=float(graph_pressure),
    )
