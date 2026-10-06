#!/usr/bin/env python3
"""Route SW Finland t0-safe columns from the frozen semicolon archive.

The future endpoint field 'outcome' is located by raw byte field boundaries but
its value bytes are never decoded or persisted. Only frozen t0/static fields are
decoded and written to a new safe comma-delimited projection.
"""
from __future__ import annotations

import argparse,csv,hashlib,io,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_t0_byte_router_contract_v1_169.json"
DEFAULT_FIREWALL=ROOT/"development/sw_finland_plant_colonization_column_firewall_v1_162.json"
DEFAULT_HEADER=ROOT/"development/sw_finland_header_audit_v1_167.json"
DEFAULT_FREEZE=ROOT/"development/sw_finland_header_freeze_v1_167.json"

class Stop(RuntimeError): pass

def loadj(p:Path)->dict:
    x=json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(x,dict): raise Stop(f"{p.name} must contain JSON object")
    return x

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def md5_file(p:Path)->str:
    h=hashlib.md5()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def raw_records(path:Path,delimiter_byte:int=59):
    """Yield one list of raw field bytes per logical record.

    Quotes/doubled quotes and quoted newlines are recognized without decoding
    any field value. The delimiter is semicolon (0x3b) by frozen contract.
    """
    data=path.read_bytes()
    fields=[];start=0;i=0;in_quotes=False;n=len(data)
    while i<n:
        b=data[i]
        if b==34:
            if in_quotes and i+1<n and data[i+1]==34:
                i+=2;continue
            in_quotes=not in_quotes;i+=1;continue
        if not in_quotes and b==delimiter_byte:
            fields.append(data[start:i]);start=i+1;i+=1;continue
        if not in_quotes and b in (10,13):
            fields.append(data[start:i]);yield fields;fields=[]
            if b==13 and i+1<n and data[i+1]==10:i+=2
            else:i+=1
            start=i;continue
        i+=1
    if in_quotes: raise Stop("unterminated quoted field")
    if start<n or fields:
        fields.append(data[start:n]);yield fields

def decode_field(raw:bytes)->str:
    """Decode one already-isolated semicolon CSV field, including quote escape."""
    text=raw.decode("utf-8")
    reader=csv.reader(io.StringIO(text),delimiter=";",quotechar='"')
    try: row=next(reader)
    except StopIteration as exc: raise Stop("empty isolated field") from exc
    if len(row)!=1: raise Stop("isolated safe field decoded to multiple fields")
    try: next(reader)
    except StopIteration: pass
    else: raise Stop("isolated safe field decoded to multiple records")
    return row[0]

