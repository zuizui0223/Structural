#!/usr/bin/env python3
"""Score the frozen boreal-bird topology-sensitivity primary exactly once."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Mapping

from structural.boreal_19island_bird_confirmatory_router import (
    BorealBirdConfirmatoryRouterError,
    route_boreal_bird_confirmatory,
)
from structural.boreal_spatial_partition import type7_quantile

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/boreal_bird_confirmatory_scoring_contract_v1_165.json"
DEFAULT_SPATIAL=ROOT/"development/boreal_19island_spatial_partition_freeze_v1_00.json"
DEFAULT_FULL=ROOT/"development/boreal_lake_islands_thesis_safe_table_v0_69.json"


class BirdConfirmatoryScoringError(RuntimeError):
    pass


def load_json(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict):raise BirdConfirmatoryScoringError("JSON object required")
    return x


def sha256_bytes(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()


def parse_hex(x)->float:
    v=float.fromhex(str(x))
    if not math.isfinite(v):raise BirdConfirmatoryScoringError("nonfinite prediction")
    return v


def logloss1(p:float)->float:
    if not 0<p<1:raise BirdConfirmatoryScoringError("probability outside (0,1)")
    return -math.log(p)


def weighted_slope(rows):
    # rows: (block,z,d). Every block gets total weight 1.
    grouped=defaultdict(list)
    for b,z,d in rows:grouped[b].append((z,d))
    weighted=[]
    for b,cells in grouped.items():
        w=1.0/len(cells)
        weighted.extend((w,z,d) for z,d in cells)
    sw=math.fsum(w for w,_,_ in weighted)
    mz=math.fsum(w*z for w,z,_ in weighted)/sw
    md=math.fsum(w*d for w,_,d in weighted)/sw
    den=math.fsum(w*(z-mz)**2 for w,z,_ in weighted)
    if den<=0:raise BirdConfirmatoryScoringError("weighted zS denominator zero")
    num=math.fsum(w*(z-mz)*(d-md) for w,z,d in weighted)
    return num/den


def equal_block_mean(values):
    by=defaultdict(list)
    for block,value in values:by[block].append(value)
    return math.fsum(math.fsum(v)/len(v) for v in by.values())/len(by)


def bootstrap_slopes(rows,replicates,seed):
    by=defaultdict(list)
    for b,z,d in rows:by[b].append((z,d))
    blocks=sorted(by)
    out=[]
    for rep in range(replicates):
        sampled=[]
        for draw in range(len(blocks)):
            h=hashlib.sha256(f"{seed}|{rep}|{draw}".encode()).digest()
            b=blocks[int.from_bytes(h[:8],"big")%len(blocks)]
            # Give each draw a unique pseudo-block label so duplicate draws count twice.
            label=f"{draw}:{b}"
            sampled.extend((label,z,d) for z,d in by[b])
        try:out.append(weighted_slope(sampled))
        except BirdConfirmatoryScoringError:
            continue
    if not out:raise BirdConfirmatoryScoringError("all bootstrap slopes unestimable")
    return out


def score(
    response_bytes:bytes,
    *,
    predictions_path:Path,
    preconfirmatory:Mapping,
    pilot_snapshot:Mapping,
    contract:Mapping,
    spatial:Mapping,
    full_source:Mapping,
)->dict:
    req=contract["required_preconfirmatory"]
    for k in ("schema","status"):
        if preconfirmatory.get(k)!=req[k]:
            raise BirdConfirmatoryScoringError("preconfirmatory freeze did not qualify")
    if preconfirmatory.get("bird_confirmatory_values_opened")!=0:
        raise BirdConfirmatoryScoringError("confirmatory already opened")
    if preconfirmatory.get("bird_confirmatory_response_authorized") is not False:
        raise BirdConfirmatoryScoringError("preconfirmatory authorization drift")

    target=contract["response_file"]
    if len(response_bytes)!=target["expected_size_bytes"] or sha256_bytes(response_bytes)!=target["expected_sha256"]:
        raise BirdConfirmatoryScoringError("bird response identity mismatch")
    if preconfirmatory.get("pilot_snapshot_fingerprint") != pilot_snapshot.get("snapshot_fingerprint"):
        raise BirdConfirmatoryScoringError("pilot snapshot/preconfirmatory fingerprint mismatch")
    if preconfirmatory.get("fixed_species_count") != pilot_snapshot.get("fixed_species_count"):
        raise BirdConfirmatoryScoringError("fixed species count drift")
    if sha256_bytes(predictions_path.read_bytes()) != preconfirmatory.get("prediction_surface_sha256"):
        raise BirdConfirmatoryScoringError("prediction surface SHA mismatch")

    fixed=list(pilot_snapshot["fixed_species"])
    routed=route_boreal_bird_confirmatory(
        response_csv_bytes=response_bytes,
        full_expected_islands=full_source["current_study_island_universe"]["codes"],
        pilot_islands=spatial["pilot_islands"],
        confirmatory_islands=spatial["confirmatory_islands"],
        fixed_species=fixed,
        expected_species_columns=target["reported_species_columns"],
    )
    expected=13*len(fixed)
    if routed.confirmatory_values_parsed!=expected:
        raise BirdConfirmatoryScoringError("confirmatory parsed-cell count drift")

    with predictions_path.open("r",encoding="utf-8",newline="") as h:
        rows=list(csv.DictReader(h))
    if len(rows)!=expected:
        raise BirdConfirmatoryScoringError("prediction row count drift")
    pmap={(r["island"],r["species"]):r for r in rows}
    if len(pmap)!=expected:
        raise BirdConfirmatoryScoringError("duplicate prediction key")

    primary_rows=[]
    d_values=[]
    per_null=[[] for _ in range(20)]
    presence_count=0
    for island in spatial["confirmatory_islands"]:
        values=routed.confirmatory_targets[island]
        block=spatial["island_to_block"][island]
        for j,species in enumerate(fixed):
            y=values[j]
            r=pmap[(island,species)]
            pa=parse_hex(r["p_C_actual_hex"])
            pn=[parse_hex(r[f"p_C_null_{k:02d}_hex"]) for k in range(1,21)]
            z=parse_hex(r["zS_hex"])
            if y==1:
                presence_count+=1
                la=logloss1(pa)
                ln=[logloss1(p) for p in pn]
                d=la-math.fsum(ln)/20
                primary_rows.append((block,z,d))
                d_values.append((block,d))
                for k in range(20):
                    per_null[k].append((block,la-ln[k]))

    presence_blocks=sorted({b for b,_,_ in primary_rows})
    minimum=contract["primary"]["minimum_presence_blocks"]
    if len(presence_blocks)<minimum:
        return {
          "schema":"structural.boreal_bird_confirmatory_result.v1_165",
          "status":"TERMINAL_NONESTIMABLE_TOO_FEW_PRESENCE_BLOCKS",
          "candidate_id":contract["candidate_id"],
          "presence_cells":presence_count,
          "presence_blocks":len(presence_blocks),
          "primary_supported":False,
          "rerun_authorized":False,
          "pilot_values_parsed":0,
          "excluded_values_parsed":0,
          "nonfixed_confirmatory_values_parsed":0,
          "confirmatory_fixed_species_values_parsed":routed.confirmatory_values_parsed,
          "counts_as_empirical_evidence":True,
        }

    beta=weighted_slope(primary_rows)
    boot=bootstrap_slopes(
        primary_rows,
        contract["primary"]["bootstrap_replicates"],
        contract["primary"]["bootstrap_seed"],
    )
    lo=type7_quantile(boot,0.025);hi=type7_quantile(boot,0.975)
    support=beta<0 and hi<0
    mean_d=equal_block_mean(d_values)
    null_means=[equal_block_mean(vals) for vals in per_null]
    actual_better=sum(x<0 for x in null_means)
    return {
      "schema":"structural.boreal_bird_confirmatory_result.v1_165",
      "status":"BIRD_TOPOLOGY_SENSITIVITY_PRIMARY_SUPPORTED" if support else "BIRD_TOPOLOGY_SENSITIVITY_PRIMARY_NOT_SUPPORTED",
      "candidate_id":contract["candidate_id"],
      "presence_cells":presence_count,
      "presence_blocks":len(presence_blocks),
      "primary_beta_S":beta,
      "bootstrap_ci95":[lo,hi],
      "bootstrap_estimable_replicates":len(boot),
      "primary_supported":support,
      "secondary_equal_block_mean_D":mean_d,
      "secondary_actual_better_than_nulls":f"{actual_better}/20",
      "secondary_actual_minus_each_null_equal_block":null_means,
      "pilot_values_parsed":0,
      "excluded_values_parsed":0,
      "nonfixed_confirmatory_values_parsed":0,
      "confirmatory_fixed_species_values_parsed":routed.confirmatory_values_parsed,
      "rerun_authorized":False,
      "beetle_primary_status_changed":False,
      "eBird_enabled":False,
      "counts_as_empirical_evidence":True,
    }


def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("response_csv",type=Path)
    p.add_argument("predictions",type=Path)
    p.add_argument("preconfirmatory",type=Path)
    p.add_argument("pilot_snapshot",type=Path)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--spatial",type=Path,default=DEFAULT_SPATIAL)
    p.add_argument("--full-source",type=Path,default=DEFAULT_FULL)
    p.add_argument("--result",type=Path)
    a=p.parse_args()
    try:
        result=score(
          a.response_csv.read_bytes(),
          predictions_path=a.predictions,
          preconfirmatory=load_json(a.preconfirmatory),
          pilot_snapshot=load_json(a.pilot_snapshot),
          contract=load_json(a.contract),
          spatial=load_json(a.spatial),
          full_source=load_json(a.full_source),
        )
    except (OSError,KeyError,TypeError,ValueError,json.JSONDecodeError,
            BorealBirdConfirmatoryRouterError,BirdConfirmatoryScoringError) as exc:
        result={
          "schema":"structural.boreal_bird_confirmatory_result.v1_165",
          "status":"TERMINAL_POST_ACCESS_SCORING_FAILURE",
          "reason":str(exc),
          "primary_supported":False,
          "rerun_authorized":False,
          "counts_as_empirical_evidence":True,
        }
        code=2
    else:
        code=0
    rendered=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.result is not None:
        a.result.parent.mkdir(parents=True,exist_ok=True);a.result.write_text(rendered)
    print(rendered,end="")
    return code


if __name__=="__main__":
    raise SystemExit(main())
