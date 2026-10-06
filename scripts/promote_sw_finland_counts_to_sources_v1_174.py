#!/usr/bin/env python3
"""Promote v1.173 t0 source counts to exact historical source identities.

This reads the exact SW Finland archive only through the v1.169 outcome-opaque
projection. It never parses the protected future colonization outcome.
"""
from __future__ import annotations

import argparse,csv,hashlib,json,math,unicodedata
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_count_to_sources_contract_v1_174.json"

class Stop(RuntimeError): pass

def norm(x:str)->str:
    return unicodedata.normalize("NFC",str(x)).strip()

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def parse_float(x:str,label:str)->float:
    try:v=float(str(x).strip())
    except ValueError as exc: raise Stop(f"invalid {label}") from exc
    if not math.isfinite(v): raise Stop(f"nonfinite {label}")
    return v

def load_count_authority(table_path:Path,receipt:dict,contract:dict):
    rule=contract["required_v1_173"]
    if receipt.get("schema")!="structural.sw_finland_standardized_historical_count_result.v1_173":
        raise Stop("unexpected v1.173 receipt schema")
    if receipt.get("status")!=rule["required_status"]:
        raise Stop("v1.173 count recovery did not qualify")
    checks={
      "species_count":rule["species_count"],
      "impossible_species":rule["impossible_species_required"],
      "future_outcome_values_opened":rule["future_outcome_values_opened_required"],
      "supplement_future_summary_values_used":rule["supplement_future_summary_values_used_required"]
    }
    for key,expected in checks.items():
        if int(receipt.get(key,-1))!=int(expected): raise Stop(f"v1.173 receipt drift: {key}")
    if int(receipt.get("anchors_matched",-1))<int(rule["minimum_anchor_matches"]):
        raise Stop("too few matched v1.173 anchors")
    if float(receipt.get("anchor_max_count_rounding_error",math.inf))>float(rule["maximum_anchor_count_rounding_error"]):
        raise Stop("v1.173 anchor rounding error exceeds frozen ceiling")
    if float(receipt.get("all_species_max_count_rounding_error",math.inf))>float(rule["maximum_all_species_count_rounding_error"]):
        raise Stop("v1.173 all-species rounding error exceeds frozen ceiling")
    if int(receipt.get("exact_source_species",-1))<int(rule["minimum_exact_source_species"]):
        raise Stop("too few exact-source species in v1.173")

    rows=list(csv.DictReader(table_path.open("r",encoding="utf-8-sig",newline="")))
    expected=(
      "species","Historical_total_log","recovered_historical_source_count",
      "recovered_Potential_islands","archived_absent_count",
      "absence_plus_source_count","count_rounding_error","support_status"
    )
    if not rows or tuple(rows[0].keys())!=expected: raise Stop("v1.173 count-table schema drift")
    if len(rows)!=int(rule["species_count"]): raise Stop("v1.173 count-table row count drift")
    out={}
    maxerr=float(rule["maximum_all_species_count_rounding_error"])
    for row in rows:
        sp=norm(row["species"])
        if not sp or sp in out: raise Stop("blank/duplicate v1.173 species")
        try:
            n=int(row["recovered_historical_source_count"])
            p=int(row["recovered_Potential_islands"])
        except ValueError as exc: raise Stop(f"invalid recovered count for {sp}") from exc
        err=parse_float(row["count_rounding_error"],"count_rounding_error")
        if not 0<=n<=471 or not 0<=p<=471 or n+p!=471:
            raise Stop(f"recovered source/potential identity drift: {sp}")
        if err>maxerr: raise Stop(f"recovered count rounding error drift: {sp}")
        out[sp]=(p,n,err,str(row["support_status"]))
    return out

