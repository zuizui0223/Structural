#!/usr/bin/env python3
"""Consume only the frozen 1,275-island mammal macro pilot response.

The exact 2024 Appendix-1 bytes are re-downloaded and verified. The full
semicolon-delimited header is decoded once to freeze species-column identity.
For data records, only the routing field is decoded unless the island belongs
to the exact frozen pilot set. Confirmatory and excluded record remainders are
never Unicode-decoded or CSV-parsed.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,os,re,tempfile
from pathlib import Path

from scripts.fetch_global_mammal_response_opaque_v1_17 import (
    GlobalMammalTransportError,
    transport as transport_v117,
)

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/global_mammals_macro_pilot_response_contract_v1_65.json"
DIGITS=re.compile(r"^[0-9]+$")

class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def canon_id_bytes(raw:bytes)->str:
    x=raw.strip(b" \t\r\n")
    if len(x)>=2 and x[:1]==b'"' and x[-1:]==b'"':
        x=x[1:-1].replace(b'""',b'"')
    try:s=x.decode("utf-8")
    except UnicodeDecodeError as e: raise Stop("routing ID is not UTF-8") from e
    s=s.strip()
    if DIGITS.fullmatch(s) is None: raise Stop("routing ID is not unsigned decimal")
    return str(int(s,10))

def iter_records(raw:bytes):
    """Yield logical CSV record bytes, excluding terminal LF/CRLF."""
    start=0; in_quotes=False; i=0
    while i<len(raw):
        b=raw[i]
        if b==34:
            if in_quotes and i+1<len(raw) and raw[i+1]==34:
                i+=2; continue
            in_quotes=not in_quotes; i+=1; continue
        if b==10 and not in_quotes:
            rec=raw[start:i]
            if rec.endswith(b"\r"): rec=rec[:-1]
            yield rec
            start=i+1
        i+=1
    if in_quotes: raise Stop("unterminated quoted field")
    if start<len(raw):
        rec=raw[start:]
        if rec.endswith(b"\r"): rec=rec[:-1]
        if rec: yield rec

def first_field_bytes(record:bytes,delimiter:int=59)->bytes:
    out=bytearray(); in_quotes=False; i=0; at_start=True
    while i<len(record):
        b=record[i]
        if in_quotes:
            if b==34:
                if i+1<len(record) and record[i+1]==34:
                    out.append(34); i+=2; continue
                in_quotes=False; i+=1; continue
            out.append(b); i+=1; continue
        if at_start and b==34:
            in_quotes=True; at_start=False; i+=1; continue
        if b==delimiter: return bytes(out)
        out.append(b); at_start=False; i+=1
    if in_quotes: raise Stop("unterminated first field")
    return bytes(out)

def parse_full_record(record:bytes,delimiter:str=";")->list[str]:
    try:text=record.decode("utf-8-sig")
    except UnicodeDecodeError as e: raise Stop("pilot/header record is not UTF-8") from e
    rows=list(csv.reader(io.StringIO(text),delimiter=delimiter,quotechar='"'))
    if len(rows)!=1: raise Stop("logical record parsed to non-single CSV row")
    return rows[0]

def load_routing(path:Path,expected_sha:str,expected_n:int)->tuple[list[str],dict[str,dict]]:
    if sha(path)!=expected_sha: raise Stop(f"{path.name} SHA mismatch")
    with path.open("r",encoding="utf-8",newline="") as h:
        rows=list(csv.DictReader(h))
    if len(rows)!=expected_n: raise Stop(f"{path.name} row-count drift")
    if not rows or tuple(rows[0].keys())!=("ID","block_id","bioregion"): raise Stop("routing header drift")
    order=[]; meta={}
    for r in rows:
        iid=str(r["ID"]).strip()
        if DIGITS.fullmatch(iid) is None: raise Stop("routing ID syntax drift")
        iid=str(int(iid,10))
        if iid in meta: raise Stop("duplicate routing ID")
        if not r["block_id"] or not r["bioregion"]: raise Stop("blank routing metadata")
        order.append(iid); meta[iid]=r
    return order,meta

def consume(response_bytes:bytes,pilot_order:list[str],pilot_meta:dict[str,dict],
            confirm_order:list[str],contract:dict)->tuple[list[tuple],list[tuple],dict]:
    records=iter(iter_records(response_bytes))
    try:header_rec=next(records)
    except StopIteration as e: raise Stop("empty response file") from e
    header=parse_full_record(header_rec)
    expected_species=int(contract["response_identity"]["expected_species_columns"])
    if len(header)!=expected_species+1: raise Stop("species header field-count drift")
    species=header[1:]
    if any(not str(x).strip() for x in species): raise Stop("blank species header")
    if len(set(species))!=len(species): raise Stop("duplicate species header identity")

    pilot_set=set(pilot_order); conf_set=set(confirm_order)
    if pilot_set & conf_set: raise Stop("pilot/confirmatory routing overlap")
    if len(pilot_set|conf_set)!=int(contract["routing"]["final_population_islands"]):
        raise Stop("final routing population drift")

    counts=[0]*expected_species
    pilot_values={}
    data_rows=0; pilot_decoded=0; confirm_seen=0; excluded_seen=0
    for rec in records:
        if not rec: continue
        data_rows+=1
        iid=canon_id_bytes(first_field_bytes(rec,59))
        if iid in pilot_set:
            fields=parse_full_record(rec)
            if len(fields)!=expected_species+1: raise Stop("pilot field-count drift")
            vals=fields[1:]
            row=[]
            for j,v in enumerate(vals):
                if v not in ("0","1"): raise Stop("pilot target outside 0/1")
                y=int(v); row.append(y); counts[j]+=y
            if iid in pilot_values: raise Stop("duplicate pilot row in response")
            pilot_values[iid]=row; pilot_decoded+=1
        elif iid in conf_set:
            confirm_seen+=1
        else:
            excluded_seen+=1

    if data_rows!=int(contract["response_identity"]["expected_data_rows"]):
        raise Stop("response data-row count drift")
    if pilot_decoded!=len(pilot_order) or set(pilot_values)!=pilot_set:
        raise Stop("not every pilot island was decoded exactly once")
    if confirm_seen!=len(confirm_order): raise Stop("confirmatory routing count drift")
    if excluded_seen!=int(contract["routing"]["excluded_rows"]): raise Stop("excluded response-row count drift")

    m=int(contract["species_universe"]["minimum_presence"]); n=len(pilot_order)
    selected=[j for j,c in enumerate(counts) if c>=m and n-c>=m]
    universe=[(si,j+2,species[j],counts[j],n-counts[j]) for si,j in enumerate(selected)]
    matrix=[]
    for iid in pilot_order:
        meta=pilot_meta[iid]; vals=pilot_values[iid]
        matrix.append((iid,meta["block_id"],meta["bioregion"],[vals[j] for j in selected]))
    positives=sum(counts[j] for j in selected)
    receipt={
      "schema":"structural.global_mammals_macro_pilot_response_result.v1_65",
      "status":"MACRO_MAMMAL_PILOT_RESPONSE_CONSUMED_AND_SPECIES_UNIVERSE_FROZEN",
      "candidate_id":contract["candidate_id"],"analysis_route":contract["analysis_route"],
      "response_data_rows_seen":data_rows,"source_species_columns":expected_species,
      "species_header_fields_decoded":expected_species,"pilot_islands_decoded":pilot_decoded,
      "pilot_occurrence_values_decoded":pilot_decoded*expected_species,
      "confirmatory_islands_seen_routing_only":confirm_seen,"confirmatory_occurrence_values_decoded":0,
      "excluded_islands_seen_routing_only":excluded_seen,"excluded_occurrence_values_decoded":0,
      "species_threshold_m":m,"focal_species":len(selected),"pilot_matrix_rows":n*len(selected),
      "pilot_matrix_positive":positives,"pilot_matrix_negative":n*len(selected)-positives,
      "pilot_response_consumed":True,"confirmatory_response_authorized":False,
      "counts_as_fresh_confirmation":False,"fresh_system_denominator_contribution":0,"fresh_status_restored":False
    }
    return universe,matrix,receipt

def write_outputs(universe,matrix,universe_path:Path,matrix_path:Path):
    universe_path.parent.mkdir(parents=True,exist_ok=True)
    with universe_path.open("w",encoding="utf-8",newline="") as h:
        w=csv.writer(h,lineterminator="\n")
        w.writerow(["species_index","source_column_index","species_name","pilot_presence","pilot_absence"])
        w.writerows(universe)
    labels=[f"S{int(row[0]):05d}" for row in universe]
    with matrix_path.open("w",encoding="utf-8",newline="") as h:
        w=csv.writer(h,lineterminator="\n")
        w.writerow(["ID","block_id","bioregion"]+labels)
        for iid,block,region,vals in matrix:w.writerow([iid,block,region]+vals)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--pilot-routing",type=Path,required=True)
    ap.add_argument("--confirmatory-routing",type=Path,required=True)
    ap.add_argument("--species-universe",type=Path,required=True)
    ap.add_argument("--pilot-matrix",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args(); semantic_started=False
    try:
        c=json.loads(a.contract.read_text())
        if c.get("schema")!="structural.global_mammals_macro_pilot_response_contract.v1_65": raise Stop("contract schema drift")
        pilot_order,pilot_meta=load_routing(a.pilot_routing,c["routing"]["pilot_ids_sha256"],c["routing"]["pilot_islands"])
        conf_order,_=load_routing(a.confirmatory_routing,c["routing"]["confirmatory_ids_sha256"],c["routing"]["confirmatory_islands"])
        target=c["response_identity"]
        transport_contract={"candidate_id":c["candidate_id"],"target":{
            "name":target["name"],"dryad_file_id":target["dryad_file_id"],"download_url":target["download_url"],
            "expected_size_bytes":target["expected_size_bytes"],"expected_sha256":target["expected_sha256"]},
            "attempt_policy":{"credentialed_attempt_limit":1,"blind_endpoint_retry_authorized":False,"alternate_file_id_retry_authorized":False}}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/target["name"]
            tr=transport_v117(p,contract=transport_contract,token=os.environ.get("DRYAD_TOKEN",""))
            if tr.get("status")!="EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED": raise Stop("exact response transport did not qualify")
            raw=p.read_bytes(); semantic_started=True
            universe,matrix,result=consume(raw,pilot_order,pilot_meta,conf_order,c)
        write_outputs(universe,matrix,a.species_universe,a.pilot_matrix)
        result["species_universe_sha256"]=sha(a.species_universe);result["pilot_matrix_sha256"]=sha(a.pilot_matrix)
        result["raw_response_retained"]=False;code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,GlobalMammalTransportError,Stop) as e:
        result={"schema":"structural.global_mammals_macro_pilot_response_result.v1_65",
          "status":"TERMINAL_AFTER_PILOT_SEMANTIC_ACCESS" if semantic_started else "HOLD_BEFORE_PILOT_SEMANTIC_ACCESS",
          "reason":str(e),"pilot_response_consumed":semantic_started,"confirmatory_occurrence_values_decoded":0,
          "excluded_occurrence_values_decoded":0,"confirmatory_response_authorized":False,
          "counts_as_fresh_confirmation":False,"fresh_system_denominator_contribution":0,"fresh_status_restored":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True));return code

if __name__=="__main__": raise SystemExit(main())
