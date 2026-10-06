#!/usr/bin/env python3
"""Recover historical source counts from standardized Historical_total_log.

Reads only t0-safe columns. The protected future outcome remains opaque.
"""
from __future__ import annotations
import argparse,csv,json,math,re,unicodedata
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_standardized_historical_count_contract_v1_173.json"

class Stop(RuntimeError): pass

def norm_species(x:str)->str:
    x=unicodedata.normalize("NFC",str(x)).strip()
    return re.sub(r"\s+"," ",x)

def parse_float(x:str,label:str)->float:
    try:v=float(str(x).strip())
    except ValueError as exc:raise Stop(f"invalid {label}") from exc
    if not math.isfinite(v):raise Stop(f"nonfinite {label}")
    return v

def ols_xy(xs,ys):
    if len(xs)!=len(ys) or len(xs)<2:raise Stop("invalid calibration vectors")
    mx=math.fsum(xs)/len(xs);my=math.fsum(ys)/len(ys)
    den=math.fsum((x-mx)**2 for x in xs)
    if den<=0:raise Stop("zero anchor z variance")
    slope=math.fsum((x-mx)*(y-my) for x,y in zip(xs,ys))/den
    intercept=my-slope*mx
    if not math.isfinite(slope) or not math.isfinite(intercept):raise Stop("nonfinite calibration")
    return intercept,slope

