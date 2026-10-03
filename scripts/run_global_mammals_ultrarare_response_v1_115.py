#!/usr/bin/env python3
"""Consume exactly the 529 preregistered ultrarare species on held-out islands."""
from __future__ import annotations
import argparse,csv,hashlib,json,os,tempfile
from pathlib import Path

from scripts.fetch_global_mammal_response_opaque_v1_17 import (
    GlobalMammalTransportError, transport as transport_v117,
)
from scripts.run_global_mammals_macro_pilot_response_v1_65 import (
    iter_records, first_field_bytes, canon_id_bytes, parse_full_record,
)
from scripts.run_global_mammals_exploratory_confirmatory_v1_74 import iter_field_bytes

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_ultrarare_scoring_contract_v1_115.json"
class Stop(RuntimeError): pass

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def load_csv(p:Path):
    with p.open("r",encoding="utf-8",newline="") as h:return list(csv.DictReader(h))

def load_manifest(p:Path,expected_sha:str):
    if sha(p)!=expected_sha:raise Stop("corrected manifest SHA drift")
    rows=load_csv(p)
    if len(rows)!=5394:raise Stop("manifest count drift")
    names=[]
    for j,r in enumerate(rows):
        if int(r["species_index"])!=j or int(r["data_column_index"])!=j+2:raise Stop("manifest index drift")
        names.append(str(r["species_name"]))
    return names

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--corrected-manifest",type=Path,required=True)
    ap.add_argument("--universe",type=Path,required=True)
    ap.add_argument("--pilot-routing",type=Path,required=True)
    ap.add_argument("--heldout-routing",type=Path,required=True)
    ap.add_argument("--matrix",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args();semantic_started=False
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_ultrarare_scoring_contract.v1_115":raise Stop("contract schema drift")
        full=load_manifest(a.corrected_manifest,c["physical_schema"]["corrected_manifest_sha256"])
        if sha(a.universe)!=c["species_layer"]["species_universe_sha256"]:raise Stop("universe SHA drift")
        universe=load_csv(a.universe)
        if len(universe)!=529:raise Stop("species count drift")
        cols=[];names=[]
        for j,r in enumerate(universe):
            if int(r["species_index"])!=j:raise Stop("species index drift")
            col=int(r["source_data_column_index"]);name=str(r["species_name"])
            if full[col-2]!=name:raise Stop("species column/name drift")
            if not 1<=int(r["pilot_presence"])<=4:raise Stop("pilot presence rule drift")
            cols.append(col);names.append(name)
        if len(set(cols))!=529 or len(set(names))!=529:raise Stop("duplicate ultrarare species")

        if sha(a.pilot_routing)!=c["routing"]["pilot_ids_sha256"]:raise Stop("pilot routing SHA drift")
        if sha(a.heldout_routing)!=c["routing"]["heldout_ids_sha256"]:raise Stop("heldout routing SHA drift")
        pilot=load_csv(a.pilot_routing);held=load_csv(a.heldout_routing)
        pilot_set={r["ID"] for r in pilot};held_order=[r["ID"] for r in held];held_set=set(held_order)
        held_meta={r["ID"]:r for r in held}
        if len(pilot_set)!=1275 or len(held_set)!=4126 or pilot_set&held_set:raise Stop("routing drift")

        target=c["response_identity"]
        tc={"candidate_id":c["candidate_id"],"target":{
          "name":target["name"],"dryad_file_id":target["dryad_file_id"],"download_url":target["download_url"],
          "expected_size_bytes":target["expected_size_bytes"],"expected_sha256":target["expected_sha256"]},
          "attempt_policy":{"credentialed_attempt_limit":1,"blind_endpoint_retry_authorized":False,"alternate_file_id_retry_authorized":False}}

        values={};data_rows=pilot_seen=held_seen=excluded_seen=0;decoded=0
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/target["name"]
            tr=transport_v117(p,contract=tc,token=os.environ.get("DRYAD_TOKEN",""))
            if tr.get("status")!="EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED":raise Stop("transport did not qualify")
            raw=p.read_bytes();recs=iter(iter_records(raw))
            header=parse_full_record(next(recs))
            if header!=full:raise Stop("header/manifest drift")
            wanted=set(cols)
            for rec in recs:
                if not rec:continue
                data_rows+=1;iid=canon_id_bytes(first_field_bytes(rec,59))
                if iid in held_set:
                    picked={};field_count=0
                    for idx,field in enumerate(iter_field_bytes(rec,59),start=1):
                        field_count=idx
                        if idx in wanted:picked[idx]=field
                    if field_count!=5395 or len(picked)!=529:raise Stop("heldout field routing drift")
                    row=[]
                    for col in cols:
                        v=picked[col].strip();semantic_started=True
                        if v not in (b"0",b"1"):raise Stop("heldout ultrarare target outside 0/1")
                        row.append(1 if v==b"1" else 0);decoded+=1
                    if iid in values:raise Stop("duplicate heldout row")
                    values[iid]=row;held_seen+=1
                elif iid in pilot_set:
                    pilot_seen+=1
                else:
                    excluded_seen+=1

        if data_rows!=5592:raise Stop("row count drift")
        if pilot_seen!=1275 or held_seen!=4126 or excluded_seen!=191:raise Stop("routing support drift")
        if decoded!=2182654:raise Stop("decoded target-cell count drift")

        labels=[f"S{j:05d}" for j in range(529)]
        a.matrix.parent.mkdir(parents=True,exist_ok=True)
        with a.matrix.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n");w.writerow(["ID","block_id","bioregion"]+labels)
            for iid in held_order:
                m=held_meta[iid];w.writerow([iid,m["block_id"],m["bioregion"]]+values[iid])

        out={
          "schema":"structural.global_mammals_ultrarare_response_result.v1_115",
          "status":"ULTRARARE_HELDOUT_RESPONSE_CONSUMED_ONCE",
          "candidate_id":c["candidate_id"],
          "heldout_entities_decoded":held_seen,
          "heldout_ultrarare_species":529,
          "heldout_ultrarare_values_decoded":decoded,
          "heldout_non_ultrarare_values_decoded":0,
          "pilot_occurrence_values_decoded_during_run":0,
          "excluded_occurrence_values_decoded":0,
          "matrix_sha256":sha(a.matrix),
          "heldout_ultrarare_response_consumed":True,
          "rerun_authorized":False,
          "raw_response_retained":False
        };code=0
    except (Stop,OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,GlobalMammalTransportError) as e:
        out={
          "schema":"structural.global_mammals_sealed_species_response_result.v1_95",
          "status":"TERMINAL_AFTER_ULTRARARE_HELDOUT_ACCESS" if semantic_started else "HOLD_BEFORE_ULTRARARE_HELDOUT_ACCESS",
          "reason":str(e),
          "heldout_ultrarare_response_consumed":semantic_started,
          "heldout_non_ultrarare_values_decoded":0,
          "pilot_occurrence_values_decoded_during_run":0,
          "excluded_occurrence_values_decoded":0,
          "rerun_authorized":False if semantic_started else None
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
