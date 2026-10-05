#!/usr/bin/env python3
"""Inventory the frozen Zenodo source without downloading dataset files."""

from __future__ import annotations
import argparse, hashlib, json, mimetypes, urllib.request
from pathlib import Path

class Stop(RuntimeError): pass

def canon_doi(x):
    s=str(x or "").strip().lower()
    for p in ("https://doi.org/","http://doi.org/","doi:"):
        if s.startswith(p): s=s[len(p):]
    return s

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()

    c=json.loads(a.contract.read_text())
    if c.get("schema")!="structural.finnish_eider_zenodo_inventory_contract.v1_151_1":
        raise Stop("contract schema drift")

    url=c["source_identity"]["api_url"]
    req=urllib.request.Request(url,headers={"User-Agent":"Structural-response-free-schema-audit/1.1"})
    with urllib.request.urlopen(req,timeout=60) as resp:
        raw=resp.read()
        resolved_url=resp.geturl()
    x=json.loads(raw.decode("utf-8"))

    requested=int(c["source_identity"]["requested_record_or_concept_id"])
    returned_id=int(x.get("id")) if x.get("id") is not None else None
    concept=x.get("conceptrecid")
    returned_concept=int(concept) if concept not in (None,"") else None
    expected_doi=canon_doi(c["source_identity"]["doi"])
    returned_doi=canon_doi(x.get("doi"))
    returned_conceptdoi=canon_doi(x.get("conceptdoi"))
    identity_ok=(
      returned_id==requested or returned_concept==requested or
      returned_doi==expected_doi or returned_conceptdoi==expected_doi
    )
    if not identity_ok:
        raise Stop(f"Zenodo identity mismatch: id={returned_id}, conceptrecid={returned_concept}, doi={returned_doi}, conceptdoi={returned_conceptdoi}")

    files=[]
    for row in x.get("files",[]):
        name=str(row.get("key") or row.get("filename") or "").strip()
        size=row.get("size"); checksum=str(row.get("checksum") or "").strip()
        if not name or not isinstance(size,int) or size<0 or not checksum:
            raise Stop("invalid Zenodo file metadata")
        links=row.get("links") or {}
        mime,_=mimetypes.guess_type(name)
        files.append({
          "name":name,"size_bytes":size,"checksum":checksum,
          "suffixes":[s.lower() for s in Path(name).suffixes],
          "guessed_mime":mime,
          "metadata_self_url":links.get("self"),
          "metadata_content_url":links.get("content")
        })
    files.sort(key=lambda z:z["name"].casefold())
    if not files: raise Stop("no files")

    names=[z["name"] for z in files]
    out={
      "schema":"structural.finnish_eider_zenodo_inventory_result.v1_151_1",
      "status":"ZENODO_METADATA_ONLY_FILE_INVENTORY_COMPLETE",
      "candidate_id":c["candidate_id"],
      "identity":{
        "requested_record_or_concept_id":requested,
        "returned_record_id":returned_id,
        "returned_conceptrecid":returned_concept,
        "returned_doi":returned_doi or None,
        "returned_conceptdoi":returned_conceptdoi or None,
        "resolved_api_url":resolved_url,
        "identity_rule_passed":True
      },
      "file_count":len(files),
      "total_file_bytes":sum(z["size_bytes"] for z in files),
      "files":files,
      "filename_hints":{
        "pos2_name_hits":[n for n in names if "pos2" in n.casefold()],
        "distance_name_hits":[n for n in names if "dist" in n.casefold() or "distance" in n.casefold()],
        "eider_name_hits":[n for n in names if "eider" in n.casefold()],
        "group_or_reconstruction_name_hits":[n for n in names if any(t in n.casefold() for t in ("group","redistrib","reconstruct","imput"))],
        "tabular_file_names":[n for n in names if Path(n).suffix.casefold() in (".csv",".tsv",".txt",".xlsx",".xls")],
        "serialized_R_file_names":[n for n in names if Path(n).suffix.casefold() in (".rdata",".rda",".rds")]
      },
      "dataset_files_downloaded":0,
      "dataset_file_bytes_downloaded":0,
      "response_values_opened":0,
      "source_loss_events_computed":0,
      "source_leverage_effects_computed":0,
      "counts_as_empirical_source_loss_evidence":False
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    digest=hashlib.sha256(a.output.read_bytes()).hexdigest()
    receipt={
      "schema":"structural.finnish_eider_zenodo_inventory_receipt.v1_151_1",
      "status":"RESPONSE_FREE_INVENTORY_FROZEN",
      "inventory_sha256":digest,
      "file_count":len(files),
      "dataset_files_downloaded":0,
      "response_values_opened":0,
      "counts_as_empirical_source_loss_evidence":False
    }
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())
