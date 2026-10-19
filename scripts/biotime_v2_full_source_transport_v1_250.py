#!/usr/bin/env python3
"""Exact publisher-source acquisition for retrospective BioTIME site-year frame inspection.

This DOES materialize a response-bearing public RDS in the runner, but no
biological outcome fields are queried or scored at this stage. It is a
retrospective design-exposed lane, not a fresh response-sealed confirmation.
No raw biological records should be uploaded into CI artifacts or committed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.error
from biotime_v2_metadata_preflight_v1_249 import source_bytes as get_official_metadata

DOI="10.5281/zenodo.15222193"
FILENAME="biotime_v2_query_15April25.rds"
MD5="2fed9f6c8028d4c44d80769c594be056"
URLS=(
    f"https://zenodo.org/records/15222193/files/{FILENAME}?download=1",
    f"https://zenodo.org/api/records/15222193/files/{FILENAME}/content",
)
MAX_BYTES=220_000_000


def download(dst:Path):
    errs=[]
    dst.parent.mkdir(parents=True,exist_ok=True)
    for url in URLS:
        tmp=dst.with_name(dst.name+".partial")
        size=0
        digest=hashlib.md5()
        req=urllib.request.Request(url,headers={"User-Agent":"Structural-temporal-ecology/1.0 (source integrity)","Accept":"application/octet-stream,*/*"})
        try:
            with urllib.request.urlopen(req,timeout=150) as response, tmp.open("wb") as out:
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk:break
                    size+=len(chunk)
                    if size>MAX_BYTES:raise RuntimeError("RDS exceeds maximum 220 MB")
                    digest.update(chunk);out.write(chunk)
        except Exception as e:
            tmp.unlink(missing_ok=True)
            errs.append({"source_route":"zenodo-browser" if "/records/" in url else "zenodo-api","error":type(e).__name__,"detail":str(e)[:150]})
            continue
        if digest.hexdigest()!=MD5:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"Original publisher MD5 mismatch, got {digest.hexdigest()}; no alternative data substitution")
        tmp.replace(dst)
        return {"source_url":url,"bytes":size,"md5":digest.hexdigest(),"publisher_md5_match":True,"transport_failures":errs}
    raise RuntimeError("Exact original source unreachable: "+json.dumps(errs))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-rds",required=True,type=Path)
    p.add_argument("--out-receipt",required=True,type=Path)
    p.add_argument("--out-meta",required=True,type=Path)
    a=p.parse_args()
    rec={
        "schema":"structural.biotime2_full_source_transport.v1_250",
        "original_doi":DOI,"file":FILENAME,"expected_md5":MD5,
        "evidence_class":"RETROSPECTIVE_DESIGN_EXPOSED_NO_BIOLOGICAL_ENDPOINT_SCORED",
        "uses_original_global_mammal_response":False,
        "new_confirmatory_admissions":0,"GEB_scientific_HOLD":True,"eBird_used":False,
    }
    try:
        meta,meta_url,_=get_official_metadata()
        a.out_meta.parent.mkdir(parents=True,exist_ok=True)
        a.out_meta.write_bytes(meta)
        rec["metadata"]={"publisher_md5_verified":True,"bytes":len(meta),"source_url":meta_url}
        rec["source"]=download(a.out_rds)
        rec["status"]="ORIGINAL_RDS_SOURCE_VERIFIED"
    except Exception as e:
        rec["status"]="TECHNICAL_STOP_NO_SAMPLE_FRAME"
        rec["stop_reason"]=str(e)
    a.out_receipt.parent.mkdir(parents=True,exist_ok=True)
    a.out_receipt.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":rec["status"],"bytes":rec.get("source",{}).get("bytes"),"doi":DOI}))
    if rec["status"]!="ORIGINAL_RDS_SOURCE_VERIFIED":
        raise SystemExit(2)


if __name__=="__main__":
    main()
