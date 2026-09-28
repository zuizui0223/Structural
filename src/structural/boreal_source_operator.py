"""Frozen R2/R3/C source-pool operators for the boreal island test."""
from __future__ import annotations

import math
from typing import Mapping, Sequence

from structural.boreal_spatial_partition import (
    BorealSpatialPartitionError,
    connected_components,
    pairwise_distances,
)


class BorealSourceOperatorError(RuntimeError):
    pass


R2_FEATURES = (
    "nearest_other_island_km",
    "surrounding_island_pressure",
    "area_weighted_surrounding_landmass_pressure",
    "unanchored_component_exposure",
    "mainland_stepping_stone_frequency",
)

R3_SOURCE_FEATURES = (
    "training_global_occupied_fraction",
    "nearest_training_presence_km",
    "multi_source_pressure",
    "area_weighted_source_pressure",
)

C_FEATURES = (
    "occupied_component_frequency",
)


def unique_scales_km(values: Sequence[float]) -> tuple[float, ...]:
    scales = sorted({float(x) for x in values})
    if not scales:
        raise BorealSourceOperatorError("no source-operator scales")
    if not all(math.isfinite(x) and x > 0.0 for x in scales):
        raise BorealSourceOperatorError(
            "source-operator scales must be positive and finite"
        )
    return tuple(scales)


def scales_from_v075_result(result: Mapping) -> tuple[float, ...]:
    if result.get("schema") != (
        "structural.boreal_lake_islands_spatial_partition_result.v0_75"
    ):
        raise BorealSourceOperatorError("unexpected v0.75 result schema")
    if result.get("status") != (
        "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY"
    ):
        raise BorealSourceOperatorError("v0.75 spatial result did not qualify")

    radii = result.get("candidate_radii")
    if not isinstance(radii, Mapping):
        raise BorealSourceOperatorError("v0.75 candidate radii missing")
    labels = ("q25", "q50", "q75", "q90")
    if set(radii) != set(labels):
        raise BorealSourceOperatorError("v0.75 candidate-radius labels drift")
    return unique_scales_km(
        [float(radii[label]["rounded_up_km"]) for label in labels]
    )


def _validate_state(
    coordinates: Mapping[str, tuple[float, float]],
    area_ha: Mapping[str, float],
    mainland_distance_km: Mapping[str, float],
) -> tuple[str, ...]:
    ids = tuple(sorted(str(x) for x in coordinates))
    if len(ids) < 2:
        raise BorealSourceOperatorError("at least two island nodes required")
    if set(area_ha) != set(ids):
        raise BorealSourceOperatorError("area island set mismatch")
    if set(mainland_distance_km) != set(ids):
        raise BorealSourceOperatorError("mainland-distance island set mismatch")

    for island in ids:
        area = float(area_ha[island])
        mainland = float(mainland_distance_km[island])
        if not math.isfinite(area) or area <= 0.0:
            raise BorealSourceOperatorError(
                f"invalid source area for {island}"
            )
        if not math.isfinite(mainland) or mainland < 0.0:
            raise BorealSourceOperatorError(
                f"invalid mainland distance for {island}"
            )
    return ids


def _distance_lookup(
    coordinates: Mapping[str, tuple[float, float]],
) -> dict[tuple[str, str], float]:
    try:
        raw = pairwise_distances(coordinates)
    except BorealSpatialPartitionError as exc:
        raise BorealSourceOperatorError(str(exc)) from exc
    out = {}
    for (left, right), value in raw.items():
        out[(left, right)] = value
        out[(right, left)] = value
    for island in coordinates:
        out[(str(island), str(island))] = 0.0
    return out


def _component_maps(
    coordinates: Mapping[str, tuple[float, float]],
    scales: Sequence[float],
) -> dict[float, dict[str, frozenset[str]]]:
    result = {}
    for scale in scales:
        try:
            components = connected_components(coordinates, float(scale))
        except BorealSpatialPartitionError as exc:
            raise BorealSourceOperatorError(str(exc)) from exc
        mapping = {}
        for members in components:
            frozen = frozenset(members)
            for island in members:
                mapping[island] = frozen
        result[float(scale)] = mapping
    return result


