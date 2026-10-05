"""Byte-level pilot router for the sealed 19-island boreal bird test.

Only the Island routing field is decoded for all 42 source rows. Bird occurrence
cells are decoded only for the six frozen pilot islands. Occurrence bytes for
the 13 confirmatory analysis islands and 23 excluded source islands remain
opaque.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Mapping, Sequence

from structural.boreal_beetle_pilot_router import (
    _decode_utf8,
    _iter_csv_records_bytes,
    _species_universe_sha,
    encode_binary_vector_hex,
)


class Boreal19BirdPilotRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class RoutedBoreal19BirdPilot:
    source_response_rows_seen: int
    routing_island_fields_decoded: int
    pilot_island_rows_semantically_parsed: int
    pilot_target_values_parsed: int
    confirmatory_target_values_parsed: int
    excluded_target_values_parsed: int
    header_species_names_parsed: int
    eligible_species: tuple[str, ...]
    eligible_species_count: int
    eligible_species_sha256: str
    pilot_support_counts: tuple[tuple[str, int], ...]
    pilot_island_order: tuple[str, ...]
    pilot_targets_hex_by_island: tuple[tuple[str, str], ...]
    raw_pilot_surface_sha256: str
    confirmatory_occurrence_values_stored: bool
    excluded_occurrence_values_stored: bool


def route_bird_pilot(
    *,
    response_csv_bytes: bytes,
    full_expected_islands: Sequence[str],
    pilot_islands: Sequence[str],
    confirmatory_islands: Sequence[str],
    expected_species_count: int = 54,
    min_support: int = 1,
    max_support: int = 4,
    minimum_eligible_species: int = 12,
) -> RoutedBoreal19BirdPilot:
    full = tuple(full_expected_islands)
    full_set = set(full)
    pilot = tuple(pilot_islands)
    pilot_set = set(pilot)
    confirmatory = tuple(confirmatory_islands)
    confirmatory_set = set(confirmatory)

    if len(full) != 42 or len(full_set) != 42:
        raise Boreal19BirdPilotRouterError("full island universe must contain 42 unique islands")
    if len(pilot) != 6 or len(pilot_set) != 6:
        raise Boreal19BirdPilotRouterError("pilot island universe must contain six unique islands")
    if len(confirmatory) != 13 or len(confirmatory_set) != 13:
        raise Boreal19BirdPilotRouterError(
            "confirmatory island universe must contain 13 unique islands"
        )
    if pilot_set & confirmatory_set:
        raise Boreal19BirdPilotRouterError("pilot/confirmatory island overlap")
    if not (pilot_set | confirmatory_set) < full_set:
        raise Boreal19BirdPilotRouterError(
            "19-island analysis universe must be a strict subset of 42 islands"
        )
    if not (1 <= min_support <= max_support < len(pilot)):
        raise Boreal19BirdPilotRouterError("invalid frozen pilot support rule")

    records = _iter_csv_records_bytes(response_csv_bytes)
    try:
        header = next(records)
    except StopIteration as exc:
        raise Boreal19BirdPilotRouterError("bird response CSV is empty") from exc
    if header and header[0].startswith(b"\xef\xbb\xbf"):
        header = (header[0][3:],) + header[1:]
    if len(header) != expected_species_count + 1:
        raise Boreal19BirdPilotRouterError("bird response header species-count mismatch")
    first = _decode_utf8(header[0], label="routing header").strip()
    if first != "Island":
        raise Boreal19BirdPilotRouterError(f"unexpected bird routing header: {first!r}")

    species = tuple(
        _decode_utf8(raw, label="bird species header").strip()
        for raw in header[1:]
    )
    if any(not value for value in species):
        raise Boreal19BirdPilotRouterError("blank bird species header")
    if len(species) != len(set(species)):
        raise Boreal19BirdPilotRouterError("duplicate bird species header")

    seen: set[str] = set()
    pilot_values: dict[str, tuple[int, ...]] = {}
    source_rows = routing_decoded = pilot_rows = pilot_targets = 0
    confirmatory_rows = excluded_rows = 0

    for fields in records:
        if not fields or fields == (b"",):
            continue
        source_rows += 1
        if len(fields) != len(header):
            raise Boreal19BirdPilotRouterError("bird response row-width drift")
        island = _decode_utf8(fields[0], label="routing Island").strip()
        routing_decoded += 1
        if not island or island not in full_set:
            raise Boreal19BirdPilotRouterError("invalid bird Island routing field")
        if island in seen:
            raise Boreal19BirdPilotRouterError(f"duplicate bird island row: {island}")
        seen.add(island)

        if island in pilot_set:
            values = []
            for raw in fields[1:]:
                text = _decode_utf8(raw, label="pilot bird occurrence").strip()
                if text not in {"0", "1"}:
                    raise Boreal19BirdPilotRouterError(
                        f"unexpected pilot bird occurrence: {text!r}"
                    )
                values.append(int(text))
            pilot_values[island] = tuple(values)
            pilot_rows += 1
            pilot_targets += len(values)
        elif island in confirmatory_set:
            # Intentionally do not decode any occurrence byte.
            confirmatory_rows += 1
        else:
            # Intentionally do not decode any occurrence byte.
            excluded_rows += 1

    if seen != full_set or source_rows != 42:
        raise Boreal19BirdPilotRouterError("bird matrix does not contain exact 42-island routing universe")
    if pilot_rows != 6 or confirmatory_rows != 13 or excluded_rows != 23:
        raise Boreal19BirdPilotRouterError("bird routing counts drift")
    if pilot_targets != 6 * expected_species_count:
        raise Boreal19BirdPilotRouterError("pilot bird target-count drift")
    if set(pilot_values) != pilot_set:
        raise Boreal19BirdPilotRouterError("not all frozen pilot islands were parsed")

    support = [0] * len(species)
    for island in pilot:
        for index, value in enumerate(pilot_values[island]):
            support[index] += value

    eligible_indices = tuple(
        index
        for index, count in enumerate(support)
        if min_support <= count <= max_support
    )
    eligible = tuple(species[index] for index in eligible_indices)
    if len(eligible) < minimum_eligible_species:
        raise Boreal19BirdPilotRouterError(
            f"eligible bird species gate failed: {len(eligible)} < {minimum_eligible_species}"
        )

    support_rows = tuple(
        (species[index], support[index]) for index in eligible_indices
    )
    targets = []
    serialized = []
    for island in pilot:
        restricted = tuple(pilot_values[island][index] for index in eligible_indices)
        encoded = encode_binary_vector_hex(restricted)
        targets.append((island, encoded))
        serialized.append(island + ":" + encoded)
    raw_surface_sha = hashlib.sha256("\n".join(serialized).encode("utf-8")).hexdigest()

    return RoutedBoreal19BirdPilot(
        source_response_rows_seen=source_rows,
        routing_island_fields_decoded=routing_decoded,
        pilot_island_rows_semantically_parsed=pilot_rows,
        pilot_target_values_parsed=pilot_targets,
        confirmatory_target_values_parsed=0,
        excluded_target_values_parsed=0,
        header_species_names_parsed=len(species),
        eligible_species=eligible,
        eligible_species_count=len(eligible),
        eligible_species_sha256=_species_universe_sha(eligible),
        pilot_support_counts=support_rows,
        pilot_island_order=pilot,
        pilot_targets_hex_by_island=tuple(targets),
        raw_pilot_surface_sha256=raw_surface_sha,
        confirmatory_occurrence_values_stored=False,
        excluded_occurrence_values_stored=False,
    )
