"""Frozen heldout scorer for the 318-island mammal independent stress test.

No model fitting occurs here. The scorer accepts a pre-heldout prediction
surface whose SHA-256 was frozen before heldout occurrence access, decodes
only the fixed 233 species on the fixed 244 heldout islands, and evaluates
the already-declared v0.47 estimands.
"""
from __future__ import annotations

from dataclasses import dataclass
import csv
import hashlib
import io
import math
import random
from collections import defaultdict
from typing import Mapping, Sequence

from .zenodo_318_mammal_pilot_router import (
    MammalStressPilotRouterError,
    _cell_ref_and_type,
    _cells,
    _decode_cell,
    _decode_schema_headers,
    _row_bytes,
    _sheet_xml_and_shared,
)


class MammalStressHeldoutError(RuntimeError):
    pass


@dataclass(frozen=True)
class HeldoutOutcomeSurface:
    targets_by_island: dict[str, tuple[int, ...]]
    canonical_csv: str
    sha256: str
    occurrence_rows_seen: int
    heldout_islands_opened: int
    heldout_occurrence_values_parsed: int
    sealed_nonheldout_occurrence_values_parsed: int


def extract_heldout_outcomes(
    *,
    workbook_bytes: bytes,
    heldout_island_ids: Sequence[str],
    fixed_species: Sequence[str],
    expected_species_headers_sha256: str,
    expected_species_count: int = 1474,
    expected_sheet_dimension: str = "A1:BDU322",
    first_data_row: int = 5,
    last_data_row: int = 322,
) -> HeldoutOutcomeSurface:
    heldout_order=tuple(str(x) for x in heldout_island_ids)
    heldout_set=set(heldout_order)
    if len(heldout_set)!=len(heldout_order):
        raise MammalStressHeldoutError("duplicate heldout island ID")
    if not fixed_species or len(set(fixed_species))!=len(fixed_species):
        raise MammalStressHeldoutError("fixed species must be nonempty and unique")

    worksheet,shared=_sheet_xml_and_shared(workbook_bytes,sheet_name="occurrence")
    dm=__import__("re").search(br'<dimension[^>]*ref="([^"]+)"',worksheet[:20000])
    if not dm or dm.group(1).decode("ascii")!=expected_sheet_dimension:
        raise MammalStressHeldoutError("occurrence sheet dimension drift")

    all_species=_decode_schema_headers(
        worksheet,
        shared,
        expected_species_headers_sha256=expected_species_headers_sha256,
        expected_species_count=expected_species_count,
    )
    index={sp:i for i,sp in enumerate(all_species)}
    missing=[sp for sp in fixed_species if sp not in index]
    if missing:
        raise MammalStressHeldoutError(
            "fixed species missing from response schema: "+", ".join(missing[:10])
        )
    selected=tuple(index[sp] for sp in fixed_species)

    targets: dict[str,tuple[int,...]]={}
    rows_seen=0
    values_parsed=0

    for row_number in range(first_data_row,last_data_row+1):
        row=_row_bytes(worksheet,row_number)
        cells=_cells(row)
        if len(cells)!=3+expected_species_count:
            raise MammalStressHeldoutError(
                f"unexpected cell count at row {row_number}: {len(cells)}"
            )
        rows_seen+=1
        island_id=_decode_cell(
            cells[0],shared=shared,label="heldout routing island ID"
        ).strip()
        if not island_id:
            raise MammalStressHeldoutError(f"blank island ID at row {row_number}")
        if island_id not in heldout_set:
            # Occurrence cells remain byte-sealed for pilot/out-of-scope rows.
            continue
        if island_id in targets:
            raise MammalStressHeldoutError(f"duplicate heldout island row: {island_id}")

        vals=[]
        for j in selected:
            value=_decode_cell(
                cells[3+j],
                shared=shared,
                label=f"heldout occurrence island {island_id}",
            ).strip()
            if value not in {"0","1"}:
                raise MammalStressHeldoutError(
                    f"unexpected heldout occurrence value {value!r} on island {island_id}"
                )
            vals.append(int(value))
            values_parsed+=1
        targets[island_id]=tuple(vals)

    missing_islands=[x for x in heldout_order if x not in targets]
    if missing_islands:
        raise MammalStressHeldoutError(
            "missing heldout islands: "+", ".join(missing_islands[:20])
        )

    out=io.StringIO(newline="")
    w=csv.writer(out,lineterminator="\n")
    w.writerow(["island_id","species","target"])
    for iid in heldout_order:
        vals=targets[iid]
        for sp,y in zip(fixed_species,vals):
            w.writerow([iid,sp,str(y)])
    text=out.getvalue()
    return HeldoutOutcomeSurface(
        targets_by_island=targets,
        canonical_csv=text,
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        occurrence_rows_seen=rows_seen,
        heldout_islands_opened=len(targets),
        heldout_occurrence_values_parsed=values_parsed,
        sealed_nonheldout_occurrence_values_parsed=0,
    )


def _log_loss(y: int,p: float) -> float:
    if y not in (0,1):
        raise MammalStressHeldoutError("target must be 0/1")
    if not 0.0<p<1.0:
        raise MammalStressHeldoutError("prediction probability outside (0,1)")
    return -math.log(p if y else 1.0-p)


def _linear_quantile(values: Sequence[float], q: float) -> float:
    if not values:
        raise MammalStressHeldoutError("quantile of empty sequence")
    xs=sorted(values)
    h=(len(xs)-1)*q
    lo=math.floor(h)
    hi=math.ceil(h)
    if lo==hi:
        return xs[lo]
    frac=h-lo
    return xs[lo]*(1.0-frac)+xs[hi]*frac


