#!/usr/bin/env python3
"""Re-audit exact SW Finland header using the committed semicolon grammar."""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_FIREWALL=ROOT/"development/sw_finland_plant_colonization_column_firewall_v1_162.json"
DEFAULT_GRAMMAR=ROOT/"development/sw_finland_header_grammar_receipt_v1_166_1.json"
DEFAULT_CONTRACT=ROOT/"development/sw_finland_header_reaudit_contract_v1_166_2.json"

class Stop(RuntimeError): pass

def load(p):
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): raise Stop("JSON object required")
    return x

def sha256_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def audit(path,firewall,grammar,contract):
    if grammar.get("status")!="HEADER_GRAMMAR_UNIQUELY_IDENTIFIED": raise Stop("grammar not qualified")
    delim=grammar.get("selected_delimiter")
    if delim!=contract["grammar"]["selected_delimiter"] or delim!=";": raise Stop("delimiter drift")
    if grammar.get("selected_header_sha256")!=contract["grammar"]["selected_header_sha256"]: raise Stop("grammar header SHA drift")
    with path.open("r",encoding="utf-8-sig",newline="") as f:
        rd=csv.reader(f,delimiter=delim)
        try: header=[str(x) for x in next(rd)]
        except StopIteration as e: raise Stop("empty CSV") from e
    if header!=grammar.get("selected_header"): raise Stop("header differs from committed grammar receipt")
    if len(header)!=len(set(header)): raise Stop("duplicate exact header names")
    required=set(firewall["required_routing_and_t0_columns"])
    protected=set(firewall["protected_future_endpoint_columns"])
    safe=set(firewall["safe_recipient_state_columns"])|set(firewall["safe_species_or_t0_columns"])
    missing=sorted((required|protected)-set(header))
    if missing: raise Stop(f"missing frozen headers: {missing}")
    unknown=sorted(set(header)-(safe|required|protected))
    if unknown: raise Stop(f"unclassified headers: {unknown}")
    result={
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
      "unknown_headers":[],
      "delimiter":delim,
      "implementation_revision":"v1.166.2",
      "grammar_receipt_header_sha256":grammar["selected_header_sha256"],
      "data_rows_semantically_opened":0,
      "outcome_values_read":0,
      "t0_projection_authorized":True,
      "counts_as_empirical_evidence":False
    }
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument("csv_file",type=Path);p.add_argument("--firewall",type=Path,default=DEFAULT_FIREWALL);p.add_argument("--grammar",type=Path,default=DEFAULT_GRAMMAR);p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT);p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args();r=audit(a.csv_file,load(a.firewall),load(a.grammar),load(a.contract))
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":r["status"],"delimiter":r["delimiter"],"field_count":len(r["header"]),"data_rows_semantically_opened":0,"outcome_values_read":0},sort_keys=True))
if __name__=="__main__": main()
