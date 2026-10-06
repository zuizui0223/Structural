#!/usr/bin/env python3
"""Recover SW Finland historical source counts with a logical-zero rule.

Numeric Historical_total_log tokens are calibrated exactly as in v1.173.
A nonnumeric token is accepted only when the t0-safe archive contains absence
rows on all 471 islands for that species, which logically fixes source count=0.
Future colonization outcome remains opaque.
"""
from __future__ import annotations
import argparse,csv,json,math,re,unicodedata
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_standardized_historical_count_contract_v1_173_2.json"
BASE_CONTRACT=ROOT/"development/sw_finland_standardized_historical_count_contract_v1_173.json"

class Stop(RuntimeError): pass

def norm_species(x:str)->str:
    return re.sub(r"\s+"," ",unicodedata.normalize("NFC",str(x)).strip())

def maybe_float(x:str):
    try:v=float(str(x).strip())
    except (ValueError,TypeError):return None
    return v if math.isfinite(v) else None

def ols_xy(xs,ys):
    if len(xs)!=len(ys) or len(xs)<2:raise Stop("invalid calibration vectors")
    mx=math.fsum(xs)/len(xs);my=math.fsum(ys)/len(ys)
    den=math.fsum((x-mx)**2 for x in xs)
    if den<=0:raise Stop("zero anchor z variance")
    slope=math.fsum((x-mx)*(y-my) for x,y in zip(xs,ys))/den
    intercept=my-slope*mx
    if not math.isfinite(slope) or not math.isfinite(intercept):raise Stop("nonfinite calibration")
    return intercept,slope

def recover(safe_path:Path,router:dict,contract:dict,base:dict):
    if contract.get("schema")!="structural.sw_finland_standardized_historical_count_contract.v1_173_2":
        raise Stop("contract schema drift")
    if router.get("status")!="T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE":
        raise Stop("t0 router not qualified")
    if router.get("protected_field_values_decoded")!=0 or router.get("outcome_values_read")!=0:
        raise Stop("future outcome boundary violated")

    token_by_species=defaultdict(set);absent=defaultdict(set);islands=set();pairs=set();rows=0
    with safe_path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None or "outcome" in rd.fieldnames:raise Stop("unsafe t0 projection")
        for key in ("spp.name","holmkod","Historical_total_log"):
            if key not in rd.fieldnames:raise Stop(f"missing safe field {key}")
        for row in rd:
            rows+=1
            sp=norm_species(row["spp.name"]);isl=str(row["holmkod"]).strip();tok=str(row["Historical_total_log"]).strip()
            if not sp or not isl:raise Stop("blank species/island key")
            pair=(sp,isl)
            if pair in pairs:raise Stop(f"duplicate species-island pair: {sp}|{isl}")
            pairs.add(pair);absent[sp].add(isl);islands.add(isl);token_by_species[sp].add(tok)

    if rows!=225345:raise Stop(f"archive row count drift: {rows}")
    if len(islands)!=471:raise Stop(f"expected 471 islands, found {len(islands)}")
    if len(token_by_species)!=587:raise Stop(f"expected 587 species, found {len(token_by_species)}")
    multi={sp:sorted(v) for sp,v in token_by_species.items() if len(v)!=1}
    if multi:raise Stop(f"Historical_total_log token drift within {len(multi)} species")

    numeric={};nonnumeric={}
    for sp,tokens in token_by_species.items():
        tok=next(iter(tokens));v=maybe_float(tok)
        if v is None:nonnumeric[sp]=tok
        else:numeric[sp]=v

    logical_zero={}
    unresolved={}
    for sp,tok in sorted(nonnumeric.items()):
        if len(absent[sp])==471:logical_zero[sp]=tok
        else:unresolved[sp]={"token":tok,"archived_absent_count":len(absent[sp])}
    if unresolved:
        raise Stop("nonnumeric Historical_total_log for species without complete 471-island absence support: "+json.dumps(unresolved,sort_keys=True))

    anchors={norm_species(k):int(v) for k,v in base["anchors"]["values"].items()}
    matched=[sp for sp in sorted(anchors) if sp in numeric]
    minimum=int(contract["unchanged_from_v1_173"]["minimum_numeric_anchor_matches"])
    if len(matched)<minimum:raise Stop(f"only {len(matched)} numeric calibration anchors matched")
    xs=[numeric[sp] for sp in matched]
    ys=[math.log10(anchors[sp]+1.0) for sp in matched]
    intercept,slope=ols_xy(xs,ys)
    if contract["unchanged_from_v1_173"]["slope_must_be_positive"] and slope<=0:
        raise Stop("recovered calibration slope is not positive")

    anchor_rows=[];anchor_max=0.0
    for sp in matched:
        raw=10.0**(intercept+slope*numeric[sp])-1.0
        nearest=int(round(raw));err=abs(raw-nearest);anchor_max=max(anchor_max,err)
        if nearest!=anchors[sp]:raise Stop(f"anchor integer recovery mismatch: {sp}: {nearest} != {anchors[sp]}")
        anchor_rows.append((sp,anchors[sp],raw,nearest,err,True))
    if anchor_max>float(contract["unchanged_from_v1_173"]["maximum_anchor_count_rounding_error"]):
        raise Stop(f"anchor rounding error too large: {anchor_max}")

    out=[];maxerr=0.0;exact=incomplete=impossible=zero=0
    for sp in sorted(token_by_species):
        n_abs=len(absent[sp])
        if sp in logical_zero:
            n=0;p=471;err=0.0;z_token=logical_zero[sp]
            status="exact_zero_historical_sources_from_complete_absence";zero+=1
        else:
            z=numeric[sp];raw=10.0**(intercept+slope*z)-1.0;n=int(round(raw));err=abs(raw-n);maxerr=max(maxerr,err)
            if not 0<=n<=471:raise Stop(f"recovered source count outside [0,471]: {sp}: {raw}")
            p=471-n;z_token=str(z)
            total=n_abs+n
            if total==471 and n>=1:status="exact_source_identity_count_supported";exact+=1
            elif total<471:status="incomplete_archive_absence_set";incomplete+=1
            elif total>471:status="impossible_absence_plus_source_gt_471";impossible+=1
            else:status="exact_zero_historical_sources";zero+=1
        total=n_abs+n
        out.append({
          "species":sp,
          "Historical_total_log":z_token,
          "recovered_historical_source_count":n,
          "recovered_Potential_islands":p,
          "archived_absent_count":n_abs,
          "absence_plus_source_count":total,
          "count_rounding_error":err,
          "support_status":status
        })

    if maxerr>float(contract["unchanged_from_v1_173"]["maximum_all_numeric_species_count_rounding_error"]):
        raise Stop(f"all-numeric-species rounding error too large: {maxerr}")
    if impossible>0:raise Stop(f"{impossible} impossible species after numeric recovery")
    min_exact=int(contract["unchanged_from_v1_173"]["minimum_exact_source_species"])
    success=exact>=min_exact

    receipt={
      "schema":contract["receipt_compatibility"]["schema"],
      "status":contract["receipt_compatibility"]["success_status"] if success else "T0_COUNT_CALIBRATION_VALID_BUT_EXACT_SOURCE_GATE_NOT_MET",
      "recovery_revision":"v1.173.2",
      "candidate_id":contract["candidate_id"],
      "archive_rows":rows,"species_count":len(token_by_species),"unique_islands":len(islands),
      "numeric_species":len(numeric),"nonnumeric_species":len(nonnumeric),
      "logical_zero_nonnumeric_species":len(logical_zero),
      "unresolved_nonnumeric_species":0,
      "logical_zero_species":sorted(logical_zero),
      "anchors_declared":len(anchors),"anchors_matched":len(matched),"anchor_species":matched,
      "calibration_intercept":intercept,"calibration_slope":slope,
      "calibration_intercept_hex":float(intercept).hex(),"calibration_slope_hex":float(slope).hex(),
      "anchor_max_count_rounding_error":anchor_max,
      "all_species_max_count_rounding_error":maxerr,
      "exact_source_species":exact,"incomplete_species":incomplete,"impossible_species":impossible,"zero_source_species":zero,
      "minimum_exact_species_required":min_exact,
      "future_outcome_values_opened":0,"protected_outcome_values_decoded":0,
      "supplement_future_summary_values_used":0,
      "pilot_future_outcome_authorized":False,"confirmatory_future_outcome_authorized":False,
      "counts_as_empirical_evidence":False
    }
    return out,anchor_rows,receipt