def reconstruct(safe_path:Path,router:dict,count_table:Path,count_receipt:dict,contract:dict):
    if contract.get("schema")!="structural.sw_finland_count_to_sources_contract.v1_174":
        raise Stop("contract schema drift")
    if router.get("status")!="T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE":
        raise Stop("t0 router not qualified")
    if router.get("protected_field_values_decoded")!=0 or router.get("outcome_values_read")!=0:
        raise Stop("future outcome boundary violated")

    authority=load_count_authority(count_table,count_receipt,contract)
    absent=defaultdict(set);geometry={};pairs=set();rows=0
    with safe_path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None or "outcome" in rd.fieldnames: raise Stop("unsafe t0 projection")
        for key in ("spp.name","holmkod","Euref_X_original","Euref_Y_original"):
            if key not in rd.fieldnames: raise Stop(f"missing safe field {key}")
        for row in rd:
            rows+=1
            sp=norm(row["spp.name"]);isl=norm(row["holmkod"])
            if not sp or not isl: raise Stop("blank species/island key")
            pair=(sp,isl)
            if pair in pairs: raise Stop(f"duplicate species-island pair: {sp}|{isl}")
            pairs.add(pair);absent[sp].add(isl)
            xy=(parse_float(row["Euref_X_original"],"Euref_X_original"),parse_float(row["Euref_Y_original"],"Euref_Y_original"))
            if isl in geometry and geometry[isl]!=xy: raise Stop(f"geometry drift: {isl}")
            geometry[isl]=xy

    expected_islands=int(contract["exact_source_reconstruction"]["island_universe"])
    universe=tuple(sorted(geometry));u=set(universe)
    if len(universe)!=expected_islands: raise Stop(f"expected {expected_islands} islands, found {len(universe)}")
    if len(absent)!=len(authority): raise Stop("archive/count-authority species count mismatch")
    if set(absent)!=set(authority): raise Stop("archive/count-authority species identity mismatch")

    statuses=[];members=[]
    exact=incomplete=impossible=zero=0
    for sp in sorted(absent):
        p,n,err,v173_status=authority[sp]
        n_abs=len(absent[sp])
        if n_abs>p:
            impossible+=1;statuses.append((sp,"impossible_absent_gt_potential",n_abs,p,n,err,v173_status));continue
        if n_abs<p:
            incomplete+=1;statuses.append((sp,"incomplete_archive_absence_set",n_abs,p,n,err,v173_status));continue
        if n==0:
            zero+=1;statuses.append((sp,"exact_zero_historical_sources",n_abs,p,n,err,v173_status));continue
        sources=sorted(u-absent[sp])
        if len(sources)!=n: raise Stop(f"source complement count mismatch: {sp}")
        exact+=1;statuses.append((sp,"exact_source_identity",n_abs,p,n,err,v173_status))
        members.extend((sp,isl) for isl in sources)

    if impossible>0: raise Stop(f"{impossible} impossible species after v1.173 authority")
    if contract["exact_source_reconstruction"]["exact_species_count_must_equal_v1_173"]:
        if exact!=int(count_receipt["exact_source_species"]):
            raise Stop(f"exact-source species count mismatch vs v1.173: {exact} != {count_receipt['exact_source_species']}")
    minimum=int(contract["exact_source_reconstruction"]["minimum_exact_species"])
    if exact<minimum: raise Stop(f"only {exact} exact-source species")

    receipt={
      "schema":contract["receipt_provenance"]["schema"],
      "status":contract["success_ceiling"]["status"],
      "candidate_id":contract["candidate_id"],
      "count_authority":contract["receipt_provenance"]["count_authority"],
      "supplement_file_required":False,
      "archive_rows":rows,
      "archive_species":len(absent),
      "unique_islands":len(universe),
      "exact_source_species":exact,
      "incomplete_species":incomplete,
      "impossible_species":impossible,
      "zero_source_species":zero,
      "source_membership_rows":len(members),
      "v1_173_exact_source_species":int(count_receipt["exact_source_species"]),
      "v1_173_anchor_matches":int(count_receipt["anchors_matched"]),
      "v1_173_anchor_max_rounding_error":float(count_receipt["anchor_max_count_rounding_error"]),
      "v1_173_all_species_max_rounding_error":float(count_receipt["all_species_max_count_rounding_error"]),
      "future_outcome_values_opened":0,
      "protected_outcome_values_decoded":0,
      "supplement_future_summary_values_used":0,
      "pilot_future_outcome_authorized":False,
      "confirmatory_future_outcome_authorized":False,
      "counts_as_empirical_evidence":False
    }
    return statuses,members,[(i,*geometry[i]) for i in universe],receipt

def write(path:Path,header,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(header);w.writerows(rows)

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("safe_csv",type=Path)
    p.add_argument("count_table",type=Path)
    p.add_argument("--router-receipt",type=Path,required=True)
    p.add_argument("--count-receipt",type=Path,required=True)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--species-output",type=Path,required=True)
    p.add_argument("--membership-output",type=Path,required=True)
    p.add_argument("--geometry-output",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        contract=json.loads(a.contract.read_text())
        router=json.loads(a.router_receipt.read_text())
        count_receipt=json.loads(a.count_receipt.read_text())
        species,members,geometry,r=reconstruct(a.safe_csv,router,a.count_table,count_receipt,contract)
        write(a.species_output,["species","status","archived_absent_count","Potential_islands","historical_source_count","count_rounding_error","v1_173_support_status"],species)
        write(a.membership_output,["species","source_holmkod"],members)
        write(a.geometry_output,["holmkod","Euref_X_original","Euref_Y_original"],geometry)
        r["species_output_sha256"]=sha256_file(a.species_output)
        r["membership_output_sha256"]=sha256_file(a.membership_output)
        r["geometry_output_sha256"]=sha256_file(a.geometry_output)
        r["v1_173_count_table_sha256"]=sha256_file(a.count_table)
        r["v1_173_receipt_sha256"]=sha256_file(a.count_receipt)
        code=0
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={
          "schema":"structural.sw_finland_exact_source_reconstruction_result.v1_174",
          "status":"STOP_T0_COUNT_AUTHORITY_TO_EXACT_SOURCES",
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
