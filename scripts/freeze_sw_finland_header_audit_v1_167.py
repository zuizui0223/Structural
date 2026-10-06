#!/usr/bin/env python3
"""Validate SW Finland v1.166 receipts for a separate canonical header freeze."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_header_freeze_contract_v1_167.json"

class Stop(RuntimeError): pass

def load(p:Path)->dict:
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict):raise Stop("JSON object required")
    return x

def canonical_sha(x:dict)->str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def verify(download:dict,header:dict,contract:dict)->dict:
    if contract.get("schema")!="structural.sw_finland_header_freeze_contract.v1_167":raise Stop("contract schema drift")
    rd=contract["required_download"];rh=contract["required_header"]
    for key in ("schema","status","md5","data_rows_semantically_opened","outcome_values_read"):
        if download.get(key)!=rd[key]:raise Stop(f"download receipt mismatch: {key}")
    for key in ("schema","status","data_rows_semantically_opened","outcome_values_read","t0_projection_authorized","unknown_headers"):
        if header.get(key)!=rh[key]:raise Stop(f"header receipt mismatch: {key}")
    if int(download.get("size_bytes",-1))!=int(header.get("file_size_bytes",-2)):raise Stop("download/header size mismatch")
    file_sha=str(header.get("file_sha256",""))
    header_sha=str(header.get("header_sha256",""))
    if len(file_sha)!=64 or len(header_sha)!=64:raise Stop("invalid SHA-256 identity")
    return {
      "schema":"structural.sw_finland_header_freeze.v1_167",
      "status":"HEADER_IDENTITY_VERIFIED_FUTURE_OUTCOME_REMAINS_SEALED",
      "candidate_id":contract["candidate_id"],
      "file_name":header.get("file_name"),
      "file_size_bytes":header["file_size_bytes"],
      "file_md5":download["md5"],
      "file_sha256":file_sha,
      "header_sha256":header_sha,
      "header_receipt_canonical_sha256":canonical_sha(header),
      "download_receipt_canonical_sha256":canonical_sha(download),
      "data_rows_semantically_opened":0,
      "outcome_values_read":0,
      "future_outcome_opened":False,
      "t0_projection_may_be_dispatched":True,
      "counts_as_empirical_evidence":False
    }

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("download_receipt",type=Path);ap.add_argument("header_receipt",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT);ap.add_argument("--freeze-output",type=Path)
    ap.add_argument("--exact-header-output",type=Path);a=ap.parse_args()
    try:
        d=load(a.download_receipt);h=load(a.header_receipt);c=load(a.contract);r=verify(d,h,c);code=0
        if a.exact_header_output:
            a.exact_header_output.parent.mkdir(parents=True,exist_ok=True)
            a.exact_header_output.write_text(json.dumps(h,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        if a.freeze_output:
            a.freeze_output.parent.mkdir(parents=True,exist_ok=True)
            a.freeze_output.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        r={"schema":"structural.sw_finland_header_freeze.v1_167","status":"STOP","reason":str(exc),
           "outcome_values_read":0,"future_outcome_opened":False,"t0_projection_may_be_dispatched":False,
           "counts_as_empirical_evidence":False};code=2
    print(json.dumps(r,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
