"""Byte-level router for one-shot boreal-bird confirmatory scoring."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from structural.boreal_beetle_pilot_router import _decode_utf8, _iter_csv_records_bytes


class BorealBirdConfirmatoryRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class RoutedBirdConfirmatory:
    fixed_species: tuple[str,...]
    confirmatory_targets: dict[str,tuple[int,...]]
    routing_fields_decoded: int
    source_rows_seen: int
    confirmatory_values_parsed: int
    pilot_values_parsed: int
    excluded_values_parsed: int
    nonfixed_confirmatory_values_parsed: int


def route_boreal_bird_confirmatory(
    *,
    response_csv_bytes: bytes,
    full_expected_islands: Sequence[str],
    pilot_islands: Sequence[str],
    confirmatory_islands: Sequence[str],
    fixed_species: Sequence[str],
    expected_species_columns: int = 54,
) -> RoutedBirdConfirmatory:
    full=set(full_expected_islands)
    pilot=set(pilot_islands)
    confirm=set(confirmatory_islands)
    fixed=tuple(fixed_species)
    if pilot & confirm or pilot|confirm - full:
        raise BorealBirdConfirmatoryRouterError("invalid frozen island sets")
    if len(fixed)!=len(set(fixed)) or not fixed:
        raise BorealBirdConfirmatoryRouterError("invalid fixed species universe")

    records=_iter_csv_records_bytes(response_csv_bytes)
    try:
        header=next(records)
    except StopIteration as exc:
        raise BorealBirdConfirmatoryRouterError("bird response CSV empty") from exc
    if header and header[0].startswith(b"\xef\xbb\xbf"):
        header=(header[0][3:],)+header[1:]
    if len(header)!=expected_species_columns+1:
        raise BorealBirdConfirmatoryRouterError("bird response species-column count drift")
    first=_decode_utf8(header[0],label="routing header").strip()
    if first!="Island":
        raise BorealBirdConfirmatoryRouterError("unexpected routing header")
    names=tuple(_decode_utf8(x,label="species header").strip() for x in header[1:])
    if any(not x for x in names) or len(names)!=len(set(names)):
        raise BorealBirdConfirmatoryRouterError("blank/duplicate species header")
    index={name:j+1 for j,name in enumerate(names)}
    if not set(fixed)<=set(index):
        raise BorealBirdConfirmatoryRouterError("fixed species absent from response header")
    fixed_indices=tuple(index[name] for name in fixed)

    seen=set();targets={};rows=routes=parsed=0
    for fields in records:
        if not fields or fields==(b"",):
            continue
        rows+=1
        if len(fields)!=len(header):
            raise BorealBirdConfirmatoryRouterError("response row width drift")
        island=_decode_utf8(fields[0],label="routing Island").strip()
        routes+=1
        if island not in full or island in seen:
            raise BorealBirdConfirmatoryRouterError("unknown/duplicate island row")
        seen.add(island)
        if island not in confirm:
            # All occurrence bytes remain opaque on pilot and excluded islands.
            continue
        values=[]
        for idx in fixed_indices:
            value=_decode_utf8(fields[idx],label="confirmatory fixed-species occurrence").strip()
            if value not in {"0","1"}:
                raise BorealBirdConfirmatoryRouterError("nonbinary fixed-species confirmatory value")
            values.append(int(value));parsed+=1
        targets[island]=tuple(values)

    if seen!=full or rows!=len(full):
        raise BorealBirdConfirmatoryRouterError("source island universe drift")
    if set(targets)!=confirm:
        raise BorealBirdConfirmatoryRouterError("confirmatory target island drift")
    return RoutedBirdConfirmatory(
        fixed_species=fixed,
        confirmatory_targets=targets,
        routing_fields_decoded=routes,
        source_rows_seen=rows,
        confirmatory_values_parsed=parsed,
        pilot_values_parsed=0,
        excluded_values_parsed=0,
        nonfixed_confirmatory_values_parsed=0,
    )
