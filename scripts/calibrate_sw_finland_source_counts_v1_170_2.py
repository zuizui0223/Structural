#!/usr/bin/env python3
"""Recover SW Finland historical source counts from t0-safe standardized logs.

No recent colonization outcome is read. Six already-frozen t0 source-count
anchors calibrate the documented affine standardization of log10(n+1).
"""
from __future__ import annotations
import argparse,csv,json,math,unicodedata
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_anchor_source_count_inversion_contract_v1_170_2.json"
DEFAULT_ANCHOR_CONTRACT=ROOT/"development/sw_finland_potential_lookup_execution_contract_v1_170.json"

class Stop(RuntimeError): pass

def norm(x:str)->str:
    return unicodedata.normalize("NFC",str(x)).strip()

def load_json(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict):raise Stop(f"{path.name} must contain object")
    return x

def parse_float(x:str,label:str)->float:
    try:v=float(str(x).strip())
    except ValueError as exc:raise Stop(f"invalid {label}") from exc
    if not math.isfinite(v):raise Stop(f"nonfinite {label}")
    return v

def ols_affine(points:list[tuple[float,float]])->tuple[float,float]:
    if len(points)<2:raise Stop("too few calibration anchors")
    mx=math.fsum(x for x,_ in points)/len(points)
    my=math.fsum(y for _,y in points)/len(points)
    sxx=math.fsum((x-mx)**2 for x,_ in points)
    if sxx<=0:raise Stop("zero anchor z variance")
    slope=math.fsum((x-mx)*(y-my) for x,y in points)/sxx
    intercept=my-slope*mx
    if not math.isfinite(intercept) or not math.isfinite(slope) or slope<=0:
        raise Stop("invalid/nonpositive calibration")
    return intercept,slope

def nearest_count(y:float,total_islands:int)->tuple[int,float,float,float]:
    vals=[]
    for n in range(total_islands+1):
        d=abs(y-math.log10(n+1))
        vals.append((d,n))
    vals.sort(key=lambda t:(t[0],t[1]))
    best_d,best_n=vals[0];second_d,_=vals[1]
    ratio=0.0 if best_d==0 else best_d/second_d
    return best_n,best_d,second_d,ratio

