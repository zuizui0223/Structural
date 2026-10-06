"""Bird-specific wrapper around the frozen 19-island byte-level pilot router.

The CSV shape is the same island x species binary matrix used by the completed
beetle route. Only the six frozen pilot-island occurrence rows are decoded;
confirmatory and excluded-island occurrence bytes remain opaque.
"""
from __future__ import annotations

from typing import Mapping, Sequence

from structural.boreal_19island_beetle_pilot_router import (
    Boreal19BeetlePilotRouterError,
    RoutedBoreal19PilotSurface,
    build_boreal_19island_beetle_pilot_surface,
)


class Boreal19BirdPilotRouterError(RuntimeError):
    pass


def build_boreal_19island_bird_pilot_surface(
    *,
    response_csv_bytes: bytes,
    full_expected_islands: Sequence[str],
    analysis_expected_islands: Sequence[str],
    analysis_island_to_block: Mapping[str, str],
    pilot_partition: Sequence[str],
    confirmatory_partition: Sequence[str],
    expected_species_count: int = 54,
) -> RoutedBoreal19PilotSurface:
    try:
        return build_boreal_19island_beetle_pilot_surface(
            response_csv_bytes=response_csv_bytes,
            full_expected_islands=full_expected_islands,
            analysis_expected_islands=analysis_expected_islands,
            analysis_island_to_block=analysis_island_to_block,
            pilot_partition=pilot_partition,
            confirmatory_partition=confirmatory_partition,
            expected_species_count=expected_species_count,
        )
    except Boreal19BeetlePilotRouterError as exc:
        raise Boreal19BirdPilotRouterError(
            str(exc).replace("beetle", "bird")
        ) from exc
