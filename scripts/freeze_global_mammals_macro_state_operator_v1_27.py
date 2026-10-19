#!/usr/bin/env python3
"""Freeze global-mammal macro state encoding and source operator v1.27.

This stage uses only the already-frozen 5,592-row Appendix 2 safe table and
response-independent spatial partition. Appendix 1 is never opened here.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import io
import json
import math
from pathlib import Path
import re
from typing import Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/global_mammals_macro_state_operator_contract_v1_27.json"
)
EARTH_RADIUS_KM = 6371.0088
SAFE_HEADER = (
    "ID",
    "Longitude_centroid",
    "Latitude_centroid",
    "Area",
    "Current_isolation",
    "Past_isolation",
    "Climate_velocity",
    "Temperature_mean",
    "Temperature_sd",
    "Precipitation_mean",
    "Precipitation_sd",
    "Elevation_sd",
    "bioregion",
)
PARTITION_HEADER = (
    "ID",
    "bioregion",
    "block_key",
    "block_id",
    "split",
    "Current_isolation_hex",
    "extreme_current_isolation",
)


class GlobalMammalStateOperatorError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise GlobalMammalStateOperatorError(
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


def canonical_sha256(value: Mapping) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _parse_number(value: object) -> float:
    text = str(value).strip()
    try:
        out = (
            float.fromhex(text)
            if text.lower().startswith(("0x", "+0x", "-0x"))
            else float(text)
        )
    except ValueError as exc:
        raise GlobalMammalStateOperatorError(
            f"invalid numeric value: {text!r}"
        ) from exc
    if not math.isfinite(out):
        raise GlobalMammalStateOperatorError("nonfinite numeric value")
    return out


def _id_fingerprint(ids: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for value in ids:
        digest.update(str(value).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _population_mean_sd(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        raise GlobalMammalStateOperatorError(
            "empty standardization vector"
        )
    if not all(math.isfinite(float(x)) for x in values):
        raise GlobalMammalStateOperatorError(
            "nonfinite standardization vector"
        )
    mean = math.fsum(float(x) for x in values) / len(values)
    variance = math.fsum(
        (float(x) - mean) ** 2 for x in values
    ) / len(values)
    sd = math.sqrt(variance)
    if not math.isfinite(sd) or sd <= 0.0:
        raise GlobalMammalStateOperatorError(
            "zero/nonfinite population SD"
        )
    return mean, sd


def _type7_quantile(values: Sequence[float], p: float) -> float:
    xs = sorted(float(x) for x in values)
    if not xs:
        raise GlobalMammalStateOperatorError("empty quantile vector")
    if not 0.0 <= p <= 1.0:
        raise GlobalMammalStateOperatorError(
            "quantile probability outside [0,1]"
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


def _haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(p1) * math.cos(p2)
        * math.sin(dlon / 2.0) ** 2
    )
    a = min(1.0, max(0.0, a))
    return EARTH_RADIUS_KM * 2.0 * math.asin(math.sqrt(a))


def _realm_column(level: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9]+", "_", level).strip("_")
    if not safe:
        raise GlobalMammalStateOperatorError(
            "blank realm dummy column after sanitization"
        )
    return f"REALM_{safe}"


def load_safe_rows(
    path: Path,
    *,
    contract: Mapping,
) -> list[dict[str, object]]:
    expected = contract["safe_artifact"]
    if sha256_file(path) != expected["safe_csv_sha256"]:
        raise GlobalMammalStateOperatorError(
            "v1.23 safe CSV SHA mismatch"
        )
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != SAFE_HEADER:
            raise GlobalMammalStateOperatorError(
                "unexpected v1.23 safe CSV header"
            )
        raw_rows = list(reader)
    if len(raw_rows) != int(expected["safe_row_count"]):
        raise GlobalMammalStateOperatorError(
            "v1.23 safe row count drift"
        )

    rows = []
    seen_ids = set()
    seen_coordinates = set()
    ids = []
    for raw in raw_rows:
        island = str(raw["ID"]).strip()
        if not island or not island.isascii() or not island.isdigit():
            raise GlobalMammalStateOperatorError(
                "safe ID is not unsigned decimal digits"
            )
        island = str(int(island, 10))
        if island in seen_ids:
            raise GlobalMammalStateOperatorError(
                f"duplicate safe ID: {island}"
            )
        seen_ids.add(island)
        ids.append(island)

        lon = _parse_number(raw["Longitude_centroid"])
        lat = _parse_number(raw["Latitude_centroid"])
        if not -180.0 <= lon <= 180.0:
            raise GlobalMammalStateOperatorError(
                f"longitude out of range: {island}"
            )
        if not -90.0 <= lat <= 90.0:
            raise GlobalMammalStateOperatorError(
                f"latitude out of range: {island}"
            )
        coordinate = (lat, lon)
        if coordinate in seen_coordinates:
            raise GlobalMammalStateOperatorError(
                "duplicate coordinate pair"
            )
        seen_coordinates.add(coordinate)

        area = _parse_number(raw["Area"])
        if area < 0.0:
            raise GlobalMammalStateOperatorError(
                f"negative island area: {island}"
            )
        past = _parse_number(raw["Past_isolation"])
        if past not in (0.0, 1.0):
            raise GlobalMammalStateOperatorError(
                "Past_isolation outside frozen binary domain"
            )
        bioregion = str(raw["bioregion"]).strip()
        if not bioregion:
            raise GlobalMammalStateOperatorError(
                "blank bioregion"
            )

        rows.append({
            "ID": island,
            "Longitude_centroid": lon,
            "Latitude_centroid": lat,
            "Area": area,
            "Current_isolation": _parse_number(
                raw["Current_isolation"]
            ),
            "Past_isolation": past,
            "Climate_velocity": _parse_number(
                raw["Climate_velocity"]
            ),
            "Temperature_mean": _parse_number(
                raw["Temperature_mean"]
            ),
            "Temperature_sd": _parse_number(
                raw["Temperature_sd"]
            ),
            "Precipitation_mean": _parse_number(
                raw["Precipitation_mean"]
            ),
            "Precipitation_sd": _parse_number(
                raw["Precipitation_sd"]
            ),
            "Elevation_sd": _parse_number(raw["Elevation_sd"]),
            "bioregion": bioregion,
        })

    if _id_fingerprint(ids) != expected["safe_id_order_sha256"]:
        raise GlobalMammalStateOperatorError(
            "safe ID order fingerprint drift"
        )
    return rows


def load_partition(
    path: Path,
    receipt_path: Path,
    *,
    contract: Mapping,
    safe_ids: Sequence[str],
) -> tuple[dict[str, dict[str, str]], dict]:
    expected = contract["spatial_artifact"]
    if sha256_file(path) != expected["island_partition_sha256"]:
        raise GlobalMammalStateOperatorError(
            "v1.25 island partition SHA mismatch"
        )
    if sha256_file(receipt_path) != expected[
        "spatial_receipt_raw_sha256"
    ]:
        raise GlobalMammalStateOperatorError(
            "v1.25 spatial receipt SHA mismatch"
        )
    receipt = _load(receipt_path)
    if receipt.get("schema") != (
        "structural.global_mammals_spatial_pilot_result.v1_25"
    ):
        raise GlobalMammalStateOperatorError(
            "unexpected v1.25 spatial receipt schema"
        )
    if receipt.get("status") != (
        "GLOBAL_SPATIAL_PILOT_DESIGN_FROZEN_RESPONSE_INDEPENDENTLY"
    ):
        raise GlobalMammalStateOperatorError(
            "v1.25 spatial design did not qualify"
        )
    if receipt.get("analysis_route") != (
        "contaminated_macro_analysis_only"
    ):
        raise GlobalMammalStateOperatorError(
            "spatial analysis route drift"
        )
    for key in (
        "response_used_in_spatial_design",
        "Appendix_1_reopened",
        "mammal_species_names_opened",
        "mammal_occurrence_values_opened",
        "counts_as_fresh_confirmation",
        "original_fresh_chain_restored",
    ):
        if receipt.get(key) is not False:
            raise GlobalMammalStateOperatorError(
                f"spatial response/freshness boundary violated: {key}"
            )
    if receipt.get("fresh_system_denominator_contribution") != 0:
        raise GlobalMammalStateOperatorError(
            "spatial fresh denominator drift"
        )

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != PARTITION_HEADER:
            raise GlobalMammalStateOperatorError(
                "unexpected v1.25 island partition header"
            )
        rows = list(reader)
    ids = [str(row["ID"]).strip() for row in rows]
    if ids != list(safe_ids):
        raise GlobalMammalStateOperatorError(
            "partition ID order differs from safe ID order"
        )
    mapping = {}
    for row in rows:
        island = str(row["ID"]).strip()
        split = str(row["split"]).strip()
        if split not in {"pilot", "confirmatory"}:
            raise GlobalMammalStateOperatorError(
                "unexpected spatial split label"
            )
        mapping[island] = {
            "bioregion": str(row["bioregion"]).strip(),
            "block_key": str(row["block_key"]).strip(),
            "block_id": str(row["block_id"]).strip(),
            "split": split,
            "extreme_current_isolation": str(
                row["extreme_current_isolation"]
            ).strip(),
        }
    return mapping, receipt


def freeze_state_reference(
    rows: Sequence[Mapping[str, object]],
    *,
    contract: Mapping,
) -> tuple[str, dict]:
    state = contract["state_reference"]
    levels = tuple(sorted({str(row["bioregion"]) for row in rows}))
    reference = state["categorical_reference"]["reference_level"]
    if reference not in levels:
        raise GlobalMammalStateOperatorError(
            "predeclared realm reference level absent"
        )
    if len(levels) != 12:
        raise GlobalMammalStateOperatorError(
            "bioregion level count drift"
        )
    dummy_levels = tuple(level for level in levels if level != reference)
    dummy_columns = tuple(_realm_column(level) for level in dummy_levels)
    if len(dummy_columns) != len(set(dummy_columns)):
        raise GlobalMammalStateOperatorError(
            "realm dummy names collide"
        )

    source_columns = (
        "Temperature_mean",
        "Temperature_sd",
        "Precipitation_mean",
        "Precipitation_sd",
        "Elevation_sd",
        "LOG10_AREA_PLUS1",
        "Current_isolation",
        "Past_isolation",
        "Climate_velocity",
    )
    raw = []
    for row in rows:
        area = float(row["Area"])
        transformed = {
            "Temperature_mean": float(row["Temperature_mean"]),
            "Temperature_sd": float(row["Temperature_sd"]),
            "Precipitation_mean": float(row["Precipitation_mean"]),
            "Precipitation_sd": float(row["Precipitation_sd"]),
            "Elevation_sd": float(row["Elevation_sd"]),
            "LOG10_AREA_PLUS1": math.log10(area + 1.0),
            "Current_isolation": float(row["Current_isolation"]),
            "Past_isolation": float(row["Past_isolation"]),
            "Climate_velocity": float(row["Climate_velocity"]),
        }
        raw.append(transformed)

    constants = {}
    for column in source_columns:
        mean, sd = _population_mean_sd(
            [row[column] for row in raw]
        )
        constants[column] = {"mean": mean, "sd": sd}

    z_names = {
        column: f"Z_{column}"
        for column in source_columns
    }
    header = (
        "ID",
        "bioregion",
        *dummy_columns,
        *(z_names[column] for column in source_columns),
    )
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(header)
    for source_row, transformed in zip(rows, raw):
        realm = str(source_row["bioregion"])
        values = [
            source_row["ID"],
            realm,
            *(
                1 if realm == level else 0
                for level in dummy_levels
            ),
        ]
        for column in source_columns:
            mean = constants[column]["mean"]
            sd = constants[column]["sd"]
            z = (transformed[column] - mean) / sd
            values.append(float(z).hex())
        writer.writerow(values)
    text = out.getvalue()

    r0_numeric = tuple(state["R0_numeric_source_columns"])
    r1_source = tuple(state["R1_add_source_columns"])
    r0_columns = list(dummy_columns) + [
        z_names[column] for column in r0_numeric
    ]
    r1_add = [
        z_names[
            "LOG10_AREA_PLUS1"
            if column == "Area"
            else column
        ]
        for column in r1_source
    ]
    receipt = {
        "bioregion_levels": list(levels),
        "bioregion_reference_level": reference,
        "realm_dummy_columns": list(dummy_columns),
        "source_columns": list(source_columns),
        "standardization_constants_hex": {
            column: {
                "mean_hex": float(values["mean"]).hex(),
                "sd_hex": float(values["sd"]).hex(),
            }
            for column, values in constants.items()
        },
        "R0_columns": r0_columns,
        "R1_add_columns": r1_add,
        "state_reference_columns": list(header),
        "state_reference_row_count": len(rows),
        "state_reference_sha256": sha256_text(text),
    }
    return text, receipt


def _update_top_k(
    heap: list[tuple[float, int, int]],
    *,
    distance_proxy: float,
    neighbor_numeric_id: int,
    neighbor_index: int,
    max_k: int,
) -> None:
    item = (
        -float(distance_proxy),
        -int(neighbor_numeric_id),
        int(neighbor_index),
    )
    if len(heap) < max_k:
        heapq.heappush(heap, item)
        return
    worst_distance = -heap[0][0]
    worst_id = -heap[0][1]
    if (
        distance_proxy < worst_distance
        or (
            distance_proxy == worst_distance
            and neighbor_numeric_id < worst_id
        )
    ):
        heapq.heapreplace(heap, item)


class _DSU:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.size = [1] * n
        self.components = n

    def find(self, x: int) -> int:
        parent = self.parent
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(self, a: int, b: int) -> bool:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return False
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.components -= 1
        return True


def freeze_source_operator(
    rows: Sequence[Mapping[str, object]],
    partition: Mapping[str, Mapping[str, str]],
    *,
    contract: Mapping,
) -> tuple[dict, dict]:
    spec = contract["source_operator"]
    max_k = int(spec["search_max_k"])
    n = len(rows)
    if max_k < 1 or max_k >= n:
        raise GlobalMammalStateOperatorError(
            "invalid kNN search ceiling"
        )

    ids = tuple(str(row["ID"]) for row in rows)
    numeric_ids = tuple(int(value) for value in ids)
    coordinates = tuple(
        (
            float(row["Latitude_centroid"]),
            float(row["Longitude_centroid"]),
        )
        for row in rows
    )
    xyz = []
    for lat, lon in coordinates:
        phi = math.radians(lat)
        lam = math.radians(lon)
        cos_phi = math.cos(phi)
        xyz.append((
            cos_phi * math.cos(lam),
            cos_phi * math.sin(lam),
            math.sin(phi),
        ))

    heaps: list[list[tuple[float, int, int]]] = [
        [] for _ in range(n)
    ]
    for i in range(n):
        xi, yi, zi = xyz[i]
        idi = numeric_ids[i]
        for j in range(i + 1, n):
            xj, yj, zj = xyz[j]
            dot = xi * xj + yi * yj + zi * zj
            dot = min(1.0, max(-1.0, dot))
            chord_sq = max(0.0, 2.0 - 2.0 * dot)
            _update_top_k(
                heaps[i],
                distance_proxy=chord_sq,
                neighbor_numeric_id=numeric_ids[j],
                neighbor_index=j,
                max_k=max_k,
            )
            _update_top_k(
                heaps[j],
                distance_proxy=chord_sq,
                neighbor_numeric_id=idi,
                neighbor_index=i,
                max_k=max_k,
            )

    neighbor_lists = []
    for heap in heaps:
        if len(heap) != max_k:
            raise GlobalMammalStateOperatorError(
                "incomplete nearest-neighbor heap"
            )
        neighbors = sorted(
            (
                (-item[0], -item[1], item[2])
                for item in heap
            ),
            key=lambda x: (x[0], x[1]),
        )
        neighbor_lists.append(neighbors)

    dsu = _DSU(n)
    selected_edges: set[tuple[int, int]] = set()
    audit = []
    selected_k = None
    for k in range(1, max_k + 1):
        for i in range(n):
            j = int(neighbor_lists[i][k - 1][2])
            pair = (i, j) if i < j else (j, i)
            if pair not in selected_edges:
                selected_edges.add(pair)
                dsu.union(pair[0], pair[1])
        audit.append({
            "k": k,
            "edge_count": len(selected_edges),
            "component_count": dsu.components,
            "connected": dsu.components == 1,
        })
        if dsu.components == 1:
            selected_k = k
            break

    if selected_k is None:
        raise GlobalMammalStateOperatorError(
            "source graph did not connect by frozen max_k"
        )

    ordered_edges = sorted(
        selected_edges,
        key=lambda pair: (
            numeric_ids[pair[0]],
            numeric_ids[pair[1]],
        ),
    )
    adjacency: list[set[int]] = [set() for _ in range(n)]
    incident_lengths: list[list[float]] = [[] for _ in range(n)]
    edge_rows = []
    edge_lengths = []
    cross_block = 0
    for i, j in ordered_edges:
        lat1, lon1 = coordinates[i]
        lat2, lon2 = coordinates[j]
        distance = _haversine_km(
            lat1, lon1, lat2, lon2
        )
        if distance <= 0.0 or not math.isfinite(distance):
            raise GlobalMammalStateOperatorError(
                "invalid selected source edge length"
            )
        adjacency[i].add(j)
        adjacency[j].add(i)
        incident_lengths[i].append(distance)
        incident_lengths[j].append(distance)
        edge_lengths.append(distance)
        left = ids[i]
        right = ids[j]
        if partition[left]["block_id"] != partition[right]["block_id"]:
            cross_block += 1
        edge_rows.append({
            "left": left,
            "right": right,
            "distance_km_hex": float(distance).hex(),
        })

    kernel_scale = _type7_quantile(edge_lengths, 0.50)
    context = {}
    for i, island in enumerate(ids):
        neighbors = adjacency[i]
        if not neighbors:
            raise GlobalMammalStateOperatorError(
                "selected source graph has isolated island"
            )
        two_hop = set(neighbors)
        for neighbor in neighbors:
            two_hop.update(adjacency[neighbor])
        two_hop.discard(i)
        context[island] = {
            "degree_fraction_hex": float(
                len(neighbors) / (n - 1)
            ).hex(),
            "mean_incident_edge_km_hex": float(
                math.fsum(incident_lengths[i])
                / len(incident_lengths[i])
            ).hex(),
            "two_hop_reach_fraction_hex": float(
                len(two_hop) / (n - 1)
            ).hex(),
        }

    expected = spec[
        "audit_expectations_from_response_independent_geometry"
    ]
    observed = {
        "selected_k": selected_k,
        "edge_count": len(edge_rows),
        "cross_validation_block_edge_count": cross_block,
        "kernel_scale_km_hex": float(kernel_scale).hex(),
    }
    if observed != expected:
        raise GlobalMammalStateOperatorError(
            "response-independent source-graph audit drift: "
            + json.dumps(observed, sort_keys=True)
        )

    operator_core = {
        "schema": "structural.global_mammals_source_operator.v1_27",
        "candidate_id": contract["candidate_id"],
        "analysis_route": contract["analysis_route"],
        "operator": "minimal_connected_global_symmetrized_knn",
        "island_order": list(ids),
        "selected_k": selected_k,
        "search_max_k": max_k,
        "kernel_scale_rule": spec["kernel_scale_rule"],
        "kernel_scale_km_hex": float(kernel_scale).hex(),
        "edge_count": len(edge_rows),
        "cross_validation_block_edge_count": cross_block,
        "connectivity_audit": audit,
        "generic_R2_context_columns": list(
            spec["generic_R2_context"]
        ),
        "generic_node_context": context,
        "edges": edge_rows,
        "validation_blocks_reused_as_source_components": False,
        "response_used_to_choose_k": False,
        "response_used_to_choose_kernel_scale": False,
        "Appendix_1_reopened": False,
        "mammal_species_names_opened": False,
        "mammal_occurrence_values_opened": False,
    }
    fingerprint = canonical_sha256(operator_core)
    operator = dict(operator_core)
    operator["operator_fingerprint"] = fingerprint
    receipt = {
        "source_operator_fingerprint": fingerprint,
        "selected_k": selected_k,
        "edge_count": len(edge_rows),
        "cross_validation_block_edge_count": cross_block,
        "kernel_scale_km_hex": float(kernel_scale).hex(),
        "connectivity_audit": audit,
    }
    return operator, receipt


def freeze(
    safe_csv: Path,
    island_partition: Path,
    spatial_receipt_path: Path,
    *,
    contract: Mapping,
) -> tuple[str, dict, dict]:
    if contract.get("schema") != (
        "structural.global_mammals_macro_state_operator_contract.v1_27"
    ):
        raise GlobalMammalStateOperatorError(
            "unexpected v1.27 contract schema"
        )
    if contract.get("status") != (
        "GLOBAL_MACRO_STATE_AND_SOURCE_OPERATOR_PREDECLARED"
    ):
        raise GlobalMammalStateOperatorError(
            "v1.27 contract status drift"
        )
    if contract.get("analysis_route") != (
        "contaminated_macro_analysis_only"
    ):
        raise GlobalMammalStateOperatorError(
            "v1.27 analysis route drift"
        )

    rows = load_safe_rows(safe_csv, contract=contract)
    safe_ids = tuple(str(row["ID"]) for row in rows)
    partition, spatial_receipt = load_partition(
        island_partition,
        spatial_receipt_path,
        contract=contract,
        safe_ids=safe_ids,
    )
    if {
        str(row["bioregion"]) for row in rows
    } != set(spatial_receipt["regional_audit"]):
        raise GlobalMammalStateOperatorError(
            "safe/spatial bioregion support mismatch"
        )

    state_text, state_receipt = freeze_state_reference(
        rows,
        contract=contract,
    )
    operator, operator_receipt = freeze_source_operator(
        rows,
        partition,
        contract=contract,
    )

    receipt = {
        "schema": (
            "structural.global_mammals_macro_state_operator_result.v1_27"
        ),
        "status": contract["success_ceiling"]["status"],
        "candidate_id": contract["candidate_id"],
        "analysis_route": contract["analysis_route"],
        "island_count": len(rows),
        "bioregion_count": len(
            state_receipt["bioregion_levels"]
        ),
        "state_reference": state_receipt,
        "source_operator": operator_receipt,
        "parent_safe_csv_sha256": sha256_file(safe_csv),
        "parent_island_partition_sha256": sha256_file(
            island_partition
        ),
        "parent_spatial_receipt_sha256": sha256_file(
            spatial_receipt_path
        ),
        "Appendix_1_reopened": False,
        "mammal_species_names_opened": False,
        "mammal_occurrence_values_opened": False,
        "response_used_in_state_reference": False,
        "response_used_in_source_operator": False,
        "counts_as_fresh_confirmation": False,
        "fresh_system_denominator_contribution": 0,
        "original_fresh_chain_restored": False,
        "mammal_response_access_authorized": False,
        "macro_response_model_design_may_be_built": True,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return state_text, operator, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("safe_csv", type=Path)
    parser.add_argument("island_partition", type=Path)
    parser.add_argument("spatial_receipt", type=Path)
    parser.add_argument(
        "--contract", type=Path, default=DEFAULT_CONTRACT
    )
    parser.add_argument("--state-reference", type=Path)
    parser.add_argument("--source-operator", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        state_text, operator, receipt = freeze(
            args.safe_csv,
            args.island_partition,
            args.spatial_receipt,
            contract=contract,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        GlobalMammalStateOperatorError,
    ) as exc:
        state_text = None
        operator = None
        receipt = {
            "schema": (
                "structural.global_mammals_macro_state_operator_result.v1_27"
            ),
            "status": "STOP",
            "reason": str(exc),
            "Appendix_1_reopened": False,
            "mammal_species_names_opened": False,
            "mammal_occurrence_values_opened": False,
            "counts_as_fresh_confirmation": False,
            "fresh_system_denominator_contribution": 0,
            "original_fresh_chain_restored": False,
            "mammal_response_access_authorized": False,
            "macro_response_model_design_may_be_built": False,
        }
        code = 2
    else:
        code = 0

    if state_text is not None and args.state_reference is not None:
        args.state_reference.parent.mkdir(
            parents=True, exist_ok=True
        )
        args.state_reference.write_text(
            state_text, encoding="utf-8"
        )
    if operator is not None and args.source_operator is not None:
        args.source_operator.parent.mkdir(
            parents=True, exist_ok=True
        )
        args.source_operator.write_text(
            json.dumps(operator, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    rendered = json.dumps(
        receipt, indent=2, sort_keys=True
    ) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
