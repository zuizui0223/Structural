#!/usr/bin/env python3
"""Recover SW Finland historical source counts for the frozen numeric t0 pool.

Species whose Historical_total_log is nonnumeric are excluded before calibration
and remain permanently ineligible for this route. Future colonization outcome is
never parsed.
"""
from __future__ import annotations
import argparse,csv,json,math,re,unicodedata
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_standardized_historical_count_contract_v1_173_3.json"
BASE_CONTRACT=ROOT/"development/sw_finland_standardized_historical_count_contract_v1_173.json"

class Stop(RuntimeError): pass

def norm(x:str)->str:
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
    if not math.isfinite(intercept) or not math.isfinite(slope):raise Stop("nonfinite calibration")
    return intercept,slope

def recover(safe_path:Path,router:dict,contract:dict,base:dict):
    if contract.get("schema")!="structural.sw_finland_standardized_historical_count_contract.v1_173_3":
        raise Stop("contract schema drift")
    if router.get("status")!="T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE":
        raise Stop("t0 router not qualified")
    if router.get("protected_field_values_decoded")!=0 or router.get("outcome_values_read")!=0:
        raise Stop("future outcome boundary violated")

    tokens=defaultdict(set);absent=defaultdict(set);islands=set();pairs=set();rows=0
    with safe_path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None or "outcome" in rd.fieldnames:raise Stop("unsafe t0 projection")
        for key in ("spp.name","holmkod","Historical_total_log"):
            if key not in rd.fieldnames:raise Stop(f"missing safe field {key}")
        for row in rd:
            rows+=1
            sp=norm(row["spp.name"]);isl=str(row["holmkod"]).strip();tok=str(row["Historical_total_log"]).strip()
            if not sp or not isl:raise Stop("blank species/island key")
            pair=(sp,isl)
            if pair in pairs:raise Stop(f"duplicate species-island pair: {sp}|{isl}")
            pairs.add(pair);tokens[sp].add(tok);absent[sp].add(isl);islands.add(isl)

    if rows!=225345:raise Stop(f"archive row count drift: {rows}")
    if len(tokens)!=587:raise Stop(f"species count drift: {len(tokens)}")
    if len(islands)!=471:raise Stop(f"island count drift: {len(islands)}")
    multi={sp:sorted(v) for sp,v in tokens.items() if len(v)!=1}
    if multi:raise Stop(f"within-species token mixture in {len(multi)} species")

    numeric={};excluded={}
    for sp,tokset in tokens.items():
        tok=next(iter(tokset));v=maybe_float(tok)
        if v is None:excluded[sp]=(tok,len(absent[sp]))
        else:numeric[sp]=v

    expected_numeric=int(contract["eligibility"]["expected_numeric_species"])
    expected_excluded=int(contract["eligibility"]["excluded_species_expected"])
    if len(numeric)!=expected_numeric:raise Stop(f"numeric species drift: {len(numeric)} != {expected_numeric}")
    if len(excluded)!=expected_excluded:raise Stop(f"excluded species drift: {len(excluded)} != {expected_excluded}")

    anchors={norm(k):int(v) for k,v in base["anchors"]["values"].items()}
    anchors.update({norm(k):int(v) for k,v in contract["anchors"]["additional_t0_anchors"].items()})
    matched=[sp for sp in sorted(anchors) if sp in numeric]
    if len(matched)<int(contract["anchors"]["minimum_numeric_anchor_matches"]):
        raise Stop(f"only {len(matched)} numeric anchors matched")
    if len(matched)!=int(contract["anchors"]["expected_numeric_anchor_matches"]):
        raise Stop(f"numeric anchor count drift: {len(matched)}")

    xs=[numeric[sp] for sp in matched]
    ys=[math.log10(anchors[sp]+1.0) for sp in matched]
    intercept,slope=ols_xy(xs,ys)
    if contract["calibration"]["slope_must_be_positive"] and slope<=0:raise Stop("nonpositive calibration slope")

    anchor_max=0.0
    anchor_rows=[]
    for sp in matched:
        raw=10.0**(intercept+slope*numeric[sp])-1.0
        nearest=int(round(raw));err=abs(raw-nearest);anchor_max=max(anchor_max,err)
        exact=nearest==anchors[sp]
        if not exact:raise Stop(f"anchor integer mismatch: {sp}: {nearest} != {anchors[sp]}")
        anchor_rows.append((sp,anchors[sp],raw,nearest,err,exact))
    if anchor_max>float(contract["calibration"]["maximum_anchor_count_rounding_error"]):
        raise Stop(f"anchor rounding error too large: {anchor_max}")

    out=[];maxerr=0.0;exact=incomplete=impossible=zero=0
    for sp in sorted(numeric):
        raw=10.0**(intercept+slope*numeric[sp])-1.0
        n=int(round(raw));err=abs(raw-n);maxerr=max(maxerr,err)
        if not 0<=n<=471:raise Stop(f"recovered count outside [0,471]: {sp}: {raw}")
        p=471-n;n_abs=len(absent[sp]);total=n_abs+n
        if n==0:
            status="zero_historical_sources";zero+=1
        elif total==471:
            status="exact_source_identity_count_supported";exact+=1
        elif total<471:
            status="incomplete_archive_absence_set";incomplete+=1
        else:
            status="impossible_absence_plus_source_gt_471";impossible+=1
        out.append({
          "species":sp,
          "Historical_total_log":numeric[sp],
          "recovered_historical_source_count":n,
          "recovered_Potential_islands":p,
          "archived_absent_count":n_abs,
          "absence_plus_source_count":total,
          "count_rounding_error":err,
          "support_status":status
        })

    if maxerr>float(contract["calibration"]["maximum_all_numeric_species_count_rounding_error"]):
        raise Stop(f"numeric-pool rounding error too large: {maxerr}")
    if impossible!=int(contract["archive_support"]["impossible_species_required"]):
        raise Stop(f"{impossible} impossible numeric species")
    if exact<int(contract["calibration"]["minimum_exact_source_species"]):
        raise Stop(f"only {exact} exact-source numeric species")

    excluded_rows=[
      {"species":sp,"Historical_total_log_token":tok,"archived_absent_count":n_abs,"exclusion_reason":"nonnumeric_t0_source_count"}
      for sp,(tok,n_abs) in sorted(excluded.items())
    ]
    receipt={
      "schema":"structural.sw_finland_numeric_historical_count_result.v1_173_3",
      "status":contract["success_ceiling"]["status"],
      "candidate_id":contract["candidate_id"],
      "archive_rows":rows,
      "species_total":len(tokens),
      "numeric_species":len(numeric),
      "excluded_nonnumeric_species":len(excluded),
      "unique_islands":len(islands),
      "anchors_total_available":len(anchors),
      "anchors_matched_numeric":len(matched),
      "anchor_species":matched,
      "calibration_intercept":intercept,
      "calibration_slope":slope,
      "calibration_intercept_hex":float(intercept).hex(),
      "calibration_slope_hex":float(slope).hex(),
      "anchor_max_count_rounding_error":anchor_max,
      "all_numeric_species_max_count_rounding_error":maxerr,
      "exact_source_species":exact,
      "incomplete_species":incomplete,
      "impossible_species":impossible,
      "zero_source_species":zero,
      "minimum_exact_source_species":int(contract["calibration"]["minimum_exact_source_species"]),
      "future_outcome_values_opened":0,
      "protected_outcome_values_decoded":0,
      "supplement_future_summary_values_used":0,
      "pilot_future_outcome_authorized":False,
      "confirmatory_future_outcome_authorized":False,
      "counts_as_empirical_evidence":False
    }
    return out,excluded_rows,anchor_rows,receipt

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("safe_csv",type=Path)
    p.add_argument("--router-receipt",type=Path,required=True)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--base-contract",type=Path,default=BASE_CONTRACT)
    p.add_argument("--species-output",type=Path,required=True)
    p.add_argument("--excluded-output",type=Path,required=True)
    p.add_argument("--anchor-output",type=Path)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        rows,excluded,anchors,r=recover(
          a.safe_csv,
          json.loads(a.router_receipt.read_text()),
          json.loads(a.contract.read_text()),
          json.loads(a.base_contract.read_text())
        )
        a.species_output.parent.mkdir(parents=True,exist_ok=True)
        fields=["species","Historical_total_log","recovered_historical_source_count","recovered_Potential_islands","archived_absent_count","absence_plus_source_count","count_rounding_error","support_status"]
        with a.species_output.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
        with a.excluded_output.open("w",encoding="utf-8",newline="") as f:
            fields2=["species","Historical_total_log_token","archived_absent_count","exclusion_reason"]
            w=csv.DictWriter(f,fieldnames=fields2,lineterminator="\n");w.writeheader();w.writerows(excluded)
        if a.anchor_output:
            with a.anchor_output.open("w",encoding="utf-8",newline="") as f:
                w=csv.writer(f,lineterminator="\n");w.writerow(["species","expected_count","raw_count","rounded_count","rounding_error","exact"]);w.writerows(anchors)
        code=0
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={
          "schema":"structural.sw_finland_numeric_historical_count_result.v1_173_3",
          "status":"STOP_T0_NUMERIC_POOL_COUNT_RECOVERY",
          "reason":str(exc),
          "future_outcome_values_opened":0,
          "protected_outcome_values_decoded":0,
          "supplement_future_summary_values_used":0,
          "counts_as_empirical_evidence":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
