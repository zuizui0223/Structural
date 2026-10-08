#!/usr/bin/env python3
"""Probe at most one header byte from nine original Dryad file URLs via Range GET.

A 206 status + an exact bytes 0-0/TOTAL Content-Range is required before any read.
No CSV header, species/island, or 0/1 cell can be semantically opened.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
from urllib import request,error,parse

ROOT=Path(__file__).resolve().parents[1]
V198=ROOT/"development/hebert_transport_preflight_receipt_v1_198.json"
FROZEN=ROOT/"development/global_mammals_independent_checklist_preintake_v1_188.json"
CONTRACT=ROOT/"development/hebert_one_byte_transport_contract_v1_199.json"

class Stop(RuntimeError):pass

def allowed(u):
    p=parse.urlsplit(u)
    host=(p.hostname or "").lower()
    return p.scheme=="https" and not p.username and not p.password and (
      host=="datadryad.org" or host.endswith(".datadryad.org")
      or host=="s3.amazonaws.com" or host.endswith(".amazonaws.com")
    )

class RedirectGuard(request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not allowed(newurl):raise Stop("redirect to unauthorized host")
        nxt=super().redirect_request(req,fp,code,msg,headers,newurl)
        if nxt is not None and nxt.get_method()!="GET":raise Stop("GET method changed")
        return nxt

def range_response_ok(status,content_range,content_type):
    if status!=206:return False
    m=re.fullmatch(r"bytes\s+0-0/(\d+)",content_range.strip(),flags=re.I)
    if not m or int(m.group(1))<12 or int(m.group(1))>200000:return False
    if "html" in content_type.lower():return False
    return True

def probe_range(u):
    if not allowed(u):return {"state":"UNSAFE_URL","range_bytes_read":0}
    opener=request.build_opener(RedirectGuard())
    req=request.Request(u,method="GET",headers={"Range":"bytes=0-0",
             "Accept-Encoding":"identity","User-Agent":"Structural-public-Hébert-range-preflight-v1.199"})
    try:
        with opener.open(req,timeout=15) as resp:
            status=int(resp.status)
            content_range=resp.headers.get("Content-Range","")
            ctype=resp.headers.get("Content-Type","").split(";")[0]
            if not range_response_ok(status,content_range,ctype):
                return {"state":"RANGE_REJECTED","http_status":status,
                        "range_header_valid":False,"range_bytes_read":0}
            if not allowed(resp.url):return {"state":"UNSAFE_REDIRECT","range_bytes_read":0}
            b=resp.read(1)
            if len(b)!=1:return {"state":"RANGE_EMPTY","range_bytes_read":len(b)}
            # Deliberately discard without decoding, retaining, or printing b.
            del b
            return {"state":"ONE_BYTE_RANGE_OK","http_status":206,
                    "range_header_valid":True,"range_bytes_read":1}
    except (error.HTTPError,error.URLError,OSError,TimeoutError,Stop) as e:
        return {"state":"RANGE_REQUEST_FAILED",
                "http_status":getattr(e,"code",None),
                "error_class":type(e).__name__,"range_bytes_read":0}

def run(receipt,source,contract,probe=probe_range):
    if contract.get("schema")!="structural.hebert_one_byte_transport_probe.v1_199":
        raise Stop("contract drift")
    if receipt.get("status")!="NO_HEAD_CANDIDATE":raise Stop("v198 result drift")
    if receipt.get("CSV_body_bytes_read")!=0 or receipt.get("island_species_binary_values_decoded")!=0:
        raise Stop("v198 response boundary drift")
    src=source.get("files",[])
    frows=receipt.get("files",[])
    if len(src)!=9 or len(frows)!=9:raise Stop("nine-source list drift")
    if [f["name"] for f in src]!=[f["file"] for f in frows]:raise Stop("source order or filenames drift")
    if [int(f["id"]) for f in src]!=contract["frozen_eligibility"]["expected_source_ids"]:
        raise Stop("original file IDs drift")
    completed=[];success=0;bytes_read=0
    for orig,previous in zip(src,frows):
        attempts=previous.get("attempts",[])
        if len(attempts)>2:raise Stop("too many public URLs in v198")
        if any(a.get("route") not in ("frozen_old_id","live_landing_exact_filename") for a in attempts):
            raise Stop("unsupported transport URL origin")
        success_this=False;results=[]
        for a in attempts:
            u=a["url"]
            if not allowed(u):raise Stop("unsafe frozen URL")
            got=probe(u)
            if got.get("range_bytes_read",0)>1:raise Stop("more than one header byte read")
            bytes_read+=got.get("range_bytes_read",0)
            if got.get("state")=="ONE_BYTE_RANGE_OK":success_this=True
            results.append({"url":u,"route":a["route"],**got})
        success+=int(success_this)
        completed.append({"file":orig["name"],"id":int(orig["id"]),"range_available":success_this,"attempts":results})
    classification="RANGE_AVAILABLE_ALL_9" if success==9 else "RANGE_AVAILABLE_PARTIAL" if success else "RANGE_UNAVAILABLE"
    return {
        "schema":"structural.hebert_one_byte_transport_result.v1_199",
        "status":classification,"dataset_doi":contract["doi"],
        "original_frozen_file_count":9,"files_with_range_available":success,
        "range_probe_bytes_read":bytes_read,"maximum_possible_probe_bytes":18,
        "source_header_fields_decoded":0,"source_island_names_decoded":0,
        "external_island_species_0_1_values_decoded":0,"original_heldout_mammal_values_opened":0,
        "external_scoring_authorized":False,"biological_evidence_produced":False,
        "files":completed
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--v198",type=Path,default=V198)
    ap.add_argument("--source",type=Path,default=FROZEN)
    ap.add_argument("--contract",type=Path,default=CONTRACT)
    ap.add_argument("--receipt",type=Path,required=True)
    args=ap.parse_args()
    try:
        x=json.loads(args.v198.read_text())
        src=json.loads(args.source.read_text())
        c=json.loads(args.contract.read_text())
        r=run(x,src,c)
    except (Stop,KeyError,ValueError,OSError,json.JSONDecodeError) as e:
        r={"schema":"structural.hebert_one_byte_transport_result.v1_199",
           "status":"RANGE_PREFLIGHT_STOP","reason_class":type(e).__name__,
           "source_header_fields_decoded":0,"source_island_names_decoded":0,
           "external_island_species_0_1_values_decoded":0,
           "original_heldout_mammal_values_opened":0,"external_scoring_authorized":False,
           "biological_evidence_produced":False}
    args.receipt.parent.mkdir(parents=True,exist_ok=True)
    args.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
