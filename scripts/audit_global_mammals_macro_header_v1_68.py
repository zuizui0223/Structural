#!/usr/bin/env python3
"""Audit only the semicolon-delimited header of the exact mammal response."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,os,tempfile
from pathlib import Path
from scripts.fetch_global_mammal_response_opaque_v1_17 import transport as transport_v117,GlobalMammalTransportError

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_macro_header_audit_contract_v1_68.json"
class Stop(RuntimeError):pass

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
    raise Stop("header record terminator not found")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_macro_header_audit_contract.v1_68":raise Stop("contract schema drift")
        t=c["response_identity"]
        tc={"candidate_id":c["candidate_id"],"target":{"name":"Appendix_1_presence_absence.csv","dryad_file_id":t["dryad_file_id"],"download_url":t["download_url"],"expected_size_bytes":t["expected_size_bytes"],"expected_sha256":t["expected_sha256"]},"attempt_policy":{"credentialed_attempt_limit":1,"blind_endpoint_retry_authorized":False,"alternate_file_id_retry_authorized":False}}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"Appendix_1_presence_absence.csv"
            tr=transport_v117(p,contract=tc,token=os.environ.get("DRYAD_TOKEN",""))
            if tr.get("status")!="EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED":raise Stop("exact response transport failed")
            raw=p.read_bytes()
            header_bytes=first_logical_record(raw)
        try:header_text=header_bytes.decode("utf-8-sig")
        except UnicodeDecodeError as e:raise Stop("header is not UTF-8") from e
        rows=list(csv.reader(io.StringIO(header_text),delimiter=";",quotechar='"'))
        if len(rows)!=1:raise Stop("header parsed to non-single record")
        fields=rows[0]
        if len(fields)<2:raise Stop("header has fewer than two fields")
        first=fields[0]
        species=fields[1:]
        if any(not str(x).strip() for x in species):raise Stop("blank species header field")
        ordered=hashlib.sha256()
        for x in species:
            ordered.update(str(x).encode("utf-8"));ordered.update(b"\n")
        result={
          "schema":"structural.global_mammals_macro_header_audit_result.v1_68",
          "status":"HEADER_ONLY_SCHEMA_AUDIT_COMPLETE",
          "header_field_count":len(fields),
          "species_header_field_count":len(species),
          "first_header_field_sha256":hashlib.sha256(first.encode("utf-8")).hexdigest(),
          "ordered_species_header_sha256":ordered.hexdigest(),
          "duplicate_species_header_count":len(species)-len(set(species)),
          "header_strings_persisted":False,
          "data_record_routing_ids_decoded":0,
          "data_record_occurrence_values_decoded":0,
          "data_record_bytes_semantically_opened":False,
          "raw_response_retained":False,
          "counts_as_empirical_evidence":False,
          "counts_as_fresh_confirmation":False,
          "fresh_status_restored":False,
          "confirmatory_response_authorized":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,GlobalMammalTransportError,Stop) as e:
        result={"schema":"structural.global_mammals_macro_header_audit_result.v1_68","status":"STOP_HEADER_ONLY_AUDIT","reason":str(e),"data_record_routing_ids_decoded":0,"data_record_occurrence_values_decoded":0,"counts_as_empirical_evidence":False,"fresh_status_restored":False,"confirmatory_response_authorized":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
