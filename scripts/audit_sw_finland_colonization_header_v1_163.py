#!/usr/bin/env python3
"""Header-only audit for the SW Finland colonization archive.

This script may hash the file as opaque bytes and decode only the first CSV
record (the header). It never reads a data row and never interprets outcome
tokens.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_plant_colonization_column_firewall_v1_162.json"

class Stop(RuntimeError):
    pass

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def read_header_only(path:Path)->list[str]:
    # newline='' lets csv parse the first logical record correctly.
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.reader(f)
        try:
            header=next(reader)
        except StopIteration as exc:
            raise Stop("empty CSV") from exc
        # Deliberately return immediately: no second next(), no data row.
        return [str(x) for x in header]

def audit(path:Path,contract:dict)->dict:
    if contract.get("schema")!="structural.sw_finland_plant_colonization_column_firewall.v1_162":
        raise Stop("contract schema drift")
    header=read_header_only(path)
    if len(header)!=len(set(header)):
        raise Stop("duplicate exact header names")
    required=set(contract["required_routing_and_t0_columns"])
    protected=set(contract["protected_future_endpoint_columns"])
    safe=set(contract["safe_recipient_state_columns"])|set(contract["safe_species_or_t0_columns"])
    missing=sorted((required|protected)-set(header))
    if missing:
        raise Stop(f"missing required/protected headers: {missing}")
    if protected!={"outcome"}:
        raise Stop("future endpoint contract drift")
    unknown=sorted(set(header)-(safe|protected))
    return {
      "schema":"structural.sw_finland_plant_colonization_header_audit.v1_163",
      "status":"HEADER_ONLY_AUDIT_COMPLETE_FUTURE_OUTCOME_ROWS_UNREAD",
      "candidate_id":contract["candidate_id"],
      "file_name":path.name,
      "file_size_bytes":path.stat().st_size,
      "file_sha256":sha256_file(path),
      "header":header,
      "header_sha256":hashlib.sha256((",".join(header)+"\n").encode("utf-8")).hexdigest(),
      "required_headers_present":True,
      "protected_future_endpoint_columns":["outcome"],
      "unknown_headers":unknown,
      "data_rows_semantically_opened":0,
      "outcome_values_read":0,
      "t0_projection_authorized": len(unknown)==0,
      "counts_as_empirical_evidence":False
    }

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("csv_file",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--receipt",type=Path)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text(encoding="utf-8"))
        result=audit(a.csv_file,c)
        code=0 if result["t0_projection_authorized"] else 2
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        result={
          "schema":"structural.sw_finland_plant_colonization_header_audit.v1_163",
          "status":"STOP_HEADER_AUDIT",
          "reason":str(exc),
          "data_rows_semantically_opened":0,
          "outcome_values_read":0,
          "t0_projection_authorized":False,
          "counts_as_empirical_evidence":False
        }
        code=2
    txt=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if a.receipt:
        a.receipt.parent.mkdir(parents=True,exist_ok=True)
        a.receipt.write_text(txt,encoding="utf-8")
    print(txt,end="")
    return code

if __name__=="__main__":
    raise SystemExit(main())
