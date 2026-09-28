"""Byte-level burned-pilot router for the boreal beetle matrix.

Only island routing fields are Unicode-decoded for all 42 rows. Species header
names and occurrence cells are decoded only where explicitly allowed. In
particular, occurrence cells for confirmatory islands remain opaque bytes.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import io
from typing import Iterator, Mapping, Sequence


class BorealBeetlePilotRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class RoutedBorealPilotSurface:
    csv_text: str
    raw_surface_sha256: str
    source_response_rows_seen: int
    routing_island_fields_decoded: int
    pilot_island_rows_semantically_parsed: int
    pilot_target_values_parsed: int
    confirmatory_target_values_parsed: int
    header_species_names_parsed: int
    pilot_species_universe: tuple[str, ...]
    pilot_species_universe_count: int
    pilot_species_universe_sha256: str
    pilot_island_order: tuple[str, ...]
    pilot_island_to_block: tuple[tuple[str, str], ...]
    pilot_targets_hex_by_island: tuple[tuple[str, str], ...]
    pilot_island_count: int
    confirmatory_island_count: int
    pilot_block_count: int


def _iter_csv_records_bytes(raw: bytes) -> Iterator[tuple[bytes, ...]]:
    record: list[bytes] = []
    field = bytearray()
    in_quotes = False
    i = 0
    while i < len(raw):
        b = raw[i]
        if in_quotes:
            if b == 34:
                if i + 1 < len(raw) and raw[i + 1] == 34:
                    field.append(34)
                    i += 2
                    continue
                in_quotes = False
                i += 1
                continue
            field.append(b)
            i += 1
            continue
        if b == 34 and not field:
            in_quotes = True
            i += 1
            continue
        if b == 44:
            record.append(bytes(field))
            field.clear()
            i += 1
            continue
        if b == 10:
            if field.endswith(b"\r"):
                del field[-1:]
            record.append(bytes(field))
            field.clear()
            yield tuple(record)
            record.clear()
            i += 1
            continue
        field.append(b)
        i += 1

    if in_quotes:
        raise BorealBeetlePilotRouterError("unterminated quoted CSV field")
    if field or record:
        if field.endswith(b"\r"):
            del field[-1:]
        record.append(bytes(field))
        yield tuple(record)


def _decode_utf8(value: bytes, *, label: str) -> str:
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BorealBeetlePilotRouterError(
            f"invalid UTF-8 in opened {label}"
        ) from exc


def _species_universe_sha(species: Sequence[str]) -> str:
    payload = "".join(f"{name}\n" for name in species).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def encode_binary_vector_hex(values: Sequence[int]) -> str:
    bits = "".join(str(int(value)) for value in values)
    if not bits or set(bits) - {"0", "1"}:
        raise BorealBeetlePilotRouterError(
            "binary vector must be nonempty 0/1 values"
        )
    width = (len(bits) + 3) // 4
    return format(int(bits, 2), f"0{width}x")


def decode_binary_vector_hex(value: str, count: int) -> tuple[int, ...]:
    if count < 1:
        raise BorealBeetlePilotRouterError(
            "binary vector count must be positive"
        )
    width = (count + 3) // 4
    text = str(value).strip().lower()
    if len(text) != width:
        raise BorealBeetlePilotRouterError(
            "binary vector hex width mismatch"
        )
    try:
        integer = int(text, 16)
    except ValueError as exc:
        raise BorealBeetlePilotRouterError(
            "binary vector is not hexadecimal"
        ) from exc
    bits = bin(integer)[2:].zfill(width * 4)
    extra = width * 4 - count
    if extra and any(bit != "0" for bit in bits[:extra]):
        raise BorealBeetlePilotRouterError(
            "binary vector has nonzero padding bits"
        )
    return tuple(int(bit) for bit in bits[-count:])


def build_boreal_beetle_pilot_surface(
    *,
    response_csv_bytes: bytes,
    island_to_block: Mapping[str, str],
    pilot_partition: Sequence[str],
    confirmatory_partition: Sequence[str],
    expected_islands: Sequence[str],
    expected_species_count: int = 466,
) -> RoutedBorealPilotSurface:
    pilot_order = tuple(pilot_partition)
    confirmatory_order = tuple(confirmatory_partition)
    pilot_set = set(pilot_order)
    confirmatory_set = set(confirmatory_order)
    expected_order = tuple(expected_islands)
    expected_set = set(expected_order)

    if not pilot_order or not confirmatory_order:
        raise BorealBeetlePilotRouterError(
            "pilot and confirmatory block partitions must be nonempty"
        )
    if pilot_set & confirmatory_set:
        raise BorealBeetlePilotRouterError(
            "pilot and confirmatory block partitions overlap"
        )
    if len(expected_order) != len(expected_set):
        raise BorealBeetlePilotRouterError("expected island universe has duplicates")
    if set(island_to_block) != expected_set:
        raise BorealBeetlePilotRouterError(
            "island-to-block mapping does not match expected island universe"
        )
    if set(island_to_block.values()) - (pilot_set | confirmatory_set):
        raise BorealBeetlePilotRouterError(
            "island-to-block mapping contains unfrozen block"
        )

    records = _iter_csv_records_bytes(response_csv_bytes)
    try:
        header = next(records)
    except StopIteration as exc:
        raise BorealBeetlePilotRouterError("beetle response CSV is empty") from exc
    if header and header[0].startswith(b"\xef\xbb\xbf"):
        header = (header[0][3:],) + header[1:]

    if len(header) != expected_species_count + 1:
        raise BorealBeetlePilotRouterError(
            "beetle response header does not match frozen species count"
        )
    first = _decode_utf8(header[0], label="routing header").strip()
    if first != "Island":
        raise BorealBeetlePilotRouterError(
            f"unexpected beetle routing header: {first!r}"
        )
    species = tuple(
        _decode_utf8(raw, label="species header").strip()
        for raw in header[1:]
    )
    if any(not name for name in species):
        raise BorealBeetlePilotRouterError("blank beetle species header")
    if len(species) != len(set(species)):
        raise BorealBeetlePilotRouterError("duplicate beetle species header")

    seen: set[str] = set()
    pilot_values: dict[str, tuple[int, ...]] = {}
    source_rows = 0
    routing_decoded = 0
    pilot_rows = 0
    pilot_targets = 0

    for fields in records:
        if not fields or fields == (b"",):
            continue
        source_rows += 1
        if len(fields) != len(header):
            raise BorealBeetlePilotRouterError(
                "beetle response row width differs from frozen header"
            )
        island = _decode_utf8(fields[0], label="routing Island").strip()
        routing_decoded += 1
        if not island:
            raise BorealBeetlePilotRouterError("blank Island routing field")
        if island not in expected_set:
            raise BorealBeetlePilotRouterError(
                f"response row references island outside frozen universe: {island}"
            )
        if island in seen:
            raise BorealBeetlePilotRouterError(
                f"duplicate response island row: {island}"
            )
        seen.add(island)

        block = island_to_block[island]
        if block in confirmatory_set:
            # Deliberately discard all occurrence bytes without decoding.
            continue
        if block not in pilot_set:
            raise BorealBeetlePilotRouterError(
                f"response island routed to unfrozen block: {block}"
            )

        targets: list[int] = []
        for raw in fields[1:]:
            value = _decode_utf8(raw, label="pilot occurrence").strip()
            if value not in {"0", "1"}:
                raise BorealBeetlePilotRouterError(
                    f"unexpected pilot occurrence value: {value!r}"
                )
            targets.append(int(value))
        pilot_values[island] = tuple(targets)
        pilot_rows += 1
        pilot_targets += len(targets)

    if seen != expected_set:
        missing = sorted(expected_set - seen)
        raise BorealBeetlePilotRouterError(
            "response matrix missing frozen islands: " + ", ".join(missing)
        )
    if source_rows != len(expected_order):
        raise BorealBeetlePilotRouterError(
            "response row count differs from frozen island count"
        )

    pilot_islands_by_block: dict[str, list[str]] = {b: [] for b in pilot_order}
    confirmatory_islands = 0
    for island in expected_order:
        block = island_to_block[island]
        if block in pilot_set:
            if island not in pilot_values:
                raise BorealBeetlePilotRouterError(
                    f"pilot island was not semantically parsed: {island}"
                )
            pilot_islands_by_block[block].append(island)
        else:
            confirmatory_islands += 1

    empty_pilot_blocks = [
        block for block, islands in pilot_islands_by_block.items()
        if not islands
    ]
    if empty_pilot_blocks:
        raise BorealBeetlePilotRouterError(
            "pilot spatial block has no frozen island: "
            + ", ".join(empty_pilot_blocks)
        )

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
        raise BorealBeetlePilotRouterError(
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

    return RoutedBorealPilotSurface(
        csv_text=text,
        raw_surface_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        source_response_rows_seen=source_rows,
        routing_island_fields_decoded=routing_decoded,
        pilot_island_rows_semantically_parsed=pilot_rows,
        pilot_target_values_parsed=pilot_targets,
        confirmatory_target_values_parsed=0,
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
        confirmatory_island_count=confirmatory_islands,
        pilot_block_count=len(pilot_order),
    )
