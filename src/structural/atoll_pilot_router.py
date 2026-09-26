"""Response-firewalled pilot router for the Indo-Pacific atoll plant system.

The monolithic plant CSV is a response file. This module may structurally scan
raw CSV bytes to recover the first (atoll) field for routing, but it only
Unicode-decodes species/presence fields after an atoll has been proven to
belong to a frozen burned-pilot spatial block.

Confirmatory and response-independent target-excluded rows therefore never
have species or presence values semantically opened.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import io
from typing import Iterable, Iterator, Mapping, Sequence


class AtollPilotRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class RoutedPilotSurface:
    csv_text: str
    raw_surface_sha256: str
    source_response_rows_seen: int
    pilot_response_rows_semantically_parsed: int
    confirmatory_species_values_parsed: int
    confirmatory_presence_values_parsed: int
    excluded_species_values_parsed: int
    excluded_presence_values_parsed: int
    pilot_catalogued_atolls: int
    pilot_blocks_with_catalogues: int
    pilot_species_universe: tuple[str, ...]
    pilot_species_universe_count: int
    pilot_species_universe_sha256: str
    blank_sentinel_blocks: tuple[str, ...]


def _iter_csv_records_bytes(raw: bytes) -> Iterator[tuple[bytes, ...]]:
    """Parse RFC4180-style CSV into byte fields without Unicode decoding.

    The parser is deliberately byte-level so non-routing fields in sealed rows
    can be discarded without semantic decoding.
    """

    record: list[bytes] = []
    field = bytearray()
    in_quotes = False
    i = 0
    n = len(raw)

    while i < n:
        b = raw[i]

        if in_quotes:
            if b == 34:  # "
                if i + 1 < n and raw[i + 1] == 34:
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
        if b == 44:  # comma
            record.append(bytes(field))
            field.clear()
            i += 1
            continue
        if b == 10:  # LF
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
        raise AtollPilotRouterError("unterminated quoted CSV field")
    if field or record:
        if field.endswith(b"\r"):
            del field[-1:]
        record.append(bytes(field))
        yield tuple(record)


def _decode_utf8(value: bytes, *, label: str) -> str:
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AtollPilotRouterError(f"invalid UTF-8 in opened {label}") from exc


def build_atoll_burned_pilot_surface(
    *,
    response_csv_bytes: bytes,
    atoll_to_block: Mapping[str, str],
    excluded_model_target_atolls: Iterable[str],
    pilot_partition: Sequence[str],
    confirmatory_partition: Sequence[str],
) -> RoutedPilotSurface:
    pilot_order = tuple(pilot_partition)
    pilot_set = set(pilot_order)
    confirmatory_set = set(confirmatory_partition)
    excluded = set(excluded_model_target_atolls)

    if not pilot_order or not confirmatory_set:
        raise AtollPilotRouterError("pilot and confirmatory partitions must be nonempty")
    if pilot_set & confirmatory_set:
        raise AtollPilotRouterError("pilot and confirmatory partitions overlap")
    if set(atoll_to_block.values()) - (pilot_set | confirmatory_set):
        raise AtollPilotRouterError("atoll mapping contains unfrozen spatial block")
    if excluded & set(atoll_to_block):
        raise AtollPilotRouterError("excluded atoll appears in model-target mapping")

    records = _iter_csv_records_bytes(response_csv_bytes)
    try:
        header = next(records)
    except StopIteration as exc:
        raise AtollPilotRouterError("plant response CSV is empty") from exc

    if header and header[0].startswith(b"\xef\xbb\xbf"):
        header = (header[0][3:],) + header[1:]
    opened_header = tuple(_decode_utf8(x, label="header") for x in header)
    if opened_header != ("atoll", "species", "presence"):
        raise AtollPilotRouterError(
            "unexpected plant response header: " + repr(opened_header)
        )

    # Only pilot rows become semantically opened response records.
    by_atoll: dict[str, dict[str, str]] = {}
    source_rows = 0
    pilot_rows = 0

    for fields in records:
        if not fields or fields == (b"",):
            continue
        source_rows += 1
        if len(fields) != 3:
            raise AtollPilotRouterError("plant response row does not have 3 CSV fields")

        atoll = _decode_utf8(fields[0], label="routing atoll").strip()
        if not atoll:
            raise AtollPilotRouterError("blank atoll routing field")

        block = atoll_to_block.get(atoll)
        if block is None:
            if atoll in excluded:
                # Deliberately discard opaque species/presence bytes.
                continue
            raise AtollPilotRouterError(
                f"response row references atoll outside frozen graph/target universes: {atoll}"
            )

        if block in confirmatory_set:
            # Deliberately discard opaque species/presence bytes.
            continue
        if block not in pilot_set:
            raise AtollPilotRouterError(f"response row routed to unfrozen block: {block}")

        species = _decode_utf8(fields[1], label="pilot species").strip()
        presence = _decode_utf8(fields[2], label="pilot presence").strip()
        if not species:
            raise AtollPilotRouterError("blank species in opened pilot row")
        if presence not in {"N", "I"}:
            raise AtollPilotRouterError(
                f"unexpected presence code in opened pilot row: {presence!r}"
            )

        species_map = by_atoll.setdefault(atoll, {})
        if species in species_map:
            raise AtollPilotRouterError(
                f"duplicate pilot atoll/species row: {atoll} / {species}"
            )
        species_map[species] = presence
        pilot_rows += 1

    block_atolls: dict[str, list[str]] = {b: [] for b in pilot_order}
    for atoll in sorted(by_atoll):
        block = atoll_to_block[atoll]
        block_atolls[block].append(atoll)

    # Freeze one pilot-supported species universe for every held-out block.
    # A species must have native support in >=2 distinct burned-pilot blocks.
    # This rule is fixed before pilot response access and avoids both
    # heldout-specific endpoint drift and single-block source support.
    native_blocks_by_species: dict[str, set[str]] = {}
    for atoll, species_map in by_atoll.items():
        block = atoll_to_block[atoll]
        for species, code in species_map.items():
            if code == "N":
                native_blocks_by_species.setdefault(species, set()).add(block)

    pilot_species_universe = tuple(
        sorted(
            species
            for species, blocks in native_blocks_by_species.items()
            if len(blocks) >= 2
        )
    )
    pilot_species_universe_sha256 = hashlib.sha256(
        ("\n".join(pilot_species_universe) + ("\n" if pilot_species_universe else "")).encode(
            "utf-8"
        )
    ).hexdigest()

    rows: list[tuple[str, str, str]] = []
    blank_blocks: list[str] = []

    for heldout in pilot_order:
        test_atolls = block_atolls[heldout]
        if not test_atolls or not pilot_species_universe:
            rows.append((heldout, heldout, ""))
            blank_blocks.append(heldout)
            continue

        for atoll in sorted(test_atolls):
            species_map = by_atoll[atoll]
            for species in pilot_species_universe:
                target = "1" if species_map.get(species) == "N" else "0"
                rows.append((heldout, heldout, target))

    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["partition_unit", "block", "target"])
    writer.writerows(rows)
    text = out.getvalue()
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()

    return RoutedPilotSurface(
        csv_text=text,
        raw_surface_sha256=digest,
        source_response_rows_seen=source_rows,
        pilot_response_rows_semantically_parsed=pilot_rows,
        confirmatory_species_values_parsed=0,
        confirmatory_presence_values_parsed=0,
        excluded_species_values_parsed=0,
        excluded_presence_values_parsed=0,
        pilot_catalogued_atolls=len(by_atoll),
        pilot_blocks_with_catalogues=sum(bool(v) for v in block_atolls.values()),
        pilot_species_universe=pilot_species_universe,
        pilot_species_universe_count=len(pilot_species_universe),
        pilot_species_universe_sha256=pilot_species_universe_sha256,
        blank_sentinel_blocks=tuple(blank_blocks),
    )