def route(mixed:Path,output:Path,contract:dict,firewall:dict,header_receipt:dict,header_freeze:dict)->dict:
    if contract.get("schema")!="structural.sw_finland_t0_byte_router_contract.v1_169": raise Stop("router contract drift")
    if firewall.get("schema")!="structural.sw_finland_plant_colonization_column_firewall.v1_162": raise Stop("firewall drift")
    if header_receipt.get("status")!="HEADER_ONLY_AUDIT_COMPLETE_FUTURE_OUTCOME_ROWS_UNREAD": raise Stop("header not qualified")
    if header_freeze.get("status")!="HEADER_IDENTITY_VERIFIED_FUTURE_OUTCOME_REMAINS_SEALED": raise Stop("header freeze not qualified")
    exact=contract["exact_input"]
    if mixed.stat().st_size!=exact["size_bytes"]: raise Stop("input size drift")
    if md5_file(mixed)!=exact["md5"]: raise Stop("input MD5 drift")
    if sha256_file(mixed)!=exact["sha256"]: raise Stop("input SHA256 drift")
    if header_receipt.get("delimiter")!=";" or exact["delimiter"]!=";": raise Stop("semicolon grammar drift")
    if header_receipt.get("file_sha256")!=exact["sha256"] or header_freeze.get("file_sha256")!=exact["sha256"]: raise Stop("header/file identity drift")
    if header_receipt.get("header_sha256")!=exact["header_sha256"] or header_freeze.get("header_sha256")!=exact["header_sha256"]: raise Stop("header SHA drift")
    if header_receipt.get("outcome_values_read")!=0 or header_freeze.get("outcome_values_read")!=0: raise Stop("future endpoint already opened")

    canonical=list(header_receipt["header"])
    protected=set(firewall["protected_future_endpoint_columns"])
    if protected!={"outcome"}: raise Stop("protected endpoint drift")
    selected=(
      set(firewall["required_routing_and_t0_columns"])
      |set(firewall["safe_recipient_state_columns"])
      |set(firewall["safe_species_or_t0_columns"])
    )-protected
    keep_names=[name for name in canonical if name in selected]
    if set(keep_names)!=selected: raise Stop("frozen safe-column set/header mismatch")
    protected_idx=[i for i,x in enumerate(canonical) if x=="outcome"]
    if protected_idx!=[0]: raise Stop("protected endpoint position drift")
    keep_idx=[i for i,x in enumerate(canonical) if x in selected]

    records=raw_records(mixed,59)
    try: raw_header=next(records)
    except StopIteration as exc: raise Stop("empty archive") from exc
    decoded_header=[decode_field(x) for x in raw_header]
    if decoded_header!=canonical: raise Stop("raw header differs from canonical freeze")

    output.parent.mkdir(parents=True,exist_ok=True)
    row_count=0;skipped=0;safe_values_decoded=0
    try:
        with output.open("w",encoding="utf-8",newline="") as out:
            w=csv.writer(out,lineterminator="\n")
            w.writerow(keep_names)
            for fields in records:
                if len(fields)!=len(canonical): raise Stop(f"ragged logical row {row_count+1}")
                row_count+=1;skipped+=1
                # Never call decode_field on fields[0] (outcome).
                vals=[decode_field(fields[i]) for i in keep_idx]
                safe_values_decoded+=len(vals)
                w.writerow(vals)
    except Exception:
        output.unlink(missing_ok=True)
        raise

    result={
      "schema":"structural.sw_finland_t0_byte_router_result.v1_169",
      "status":"T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE",
      "candidate_id":contract["candidate_id"],
      "raw_mixed_file_size_bytes":mixed.stat().st_size,
      "raw_mixed_file_md5":exact["md5"],
      "raw_mixed_file_sha256":exact["sha256"],
      "canonical_header_sha256":exact["header_sha256"],
      "source_delimiter":";",
      "data_row_count":row_count,
      "safe_column_count":len(keep_names),
      "safe_columns":keep_names,
      "safe_field_values_decoded":safe_values_decoded,
      "safe_projection_sha256":sha256_file(output),
      "protected_columns":["outcome"],
      "protected_field_count_skipped":skipped,
      "protected_field_values_decoded":0,
      "protected_field_bytes_persisted":0,
      "outcome_values_read":0,
      "future_outcome_opened":False,
      "counts_as_empirical_evidence":False,
      "next_action":contract["next_gate"]
    }
    return result

def main()->int:
    p=argparse.ArgumentParser();p.add_argument("mixed_csv",type=Path);p.add_argument("--safe-output",type=Path,required=True);p.add_argument("--receipt",type=Path,required=True)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT);p.add_argument("--firewall",type=Path,default=DEFAULT_FIREWALL);p.add_argument("--header",type=Path,default=DEFAULT_HEADER);p.add_argument("--header-freeze",type=Path,default=DEFAULT_FREEZE)
    a=p.parse_args()
    try:
        r=route(a.mixed_csv,a.safe_output,loadj(a.contract),loadj(a.firewall),loadj(a.header),loadj(a.header_freeze));code=0
    except (OSError,UnicodeDecodeError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        a.safe_output.unlink(missing_ok=True)
        r={"schema":"structural.sw_finland_t0_byte_router_result.v1_169","status":"STOP_T0_BYTE_ROUTER","reason":str(exc),"protected_field_values_decoded":0,"protected_field_bytes_persisted":0,"outcome_values_read":0,"future_outcome_opened":False,"counts_as_empirical_evidence":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:r.get(k) for k in ("status","data_row_count","safe_column_count","protected_field_count_skipped","protected_field_values_decoded","outcome_values_read")},sort_keys=True))
    return code
if __name__=="__main__": raise SystemExit(main())
