#!/usr/bin/env python3
"""Select the preregistered second mammal species layer from already-open pilot rows.

Only pilot occurrence rows are decoded. Held-out rows are routed by their first
field only; every held-out occurrence field remains opaque and undecoded.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,os,tempfile
from pathlib import Path

from scripts.fetch_global_mammal_response_opaque_v1_17 import (
    GlobalMammalTransportError, transport as transport_v117,
)
from scripts.run_global_mammals_macro_pilot_response_v1_65 import (
    iter_records, first_field_bytes, parse_full_record, canon_id_bytes, load_routing,
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_sealed_species_pilot_contract_v1_93.json"
class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def species_fp(names:list[str])->str:
    h=hashlib.sha256()
    for x in names:
        h.update(x.encode("utf-8"));h.update(b"\n")
    return h.hexdigest()

def load_corrected_manifest(path:Path,expected_fp:str)->list[str]:
    with path.open("r",encoding="utf-8",newline="") as h:
        rows=list(csv.DictReader(h))
    if len(rows)!=5394: raise Stop("corrected manifest species-count drift")
    if tuple(rows[0].keys())!=("species_index","data_column_index","species_name"):
        raise Stop("corrected manifest header drift")
    names=[]
    for j,r in enumerate(rows):
        if int(r["species_index"])!=j: raise Stop("species_index drift")
        if int(r["data_column_index"])!=j+2: raise Stop("data_column_index drift")
        name=str(r["species_name"])
        if not name.strip(): raise Stop("blank species identity")
        names.append(name)
    if len(set(names))!=len(names): raise Stop("duplicate species identity")
    if species_fp(names)!=expected_fp: raise Stop("corrected species-order fingerprint drift")
    return names

def consume(raw:bytes,species:list[str],pilot_order:list[str],pilot_meta:dict[str,dict],
            heldout_order:list[str],contract:dict):
    records=iter(iter_records(raw))
    try: header_rec=next(records)
    except StopIteration as e: raise Stop("empty response") from e
    header=parse_full_record(header_rec)
    if header!=species: raise Stop("response header does not equal corrected species manifest")

    pilot_set=set(pilot_order); heldout_set=set(heldout_order)
    if pilot_set & heldout_set: raise Stop("pilot/heldout overlap")
    if len(pilot_set|heldout_set)!=5401: raise Stop("final population routing drift")

    nsp=len(species);counts=[0]*nsp;pilot_values={}
    data_rows=pilot_decoded=heldout_seen=excluded_seen=0
    for rec in records:
        if not rec: continue
        data_rows+=1
        iid=canon_id_bytes(first_field_bytes(rec,59))
        if iid in pilot_set:
            fields=parse_full_record(rec)
            if len(fields)!=nsp+1: raise Stop("pilot field-count drift")
            if canon_id_bytes(fields[0].encode("utf-8"))!=iid:
                raise Stop("pilot routing disagreement")
            vals=fields[1:];row=[]
            for j,v in enumerate(vals):
                if v not in ("0","1"): raise Stop("pilot target outside 0/1")
                y=1 if v=="1" else 0
                row.append(y);counts[j]+=y
            if iid in pilot_values: raise Stop("duplicate pilot row")
            pilot_values[iid]=row;pilot_decoded+=1
        elif iid in heldout_set:
            # Do not decode any occurrence field from this record.
            heldout_seen+=1
        else:
            excluded_seen+=1

    if data_rows!=contract["response_identity"]["expected_data_rows"]: raise Stop("data-row count drift")
    if pilot_decoded!=1275 or set(pilot_values)!=pilot_set: raise Stop("pilot support incomplete")
    if heldout_seen!=4126: raise Stop("heldout routing count drift")
    if excluded_seen!=191: raise Stop("excluded routing count drift")

    rule=contract["second_layer_species_rule"]
    lo=int(rule["pilot_presence_min_inclusive"]);hi=int(rule["pilot_presence_max_inclusive"])
    minabs=int(rule["pilot_absence_min_inclusive"]);n=len(pilot_order)
    selected=[j for j,c in enumerate(counts) if lo<=c<=hi and n-c>=minabs]
    if len(selected)<int(rule["minimum_species_count_gate"]):
        raise Stop("second-layer species count below preregistered minimum")

    universe=[]
    for si,j in enumerate(selected):
        universe.append((si,j+2,species[j],counts[j],n-counts[j]))
    matrix=[]
    for iid in pilot_order:
        meta=pilot_meta[iid];vals=pilot_values[iid]
        matrix.append((iid,meta["block_id"],meta["bioregion"],[vals[j] for j in selected]))

    positives=sum(counts[j] for j in selected)
    receipt={
      "schema":"structural.global_mammals_sealed_species_pilot_result.v1_93",
      "status":"SECOND_SPECIES_LAYER_FROZEN_FROM_PILOT_ONLY",
      "candidate_id":contract["candidate_id"],
      "replication_role":contract["replication_role"],
      "pilot_islands_decoded":pilot_decoded,
      "pilot_occurrence_values_decoded":pilot_decoded*nsp,
      "heldout_islands_seen_routing_only":heldout_seen,
      "heldout_occurrence_values_decoded":0,
      "excluded_occurrence_values_decoded":0,
      "pilot_presence_min_inclusive":lo,
      "pilot_presence_max_inclusive":hi,
      "selected_species":len(selected),
      "selected_pilot_positive_cells":positives,
      "selected_pilot_negative_cells":n*len(selected)-positives,
      "selected_pilot_target_cells":n*len(selected),
      "minimum_selected_pilot_presence":min(counts[j] for j in selected),
      "maximum_selected_pilot_presence":max(counts[j] for j in selected),
      "heldout_second_layer_response_still_sealed":True,
      "heldout_response_authorized":False,
      "raw_response_retained":False,
      "counts_as_current_empirical_result":False
    }
    return universe,matrix,receipt

def write_outputs(universe,matrix,universe_path:Path,matrix_path:Path):
    universe_path.parent.mkdir(parents=True,exist_ok=True)
    with universe_path.open("w",encoding="utf-8",newline="") as h:
        w=csv.writer(h,lineterminator="\n")
        w.writerow(["species_index","source_data_column_index","species_name","pilot_presence","pilot_absence"])
        w.writerows(universe)
    labels=[f"S{int(r[0]):05d}" for r in universe]
    with matrix_path.open("w",encoding="utf-8",newline="") as h:
        w=csv.writer(h,lineterminator="\n")
        w.writerow(["ID","block_id","bioregion"]+labels)
        for iid,block,region,vals in matrix:
            w.writerow([iid,block,region]+vals)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--corrected-manifest",type=Path,required=True)
    ap.add_argument("--pilot-routing",type=Path,required=True)
    ap.add_argument("--heldout-routing",type=Path,required=True)
    ap.add_argument("--species-universe",type=Path,required=True)
    ap.add_argument("--pilot-matrix",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_sealed_species_pilot_contract.v1_93":
            raise Stop("contract schema drift")
        species=load_corrected_manifest(a.corrected_manifest,c["physical_schema"]["species_order_sha256"])
        pilot_order,pilot_meta=load_routing(a.pilot_routing,c["routing"]["pilot_ids_sha256"],1275)
        heldout_order,_=load_routing(a.heldout_routing,c["routing"]["confirmatory_ids_sha256"],4126)
        target=c["response_identity"]
        tc={"candidate_id":c["candidate_id"],"target":{
          "name":target["name"],"dryad_file_id":target["dryad_file_id"],"download_url":target["download_url"],
          "expected_size_bytes":target["expected_size_bytes"],"expected_sha256":target["expected_sha256"]},
          "attempt_policy":{"credentialed_attempt_limit":1,"blind_endpoint_retry_authorized":False,"alternate_file_id_retry_authorized":False}}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/target["name"]
            tr=transport_v117(p,contract=tc,token=os.environ.get("DRYAD_TOKEN",""))
            if tr.get("status")!="EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED":
                raise Stop("exact response transport did not qualify")
            raw=p.read_bytes()
            universe,matrix,result=consume(raw,species,pilot_order,pilot_meta,heldout_order,c)
        write_outputs(universe,matrix,a.species_universe,a.pilot_matrix)
        result["species_universe_sha256"]=sha(a.species_universe)
        result["pilot_matrix_sha256"]=sha(a.pilot_matrix)
        code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,GlobalMammalTransportError,Stop) as e:
        result={
          "schema":"structural.global_mammals_sealed_species_pilot_result.v1_93",
          "status":"STOP",
          "reason":str(e),
          "heldout_occurrence_values_decoded":0,
          "excluded_occurrence_values_decoded":0,
          "heldout_second_layer_response_still_sealed":True,
          "heldout_response_authorized":False,
          "counts_as_current_empirical_result":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__": raise SystemExit(main())
