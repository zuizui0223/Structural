"""One-shot pilot router for the sealed boreal bird matrix.

All 42 Island routing fields and 54 species-header names are decoded. Occurrence
cells are decoded only for the six frozen pilot islands. The 13 confirmatory
analysis islands and 23 excluded islands remain opaque at the occurrence level.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Mapping,Sequence

from structural.boreal_beetle_pilot_router import (
    _decode_utf8,
    _iter_csv_records_bytes,
    _species_universe_sha,
    encode_binary_vector_hex,
)

class BorealBirdPilotRouterError(RuntimeError):
    pass

@dataclass(frozen=True)
class RoutedBorealBirdPilot:
    source_response_rows_seen:int
    routing_island_fields_decoded:int
    header_species_names_parsed:int
    pilot_island_rows_semantically_parsed:int
    pilot_target_values_parsed:int
    confirmatory_target_values_parsed:int
    excluded_target_values_parsed:int
    pilot_species_universe:tuple[str,...]
    pilot_species_universe_count:int
    pilot_species_universe_sha256:str
    pilot_species_n:tuple[tuple[str,int],...]
    distinct_eligible_n:tuple[int,...]
    pilot_island_order:tuple[str,...]
    pilot_island_to_block:tuple[tuple[str,str],...]
    pilot_targets_hex_by_island:tuple[tuple[str,str],...]
    snapshot_fingerprint:str

def _snapshot_fingerprint(payload:dict)->str:
    import json
    return hashlib.sha256(
        json.dumps(payload,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")
    ).hexdigest()

def route_boreal_bird_pilot(
    *,
    response_csv_bytes:bytes,
    full_expected_islands:Sequence[str],
    analysis_expected_islands:Sequence[str],
    analysis_island_to_block:Mapping[str,str],
    pilot_block_ids:Sequence[str],
    confirmatory_block_ids:Sequence[str],
    expected_species_count:int=54,
    minimum_eligible_species:int=8,
    minimum_distinct_n_values:int=2,
)->RoutedBorealBirdPilot:
    full_order=tuple(full_expected_islands);full_set=set(full_order)
    analysis_order=tuple(analysis_expected_islands);analysis_set=set(analysis_order)
    pilot_blocks=tuple(pilot_block_ids);pilot_block_set=set(pilot_blocks)
    confirmatory_blocks=tuple(confirmatory_block_ids);confirmatory_block_set=set(confirmatory_blocks)

    if len(full_order)!=42 or len(full_set)!=42:
        raise BorealBirdPilotRouterError("full source island universe must contain 42 unique islands")
    if len(analysis_order)!=19 or len(analysis_set)!=19 or not analysis_set<full_set:
        raise BorealBirdPilotRouterError("analysis universe must be the frozen 19-island strict subset")
    if pilot_block_set & confirmatory_block_set:
        raise BorealBirdPilotRouterError("pilot/confirmatory blocks overlap")
    if set(analysis_island_to_block)!=analysis_set:
        raise BorealBirdPilotRouterError("analysis island/block map drift")

    records=_iter_csv_records_bytes(response_csv_bytes)
    try: header=next(records)
    except StopIteration as exc: raise BorealBirdPilotRouterError("bird response CSV is empty") from exc
    if header and header[0].startswith(b"\xef\xbb\xbf"):
        header=(header[0][3:],)+header[1:]
    if len(header)!=expected_species_count+1:
        raise BorealBirdPilotRouterError("bird response header does not match frozen 54-species count")
    first=_decode_utf8(header[0],label="routing header").strip()
    if first!="Island":
        raise BorealBirdPilotRouterError(f"unexpected bird routing header: {first!r}")
    species=tuple(_decode_utf8(x,label="bird species header").strip() for x in header[1:])
    if any(not x for x in species) or len(species)!=len(set(species)):
        raise BorealBirdPilotRouterError("blank or duplicate bird species header")

    seen=set();pilot_values={}
    source_rows=routing_decoded=pilot_rows=pilot_targets=confirmatory_rows=excluded_rows=0
    for fields in records:
        if not fields or fields==(b"",): continue
        source_rows+=1
        if len(fields)!=len(header):
            raise BorealBirdPilotRouterError("bird response row width differs from frozen header")
        island=_decode_utf8(fields[0],label="routing Island").strip();routing_decoded+=1
        if not island or island not in full_set or island in seen:
            raise BorealBirdPilotRouterError("blank, unknown, or duplicate Island routing field")
        seen.add(island)

        if island not in analysis_set:
            excluded_rows+=1
            continue
        block=analysis_island_to_block[island]
        if block in confirmatory_block_set:
            confirmatory_rows+=1
            continue
        if block not in pilot_block_set:
            raise BorealBirdPilotRouterError("analysis island routed to unfrozen block")

        vals=[]
        for raw in fields[1:]:
            value=_decode_utf8(raw,label="pilot bird occurrence").strip()
            if value not in {"0","1"}:
                raise BorealBirdPilotRouterError(f"unexpected pilot bird occurrence: {value!r}")
            vals.append(int(value))
        pilot_values[island]=tuple(vals)
        pilot_rows+=1;pilot_targets+=len(vals)

    if seen!=full_set or source_rows!=42:
        raise BorealBirdPilotRouterError("bird response source-island universe drift")
    if pilot_rows!=6 or confirmatory_rows!=13 or excluded_rows!=23:
        raise BorealBirdPilotRouterError("bird pilot/confirmatory/excluded row count drift")
    if pilot_targets!=6*expected_species_count:
        raise BorealBirdPilotRouterError("bird pilot target parse count drift")

    support=[0]*len(species)
    for vals in pilot_values.values():
        for j,v in enumerate(vals): support[j]+=v
    eligible_indices=tuple(j for j,n in enumerate(support) if 1<=n<=5)
    universe=tuple(species[j] for j in eligible_indices)
    n_by_species=tuple((species[j],support[j]) for j in eligible_indices)
    distinct_n=tuple(sorted({support[j] for j in eligible_indices}))
    if len(universe)<minimum_eligible_species:
        raise BorealBirdPilotRouterError("fewer than frozen minimum eligible bird species")
    if len(distinct_n)<minimum_distinct_n_values:
        raise BorealBirdPilotRouterError("insufficient distinct pilot occupancy counts")

    pilot_by_block={b:[] for b in pilot_blocks}
    for island in analysis_order:
        block=analysis_island_to_block[island]
        if block in pilot_block_set:
            if island not in pilot_values:
                raise BorealBirdPilotRouterError("frozen pilot island was not semantically parsed")
            pilot_by_block[block].append(island)
    if any(not xs for xs in pilot_by_block.values()):
        raise BorealBirdPilotRouterError("pilot spatial block has no island")

    pilot_order=[];island_block=[];target_hex=[]
    for block in pilot_blocks:
        for island in sorted(pilot_by_block[block]):
            restricted=tuple(pilot_values[island][j] for j in eligible_indices)
            pilot_order.append(island);island_block.append((island,block))
            target_hex.append((island,encode_binary_vector_hex(restricted)))

    core={
        "pilot_species_universe":list(universe),
        "pilot_species_n":[{"species":s,"n":n} for s,n in n_by_species],
        "pilot_island_order":pilot_order,
        "pilot_island_to_block":dict(island_block),
        "targets_hex_by_island":dict(target_hex),
    }
    return RoutedBorealBirdPilot(
        source_response_rows_seen=source_rows,
        routing_island_fields_decoded=routing_decoded,
        header_species_names_parsed=len(species),
        pilot_island_rows_semantically_parsed=pilot_rows,
        pilot_target_values_parsed=pilot_targets,
        confirmatory_target_values_parsed=0,
        excluded_target_values_parsed=0,
        pilot_species_universe=universe,
        pilot_species_universe_count=len(universe),
        pilot_species_universe_sha256=_species_universe_sha(universe),
        pilot_species_n=n_by_species,
        distinct_eligible_n=distinct_n,
        pilot_island_order=tuple(pilot_order),
        pilot_island_to_block=tuple(island_block),
        pilot_targets_hex_by_island=tuple(target_hex),
        snapshot_fingerprint=_snapshot_fingerprint(core),
    )