def freeze_generic_geometry_context(
    coordinates: Mapping[str, tuple[float, float]],
    *,
    area_ha: Mapping[str, float],
    mainland_distance_km: Mapping[str, float],
    scales_km: Sequence[float],
) -> dict:
    """Compute response-independent R2 geometry terms for every island."""
    ids = _validate_state(coordinates, area_ha, mainland_distance_km)
    scales = unique_scales_km(scales_km)
    distance = _distance_lookup(coordinates)
    components = _component_maps(coordinates, scales)
    n = len(ids)

    rows = {}
    for target in ids:
        other_distances = [
            distance[(target, other)]
            for other in ids
            if other != target
        ]
        nearest_other = min(other_distances)

        pressure_by_scale = []
        area_pressure_by_scale = []
        exposure_by_scale = []
        mainland_step_by_scale = []

        for scale in scales:
            kernel = [
                math.exp(-distance[(target, other)] / scale)
                for other in ids
                if other != target
            ]
            weighted_kernel = [
                float(area_ha[other])
                * math.exp(-distance[(target, other)] / scale)
                for other in ids
                if other != target
            ]
            pressure_by_scale.append(
                math.log1p(math.fsum(kernel))
            )
            area_pressure_by_scale.append(
                math.log1p(math.fsum(weighted_kernel))
            )

            component = components[scale][target]
            exposure_by_scale.append(
                (len(component) - 1) / (n - 1)
            )
            mainland_step_by_scale.append(
                1.0
                if any(
                    float(mainland_distance_km[island]) <= scale
                    for island in component
                )
                else 0.0
            )

        rows[target] = {
            "nearest_other_island_km": nearest_other,
            "surrounding_island_pressure": (
                math.fsum(pressure_by_scale) / len(scales)
            ),
            "area_weighted_surrounding_landmass_pressure": (
                math.fsum(area_pressure_by_scale) / len(scales)
            ),
            "unanchored_component_exposure": (
                math.fsum(exposure_by_scale) / len(scales)
            ),
            "mainland_stepping_stone_frequency": (
                math.fsum(mainland_step_by_scale) / len(scales)
            ),
        }

    return {
        "island_ids": list(ids),
        "unique_scales_km": list(scales),
        "duplicate_named_scales_collapsed": True,
        "features": list(R2_FEATURES),
        "rows": rows,
    }


def training_source_features(
    target: str,
    *,
    training_islands: Sequence[str],
    training_presence_islands: Sequence[str],
    coordinates: Mapping[str, tuple[float, float]],
    area_ha: Mapping[str, float],
    scales_km: Sequence[float],
) -> dict:
    """Compute training-only R3 and C terms with focal self-exclusion."""
    ids = set(str(x) for x in coordinates)
    target = str(target)
    if target not in ids:
        raise BorealSourceOperatorError("target outside island universe")

    training = {str(x) for x in training_islands}
    presences = {str(x) for x in training_presence_islands}
    if not training <= ids:
        raise BorealSourceOperatorError("training island outside universe")
    if not presences <= training:
        raise BorealSourceOperatorError(
            "training presences must be a subset of training islands"
        )

    focal_self_excluded = target in training
    if focal_self_excluded:
        training.remove(target)
        presences.discard(target)

    if not training:
        raise BorealSourceOperatorError(
            "no effective training islands after focal self-exclusion"
        )
    if not presences:
        raise BorealSourceOperatorError(
            "no effective training presence after focal self-exclusion"
        )

    scales = unique_scales_km(scales_km)
    distance = _distance_lookup(coordinates)
    components = _component_maps(coordinates, scales)

    source_distances = [
        distance[(target, source)]
        for source in sorted(presences)
    ]
    nearest = min(source_distances)

    pressure_by_scale = []
    area_pressure_by_scale = []
    direct_by_scale = []
    connected_by_scale = []
    multihop_by_scale = []

    for scale in scales:
        unweighted = [
            math.exp(-distance[(target, source)] / scale)
            for source in sorted(presences)
        ]
        weighted = [
            float(area_ha[source])
            * math.exp(-distance[(target, source)] / scale)
            for source in sorted(presences)
        ]
        pressure_by_scale.append(
            math.log1p(math.fsum(unweighted))
        )
        area_pressure_by_scale.append(
            math.log1p(math.fsum(weighted))
        )

        direct = any(
            distance[(target, source)] <= scale + 1e-12
            for source in presences
        )
        connected = bool(
            components[scale][target] & presences
        )
        direct_by_scale.append(1.0 if direct else 0.0)
        connected_by_scale.append(1.0 if connected else 0.0)
        multihop_by_scale.append(
            1.0 if connected and not direct else 0.0
        )

    return {
        "training_island_count": len(training),
        "training_presence_count": len(presences),
        "focal_self_excluded": focal_self_excluded,
        "training_global_occupied_fraction": (
            len(presences) / len(training)
        ),
        "nearest_training_presence_km": nearest,
        "multi_source_pressure": (
            math.fsum(pressure_by_scale) / len(scales)
        ),
        "area_weighted_source_pressure": (
            math.fsum(area_pressure_by_scale) / len(scales)
        ),
        "occupied_component_frequency": (
            math.fsum(connected_by_scale) / len(scales)
        ),
        "direct_occupied_neighbor_frequency_diagnostic": (
            math.fsum(direct_by_scale) / len(scales)
        ),
        "multi_hop_only_frequency_diagnostic": (
            math.fsum(multihop_by_scale) / len(scales)
        ),
        "unique_scale_count": len(scales),
    }