def main():
    p=argparse.ArgumentParser();p.add_argument("safe_csv",type=Path)
    p.add_argument("--router-receipt",type=Path,required=True)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--base-contract",type=Path,default=BASE_CONTRACT)
    p.add_argument("--species-output",type=Path,required=True)
    p.add_argument("--anchor-output",type=Path);p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        rows,anchors,r=recover(a.safe_csv,json.loads(a.router_receipt.read_text()),json.loads(a.contract.read_text()),json.loads(a.base_contract.read_text()))
        a.species_output.parent.mkdir(parents=True,exist_ok=True)
        fields=["species","Historical_total_log","recovered_historical_source_count","recovered_Potential_islands","archived_absent_count","absence_plus_source_count","count_rounding_error","support_status"]
        with a.species_output.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
        if a.anchor_output:
            a.anchor_output.parent.mkdir(parents=True,exist_ok=True)
            with a.anchor_output.open("w",encoding="utf-8",newline="") as f:
                w=csv.writer(f,lineterminator="\n");w.writerow(["species","expected_count","raw_count","rounded_count","rounding_error","exact"]);w.writerows(anchors)
        code=0 if r["status"]=="STANDARDIZED_HISTORICAL_SOURCE_COUNTS_RECOVERED_T0_ONLY" else 2
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={"schema":"structural.sw_finland_standardized_historical_count_result.v1_173",
           "status":"STOP_T0_STANDARDIZED_COUNT_RECOVERY_V1_173_2","recovery_revision":"v1.173.2",
           "reason":str(exc),"future_outcome_values_opened":0,"protected_outcome_values_decoded":0,
           "supplement_future_summary_values_used":0,"counts_as_empirical_evidence":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
