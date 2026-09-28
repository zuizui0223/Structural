"""Byte-level confirmatory router for the frozen 19-island boreal system.

The source response file contains all 42 study islands and 466 beetle species.
This router decodes the Island routing field on all rows and species header
names once, but occurrence cells are semantically decoded only for the exact
99 pilot-supported species on the 13 frozen confirmatory islands. Occurrence
cells on the six pilot islands, the 23 excluded islands, and non-focal species
on confirmatory islands remain opaque bytes.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import io
from typing import Mapping, Sequence

from .boreal_beetle_pilot_router import _decode_utf8, _iter_csv_records_bytes


class Boreal19ConfirmatoryRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class RoutedBoreal19ConfirmatorySurface:
    csv_text: str
    surface_sha256: str
    source_response_rows_seen: int
    routing_island_fields_decoded: int
    confirmatory_island_rows_semantically_parsed: int
    confirmatory_target_values_parsed: int
    pilot_target_values_parsed: int
    excluded_target_values_parsed: int
    nonfocal_confirmatory_target_values_parsed: int
    fixed_species_count: int
    confirmatory_island_count: int
    confirmatory_block_count: int
    excluded_island_count: int


def build_boreal_19island_confirmatory_surface(
    *,
    response_csv_bytes: bytes,
    full_expected_islands: Sequence[str],
    analysis_expected_islands: Sequence[str],
    analysis_island_to_block: Mapping[str, str],
    pilot_partition: Sequence[str],
    confirmatory_partition: Sequence[str],
    fixed_species: Sequence[str],
    expected_species_count: int = 466,
) -> RoutedBoreal19ConfirmatorySurface:
    full_order = tuple(full_expected_islands)
    full_set = set(full_order)
    analysis_order = tuple(analysis_expected_islands)
    analysis_set = set(analysis_order)
    pilot_blocks = tuple(pilot_partition)
    confirmatory_blocks = tuple(confirmatory_partition)
    pilot_set = set(pilot_blocks)
    confirmatory_set = set(confirmatory_blocks)
    species_order = tuple(fixed_species)

    if len(full_order) != len(full_set) or not full_order:
        raise Boreal19ConfirmatoryRouterError(
            "full source island universe is empty or duplicated"
        )
    if len(analysis_order) != len(analysis_set) or not analysis_order:
        raise Boreal19ConfirmatoryRouterError(
            "analysis island universe is empty or duplicated"
        )
    if not analysis_set < full_set:
        raise Boreal19ConfirmatoryRouterError(
            "analysis universe must be a strict subset of source universe"
        )
    if set(analysis_island_to_block) != analysis_set:
        raise Boreal19ConfirmatoryRouterError(
            "analysis island-to-block map differs from analysis universe"
        )
    if not pilot_blocks or not confirmatory_blocks:
        raise Boreal19ConfirmatoryRouterError(
            "pilot/confirmatory block partitions must be nonempty"
        )
    if pilot_set & confirmatory_set:
        raise Boreal19ConfirmatoryRouterError(
            "pilot/confirmatory blocks overlap"
        )
    if set(analysis_island_to_block.values()) - (pilot_set | confirmatory_set):
        raise Boreal19ConfirmatoryRouterError(
            "analysis island-to-block map contains unfrozen block"
        )
    if not species_order or len(species_order) != len(set(species_order)):
        raise Boreal19ConfirmatoryRouterError(
            "fixed species universe is empty or duplicated"
        )

    records = _iter_csv_records_bytes(response_csv_bytes)
    try:
        header = next(records)
    except StopIteration as exc:
        raise Boreal19ConfirmatoryRouterError(
            "beetle response CSV is empty"
        ) from exc
    if header and header[0].startswith(b"\xef\xbb\xbf"):
        header = (header[0][3:],) + header[1:]

    if len(header) != expected_species_count + 1:
        raise Boreal19ConfirmatoryRouterError(
            "beetle response header differs from frozen species count"
        )
    routing_header = _decode_utf8(
        header[0], label="routing header"
    ).strip()
    if routing_header != "Island":
        raise Boreal19ConfirmatoryRouterError(
            f"unexpected routing header: {routing_header!r}"
        )

    all_species = tuple(
        _decode_utf8(raw, label="species header").strip()
        for raw in header[1:]
    )
    if any(not name for name in all_species):
        raise Boreal19ConfirmatoryRouterError("blank species header")
    if len(all_species) != len(set(all_species)):
        raise Boreal19ConfirmatoryRouterError("duplicate species header")
    species_index = {
        name: index + 1 for index, name in enumerate(all_species)
    }
    missing_species = [
        name for name in species_order if name not in species_index
    ]
    if missing_species:
        raise Boreal19ConfirmatoryRouterError(
            "fixed species missing from response header: "
            + ", ".join(missing_species)
        )

    seen: set[str] = set()
    confirmatory_values: dict[str, tuple[int, ...]] = {}
    source_rows = 0
    routing_decoded = 0
    confirmatory_rows = 0
    confirmatory_targets = 0
    excluded_rows = 0

    for fields in records:
        if not fields or fields == (b"",):
            continue
        source_rows += 1
        if len(fields) != len(header):
            raise Boreal19ConfirmatoryRouterError(
                "response row width differs from frozen header"
            )
        island = _decode_utf8(
            fields[0], label="routing Island"
        ).strip()
        routing_decoded += 1
        if not island:
            raise Boreal19ConfirmatoryRouterError(
                "blank Island routing field"
            )
        if island not in full_set:
            raise Boreal19ConfirmatoryRouterError(
                f"response island outside frozen source universe: {island}"
            )
        if island in seen:
            raise Boreal19ConfirmatoryRouterError(
                f"duplicate response island row: {island}"
            )
        seen.add(island)

        if island not in analysis_set:
            # All 466 occurrence cells stay opaque for excluded islands.
            excluded_rows += 1
            continue

        block = analysis_island_to_block[island]
        if block in pilot_set:
            # All pilot occurrence cells stay opaque after pilot consumption.
            continue
        if block not in confirmatory_set:
            raise Boreal19ConfirmatoryRouterError(
                f"analysis island routed to unfrozen block: {block}"
            )

        targets: list[int] = []
        for species in species_order:
            raw = fields[species_index[species]]
            value = _decode_utf8(
                raw,
                label="confirmatory focal occurrence",
            ).strip()
            if value not in {"0", "1"}:
                raise Boreal19ConfirmatoryRouterError(
                    f"unexpected confirmatory focal occurrence: {value!r}"
                )
            targets.append(int(value))
        confirmatory_values[island] = tuple(targets)
        confirmatory_rows += 1
        confirmatory_targets += len(targets)

    if seen != full_set:
        missing = sorted(full_set - seen)
        raise Boreal19ConfirmatoryRouterError(
            "response matrix missing frozen source islands: "
            + ", ".join(missing)
        )
    if source_rows != len(full_order):
        raise Boreal19ConfirmatoryRouterError(
            "response row count differs from frozen source universe"
        )
    excluded_expected = len(full_order) - len(analysis_order)
    if excluded_rows != excluded_expected:
        raise Boreal19ConfirmatoryRouterError(
            "excluded island routing count drift"
        )

    confirmatory_islands_by_block = {
        block: sorted(
            island
            for island in analysis_order
            if analysis_island_to_block[island] == block
        )
        for block in confirmatory_blocks
    }
    if any(
        not islands
        for islands in confirmatory_islands_by_block.values()
    ):
        raise Boreal19ConfirmatoryRouterError(
            "confirmatory block has no analysis island"
        )

    expected_confirmatory = {
        island
        for island in analysis_order
        if analysis_island_to_block[island] in confirmatory_set
    }
    if set(confirmatory_values) != expected_confirmatory:
        missing = sorted(expected_confirmatory - set(confirmatory_values))
        raise Boreal19ConfirmatoryRouterError(
            "confirmatory analysis islands were not all parsed: "
            + ", ".join(missing)
        )

    rows: list[tuple[str, str, str, str]] = []
    for block in confirmatory_blocks:
        for island in confirmatory_islands_by_block[block]:
            targets = confirmatory_values[island]
            for species, target in zip(species_order, targets):
                rows.append((island, block, species, str(target)))

    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["island", "block", "species", "target"])
    writer.writerows(rows)
    text = out.getvalue()

    return RoutedBoreal19ConfirmatorySurface(
        csv_text=text,
        surface_sha256=hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest(),
        source_response_rows_seen=source_rows,
        routing_island_fields_decoded=routing_decoded,
        confirmatory_island_rows_semantically_parsed=confirmatory_rows,
        confirmatory_target_values_parsed=confirmatory_targets,
        pilot_target_values_parsed=0,
        excluded_target_values_parsed=0,
        nonfocal_confirmatory_target_values_parsed=0,
        fixed_species_count=len(species_order),
        confirmatory_island_count=confirmatory_rows,
        confirmatory_block_count=len(confirmatory_blocks),
        excluded_island_count=excluded_rows,
    )