def score_frozen_predictions(
    *,
    prediction_csv: str,
    expected_prediction_sha256: str,
    outcomes: HeldoutOutcomeSurface,
    heldout_order: Sequence[str],
    fixed_species: Sequence[str],
    bootstrap_replicates: int = 10000,
    bootstrap_seed: int = 20260927,
) -> dict:
    observed=hashlib.sha256(prediction_csv.encode("utf-8")).hexdigest()
    if observed!=expected_prediction_sha256:
        raise MammalStressHeldoutError("heldout prediction surface SHA-256 mismatch")

    heldout_order=tuple(str(x) for x in heldout_order)
    species=tuple(fixed_species)
    expected_pairs={(iid,sp) for iid in heldout_order for sp in species}

    rows=list(csv.DictReader(io.StringIO(prediction_csv)))
    if tuple(rows[0].keys())!=(
        "island_id","species","p_R3_hex","p_C_hex",
        "extreme_q75","archipelago","type"
    ):
        raise MammalStressHeldoutError("unexpected heldout prediction schema")
    if len(rows)!=len(expected_pairs):
        raise MammalStressHeldoutError("heldout prediction row count mismatch")

    seen=set()
    deltas=[]
    extreme_delta=[]
    nonextreme_delta=[]
    by_arch=defaultdict(lambda: {"ext_sum":0.0,"ext_n":0,"non_sum":0.0,"non_n":0})
    by_type=defaultdict(list)
    heldout_positive=0
    heldout_negative=0

    species_index={sp:i for i,sp in enumerate(species)}
    for row in rows:
        key=(row["island_id"],row["species"])
        if key in seen or key not in expected_pairs:
            raise MammalStressHeldoutError(f"unexpected/duplicate prediction pair: {key}")
        seen.add(key)
        iid,sp=key
        y=outcomes.targets_by_island[iid][species_index[sp]]
        heldout_positive+=y
        heldout_negative+=1-y

        p3=float.fromhex(row["p_R3_hex"])
        pc=float.fromhex(row["p_C_hex"])
        delta=_log_loss(y,pc)-_log_loss(y,p3)
        deltas.append(delta)
        extreme=row["extreme_q75"]
        if extreme not in {"0","1"}:
            raise MammalStressHeldoutError("invalid extreme_q75 flag")
        a=row["archipelago"]
        if extreme=="1":
            extreme_delta.append(delta)
            by_arch[a]["ext_sum"]+=delta
            by_arch[a]["ext_n"]+=1
        else:
            nonextreme_delta.append(delta)
            by_arch[a]["non_sum"]+=delta
            by_arch[a]["non_n"]+=1
        by_type[row["type"]].append(delta)

    if seen!=expected_pairs:
        raise MammalStressHeldoutError("heldout prediction pair set mismatch")
    if not extreme_delta or not nonextreme_delta:
        raise MammalStressHeldoutError("primary estimand lacks one isolation regime")

    extreme_mean=math.fsum(extreme_delta)/len(extreme_delta)
    nonextreme_mean=math.fsum(nonextreme_delta)/len(nonextreme_delta)
    primary=extreme_mean-nonextreme_mean
    overall=math.fsum(deltas)/len(deltas)

    clusters=tuple(sorted(by_arch))
    rng=random.Random(bootstrap_seed)
    draws=[]
    invalid=0
    for _ in range(bootstrap_replicates):
        ext_sum=0.0
        ext_n=0
        non_sum=0.0
        non_n=0
        for _j in range(len(clusters)):
            a=clusters[rng.randrange(len(clusters))]
            d=by_arch[a]
            ext_sum+=d["ext_sum"]
            ext_n+=d["ext_n"]
            non_sum+=d["non_sum"]
            non_n+=d["non_n"]
        if ext_n==0 or non_n==0:
            invalid+=1
            continue
        draws.append(ext_sum/ext_n - non_sum/non_n)

    if not draws:
        raise MammalStressHeldoutError("all bootstrap replicates invalid")
    ci_low=_linear_quantile(draws,0.025)
    ci_high=_linear_quantile(draws,0.975)
    supported=primary<0.0 and ci_high<0.0

    type_summary={}
    for typ,vals in sorted(by_type.items()):
        type_summary[typ]={
            "rows":len(vals),
            "mean_C_minus_R3_log_loss":math.fsum(vals)/len(vals),
        }

    return {
        "schema":"structural.zenodo_318_mammal_stress_score.v0_51",
        "heldout_islands":len(heldout_order),
        "species_count":len(species),
        "scored_rows":len(rows),
        "heldout_positive":heldout_positive,
        "heldout_negative":heldout_negative,
        "heldout_outcome_surface_sha256":outcomes.sha256,
        "prediction_surface_sha256":expected_prediction_sha256,
        "mean_C_minus_R3_log_loss_extreme_q75":extreme_mean,
        "mean_C_minus_R3_log_loss_nonextreme":nonextreme_mean,
        "primary_extreme_minus_nonextreme":primary,
        "overall_mean_C_minus_R3_log_loss":overall,
        "type_summary":type_summary,
        "bootstrap":{
            "unit":"Archipielago",
            "clusters":list(clusters),
            "replicates_requested":bootstrap_replicates,
            "replicates_accepted":len(draws),
            "replicates_invalid":invalid,
            "seed":bootstrap_seed,
            "rng":"python.random.Random (MT19937)",
            "sampling":"sample len(clusters) archipelago labels with replacement",
            "quantile_method":"linear",
            "ci_95_low":ci_low,
            "ci_95_high":ci_high,
        },
        "primary_prediction":"negative",
        "primary_supported":supported,
        "counts_as_fresh_confirmation":False,
        "counts_as_primary_confirmatory_evidence":False,
    }
