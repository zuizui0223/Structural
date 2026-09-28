"""Byte-level burned-pilot router for the frozen 19-island boreal system.

The source response file contains all 42 study islands. This router decodes the
Island routing field for all 42 rows, but decodes occurrence cells only for the
six frozen pilot islands in the 19-island analysis population. Occurrence bytes
for the 13 confirmatory analysis islands and 23 excluded source islands remain
opaque.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import io
from typing import Mapping, Sequence

from structural.boreal_beetle_pilot_router import (
    _decode_utf8,
    _iter_csv_records_bytes,
    _species_universe_sha,
    encode_binary_vector_hex,
)


class Boreal19BeetlePilotRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class RoutedBoreal19PilotSurface:
    csv_text: str
    raw_surface_sha256: str
    source_response_rows_seen: int
    routing_island_fields_decoded: int
    pilot_island_rows_semantically_parsed: int
    pilot_target_values_parsed: int
    confirmatory_target_values_parsed: int
    excluded_target_values_parsed: int
    header_species_names_parsed: int
    pilot_species_universe: tuple[str, ...]
    pilot_species_universe_count: int
    pilot_species_universe_sha256: str
    pilot_island_order: tuple[str, ...]
    pilot_island_to_block: tuple[tuple[str, str], ...]
    pilot_targets_hex_by_island: tuple[tuple[str, str], ...]
    pilot_island_count: int
    confirmatory_island_count: int
    excluded_island_count: int
    pilot_block_count: int


def build_boreal_19island_beetle_pilot_surface(
    *,
    response_csv_bytes: bytes,
    full_expected_islands: Sequence[str],
    analysis_expected_islands: Sequence[str],
    analysis_island_to_block: Mapping[str, str],
    pilot_partition: Sequence[str],
    confirmatory_partition: Sequence[str],
    expected_species_count: int = 466,
) -> RoutedBoreal19PilotSurface:
    full_order = tuple(full_expected_islands)
    full_set = set(full_order)
    analysis_order = tuple(analysis_expected_islands)
    analysis_set = set(analysis_order)
    pilot_order = tuple(pilot_partition)
    confirmatory_order = tuple(confirmatory_partition)
    pilot_set = set(pilot_order)
    confirmatory_set = set(confirmatory_order)

    if not full_order or len(full_order) != len(full_set):
        raise Boreal19BeetlePilotRouterError(
            "full source island universe must be nonempty and unique"
        )
    if not analysis_order or len(analysis_order) != len(analysis_set):
        raise Boreal19BeetlePilotRouterError(
            "analysis island universe must be nonempty and unique"
        )
    if not analysis_set < full_set:
        raise Boreal19BeetlePilotRouterError(
            "analysis island universe must be a strict subset of full source universe"
        )
    if not pilot_order or not confirmatory_order:
        raise Boreal19BeetlePilotRouterError(
            "pilot and confirmatory block partitions must be nonempty"
        )
    if pilot_set & confirmatory_set:
        raise Boreal19BeetlePilotRouterError(
            "pilot and confirmatory block partitions overlap"
        )
    if set(analysis_island_to_block) != analysis_set:
        raise Boreal19BeetlePilotRouterError(
            "analysis island-to-block mapping does not match analysis universe"
        )
    if set(analysis_island_to_block.values()) - (pilot_set | confirmatory_set):
        raise Boreal19BeetlePilotRouterError(
            "analysis island-to-block mapping contains unfrozen block"
        )

    records = _iter_csv_records_bytes(response_csv_bytes)
    try:
        header = next(records)
    except StopIteration as exc:
        raise Boreal19BeetlePilotRouterError("beetle response CSV is empty") from exc
    if header and header[0].startswith(b"\xef\xbb\xbf"):
        header = (header[0][3:],) + header[1:]

    if len(header) != expected_species_count + 1:
        raise Boreal19BeetlePilotRouterError(
            "beetle response header does not match frozen species count"
        )
    first = _decode_utf8(header[0], label="routing header").strip()
    if first != "Island":
        raise Boreal19BeetlePilotRouterError(
            f"unexpected beetle routing header: {first!r}"
        )
    species = tuple(
        _decode_utf8(raw, label="species header").strip()
        for raw in header[1:]
    )
    if any(not name for name in species):
        raise Boreal19BeetlePilotRouterError("blank beetle species header")
    if len(species) != len(set(species)):
        raise Boreal19BeetlePilotRouterError("duplicate beetle species header")

    seen: set[str] = set()
    pilot_values: dict[str, tuple[int, ...]] = {}
    source_rows = 0
    routing_decoded = 0
    pilot_rows = 0
    pilot_targets = 0
    confirmatory_rows = 0
    excluded_rows = 0

    for fields in records:
        if not fields or fields == (b"",):
            continue
        source_rows += 1
        if len(fields) != len(header):
            raise Boreal19BeetlePilotRouterError(
                "beetle response row width differs from frozen header"
            )
        island = _decode_utf8(fields[0], label="routing Island").strip()
        routing_decoded += 1
        if not island:
            raise Boreal19BeetlePilotRouterError("blank Island routing field")
        if island not in full_set:
            raise Boreal19BeetlePilotRouterError(
                f"response row references island outside frozen full universe: {island}"
            )
        if island in seen:
            raise Boreal19BeetlePilotRouterError(
                f"duplicate response island row: {island}"
            )
        seen.add(island)

        if island not in analysis_set:
            # Excluded source-island occurrence bytes remain opaque.
            excluded_rows += 1
            continue

        block = analysis_island_to_block[island]
        if block in confirmatory_set:
            # Confirmatory occurrence bytes remain opaque.
            confirmatory_rows += 1
            continue
        if block not in pilot_set:
            raise Boreal19BeetlePilotRouterError(
                f"analysis island routed to unfrozen block: {block}"
            )

        targets: list[int] = []
        for raw in fields[1:]:
            value = _decode_utf8(raw, label="pilot occurrence").strip()
            if value not in {"0", "1"}:
                raise Boreal19BeetlePilotRouterError(
                    f"unexpected pilot occurrence value: {value!r}"
                )
            targets.append(int(value))
        pilot_values[island] = tuple(targets)
        pilot_rows += 1
        pilot_targets += len(targets)

    if seen != full_set:
        missing = sorted(full_set - seen)
        raise Boreal19BeetlePilotRouterError(
            "response matrix missing frozen source islands: " + ", ".join(missing)
        )
    if source_rows != len(full_order):
        raise Boreal19BeetlePilotRouterError(
            "response row count differs from frozen full source island count"
        )

    pilot_islands_by_block: dict[str, list[str]] = {b: [] for b in pilot_order}
    for island in analysis_order:
        block = analysis_island_to_block[island]
        if block in pilot_set:
            if island not in pilot_values:
                raise Boreal19BeetlePilotRouterError(
                    f"pilot island was not semantically parsed: {island}"
                )
            pilot_islands_by_block[block].append(island)

    empty_pilot_blocks = [
        block for block, islands in pilot_islands_by_block.items()
        if not islands
    ]
    if empty_pilot_blocks:
        raise Boreal19BeetlePilotRouterError(
            "pilot spatial block has no frozen island: "
            + ", ".join(empty_pilot_blocks)
        )

    expected_confirmatory_rows = sum(
        analysis_island_to_block[island] in confirmatory_set
        for island in analysis_order
    )
    expected_pilot_rows = len(analysis_order) - expected_confirmatory_rows
    expected_excluded_rows = len(full_order) - len(analysis_order)
    if pilot_rows != expected_pilot_rows:
        raise Boreal19BeetlePilotRouterError("pilot island row count drift")
    if confirmatory_rows != expected_confirmatory_rows:
        raise Boreal19BeetlePilotRouterError("confirmatory island row count drift")
    if excluded_rows != expected_excluded_rows:
        raise Boreal19BeetlePilotRouterError("excluded island row count drift")

    support = [0] * len(species)
    for targets in pilot_values.values():
        for j, target in enumerate(targets):
            support[j] += int(target == 1)
    universe_indices = tuple(
        j for j, count in enumerate(support)
        if count >= 2
    )
    pilot_species_universe = tuple(species[j] for j in universe_indices)
    if not pilot_species_universe:
        raise Boreal19BeetlePilotRouterError(
            "common pilot-supported beetle species universe is empty"
        )

    rows: list[tuple[str, str, str]] = []
    pilot_island_order: list[str] = []
    pilot_island_to_block: list[tuple[str, str]] = []
    pilot_targets_hex_by_island: list[tuple[str, str]] = []
    for block in pilot_order:
        for island in sorted(pilot_islands_by_block[block]):
            targets = pilot_values[island]
            restricted = tuple(targets[j] for j in universe_indices)
            pilot_island_order.append(island)
            pilot_island_to_block.append((island, block))
            pilot_targets_hex_by_island.append(
                (island, encode_binary_vector_hex(restricted))
            )
            for target in restricted:
                rows.append((block, block, str(target)))

    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["partition_unit", "block", "target"])
    writer.writerows(rows)
    text = out.getvalue()

    return RoutedBoreal19PilotSurface(
        csv_text=text,
        raw_surface_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        source_response_rows_seen=source_rows,
        routing_island_fields_decoded=routing_decoded,
        pilot_island_rows_semantically_parsed=pilot_rows,
        pilot_target_values_parsed=pilot_targets,
        confirmatory_target_values_parsed=0,
        excluded_target_values_parsed=0,
        header_species_names_parsed=len(species),
        pilot_species_universe=pilot_species_universe,
        pilot_species_universe_count=len(pilot_species_universe),
        pilot_species_universe_sha256=_species_universe_sha(
            pilot_species_universe
        ),
        pilot_island_order=tuple(pilot_island_order),
        pilot_island_to_block=tuple(pilot_island_to_block),
        pilot_targets_hex_by_island=tuple(pilot_targets_hex_by_island),
        pilot_island_count=pilot_rows,
        confirmatory_island_count=confirmatory_rows,
        excluded_island_count=excluded_rows,
        pilot_block_count=len(pilot_order),
    )
