#!/usr/bin/env python3
"""Consume the frozen mammal pilot rows in a new nonconfirmatory exploratory lineage.

The v1.65 one-shot remains terminal. This parser uses the separately corrected
physical schema: the header has 5,394 species fields and each data row has an
unlabeled source-local ID followed by 5,394 binary occurrence fields.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,os,re,tempfile
from pathlib import Path
from scripts.fetch_global_mammal_response_opaque_v1_17 import (
    GlobalMammalTransportError, transport as transport_v117,
)
from scripts.run_global_mammals_macro_pilot_response_v1_65 import (
    iter_records, first_field_bytes, parse_full_record, canon_id_bytes, load_routing,
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_exploratory_pilot_contract_v1_70.json"
DIGITS=re.compile(r"^[0-9]+$")
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
            confirm_order:list[str],contract:dict):
    records=iter(iter_records(raw))
    try: header_rec=next(records)
    except StopIteration as e: raise Stop("empty response") from e
    header=parse_full_record(header_rec)
    if header!=species: raise Stop("response header does not equal corrected 5394-species manifest")

    pilot_set=set(pilot_order); conf_set=set(confirm_order)
    if pilot_set & conf_set: raise Stop("pilot/confirmatory overlap")
    if len(pilot_set|conf_set)!=contract["routing"]["final_population_islands"]:
        raise Stop("final population routing drift")

    nsp=len(species); counts=[0]*nsp; pilot_values={}
    data_rows=pilot_decoded=conf_seen=excluded_seen=0
    semantic_pilot_started=False
    for rec in records:
        if not rec: continue
        data_rows+=1
        iid=canon_id_bytes(first_field_bytes(rec,59))
        if iid in pilot_set:
            semantic_pilot_started=True
            fields=parse_full_record(rec)
            if len(fields)!=nsp+1: raise Stop("pilot data field-count drift")
            if canon_id_bytes(fields[0].encode("utf-8"))!=iid:
                raise Stop("pilot routing field parse disagreement")
            vals=fields[1:]
            row=[]
            for j,v in enumerate(vals):
                if v not in ("0","1"): raise Stop("pilot target outside 0/1")
                y=int(v);row.append(y);counts[j]+=y
            if iid in pilot_values: raise Stop("duplicate pilot response row")
            pilot_values[iid]=row;pilot_decoded+=1
        elif iid in conf_set:
            conf_seen+=1
        else:
            excluded_seen+=1

    if data_rows!=contract["response_identity"]["expected_data_rows"]: raise Stop("data-row count drift")
    if pilot_decoded!=len(pilot_order) or set(pilot_values)!=pilot_set: raise Stop("pilot support incomplete")
    if conf_seen!=len(confirm_order): raise Stop("confirmatory routing count drift")
    if excluded_seen!=contract["routing"]["excluded_rows"]: raise Stop("excluded routing count drift")

    m=contract["species_universe"]["minimum_presence"];n=len(pilot_order)
    selected=[j for j,c in enumerate(counts) if c>=m and n-c>=m]
    universe=[(si,j+2,species[j],counts[j],n-counts[j]) for si,j in enumerate(selected)]
    matrix=[]
    for iid in pilot_order:
        meta=pilot_meta[iid]; vals=pilot_values[iid]
        matrix.append((iid,meta["block_id"],meta["bioregion"],[vals[j] for j in selected]))
    positives=sum(counts[j] for j in selected)
    receipt={
      "schema":"structural.global_mammals_exploratory_pilot_result.v1_70",
      "status":"NONCONFIRMATORY_EXPLORATORY_PILOT_CONSUMED_AND_SPECIES_UNIVERSE_FROZEN",
      "candidate_id":contract["candidate_id"],
      "analysis_route":contract["analysis_route"],
      "response_data_rows_seen":data_rows,
      "source_species_columns":nsp,
      "pilot_islands_decoded":pilot_decoded,
      "pilot_occurrence_values_decoded":pilot_decoded*nsp,
      "confirmatory_islands_seen_routing_only":conf_seen,
      "confirmatory_occurrence_values_decoded":0,
      "excluded_islands_seen_routing_only":excluded_seen,
      "excluded_occurrence_values_decoded":0,
      "species_threshold_m":m,
      "focal_species":len(selected),
      "pilot_matrix_rows":n*len(selected),
      "pilot_matrix_positive":positives,
      "pilot_matrix_negative":n*len(selected)-positives,
      "exploratory_pilot_consumed":True,
      "fresh_status_restored":False,
      "counts_as_fresh_confirmation":False,
      "counts_as_primary_confirmatory_evidence":False,
      "confirmatory_response_authorized":False
    }
    return universe,matrix,receipt,semantic_pilot_started

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
    ap.add_argument("--confirmatory-routing",type=Path,required=True)
    ap.add_argument("--species-universe",type=Path,required=True)
    ap.add_argument("--pilot-matrix",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args(); semantic_started=False
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_exploratory_pilot_contract.v1_70":
            raise Stop("contract schema drift")
        species=load_corrected_manifest(a.corrected_manifest,c["physical_schema"]["species_order_sha256"])
        pilot_order,pilot_meta=load_routing(a.pilot_routing,c["routing"]["pilot_ids_sha256"],c["routing"]["pilot_islands"])
        conf_order,_=load_routing(a.confirmatory_routing,c["routing"]["confirmatory_ids_sha256"],c["routing"]["confirmatory_islands"])
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
            universe,matrix,result,semantic_started=consume(raw,species,pilot_order,pilot_meta,conf_order,c)
        write_outputs(universe,matrix,a.species_universe,a.pilot_matrix)
        result["species_universe_sha256"]=sha(a.species_universe)
        result["pilot_matrix_sha256"]=sha(a.pilot_matrix)
        result["raw_response_retained"]=False;code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,GlobalMammalTransportError,Stop) as e:
        result={
          "schema":"structural.global_mammals_exploratory_pilot_result.v1_70",
          "status":"TERMINAL_AFTER_EXPLORATORY_PILOT_ACCESS" if semantic_started else "HOLD_BEFORE_EXPLORATORY_PILOT_ACCESS",
          "reason":str(e),
          "exploratory_pilot_consumed":semantic_started,
          "confirmatory_occurrence_values_decoded":0,
          "excluded_occurrence_values_decoded":0,
          "fresh_status_restored":False,
          "counts_as_fresh_confirmation":False,
          "counts_as_primary_confirmatory_evidence":False,
          "confirmatory_response_authorized":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True));return code

if __name__=="__main__": raise SystemExit(main())
