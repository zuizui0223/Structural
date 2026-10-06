#!/usr/bin/env python3
"""Byte-route SW Finland t0 columns while keeping future outcome field opaque.

The mixed CSV is read as raw bytes. CSV field boundaries are located without
decoding data-field contents. Only prospectively allowlisted t0/static fields
are copied into a new safe CSV. Bytes belonging to the protected future
endpoint field are never decoded or persisted.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_FIREWALL=ROOT/"development/sw_finland_plant_colonization_column_firewall_v1_162.json"

class Stop(RuntimeError): pass

def sha256_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def _records(data:bytes):
    """Yield lists of raw field byte slices for RFC4180-like CSV."""
    fields=[]
    start=0
    i=0
    in_quotes=False
    n=len(data)
    while i<n:
        b=data[i]
        if b==34:  # quote
            if in_quotes and i+1<n and data[i+1]==34:
                i+=2
                continue
            in_quotes=not in_quotes
            i+=1
            continue
        if not in_quotes and b==44:  # comma
            fields.append(data[start:i])
            start=i+1
            i+=1
            continue
        if not in_quotes and b in (10,13):
            fields.append(data[start:i])
            yield fields
            fields=[]
            if b==13 and i+1<n and data[i+1]==10:
                i+=2
            else:
                i+=1
            start=i
            continue
        i+=1
    if in_quotes:
        raise Stop("unterminated quoted CSV field")
    if start<n or fields:
        fields.append(data[start:n])
        yield fields

def _decode_header(raw_fields:list[bytes])->list[str]:
    joined=b",".join(raw_fields).decode("utf-8-sig")
    rows=list(csv.reader([joined]))
    if len(rows)!=1:raise Stop("invalid header record")
    return [str(x) for x in rows[0]]

def route(mixed_path:Path,header_receipt:dict,firewall:dict,output_path:Path)->dict:
    if firewall.get("schema")!="structural.sw_finland_plant_colonization_column_firewall.v1_162":
        raise Stop("firewall schema drift")
    if header_receipt.get("schema")!="structural.sw_finland_plant_colonization_header_audit.v1_163":
        raise Stop("header receipt schema drift")
    if header_receipt.get("status")!="HEADER_ONLY_AUDIT_COMPLETE_FUTURE_OUTCOME_ROWS_UNREAD":
        raise Stop("header audit not qualified")
    if header_receipt.get("outcome_values_read")!=0:
        raise Stop("future outcome boundary already violated")
    raw_sha=sha256_file(mixed_path)
    if raw_sha!=header_receipt.get("file_sha256"):
        raise Stop("mixed file/header receipt SHA mismatch")

    protected=set(firewall["protected_future_endpoint_columns"])
    if protected!={"outcome"}:raise Stop("protected endpoint drift")
    selected=(
        set(firewall["required_routing_and_t0_columns"])
        | set(firewall["safe_recipient_state_columns"])
        | set(firewall["safe_species_or_t0_columns"])
    )-protected

    data=mixed_path.read_bytes()  # opaque byte transport; no data field is decoded here.
    it=_records(data)
    try: raw_header=next(it)
    except StopIteration as exc:raise Stop("empty CSV") from exc
    header=_decode_header(raw_header)
    if header!=header_receipt.get("header"):
        raise Stop("header identity drift")
    if len(header)!=len(set(header)):raise Stop("duplicate header names")
    missing=sorted(selected-set(header))
    if missing:raise Stop(f"safe routing columns missing: {missing}")
    protected_idx=[i for i,name in enumerate(header) if name in protected]
    if len(protected_idx)!=1:raise Stop("expected exactly one protected future endpoint column")
    keep_idx=[i for i,name in enumerate(header) if name in selected]
    keep_names=[header[i] for i in keep_idx]

    output_path.parent.mkdir(parents=True,exist_ok=True)
    rows=0
    skipped_protected_fields=0
    with output_path.open("wb") as out:
        out.write((",".join(keep_names)+"\n").encode("utf-8"))
        for raw_fields in it:
            if len(raw_fields)!=len(header):
                raise Stop(f"ragged CSV record at data row {rows+1}")
            rows+=1
            skipped_protected_fields+=len(protected_idx)
            out.write(b",".join(raw_fields[i] for i in keep_idx)+b"\n")

    result={
      "schema":"structural.sw_finland_t0_byte_router_result.v1_164",
      "status":"T0_SAFE_COLUMNS_ROUTED_PROTECTED_OUTCOME_OPAQUE",
      "candidate_id":firewall["candidate_id"],
      "raw_mixed_file_sha256":raw_sha,
      "safe_projection_sha256":sha256_file(output_path),
      "data_row_count":rows,
      "safe_column_count":len(keep_names),
      "safe_columns":keep_names,
      "protected_columns":["outcome"],
      "protected_field_count_skipped":skipped_protected_fields,
      "protected_field_values_decoded":0,
      "protected_field_bytes_persisted":0,
      "outcome_values_read":0,
      "future_outcome_opened":False,
      "counts_as_empirical_evidence":False
    }
    return result

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("mixed_csv",type=Path);ap.add_argument("--header-receipt",type=Path,required=True)
    ap.add_argument("--firewall",type=Path,default=DEFAULT_FIREWALL);ap.add_argument("--safe-output",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True);a=ap.parse_args()
    try:
        h=json.loads(a.header_receipt.read_text());f=json.loads(a.firewall.read_text())
        r=route(a.mixed_csv,h,f,a.safe_output);code=0
    except (OSError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        if a.safe_output.exists():a.safe_output.unlink()
        r={"schema":"structural.sw_finland_t0_byte_router_result.v1_164","status":"STOP_T0_BYTE_ROUTER","reason":str(exc),
           "protected_field_values_decoded":0,"protected_field_bytes_persisted":0,"outcome_values_read":0,
           "future_outcome_opened":False,"counts_as_empirical_evidence":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
