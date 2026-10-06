#!/usr/bin/env python3
"""Header-only delimiter diagnostic for exact SW Finland archive bytes."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_header_grammar_diagnostic_contract_v1_166_1.json"

class Stop(RuntimeError): pass

def load(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): raise Stop("contract not object")
    return x

def md5_file(p):
    h=hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def first_record(path,delimiter):
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        r=csv.reader(f,delimiter=delimiter)
        try: return [str(x) for x in next(r)]
        except StopIteration as e: raise Stop("empty CSV") from e

def audit(path,contract):
    if contract.get("schema")!="structural.sw_finland_header_grammar_diagnostic_contract.v1_166_1":
        raise Stop("contract schema drift")
    if md5_file(path)!=contract["parent_failure"]["exact_file_md5"]:
        raise Stop("exact file MD5 drift")
    required=set(contract["required_headers"])
    candidates=[]
    for delim in contract["permitted_delimiters"]:
        header=first_record(path,delim)
        dup=len(header)!=len(set(header))
        missing=sorted(required-set(header))
        candidates.append({
          "delimiter":delim,
          "field_count":len(header),
          "header":header,
          "duplicate_exact_headers":dup,
          "missing_required_headers":missing,
          "qualifies":(not dup and not missing)
        })
    good=[x for x in candidates if x["qualifies"]]
    status="HEADER_GRAMMAR_UNIQUELY_IDENTIFIED" if len(good)==1 else "STOP_HEADER_GRAMMAR_NOT_UNIQUE"
    return {
      "schema":"structural.sw_finland_header_grammar_diagnostic.v1_166_1",
      "status":status,
      "candidate_id":contract["candidate_id"],
      "file_md5":contract["parent_failure"]["exact_file_md5"],
      "candidates":candidates,
      "selected_delimiter":good[0]["delimiter"] if len(good)==1 else None,
      "selected_header":good[0]["header"] if len(good)==1 else None,
      "selected_header_sha256":(
        hashlib.sha256((good[0]["delimiter"].join(good[0]["header"])+"\n").encode()).hexdigest()
        if len(good)==1 else None
      ),
      "data_rows_semantically_opened":0,
      "outcome_values_read":0,
      "t0_projection_authorized":False,
      "counts_as_empirical_evidence":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("csv_file",type=Path);p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT);p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args();x=audit(a.csv_file,load(a.contract))
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":x["status"],"selected_delimiter":x["selected_delimiter"],"field_counts":[c["field_count"] for c in x["candidates"]],"data_rows_semantically_opened":0,"outcome_values_read":0},sort_keys=True))
    return 0 if x["status"]=="HEADER_GRAMMAR_UNIQUELY_IDENTIFIED" else 2
if __name__=="__main__": raise SystemExit(main())