def calibrate(safe_path:Path,contract:dict,anchor_contract:dict):
    if contract.get("schema")!="structural.sw_finland_anchor_source_count_inversion_contract.v1_170_2":
        raise Stop("contract schema drift")
    anchors=anchor_contract.get("anchor_checks")
    if not isinstance(anchors,dict) or len(anchors)!=int(contract["anchor_source"]["required_anchor_species"]):
        raise Stop("frozen anchor set drift")

    z_by_species={}
    absent=Counter()
    rows=0
    with safe_path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None or "outcome" in rd.fieldnames:raise Stop("unsafe t0 projection")
        for key in ("spp.name","holmkod","Historical_total_log"):
            if key not in rd.fieldnames:raise Stop(f"missing {key}")
        seen_pairs=set()
        for row in rd:
            rows+=1
            sp=norm(row["spp.name"]);isl=norm(row["holmkod"])
            if not sp or not isl:raise Stop("blank routing key")
            pair=(sp,isl)
            if pair in seen_pairs:raise Stop(f"duplicate species-island pair: {sp}|{isl}")
            seen_pairs.add(pair)
            absent[sp]+=1
            raw=str(row["Historical_total_log"]).strip()
            z=parse_float(raw,"Historical_total_log")
            if sp in z_by_species and z_by_species[sp][0]!=raw:
                raise Stop(f"Historical_total_log token drift within {sp}")
            z_by_species[sp]=(raw,z)

    if len(z_by_species)!=587:raise Stop(f"expected 587 species, found {len(z_by_species)}")
    total=471
    points=[]
    anchor_expected={}
    for sp,potential in anchors.items():
        sp=norm(sp)
        if sp not in z_by_species:raise Stop(f"anchor missing from archive: {sp}")
        n=total-int(potential)
        if not 0<=n<=total:raise Stop(f"anchor source count outside range: {sp}")
        anchor_expected[sp]=n
        points.append((z_by_species[sp][1],math.log10(n+1)))
    intercept,slope=ols_affine(points)

    max_ratio=float(contract["calibration"]["maximum_ambiguity_ratio"])
    results=[];unresolved=[];impossible=[];exact=0;incomplete=0;zero=0
    anchor_audit={}
    ratios=[]
    for sp in sorted(z_by_species):
        z=z_by_species[sp][1]
        y=intercept+slope*z
        n,best,second,ratio=nearest_count(y,total)
        ratios.append(ratio)
        if ratio>max_ratio:
            unresolved.append(sp)
            status="lattice_ambiguous"
        else:
            s=absent[sp]+n
            if s==total and n>=1:
                status="exact_source_identity";exact+=1
            elif s<total:
                status="incomplete_archive_absence_set";incomplete+=1
            elif s>total:
                status="impossible_absent_plus_source_gt_471";impossible.append(sp)
            else:
                status="exact_zero_historical_sources";zero+=1
        results.append({
          "species":sp,
          "Potential_islands":total-n,
          "historical_source_count":n,
          "archive_absent_count":absent[sp],
          "status":status,
          "Historical_total_log_hex":float(z).hex(),
          "backtransformed_log10_hex":float(y).hex(),
          "best_lattice_distance_hex":float(best).hex(),
          "second_lattice_distance_hex":float(second).hex(),
          "ambiguity_ratio_hex":float(ratio).hex(),
        })
        if sp in anchor_expected:
            anchor_audit[sp]={
              "expected_source_count":anchor_expected[sp],
              "recovered_source_count":n,
              "ambiguity_ratio_hex":float(ratio).hex(),
            }

    if unresolved:raise Stop(f"{len(unresolved)} species fail frozen lattice-separation gate")
    if impossible:raise Stop(f"{len(impossible)} species have absent+source > 471")
    for sp,expected in anchor_expected.items():
        if anchor_audit[sp]["recovered_source_count"]!=expected:
            raise Stop(f"anchor count not recovered: {sp}")
    if exact<int(contract["exact_source_gate"]["minimum_exact_species"]):
        raise Stop(f"only {exact} exact-source species")

    receipt={
      "schema":"structural.sw_finland_anchor_source_count_inversion_result.v1_170_2",
      "status":contract["success_ceiling"]["status"],
      "candidate_id":contract["candidate_id"],
      "archive_rows":rows,
      "archive_species":len(z_by_species),
      "calibration_intercept_hex":float(intercept).hex(),
      "calibration_slope_hex":float(slope).hex(),
      "anchor_count":len(anchor_expected),
      "anchor_audit":anchor_audit,
      "maximum_ambiguity_ratio_observed_hex":float(max(ratios)).hex(),
      "frozen_maximum_ambiguity_ratio_hex":float(max_ratio).hex(),
      "exact_source_species":exact,
      "incomplete_species":incomplete,
      "zero_source_species":zero,
      "impossible_species":0,
      "ambiguous_species":0,
      "protected_outcome_values_decoded":0,
      "future_outcome_values_opened":0,
      "published_future_summary_values_used":0,
      "pilot_future_outcome_authorized":False,
      "confirmatory_future_outcome_authorized":False,
      "counts_as_empirical_evidence":False
    }
    return results,receipt

def main():
    p=argparse.ArgumentParser()
    p.add_argument("safe_csv",type=Path)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--anchor-contract",type=Path,default=DEFAULT_ANCHOR_CONTRACT)
    p.add_argument("--lookup-output",type=Path,required=True)
    p.add_argument("--audit-output",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        rows,r=calibrate(a.safe_csv,load_json(a.contract),load_json(a.anchor_contract))
        a.lookup_output.parent.mkdir(parents=True,exist_ok=True)
        with a.lookup_output.open("w",encoding="utf-8",newline="") as f:
            w=csv.writer(f,lineterminator="\n")
            w.writerow(["species","Potential_islands","historical_source_count"])
            for row in rows:w.writerow([row["species"],row["Potential_islands"],row["historical_source_count"]])
        with a.audit_output.open("w",encoding="utf-8",newline="") as f:
            fields=list(rows[0].keys());w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
        validation={
          "schema":"structural.sw_finland_potential_islands_lookup_result.v1_168",
          "status":"T0_SOURCE_COUNT_LOOKUP_VALIDATED_NO_FUTURE_SUMMARIES_PERSISTED",
          "candidate_id":r["candidate_id"],
          "species_count":len(rows),
          "source_method":"six-anchor affine inversion of documented standardized log10(historical_source_count+1)",
          "future_summary_columns_present_in_input":False,
          "future_summary_values_persisted":0,
          "row_level_recent_outcome_opened":False,
          "counts_as_empirical_evidence":False
        }
        r["canonical_validation"]=validation
        code=0
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={
          "schema":"structural.sw_finland_anchor_source_count_inversion_result.v1_170_2",
          "status":"STOP_T0_ANCHOR_SOURCE_COUNT_INVERSION",
          "reason":str(exc),
          "protected_outcome_values_decoded":0,
          "future_outcome_values_opened":0,
          "published_future_summary_values_used":0,
          "counts_as_empirical_evidence":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    if code==0:
        Path(str(a.receipt)+".validation.json").write_text(json.dumps(r["canonical_validation"],indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
