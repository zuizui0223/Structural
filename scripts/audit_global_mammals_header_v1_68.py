#!/usr/bin/env python3
"""Persist the exact mammal response header only after the v1.65 header exposure.

This is a contaminated-macro physical schema audit. It downloads and verifies
the frozen response bytes, decodes exactly the first logical semicolon-delimited
record, writes a header manifest, and never decodes any data-record field.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,os,tempfile
from pathlib import Path

from scripts.fetch_global_mammal_response_opaque_v1_17 import (
    GlobalMammalTransportError,
    transport as transport_v117,
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_header_exposed_schema_contract_v1_68.json"
class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def first_logical_record(raw:bytes)->bytes:
    in_quotes=False;i=0
    while i<len(raw):
        b=raw[i]
        if b==34:
            if in_quotes and i+1<len(raw) and raw[i+1]==34:
                i+=2;continue
            in_quotes=not in_quotes;i+=1;continue
        if b==10 and not in_quotes:
            rec=raw[:i]
            return rec[:-1] if rec.endswith(b"\r") else rec
        i+=1
    raise Stop("header logical record not terminated")

def parse_header(record:bytes)->list[str]:
    try:text=record.decode("utf-8-sig")
    except UnicodeDecodeError as e:raise Stop("header is not UTF-8") from e
    rows=list(csv.reader(io.StringIO(text),delimiter=";",quotechar='"'))
    if len(rows)!=1:raise Stop("header parsed to non-single CSV row")
    return rows[0]

def species_fingerprint(species:list[str])->str:
    h=hashlib.sha256()
    for s in species:
        h.update(s.encode("utf-8"));h.update(b"\n")
    return h.hexdigest()

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--manifest",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_header_exposed_schema_contract.v1_68":
            raise Stop("contract schema drift")
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
            with p.open("rb") as h:
                # Read only enough bytes to cover the first logical record.
                buf=bytearray()
                in_quotes=False
                while True:
                    b=h.read(1)
                    if not b:raise Stop("EOF before header termination")
                    buf.extend(b)
                    if b==b'"':
                        if in_quotes:
                            nxt=h.peek(1)[:1] if hasattr(h,"peek") else b""
                            if nxt==b'"':
                                buf.extend(h.read(1));continue
                        in_quotes=not in_quotes
                    if b==b"\n" and not in_quotes:break
                rec=bytes(buf).rstrip(b"\r\n")
            fields=parse_header(rec)
        if len(fields)<2:raise Stop("header has fewer than two fields")
        routing=fields[0]
        species=fields[1:]
        blanks=sum(1 for x in species if not str(x).strip())
        duplicates=len(species)-len(set(species))
        a.manifest.parent.mkdir(parents=True,exist_ok=True)
        with a.manifest.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n")
            w.writerow(["source_column_index","role","header_string"])
            w.writerow([1,"routing",routing])
            for j,name in enumerate(species,start=2):w.writerow([j,"species",name])
        status="HEADER_ONLY_SCHEMA_FROZEN" if blanks==0 and duplicates==0 else "STOP_HEADER_IDENTITY_INVALID"
        result={
          "schema":"structural.global_mammals_header_exposed_schema_result.v1_68",
          "status":status,
          "total_header_fields":len(fields),
          "routing_header":routing,
          "observed_species_columns":len(species),
          "blank_species_headers":blanks,
          "duplicate_species_headers":duplicates,
          "species_order_sha256":species_fingerprint(species),
          "header_manifest_sha256":sha(a.manifest),
          "data_record_routing_fields_decoded":0,
          "pilot_occurrence_values_decoded":0,
          "confirmatory_occurrence_values_decoded":0,
          "excluded_occurrence_values_decoded":0,
          "fresh_status_restored":False,
          "counts_as_empirical_evidence":False,
          "continuation_authorized":status=="HEADER_ONLY_SCHEMA_FROZEN"
        }
        code=0 if status=="HEADER_ONLY_SCHEMA_FROZEN" else 2
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,GlobalMammalTransportError,Stop) as e:
        result={"schema":"structural.global_mammals_header_exposed_schema_result.v1_68","status":"STOP","reason":str(e),
          "data_record_routing_fields_decoded":0,"pilot_occurrence_values_decoded":0,"confirmatory_occurrence_values_decoded":0,
          "excluded_occurrence_values_decoded":0,"fresh_status_restored":False,"counts_as_empirical_evidence":False,
          "continuation_authorized":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
