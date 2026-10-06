#!/usr/bin/env python3
"""Reconstruct exact SW Finland historical source identities from t0 only."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,unicodedata
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_exact_source_reconstruction_contract_v1_171.json"

class Stop(RuntimeError): pass

def norm(x:str)->str:
    return unicodedata.normalize("NFC",str(x)).strip()

def parse_float(x:str,label:str)->float:
    try:v=float(str(x).strip())
    except ValueError as exc:raise Stop(f"invalid {label}") from exc
    if not math.isfinite(v):raise Stop(f"nonfinite {label}")
    return v

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def load_lookup(path:Path,total_islands:int=471)->dict[str,tuple[int,int]]:
    rows=list(csv.DictReader(path.open("r",encoding="utf-8-sig",newline="")))
    if not rows or tuple(rows[0].keys())!=("species","Potential_islands","historical_source_count"):
        raise Stop("lookup schema drift")
    out={}
    for r in rows:
        sp=norm(r["species"])
        if not sp or sp in out:raise Stop("blank/duplicate lookup species")
        try:p=int(r["Potential_islands"]);n=int(r["historical_source_count"])
        except ValueError as exc:raise Stop("invalid lookup integer") from exc
        if not 0<=p<=total_islands or n!=total_islands-p:raise Stop("lookup source-count identity drift")
        out[sp]=(p,n)
    return out

def reconstruct(safe_path:Path,lookup_path:Path,router:dict,validation:dict,contract:dict):
    if contract.get("schema")!="structural.sw_finland_exact_source_reconstruction_contract.v1_171":
        raise Stop("contract schema drift")
    if router.get("status")!="T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE":
        raise Stop("router not qualified")
    if router.get("protected_field_values_decoded")!=0 or router.get("outcome_values_read")!=0:
        raise Stop("future outcome boundary violated")
    if validation.get("status")!="T0_SOURCE_COUNT_LOOKUP_VALIDATED_NO_FUTURE_SUMMARIES_PERSISTED":
        raise Stop("lookup validation not qualified")
    if validation.get("future_summary_values_persisted")!=0:
        raise Stop("supplement future summaries persisted")

    expected_islands=int(contract["island_universe"]["expected_unique_islands"])
    lookup=load_lookup(lookup_path,total_islands=expected_islands)
    absent=defaultdict(set)
    pairs=set()
    geometry={}
    rows=0
    with safe_path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None or "outcome" in rd.fieldnames:raise Stop("unsafe routed schema")
        for key in ("spp.name","holmkod","Euref_X_original","Euref_Y_original"):
            if key not in rd.fieldnames:raise Stop(f"missing safe field {key}")
        for r in rd:
            rows+=1
            sp=norm(r["spp.name"]);isl=norm(r["holmkod"])
            if not sp or not isl:raise Stop("blank species/island key")
            pair=(sp,isl)
            if pair in pairs:raise Stop(f"duplicate species-island pair: {sp}|{isl}")
            pairs.add(pair);absent[sp].add(isl)
            xy=(parse_float(r["Euref_X_original"],"Euref_X_original"),parse_float(r["Euref_Y_original"],"Euref_Y_original"))
            if isl in geometry and geometry[isl]!=xy:raise Stop(f"geometry drift within island {isl}")
            geometry[isl]=xy

    universe=tuple(sorted(geometry))
    if len(universe)!=expected_islands:
        raise Stop(f"expected {expected_islands} islands, found {len(universe)}")
    u=set(universe)
    statuses=[];members=[]
    exact=0;incomplete=0;impossible=0;zero=0;missing=0
    sum_abs=0;sum_potential_joined=0
    for sp in sorted(absent):
        n_abs=len(absent[sp]);sum_abs+=n_abs
        if not absent[sp] <= u:raise Stop("absence set outside island universe")
        if sp not in lookup:
            missing+=1
            statuses.append((sp,"lookup_missing",n_abs,"",""))
            continue
        p,n_source=lookup[sp];sum_potential_joined+=p
        if n_abs>p:
            impossible+=1
            statuses.append((sp,"impossible_absent_gt_potential",n_abs,p,n_source))
            continue
        if n_abs<p:
            incomplete+=1
            statuses.append((sp,"incomplete_archive_absence_set",n_abs,p,n_source))
            continue
        if n_source==0:
            zero+=1
            statuses.append((sp,"exact_zero_historical_sources",n_abs,p,n_source))
            continue
        sources=sorted(u-absent[sp])
        if len(sources)!=n_source:raise Stop(f"source complement count mismatch: {sp}")
        exact+=1
        statuses.append((sp,"exact_source_identity",n_abs,p,n_source))
        members.extend((sp,isl) for isl in sources)

    if impossible>0:raise Stop(f"{impossible} species have archived_absent_count > Potential_islands")
    minimum=int(contract["exact_identity_rule"]["minimum_exact_species"])
    status=(
      contract["success_ceiling"]["status"]
      if exact>=minimum else "STOP_INSUFFICIENT_EXACT_SOURCE_SPECIES"
    )
    receipt={
      "schema":"structural.sw_finland_exact_source_reconstruction_result.v1_171",
      "status":status,
      "candidate_id":contract["candidate_id"],
      "archive_rows":rows,
      "archive_species":len(absent),
      "lookup_species":len(lookup),
      "unique_islands":len(universe),
      "exact_source_species":exact,
      "incomplete_species":incomplete,
      "impossible_species":impossible,
      "zero_source_species":zero,
      "lookup_missing_species":missing,
      "minimum_exact_species_required":minimum,
      "sum_archived_absent_rows":sum_abs,
      "sum_potential_islands_for_joined_archive_species":sum_potential_joined,
      "source_membership_rows":len(members),
      "future_outcome_values_opened":0,
      "protected_outcome_values_decoded":0,
      "pilot_future_outcome_authorized":False,
      "confirmatory_future_outcome_authorized":False,
      "counts_as_empirical_evidence":False
    }
    return statuses,members,[(i,*geometry[i]) for i in universe],receipt

def write_csv(path:Path,header,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(header);w.writerows(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("safe_csv",type=Path);p.add_argument("lookup_csv",type=Path)
    p.add_argument("--router-receipt",type=Path,required=True)
    p.add_argument("--lookup-validation",type=Path,required=True)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--species-output",type=Path,required=True)
    p.add_argument("--membership-output",type=Path,required=True)
    p.add_argument("--geometry-output",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        c=json.loads(a.contract.read_text());router=json.loads(a.router_receipt.read_text());validation=json.loads(a.lookup_validation.read_text())
        species,members,geometry,r=reconstruct(a.safe_csv,a.lookup_csv,router,validation,c)
        if r["status"]==c["success_ceiling"]["status"]:
            write_csv(a.species_output,["species","status","archived_absent_count","Potential_islands","historical_source_count"],species)
            write_csv(a.membership_output,["species","source_holmkod"],members)
            write_csv(a.geometry_output,["holmkod","Euref_X_original","Euref_Y_original"],geometry)
            r["species_output_sha256"]=sha256_file(a.species_output)
            r["membership_output_sha256"]=sha256_file(a.membership_output)
            r["geometry_output_sha256"]=sha256_file(a.geometry_output)
            code=0
        else:code=2
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={
          "schema":"structural.sw_finland_exact_source_reconstruction_result.v1_171",
          "status":"STOP_T0_SOURCE_RECONSTRUCTION",
          "reason":str(exc),
          "future_outcome_values_opened":0,
          "protected_outcome_values_decoded":0,
          "counts_as_empirical_evidence":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