def recover(safe_path:Path,router:dict,contract:dict):
    if contract.get("schema")!="structural.sw_finland_standardized_historical_count_contract.v1_173":
        raise Stop("contract schema drift")
    if router.get("status")!="T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE":
        raise Stop("t0 router not qualified")
    if router.get("protected_field_values_decoded")!=0 or router.get("outcome_values_read")!=0:
        raise Stop("future outcome boundary violated")

    z_by_species={}
    absent=defaultdict(set)
    islands=set()
    rows=0
    with safe_path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None or "outcome" in rd.fieldnames:raise Stop("unsafe t0 projection")
        for key in ("spp.name","holmkod","Historical_total_log"):
            if key not in rd.fieldnames:raise Stop(f"missing safe field {key}")
        seen_pairs=set()
        for row in rd:
            rows+=1
            sp=norm_species(row["spp.name"]);isl=str(row["holmkod"]).strip()
            if not sp or not isl:raise Stop("blank species/island routing key")
            pair=(sp,isl)
            if pair in seen_pairs:raise Stop(f"duplicate species-island pair: {sp}|{isl}")
            seen_pairs.add(pair);absent[sp].add(isl);islands.add(isl)
            z=parse_float(row["Historical_total_log"],"Historical_total_log")
            if sp in z_by_species and abs(z_by_species[sp]-z)>1e-12:
                raise Stop(f"Historical_total_log drift within species: {sp}")
            z_by_species[sp]=z

    if len(islands)!=471:raise Stop(f"expected 471 islands, found {len(islands)}")
    if len(z_by_species)!=587:raise Stop(f"expected 587 species, found {len(z_by_species)}")

    anchors_raw=contract["anchors"]["values"]
    anchors={norm_species(k):int(v) for k,v in anchors_raw.items()}
    matched=[sp for sp in sorted(anchors) if sp in z_by_species]
    if len(matched)<int(contract["calibration"]["minimum_anchor_matches"]):
        raise Stop(f"only {len(matched)} calibration anchors matched")
    xs=[z_by_species[sp] for sp in matched]
    ys=[math.log10(anchors[sp]+1.0) for sp in matched]
    intercept,slope=ols_xy(xs,ys)
    if contract["calibration"]["slope_must_be_positive"] and slope<=0:
        raise Stop("recovered calibration slope is not positive")

    anchor_rows=[];anchor_exact=True;anchor_max_error=0.0
    for sp in matched:
        raw=10.0**(intercept+slope*z_by_species[sp])-1.0
        nearest=int(round(raw))
        err=abs(raw-nearest)
        anchor_max_error=max(anchor_max_error,err)
        ok=nearest==anchors[sp]
        anchor_exact=anchor_exact and ok
        anchor_rows.append((sp,anchors[sp],raw,nearest,err,ok))

    if not anchor_exact:raise Stop("one or more t0 anchors failed exact integer recovery")
    if anchor_max_error>float(contract["calibration"]["maximum_anchor_count_rounding_error"]):
        raise Stop(f"anchor rounding error too large: {anchor_max_error}")

    out=[];max_err=0.0
    exact=incomplete=impossible=zero=0
    for sp in sorted(z_by_species):
        z=z_by_species[sp]
        raw=10.0**(intercept+slope*z)-1.0
        n=int(round(raw))
        if not 0<=n<=471:raise Stop(f"recovered source count outside [0,471]: {sp}: {raw}")
        err=abs(raw-n);max_err=max(max_err,err)
        n_abs=len(absent[sp]);total=n_abs+n
        if total==471 and n>=1:status="exact_source_identity_count_supported";exact+=1
        elif total<471:status="incomplete_archive_absence_set";incomplete+=1
        elif total>471:status="impossible_absence_plus_source_gt_471";impossible+=1
        else:status="exact_zero_historical_sources";zero+=1
        out.append({
          "species":sp,
          "Historical_total_log":z,
          "recovered_historical_source_count":n,
          "recovered_Potential_islands":471-n,
          "archived_absent_count":n_abs,
          "absence_plus_source_count":total,
          "count_rounding_error":err,
          "support_status":status
        })
    if max_err>float(contract["calibration"]["maximum_all_species_count_rounding_error"]):
        raise Stop(f"all-species rounding error too large: {max_err}")

    success=(
      impossible==0 and exact>=int(contract["support_audit"]["minimum_exact_species"])
    )
    receipt={
      "schema":"structural.sw_finland_standardized_historical_count_result.v1_173",
      "status":contract["success_ceiling"]["status"] if success else "T0_COUNT_CALIBRATION_VALID_BUT_EXACT_SOURCE_GATE_NOT_MET",
      "candidate_id":contract["candidate_id"],
      "archive_rows":rows,
      "species_count":len(z_by_species),
      "unique_islands":len(islands),
      "anchors_declared":len(anchors),
      "anchors_matched":len(matched),
      "anchor_species":matched,
      "calibration_intercept":intercept,
      "calibration_slope":slope,
      "calibration_intercept_hex":float(intercept).hex(),
      "calibration_slope_hex":float(slope).hex(),
      "anchor_max_count_rounding_error":anchor_max_error,
      "all_species_max_count_rounding_error":max_err,
      "exact_source_species":exact,
      "incomplete_species":incomplete,
      "impossible_species":impossible,
      "zero_source_species":zero,
      "minimum_exact_species_required":int(contract["support_audit"]["minimum_exact_species"]),
      "future_outcome_values_opened":0,
      "protected_outcome_values_decoded":0,
      "supplement_future_summary_values_used":0,
      "pilot_future_outcome_authorized":False,
      "confirmatory_future_outcome_authorized":False,
      "counts_as_empirical_evidence":False
    }
    return out,anchor_rows,receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("safe_csv",type=Path)
    p.add_argument("--router-receipt",type=Path,required=True)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--species-output",type=Path,required=True)
    p.add_argument("--anchor-output",type=Path)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        contract=json.loads(a.contract.read_text())
        router=json.loads(a.router_receipt.read_text())
        rows,anchors,r=recover(a.safe_csv,router,contract)
        a.species_output.parent.mkdir(parents=True,exist_ok=True)
        with a.species_output.open("w",encoding="utf-8",newline="") as f:
            fields=["species","Historical_total_log","recovered_historical_source_count","recovered_Potential_islands","archived_absent_count","absence_plus_source_count","count_rounding_error","support_status"]
            w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
        if a.anchor_output:
            a.anchor_output.parent.mkdir(parents=True,exist_ok=True)
            with a.anchor_output.open("w",encoding="utf-8",newline="") as f:
                w=csv.writer(f,lineterminator="\n");w.writerow(["species","expected_count","raw_count","rounded_count","rounding_error","exact"]);w.writerows(anchors)
        code=0 if r["status"]==contract["success_ceiling"]["status"] else 2
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={
          "schema":"structural.sw_finland_standardized_historical_count_result.v1_173",
          "status":"STOP_T0_STANDARDIZED_COUNT_RECOVERY",
          "reason":str(exc),
          "future_outcome_values_opened":0,
          "protected_outcome_values_decoded":0,
          "supplement_future_summary_values_used":0,
          "counts_as_empirical_evidence":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
