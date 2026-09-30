#!/usr/bin/env python3
"""Consume only the 79 frozen focal mammal values on 4,126 confirmatory islands.

Pilot and excluded occurrence values remain byte-sealed. On confirmatory rows,
nonfocal occurrence fields are scanned only as opaque bytes to locate the 79
frozen focal columns and are never decoded.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,os,tempfile
from pathlib import Path

from scripts.fetch_global_mammal_response_opaque_v1_17 import (
    GlobalMammalTransportError, transport as transport_v117,
)
from scripts.run_global_mammals_macro_pilot_response_v1_65 import (
    iter_records, first_field_bytes, canon_id_bytes, parse_full_record,
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_exploratory_scoring_contract_v1_74.json"
class Stop(RuntimeError): pass

def sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def load_csv(p:Path)->list[dict]:
    with p.open("r",encoding="utf-8",newline="") as h:return list(csv.DictReader(h))

def iter_field_bytes(record:bytes,delimiter:int=59):
    field=bytearray();in_quotes=False;at_start=True;i=0
    while i<len(record):
        b=record[i]
        if in_quotes:
            if b==34:
                if i+1<len(record) and record[i+1]==34:
                    field.append(34);i+=2;continue
                in_quotes=False;i+=1;continue
            field.append(b);i+=1;continue
        if at_start and b==34:
            in_quotes=True;at_start=False;i+=1;continue
        if b==delimiter:
            yield bytes(field)
            field.clear();at_start=True;i+=1;continue
        field.append(b);at_start=False;i+=1
    if in_quotes:raise Stop("unterminated quoted field")
    yield bytes(field)

def load_corrected_manifest(path:Path,expected_sha:str)->list[str]:
    if sha(path)!=expected_sha:raise Stop("corrected manifest SHA drift")
    rows=load_csv(path)
    if len(rows)!=5394:raise Stop("corrected manifest count drift")
    names=[]
    for j,r in enumerate(rows):
        if int(r["species_index"])!=j or int(r["data_column_index"])!=j+2:
            raise Stop("corrected manifest index drift")
        names.append(str(r["species_name"]))
    return names

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--corrected-manifest",type=Path,required=True)
    ap.add_argument("--universe",type=Path,required=True)
    ap.add_argument("--pilot-routing",type=Path,required=True)
    ap.add_argument("--confirmatory-routing",type=Path,required=True)
    ap.add_argument("--matrix",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args();confirm_semantic_started=False

    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_exploratory_scoring_contract.v1_74":
            raise Stop("contract schema drift")
        full_species=load_corrected_manifest(
            a.corrected_manifest,
            "882af8216d94dcb18fdafe8f9b3d363cadc2e7afbc1c227ba65d29848dea63d6",
        )
        if sha(a.universe)!=c["focal_response"]["species_universe_sha256"]:
            raise Stop("focal universe SHA drift")
        universe=load_csv(a.universe)
        if len(universe)!=79:raise Stop("focal species count drift")
        focal_columns=[];focal_names=[]
        for j,r in enumerate(universe):
            if int(r["species_index"])!=j:raise Stop("focal species index drift")
            col=int(r["source_data_column_index"])
            name=str(r["species_name"])
            if not 2<=col<=5395:raise Stop("focal source column outside physical schema")
            if full_species[col-2]!=name:raise Stop("focal species identity/column mismatch")
            focal_columns.append(col);focal_names.append(name)
        if len(set(focal_columns))!=79 or len(set(focal_names))!=79:
            raise Stop("duplicate focal identity")

        if sha(a.pilot_routing)!=c["confirmatory_routing"]["pilot_ids_sha256"]:
            raise Stop("pilot routing SHA drift")
        if sha(a.confirmatory_routing)!=c["confirmatory_routing"]["confirmatory_ids_sha256"]:
            raise Stop("confirmatory routing SHA drift")
        pilot=load_csv(a.pilot_routing);conf=load_csv(a.confirmatory_routing)
        if len(pilot)!=1275 or len(conf)!=4126:raise Stop("routing count drift")
        pilot_set={str(r["ID"]) for r in pilot}
        conf_order=[str(r["ID"]) for r in conf]
        conf_set=set(conf_order)
        if len(pilot_set)!=1275 or len(conf_set)!=4126 or pilot_set&conf_set:
            raise Stop("routing identity drift")
        conf_meta={str(r["ID"]):r for r in conf}

        target=c["response_identity"]
        tc={"candidate_id":c["candidate_id"],"target":{
          "name":target["name"],"dryad_file_id":target["dryad_file_id"],"download_url":target["download_url"],
          "expected_size_bytes":target["expected_size_bytes"],"expected_sha256":target["expected_sha256"]},
          "attempt_policy":{"credentialed_attempt_limit":1,"blind_endpoint_retry_authorized":False,"alternate_file_id_retry_authorized":False}}
        values={};data_rows=pilot_seen=conf_seen=excluded_seen=0
        header_decoded=0;focal_decoded=0
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/target["name"]
            tr=transport_v117(p,contract=tc,token=os.environ.get("DRYAD_TOKEN",""))
            if tr.get("status")!="EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED":
                raise Stop("exact response transport did not qualify")
            raw=p.read_bytes()
            recs=iter(iter_records(raw))
            try:header_rec=next(recs)
            except StopIteration as e:raise Stop("empty response") from e
            header=parse_full_record(header_rec)
            if header!=full_species:raise Stop("response header differs from corrected manifest")
            header_decoded=len(header)

            wanted=set(focal_columns)
            for rec in recs:
                if not rec:continue
                data_rows+=1
                iid=canon_id_bytes(first_field_bytes(rec,59))
                if iid in conf_set:
                    fields={}
                    field_count=0
                    for idx,raw_field in enumerate(iter_field_bytes(rec,59),start=1):
                        field_count=idx
                        if idx in wanted:
                            fields[idx]=raw_field
                    if field_count!=5395:raise Stop("confirmatory data field-count drift")
                    if len(fields)!=79:raise Stop("not every focal field was routed")
                    row=[]
                    for col in focal_columns:
                        rawv=fields[col].strip()
                        if rawv not in (b"0",b"1"):raise Stop("confirmatory focal target outside 0/1")
                        confirm_semantic_started=True
                        row.append(1 if rawv==b"1" else 0)
                        focal_decoded+=1
                    if iid in values:raise Stop("duplicate confirmatory response row")
                    values[iid]=row;conf_seen+=1
                elif iid in pilot_set:
                    pilot_seen+=1
                else:
                    excluded_seen+=1

        if data_rows!=5592:raise Stop("response row-count drift")
        if pilot_seen!=1275:raise Stop("pilot routing count drift")
        if conf_seen!=4126 or set(values)!=conf_set:raise Stop("confirmatory routing support drift")
        if excluded_seen!=191:raise Stop("excluded routing count drift")
        if focal_decoded!=325954:raise Stop("confirmatory focal value count drift")

        labels=[f"S{j:05d}" for j in range(79)]
        a.matrix.parent.mkdir(parents=True,exist_ok=True)
        with a.matrix.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n")
            w.writerow(["ID","block_id","bioregion"]+labels)
            for iid in conf_order:
                meta=conf_meta[iid]
                w.writerow([iid,meta["block_id"],meta["bioregion"]]+values[iid])

        result={
          "schema":"structural.global_mammals_exploratory_confirmatory_response_result.v1_74",
          "status":"NONCONFIRMATORY_EXPLORATORY_CONFIRMATORY_RESPONSE_CONSUMED_FOCAL_MATRIX_FROZEN",
          "candidate_id":c["candidate_id"],
          "analysis_route":c["analysis_route"],
          "response_data_rows_seen":data_rows,
          "species_header_fields_decoded":header_decoded,
          "confirmatory_entities_decoded":conf_seen,
          "confirmatory_focal_species":79,
          "confirmatory_focal_values_decoded":focal_decoded,
          "confirmatory_nonfocal_values_decoded":0,
          "pilot_occurrence_values_decoded":0,
          "excluded_occurrence_values_decoded":0,
          "matrix_sha256":sha(a.matrix),
          "confirmatory_response_consumed":True,
          "fresh_status_restored":False,
          "counts_as_fresh_confirmation":False,
          "counts_as_primary_confirmatory_evidence":False,
          "rerun_authorized":False,
          "raw_response_retained":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,GlobalMammalTransportError,Stop) as e:
        result={
          "schema":"structural.global_mammals_exploratory_confirmatory_response_result.v1_74",
          "status":"TERMINAL_AFTER_EXPLORATORY_CONFIRMATORY_ACCESS" if confirm_semantic_started else "HOLD_BEFORE_EXPLORATORY_CONFIRMATORY_ACCESS",
          "reason":str(e),
          "confirmatory_response_consumed":confirm_semantic_started,
          "confirmatory_nonfocal_values_decoded":0,
          "pilot_occurrence_values_decoded":0,
          "excluded_occurrence_values_decoded":0,
          "fresh_status_restored":False,
          "counts_as_fresh_confirmation":False,
          "counts_as_primary_confirmatory_evidence":False,
          "rerun_authorized":False if confirm_semantic_started else None
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    return code

if __name__=="__main__":raise SystemExit(main())
