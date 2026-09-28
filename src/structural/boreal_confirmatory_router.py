"""Byte-level confirmatory router for the boreal beetle matrix.

Only the fixed v0.84 species universe is decoded on confirmatory islands.
Pilot-island occurrence cells and non-focal confirmatory species cells remain
opaque bytes.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import io
from typing import Mapping, Sequence

from .boreal_beetle_pilot_router import (
    _decode_utf8,
    _iter_csv_records_bytes,
)


class BorealConfirmatoryRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class RoutedBorealConfirmatorySurface:
    csv_text: str
    surface_sha256: str
    source_response_rows_seen: int
    routing_island_fields_decoded: int
    confirmatory_island_rows_semantically_parsed: int
    confirmatory_target_values_parsed: int
    pilot_target_values_parsed: int
    nonfocal_confirmatory_target_values_parsed: int
    fixed_species_count: int
    confirmatory_island_count: int
    confirmatory_block_count: int


def build_boreal_confirmatory_surface(
    *,
    response_csv_bytes: bytes,
    island_to_block: Mapping[str, str],
    pilot_partition: Sequence[str],
    confirmatory_partition: Sequence[str],
    expected_islands: Sequence[str],
    fixed_species: Sequence[str],
    expected_species_count: int = 466,
) -> RoutedBorealConfirmatorySurface:
    pilot_blocks = tuple(pilot_partition)
    confirmatory_blocks = tuple(confirmatory_partition)
    pilot_set = set(pilot_blocks)
    confirm_set = set(confirmatory_blocks)
    expected_order = tuple(expected_islands)
    expected_set = set(expected_order)
    species_order = tuple(fixed_species)

    if not pilot_blocks or not confirmatory_blocks:
        raise BorealConfirmatoryRouterError(
            "pilot/confirmatory block partitions must be nonempty"
        )
    if pilot_set & confirm_set:
        raise BorealConfirmatoryRouterError(
            "pilot/confirmatory blocks overlap"
        )
    if len(expected_order) != len(expected_set):
        raise BorealConfirmatoryRouterError(
            "expected island universe contains duplicates"
        )
    if set(island_to_block) != expected_set:
        raise BorealConfirmatoryRouterError(
            "island-to-block map differs from frozen island universe"
        )
    if set(island_to_block.values()) - (pilot_set | confirm_set):
        raise BorealConfirmatoryRouterError(
            "island-to-block map contains unfrozen block"
        )
    if not species_order or len(species_order) != len(set(species_order)):
        raise BorealConfirmatoryRouterError(
            "fixed species universe is empty or duplicated"
        )

    records = _iter_csv_records_bytes(response_csv_bytes)
    try:
        header = next(records)
    except StopIteration as exc:
        raise BorealConfirmatoryRouterError(
            "beetle response CSV is empty"
        ) from exc
    if header and header[0].startswith(b"\xef\xbb\xbf"):
        header = (header[0][3:],) + header[1:]

    if len(header) != expected_species_count + 1:
        raise BorealConfirmatoryRouterError(
            "beetle response header differs from frozen species count"
        )
    first = _decode_utf8(header[0], label="routing header").strip()
    if first != "Island":
        raise BorealConfirmatoryRouterError(
            f"unexpected routing header: {first!r}"
        )
    all_species = tuple(
        _decode_utf8(raw, label="species header").strip()
        for raw in header[1:]
    )
    if any(not name for name in all_species):
        raise BorealConfirmatoryRouterError(
            "blank species header"
        )
    if len(all_species) != len(set(all_species)):
        raise BorealConfirmatoryRouterError(
            "duplicate species header"
        )

    index = {name: i + 1 for i, name in enumerate(all_species)}
    missing = [name for name in species_order if name not in index]
    if missing:
        raise BorealConfirmatoryRouterError(
            "fixed species missing from response header: "
            + ", ".join(missing)
        )

    seen = set()
    confirmatory_values: dict[str, tuple[int, ...]] = {}
    source_rows = 0
    routing_decoded = 0
    confirm_rows_parsed = 0
    confirm_targets = 0

    for fields in records:
        if not fields or fields == (b"",):
            continue
        source_rows += 1
        if len(fields) != len(header):
            raise BorealConfirmatoryRouterError(
                "response row width differs from frozen header"
            )
        island = _decode_utf8(
            fields[0],
            label="routing Island",
        ).strip()
        routing_decoded += 1
        if not island:
            raise BorealConfirmatoryRouterError(
                "blank Island routing field"
            )
        if island not in expected_set:
            raise BorealConfirmatoryRouterError(
                f"response island outside frozen universe: {island}"
            )
        if island in seen:
            raise BorealConfirmatoryRouterError(
                f"duplicate response island row: {island}"
            )
        seen.add(island)
        block = island_to_block[island]

        if block in pilot_set:
            # Deliberately leave every pilot occurrence cell opaque.
            continue
        if block not in confirm_set:
            raise BorealConfirmatoryRouterError(
                f"response island routed to unfrozen block: {block}"
            )

        targets = []
        for species in species_order:
            raw = fields[index[species]]
            value = _decode_utf8(
                raw,
                label="confirmatory focal occurrence",
            ).strip()
            if value not in {"0", "1"}:
                raise BorealConfirmatoryRouterError(
                    f"unexpected confirmatory focal occurrence: {value!r}"
                )
            targets.append(int(value))
        confirmatory_values[island] = tuple(targets)
        confirm_rows_parsed += 1
        confirm_targets += len(targets)

    if seen != expected_set:
        missing_islands = sorted(expected_set - seen)
        raise BorealConfirmatoryRouterError(
            "response matrix missing frozen islands: "
            + ", ".join(missing_islands)
        )
    if source_rows != len(expected_order):
        raise BorealConfirmatoryRouterError(
            "response row count differs from frozen island universe"
        )

    confirmatory_islands_by_block = {
        block: sorted(
            island
            for island in expected_order
            if island_to_block[island] == block
        )
        for block in confirmatory_blocks
    }
    if any(
        not islands
        for islands in confirmatory_islands_by_block.values()
    ):
        raise BorealConfirmatoryRouterError(
            "confirmatory block has no island"
        )

    rows = []
    for block in confirmatory_blocks:
        for island in confirmatory_islands_by_block[block]:
            if island not in confirmatory_values:
                raise BorealConfirmatoryRouterError(
                    f"confirmatory island not semantically parsed: {island}"
                )
            targets = confirmatory_values[island]
            for species, target in zip(species_order, targets):
                rows.append((island, block, species, str(target)))

    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["island", "block", "species", "target"])
    writer.writerows(rows)
    text = out.getvalue()

    return RoutedBorealConfirmatorySurface(
        csv_text=text,
        surface_sha256=hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest(),
        source_response_rows_seen=source_rows,
        routing_island_fields_decoded=routing_decoded,
        confirmatory_island_rows_semantically_parsed=confirm_rows_parsed,
        confirmatory_target_values_parsed=confirm_targets,
        pilot_target_values_parsed=0,
        nonfocal_confirmatory_target_values_parsed=0,
        fixed_species_count=len(species_order),
        confirmatory_island_count=confirm_rows_parsed,
        confirmatory_block_count=len(confirmatory_blocks),
    )
