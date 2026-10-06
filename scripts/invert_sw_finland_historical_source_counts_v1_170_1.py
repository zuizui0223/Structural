#!/usr/bin/env python3
"""Recover SW Finland historical source counts from standardized t0 breadth.

Only t0-safe routed fields are read. Future colonization outcome bytes remain
opaque upstream. Two frozen public Potential_islands anchors calibrate the
affine z-standardization; four disjoint anchors validate the inversion.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,unicodedata
from collections import defaultdict
from pathlib import Path
from typing import Mapping

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_anchor_inversion_contract_v1_170_1.json"

class Stop(RuntimeError):pass

def norm(x:str)->str:
    return unicodedata.normalize("NFC",str(x)).strip()

def loadj(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict):raise Stop(f"{path.name} must contain object")
    return x

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def parse_float(x,label):
    try:v=float(str(x).strip())
    except ValueError as exc:raise Stop(f"invalid {label}") from exc
    if not math.isfinite(v):raise Stop(f"nonfinite {label}")
    return v

def collect(safe_csv:Path,router:Mapping,contract:Mapping):
    if router.get("status")!="T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE":
        raise Stop("t0 router did not qualify")
    if router.get("protected_field_values_decoded")!=0 or router.get("outcome_values_read")!=0:
        raise Stop("future outcome boundary violated")
    required=("spp.name","holmkod","Euref_X_original","Euref_Y_original","Historical_total_log")
    absent=defaultdict(set); z_by_species={}; geometry={};pairs=set();rows=0
    with safe_csv.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None or "outcome" in rd.fieldnames:
            raise Stop("unsafe t0 projection schema")
        for key in required:
            if key not in rd.fieldnames:raise Stop(f"missing safe field: {key}")
        for r in rd:
            rows+=1
            sp=norm(r["spp.name"]);isl=norm(r["holmkod"])
            if not sp or not isl:raise Stop("blank species/island routing")
            key=(sp,isl)
            if key in pairs:raise Stop(f"duplicate species-island pair: {sp}|{isl}")
            pairs.add(key);absent[sp].add(isl)
            z=parse_float(r["Historical_total_log"],"Historical_total_log")
            if sp in z_by_species and abs(z-z_by_species[sp])>1e-12:
                raise Stop(f"Historical_total_log varies within species: {sp}")
            z_by_species[sp]=z
            xy=(parse_float(r["Euref_X_original"],"Euref_X_original"),parse_float(r["Euref_Y_original"],"Euref_Y_original"))
            if isl in geometry and (abs(xy[0]-geometry[isl][0])>1e-9 or abs(xy[1]-geometry[isl][1])>1e-9):
                raise Stop(f"geometry varies within island: {isl}")
            geometry[isl]=xy
    gate=contract["inversion_gate"]
    if len(z_by_species)!=int(gate["expected_species"]):
        raise Stop(f"expected {gate['expected_species']} species, found {len(z_by_species)}")
    if len(geometry)!=int(gate["expected_islands"]):
        raise Stop(f"expected {gate['expected_islands']} islands, found {len(geometry)}")
    return absent,z_by_species,geometry,rows

def calibrate(z_by_species:Mapping[str,float],contract:Mapping):
    cal=contract["calibration_anchors"]
    if len(cal)!=2:raise Stop("calibration requires exactly two frozen anchors")
    items=[]
    for sp,spec in cal.items():
        if sp not in z_by_species:raise Stop(f"calibration anchor absent: {sp}")
        n=int(spec["historical_source_count"])
        if int(spec["Potential_islands"])!=471-n:raise Stop("calibration anchor identity drift")
        L=math.log10(n+1.0);items.append((sp,z_by_species[sp],n,L))
    (_,z0,_,L0),(_,z1,_,L1)=items
    if abs(z1-z0)<1e-12:raise Stop("calibration anchors have identical z")
    sd=(L1-L0)/(z1-z0);mean=L0-sd*z0
    if not math.isfinite(mean) or not math.isfinite(sd) or sd<=0:
        raise Stop("invalid recovered standardization constants")
    return mean,sd,items

def invert(z:float,mean:float,sd:float):
    L=mean+sd*z
    raw=10.0**L-1.0
    if not math.isfinite(raw):raise Stop("nonfinite inverse count")
    n=int(round(raw));res=abs(raw-n)
    return raw,n,res

def run(safe_csv:Path,router:Mapping,contract:Mapping):
    if contract.get("schema")!="structural.sw_finland_anchor_inversion_contract.v1_170_1":
        raise Stop("anchor inversion contract drift")
    absent,zs,geometry,row_count=collect(safe_csv,router,contract)
    mean,sd,cal_items=calibrate(zs,contract)
    tol=float(contract["inversion_gate"]["maximum_absolute_raw_count_residual"])

    anchor_validation=[]
    for sp,spec in contract["validation_anchors"].items():
        if sp not in zs:raise Stop(f"validation anchor absent: {sp}")
        expected=int(spec["historical_source_count"])
        if int(spec["Potential_islands"])!=471-expected:raise Stop("validation anchor identity drift")
        raw,n,res=invert(zs[sp],mean,sd)
        anchor_validation.append((sp,expected,n,res))
        if n!=expected or res>tol:
            raise Stop(f"validation anchor failed: {sp}, expected={expected}, got={n}, residual={res}")

    recovered={}; residuals=[];unresolved=[]
    lo,hi=map(int,contract["inversion_gate"]["integer_domain"])
    for sp in sorted(zs):
        raw,n,res=invert(zs[sp],mean,sd)
        residuals.append(res)
        if not lo<=n<=hi or res>tol:
            unresolved.append((sp,zs[sp],raw,n,res))
        else:
            recovered[sp]=n
    if unresolved:
        worst=max(x[4] for x in unresolved)
        raise Stop(f"{len(unresolved)} species fail integer inversion; max unresolved residual={worst}")

    universe=set(geometry)
    statuses=[];members=[];exact_positive=0;exact_zero=0;incomplete=0;impossible=0
    for sp in sorted(recovered):
        n=recovered[sp];n_abs=len(absent[sp]);total=n+n_abs
        if total>471:
            impossible+=1;statuses.append((sp,zs[sp].hex(),n,n_abs,total,"impossible_absent_plus_source_gt_471"))
            continue
        if total<471:
            incomplete+=1;statuses.append((sp,zs[sp].hex(),n,n_abs,total,"incomplete_archive_absence_set"))
            continue
        if n==0:
            exact_zero+=1;statuses.append((sp,zs[sp].hex(),n,n_abs,total,"exact_zero_historical_sources"))
            continue
        sources=sorted(universe-absent[sp])
        if len(sources)!=n:raise Stop(f"source complement count mismatch: {sp}")
        exact_positive+=1;statuses.append((sp,zs[sp].hex(),n,n_abs,total,"exact_source_identity"))
        members.extend((sp,isl) for isl in sources)
    if impossible:
        raise Stop(f"{impossible} species have archived_absent_count + recovered_source_count > 471")
    minimum=int(contract["source_identity_gate"]["minimum_positive_source_exact_species"])
    if exact_positive<minimum:
        status="STOP_INSUFFICIENT_EXACT_SOURCE_SPECIES"
    else:
        status=contract["success_ceiling"]["status"]
    receipt={
      "schema":"structural.sw_finland_anchor_inversion_result.v1_170_1",
      "status":status,
      "candidate_id":contract["candidate_id"],
      "archive_rows":row_count,
      "species_count":len(recovered),
      "island_count":len(universe),
      "recovered_standardization_mean_hex":float(mean).hex(),
      "recovered_standardization_sd_hex":float(sd).hex(),
      "calibration_anchors":[
        {"species":sp,"z_hex":float(z).hex(),"source_count":n,"prestandard_log10_hex":float(L).hex()}
        for sp,z,n,L in cal_items
      ],
      "validation_anchors":[
        {"species":sp,"expected_source_count":exp,"recovered_source_count":got,"raw_count_abs_residual_hex":float(res).hex()}
        for sp,exp,got,res in anchor_validation
      ],
      "integer_inversion_species":len(recovered),
      "integer_inversion_unresolved_species":0,
      "maximum_absolute_raw_count_residual_hex":float(max(residuals)).hex(),
      "exact_positive_source_species":exact_positive,
      "exact_zero_source_species":exact_zero,
      "incomplete_species":incomplete,
      "impossible_species":impossible,
      "minimum_exact_positive_species_required":minimum,
      "source_membership_rows":len(members),
      "future_outcome_values_opened":0,
      "protected_outcome_values_decoded":0,
      "future_summary_values_used":0,
      "pilot_future_outcome_authorized":False,
      "confirmatory_future_outcome_authorized":False,
      "counts_as_empirical_evidence":False
    }
    geometry_rows=[(isl,geometry[isl][0],geometry[isl][1]) for isl in sorted(geometry)]
    return statuses,members,geometry_rows,receipt

def write_csv(path:Path,header,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(header);w.writerows(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("safe_csv",type=Path)
    p.add_argument("--router-receipt",type=Path,required=True)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--species-output",type=Path,required=True)
    p.add_argument("--membership-output",type=Path,required=True)
    p.add_argument("--geometry-output",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        c=loadj(a.contract);router=loadj(a.router_receipt)
        species,members,geometry,r=run(a.safe_csv,router,c)
        if r["status"]==c["success_ceiling"]["status"]:
            write_csv(a.species_output,["species","Historical_total_log_hex","historical_source_count","archived_absent_count","accounted_islands","status"],species)
            write_csv(a.membership_output,["species","source_holmkod"],members)
            write_csv(a.geometry_output,["holmkod","Euref_X_original","Euref_Y_original"],geometry)
            r["species_output_sha256"]=sha256_file(a.species_output)
            r["membership_output_sha256"]=sha256_file(a.membership_output)
            r["geometry_output_sha256"]=sha256_file(a.geometry_output)
            code=0
        else:
            code=2
    except (OSError,ValueError,KeyError,json.JSONDecodeError,OverflowError,Stop) as exc:
        r={
          "schema":"structural.sw_finland_anchor_inversion_result.v1_170_1",
          "status":"STOP_T0_ANCHOR_INVERSION",
          "reason":str(exc),
          "future_outcome_values_opened":0,
          "protected_outcome_values_decoded":0,
          "future_summary_values_used":0,
          "counts_as_empirical_evidence":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(r,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
