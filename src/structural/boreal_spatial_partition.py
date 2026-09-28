"""Response-independent spatial partitioning for the boreal lake-island test."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING
import hashlib
import math
from typing import Mapping, Sequence


EARTH_RADIUS_KM = 6371.0088


class BorealSpatialPartitionError(RuntimeError):
    pass


@dataclass(frozen=True)
class SpatialBlock:
    block_id: str
    islands: tuple[str, ...]
    rank_sha256: str


def haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    values = (lat1, lon1, lat2, lon2)
    if not all(math.isfinite(x) for x in values):
        raise BorealSpatialPartitionError("nonfinite coordinate")
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2.0) ** 2
    )
    a = min(1.0, max(0.0, a))
    return EARTH_RADIUS_KM * 2.0 * math.asin(math.sqrt(a))


def type7_quantile(values: Sequence[float], p: float) -> float:
    """Hyndman-Fan type 7 / R default linear quantile."""
    if not 0.0 <= p <= 1.0:
        raise BorealSpatialPartitionError("quantile p outside [0,1]")
    xs = sorted(float(x) for x in values)
    if not xs:
        raise BorealSpatialPartitionError("empty quantile vector")
    if not all(math.isfinite(x) for x in xs):
        raise BorealSpatialPartitionError("nonfinite quantile value")
    if len(xs) == 1:
        return xs[0]
    h = (len(xs) - 1) * p
    lo = int(math.floor(h))
    hi = int(math.ceil(h))
    if lo == hi:
        return xs[lo]
    frac = h - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


def round_up_tenth_km(value: float) -> float:
    if not math.isfinite(value) or value < 0:
        raise BorealSpatialPartitionError("invalid radius")
    rounded = Decimal(str(value)).quantize(
        Decimal("0.1"),
        rounding=ROUND_CEILING,
    )
    return float(rounded)


def _validate_coordinates(
    coordinates: Mapping[str, tuple[float, float]],
) -> dict[str, tuple[float, float]]:
    if not coordinates:
        raise BorealSpatialPartitionError("empty coordinate map")
    out: dict[str, tuple[float, float]] = {}
    for raw_island, raw_pair in coordinates.items():
        island = str(raw_island).strip()
        if not island:
            raise BorealSpatialPartitionError("blank island ID")
        if island in out:
            raise BorealSpatialPartitionError(f"duplicate island ID: {island}")
        if len(raw_pair) != 2:
            raise BorealSpatialPartitionError(
                f"coordinate pair malformed for {island}"
            )
        lat, lon = float(raw_pair[0]), float(raw_pair[1])
        if not math.isfinite(lat) or not math.isfinite(lon):
            raise BorealSpatialPartitionError(
                f"nonfinite coordinate for {island}"
            )
        if not -90.0 <= lat <= 90.0:
            raise BorealSpatialPartitionError(
                f"latitude outside [-90,90] for {island}"
            )
        if not -180.0 <= lon <= 180.0:
            raise BorealSpatialPartitionError(
                f"longitude outside [-180,180] for {island}"
            )
        out[island] = (lat, lon)
    return out


def pairwise_distances(
    coordinates: Mapping[str, tuple[float, float]],
) -> dict[tuple[str, str], float]:
    coords = _validate_coordinates(coordinates)
    ids = sorted(coords)
    distances: dict[tuple[str, str], float] = {}
    for i, left in enumerate(ids):
        for right in ids[i + 1 :]:
            lat1, lon1 = coords[left]
            lat2, lon2 = coords[right]
            distances[(left, right)] = haversine_km(
                lat1, lon1, lat2, lon2
            )
    return distances


def nearest_neighbor_distances(
    coordinates: Mapping[str, tuple[float, float]],
) -> dict[str, float]:
    coords = _validate_coordinates(coordinates)
    if len(coords) < 2:
        raise BorealSpatialPartitionError(
            "at least two islands required for nearest-neighbor distances"
        )
    distances = pairwise_distances(coords)
    out: dict[str, float] = {}
    for island in sorted(coords):
        candidates = [
            value
            for pair, value in distances.items()
            if island in pair
        ]
        out[island] = min(candidates)
    return out


def candidate_radii(
    coordinates: Mapping[str, tuple[float, float]],
) -> dict[str, dict[str, float]]:
    nn = nearest_neighbor_distances(coordinates)
    values = list(nn.values())
    result = {}
    for label, p in (
        ("q25", 0.25),
        ("q50", 0.50),
        ("q75", 0.75),
        ("q90", 0.90),
    ):
        raw = type7_quantile(values, p)
        result[label] = {
            "quantile": p,
            "raw_km": raw,
            "rounded_up_km": round_up_tenth_km(raw),
        }
    return result


def connected_components(
    coordinates: Mapping[str, tuple[float, float]],
    radius_km: float,
) -> tuple[tuple[str, ...], ...]:
    coords = _validate_coordinates(coordinates)
    if not math.isfinite(radius_km) or radius_km < 0:
        raise BorealSpatialPartitionError("invalid graph radius")

    ids = sorted(coords)
    adjacency = {island: set() for island in ids}
    for (left, right), distance in pairwise_distances(coords).items():
        if distance <= radius_km + 1e-12:
            adjacency[left].add(right)
            adjacency[right].add(left)

    unseen = set(ids)
    components: list[tuple[str, ...]] = []
    while unseen:
        seed = min(unseen)
        stack = [seed]
        members = []
        unseen.remove(seed)
        while stack:
            node = stack.pop()
            members.append(node)
            for neighbor in sorted(adjacency[node], reverse=True):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(members)))

    return tuple(sorted(components, key=lambda x: (x[0], len(x), x)))


def _component_id(members: Sequence[str]) -> str:
    payload = ",".join(sorted(members)).encode("utf-8")
    return "SC_" + hashlib.sha256(payload).hexdigest()[:12]


def _rank_sha(block_id: str, salt: str) -> str:
    return hashlib.sha256(
        f"{salt}|{block_id}".encode("utf-8")
    ).hexdigest()


def freeze_spatial_partition(
    coordinates: Mapping[str, tuple[float, float]],
    *,
    minimum_total_blocks: int = 9,
    minimum_pilot_blocks: int = 3,
    minimum_confirmatory_blocks: int = 6,
    pilot_fraction: float = 0.20,
    ranking_salt: str = "boreal-v0.75-pilot-split",
) -> dict:
    coords = _validate_coordinates(coordinates)
    if minimum_total_blocks < 1:
        raise BorealSpatialPartitionError(
            "minimum_total_blocks must be >=1"
        )
    if minimum_pilot_blocks < 1 or minimum_confirmatory_blocks < 1:
        raise BorealSpatialPartitionError(
            "pilot/confirmatory minima must be >=1"
        )
    if not 0.0 < pilot_fraction < 1.0:
        raise BorealSpatialPartitionError(
            "pilot_fraction must lie in (0,1)"
        )

    nn = nearest_neighbor_distances(coords)
    radii = candidate_radii(coords)
    candidate_audits = {}
    selected_label = None
    selected_components = None

    for label in ("q90", "q75", "q50", "q25"):
        radius = radii[label]["rounded_up_km"]
        components = connected_components(coords, radius)
        candidate_audits[label] = {
            "radius_km": radius,
            "component_count": len(components),
            "components": [list(x) for x in components],
            "meets_minimum_total_blocks": (
                len(components) >= minimum_total_blocks
            ),
        }
        if selected_label is None and len(components) >= minimum_total_blocks:
            selected_label = label
            selected_components = components

    if selected_label is None or selected_components is None:
        raise BorealSpatialPartitionError(
            "no frozen q25/q50/q75/q90 radius retains enough spatial blocks"
        )

    blocks: list[SpatialBlock] = []
    for members in selected_components:
        block_id = _component_id(members)
        blocks.append(
            SpatialBlock(
                block_id=block_id,
                islands=tuple(members),
                rank_sha256=_rank_sha(block_id, ranking_salt),
            )
        )
    if len({b.block_id for b in blocks}) != len(blocks):
        raise BorealSpatialPartitionError("spatial block ID collision")

    ranked = sorted(blocks, key=lambda b: (b.rank_sha256, b.block_id))
    n_blocks = len(ranked)
    pilot_count = max(
        minimum_pilot_blocks,
        math.ceil(pilot_fraction * n_blocks),
    )
    confirmatory_count = n_blocks - pilot_count
    if confirmatory_count < minimum_confirmatory_blocks:
        raise BorealSpatialPartitionError(
            "deterministic split leaves too few confirmatory spatial blocks"
        )

    pilot = ranked[:pilot_count]
    confirmatory = ranked[pilot_count:]
    island_to_block = {}
    for block in blocks:
        for island in block.islands:
            island_to_block[island] = block.block_id

    return {
        "status": "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY",
        "earth_radius_km": EARTH_RADIUS_KM,
        "distance_metric": "great_circle_haversine_decimal_degree_centers",
        "nearest_neighbor_km": {
            island: nn[island] for island in sorted(nn)
        },
        "candidate_radii": radii,
        "candidate_audits": candidate_audits,
        "selected_quantile": selected_label,
        "selected_radius_km": radii[selected_label]["rounded_up_km"],
        "spatial_block_count": n_blocks,
        "blocks": [
            {
                "block_id": block.block_id,
                "islands": list(block.islands),
                "rank_sha256": block.rank_sha256,
            }
            for block in sorted(blocks, key=lambda b: b.block_id)
        ],
        "island_to_block": {
            island: island_to_block[island]
            for island in sorted(island_to_block)
        },
        "pilot_block_count": len(pilot),
        "confirmatory_block_count": len(confirmatory),
        "pilot_block_ids": [block.block_id for block in pilot],
        "confirmatory_block_ids": [
            block.block_id for block in confirmatory
        ],
        "pilot_islands": sorted(
            island for block in pilot for island in block.islands
        ),
        "confirmatory_islands": sorted(
            island for block in confirmatory for island in block.islands
        ),
        "pilot_fraction_rule": pilot_fraction,
        "minimum_total_blocks": minimum_total_blocks,
        "minimum_pilot_blocks": minimum_pilot_blocks,
        "minimum_confirmatory_blocks": minimum_confirmatory_blocks,
        "ranking_salt": ranking_salt,
    }
