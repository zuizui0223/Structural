"""Pilot-only router for the frozen 19-island boreal bird mechanism test.

This module deliberately reuses the already-audited byte-level 19-island router
from the beetle route. Only the expected species count changes. It additionally
records each fixed bird species' pilot occupancy count n, which is the only
response-derived quantity needed to map the pre-response S_i(n) surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from structural.boreal_19island_beetle_pilot_router import (
    Boreal19BeetlePilotRouterError,
    RoutedBoreal19PilotSurface,
    build_boreal_19island_beetle_pilot_surface,
)
from structural.boreal_beetle_pilot_router import decode_binary_vector_hex


class Boreal19BirdPilotRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class RoutedBoreal19BirdPilotSurface:
    base: RoutedBoreal19PilotSurface
    pilot_occupancy_count_by_species: tuple[tuple[str, int], ...]
    distinct_pilot_occupancy_counts: tuple[int, ...]


def build_boreal_19island_bird_pilot_surface(
    *,
    response_csv_bytes: bytes,
    full_expected_islands: Sequence[str],
    analysis_expected_islands: Sequence[str],
    analysis_island_to_block: Mapping[str, str],
    pilot_partition: Sequence[str],
    confirmatory_partition: Sequence[str],
    expected_species_count: int = 54,
) -> RoutedBoreal19BirdPilotSurface:
    try:
        base = build_boreal_19island_beetle_pilot_surface(
            response_csv_bytes=response_csv_bytes,
            full_expected_islands=full_expected_islands,
            analysis_expected_islands=analysis_expected_islands,
            analysis_island_to_block=analysis_island_to_block,
            pilot_partition=pilot_partition,
            confirmatory_partition=confirmatory_partition,
            expected_species_count=expected_species_count,
        )
    except Boreal19BeetlePilotRouterError as exc:
        raise Boreal19BirdPilotRouterError(str(exc)) from exc

    count = base.pilot_species_universe_count
    vectors = []
    for _, encoded in base.pilot_targets_hex_by_island:
        try:
            vectors.append(decode_binary_vector_hex(encoded, count))
        except Exception as exc:
            raise Boreal19BirdPilotRouterError(
                "failed to decode frozen bird pilot target vector"
            ) from exc

    occupancy = []
    for j, species in enumerate(base.pilot_species_universe):
        n = sum(vector[j] for vector in vectors)
        if n < 2 or n > base.pilot_island_count:
            raise Boreal19BirdPilotRouterError(
                "bird pilot species occupancy count outside frozen eligibility domain"
            )
        occupancy.append((species, int(n)))

    return RoutedBoreal19BirdPilotSurface(
        base=base,
        pilot_occupancy_count_by_species=tuple(occupancy),
        distinct_pilot_occupancy_counts=tuple(sorted({n for _, n in occupancy})),
    )
