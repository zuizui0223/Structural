#!/usr/bin/env python3
"""Promote v1.173.4 exact numeric source counts to exact source identities."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,re,unicodedata
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_numeric_count_to_sources_contract_v1_174_2.json"

class Stop(RuntimeError): pass

def norm(x:str)->str:
    return re.sub(r"\s+"," ",unicodedata.normalize("NFC",str(x)).strip())

def parse_float(x:str,label:str)->float:
    try:v=float(str(x).strip())
    except ValueError as exc:raise Stop(f"invalid {label}") from exc
    if not math.isfinite(v):raise Stop(f"nonfinite {label}")
    return v

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def load_authority(species_path:Path,excluded_path:Path,receipt:dict,contract:dict):
    r=contract["required_v1_173_4"]
    for key,expected in {
      "status":r["required_status"],
      "calibration_transform":r["calibration_transform"],
      "numeric_species":r["numeric_species"],
      "excluded_nonnumeric_species":r["excluded_nonnumeric_species"],
      "anchors_matched_numeric":r["anchors_matched_numeric"],
      "impossible_species":r["impossible_species"],
      "future_outcome_values_opened":r["future_outcome_values_opened"]
    }.items():
        if receipt.get(key)!=expected:raise Stop(f"v1.173.4 receipt drift: {key}")
    if int(receipt.get("exact_source_species",-1))<int(r["minimum_exact_source_species"]):
        raise Stop("too few exact source species in v1.173.4")

    rows=list(csv.DictReader(species_path.open("r",encoding="utf-8-sig",newline="")))
    expected=("species","Historical_total_log","recovered_historical_source_count","recovered_Potential_islands","archived_absent_count","absence_plus_source_count","count_rounding_error","support_status")
    if not rows or tuple(rows[0].keys())!=expected:raise Stop("v1.173.4 species schema drift")
    if len(rows)!=int(r["numeric_species"]):raise Stop("numeric authority row count drift")
    authority={}
    for row in rows:
        sp=norm(row["species"])
        if not sp or sp in authority:raise Stop("blank/duplicate numeric authority species")
        n=int(row["recovered_historical_source_count"]);p=int(row["recovered_Potential_islands"])
        nabs=int(row["archived_absent_count"]);total=int(row["absence_plus_source_count"])
        if not 1<=n<=471 or p!=471-n or total!=nabs+n:raise Stop(f"numeric authority identity drift: {sp}")
        authority[sp]=(n,p,nabs,row["support_status"])

    ex=list(csv.DictReader(excluded_path.open("r",encoding="utf-8-sig",newline="")))
    if len(ex)!=int(r["excluded_nonnumeric_species"]):raise Stop("excluded species row count drift")
    excluded={norm(row["species"]) for row in ex}
    if len(excluded)!=len(ex) or authority.keys() & excluded:raise Stop("authority/excluded overlap")
    return authority,excluded

def reconstruct(safe_path:Path,router:dict,species_path:Path,excluded_path:Path,receipt:dict,contract:dict):
    if contract.get("schema")!="structural.sw_finland_numeric_count_to_sources_contract.v1_174_2":raise Stop("contract schema drift")
    if router.get("status")!="T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE":raise Stop("router not qualified")
    if router.get("protected_field_values_decoded")!=0 or router.get("outcome_values_read")!=0:raise Stop("future outcome boundary violated")
    authority,excluded=load_authority(species_path,excluded_path,receipt,contract)

    absent=defaultdict(set);geometry={};pairs=set();archive_species=set();rows=0
    with safe_path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f)
        if rd.fieldnames is None or "outcome" in rd.fieldnames:raise Stop("unsafe t0 projection")
        for key in ("spp.name","holmkod","Euref_X_original","Euref_Y_original"):
            if key not in rd.fieldnames:raise Stop(f"missing safe field {key}")
        for row in rd:
            rows+=1
            sp=norm(row["spp.name"]);isl=str(row["holmkod"]).strip()
            archive_species.add(sp)
            pair=(sp,isl)
            if pair in pairs:raise Stop(f"duplicate species-island pair: {sp}|{isl}")
            pairs.add(pair)
            if sp in authority:absent[sp].add(isl)
            xy=(parse_float(row["Euref_X_original"],"Euref_X_original"),parse_float(row["Euref_Y_original"],"Euref_Y_original"))
            if isl in geometry and geometry[isl]!=xy:raise Stop(f"geometry drift: {isl}")
            geometry[isl]=xy

    if len(archive_species)!=587:raise Stop("archive species universe drift")
    if archive_species != set(authority)|excluded:raise Stop("archive species != numeric authority plus frozen exclusions")
    u=set(geometry)
    if len(u)!=int(contract["exact_source_rule"]["island_universe"]):raise Stop("island universe drift")
    if set(absent)!=set(authority):raise Stop("numeric authority species missing archive rows")

    statuses=[];members=[];exact=incomplete=0
    for sp in sorted(authority):
        n,p,nabs_frozen,status_frozen=authority[sp]
        nabs=len(absent[sp])
        if nabs!=nabs_frozen:raise Stop(f"archived absent count replay drift: {sp}")
        if status_frozen=="exact_source_identity_count_supported":
            if nabs+n!=471:raise Stop(f"exact count identity failed: {sp}")
            sources=sorted(u-absent[sp])
            if len(sources)!=n:raise Stop(f"source complement mismatch: {sp}")
            exact+=1;statuses.append((sp,"exact_source_identity",nabs,p,n));members.extend((sp,i) for i in sources)
        elif status_frozen=="incomplete_archive_absence_set":
            incomplete+=1;statuses.append((sp,"incomplete_archive_absence_set",nabs,p,n))
        else:
            raise Stop(f"unexpected authority support status: {sp}: {status_frozen}")

    if contract["exact_source_rule"]["exact_species_count_must_equal_v1_173_4_receipt"]:
        if exact!=int(receipt["exact_source_species"]):raise Stop("exact-source species count drift vs v1.173.4")
    if exact<int(contract["exact_source_rule"]["minimum_exact_species"]):raise Stop("too few exact-source species")

    out={
      "schema":"structural.sw_finland_exact_source_reconstruction_result.v1_174_2",
      "status":contract["success_ceiling"]["status"],
      "candidate_id":contract["candidate_id"],
      "count_authority":"v1.173.4 numeric log10(n) pool",
      "archive_rows":rows,"archive_species":len(archive_species),"unique_islands":len(u),
      "numeric_authority_species":len(authority),"excluded_nonnumeric_species":len(excluded),
      "exact_source_species":exact,"incomplete_species":incomplete,"impossible_species":0,
      "source_membership_rows":len(members),
      "future_outcome_values_opened":0,"protected_outcome_values_decoded":0,
      "pilot_future_outcome_authorized":False,"confirmatory_future_outcome_authorized":False,
      "counts_as_empirical_evidence":False
    }
    return statuses,members,[(i,*geometry[i]) for i in sorted(geometry)],out

def write(path,header,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,lineterminator="\n");w.writerow(header);w.writerows(rows)

def main()->int:
    p=argparse.ArgumentParser()
    p.add_argument("safe_csv",type=Path);p.add_argument("species_table",type=Path);p.add_argument("excluded_table",type=Path)
    p.add_argument("--router-receipt",type=Path,required=True);p.add_argument("--count-receipt",type=Path,required=True)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--species-output",type=Path,required=True);p.add_argument("--membership-output",type=Path,required=True)
    p.add_argument("--geometry-output",type=Path,required=True);p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        c=json.loads(a.contract.read_text());rr=json.loads(a.router_receipt.read_text());cr=json.loads(a.count_receipt.read_text())
        statuses,members,geometry,r=reconstruct(a.safe_csv,rr,a.species_table,a.excluded_table,cr,c)
        write(a.species_output,["species","status","archived_absent_count","Potential_islands","historical_source_count"],statuses)
        write(a.membership_output,["species","source_holmkod"],members)
        write(a.geometry_output,["holmkod","Euref_X_original","Euref_Y_original"],geometry)
        r["species_output_sha256"]=sha(a.species_output);r["membership_output_sha256"]=sha(a.membership_output);r["geometry_output_sha256"]=sha(a.geometry_output)
        r["count_receipt_sha256"]=sha(a.count_receipt);r["count_table_sha256"]=sha(a.species_table);r["excluded_table_sha256"]=sha(a.excluded_table)
        code=0
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={"schema":"structural.sw_finland_exact_source_reconstruction_result.v1_174_2","status":"STOP_T0_LOGX_COUNTS_TO_EXACT_SOURCES","reason":str(exc),
           "future_outcome_values_opened":0,"protected_outcome_values_decoded":0,"counts_as_empirical_evidence":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
