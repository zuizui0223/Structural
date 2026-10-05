#!/usr/bin/env python3
"""Audit only the first physical line of the mixed Finnish eider file."""

from __future__ import annotations
import argparse, csv, hashlib, io, json, urllib.request
from pathlib import Path

class Stop(RuntimeError): pass

def digest(path: Path, algo: str) -> str:
    h=hashlib.new(algo)
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def first_line_bytes(path: Path, max_bytes: int=65536) -> tuple[bytes,int]:
    with path.open("rb") as f:
        data=f.read(max_bytes)
    idx=data.find(b"\n")
    if idx<0: raise Stop("no first-line terminator within limit")
    line=data[:idx+1]
    return line,idx+1

def infer_delimiter(text: str) -> str:
    candidates=["\t",",",";"]
    counts={d:text.count(d) for d in candidates}
    d=max(candidates,key=lambda z:counts[z])
    if counts[d]==0: raise Stop("could not infer delimiter")
    return d

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--work-file",type=Path,required=True)
    ap.add_argument("--header-output",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()

    c=json.loads(a.contract.read_text())
    if c.get("schema")!="structural.finnish_eider_mixed_header_contract.v1_152":
        raise Stop("contract schema drift")
    src=c["source_file"]

    req=urllib.request.Request(src["download_url"],headers={"User-Agent":"Structural-header-only-audit/1.0"})
    with urllib.request.urlopen(req,timeout=120) as resp, a.work_file.open("wb") as out:
        while True:
            b=resp.read(1024*1024)
            if not b: break
            out.write(b)

    if a.work_file.stat().st_size!=int(src["size_bytes"]): raise Stop("file size drift")
    md5=digest(a.work_file,"md5")
    sha=digest(a.work_file,"sha256")
    if md5!=src["md5"]: raise Stop("file MD5 drift")

    first,nbytes=first_line_bytes(a.work_file)
    # Decode only the header bytes. No byte after nbytes is decoded or parsed.
    header_text=first.decode("utf-8-sig").rstrip("\r\n")
    delim=infer_delimiter(header_text)
    headers=next(csv.reader(io.StringIO(header_text),delimiter=delim))
    headers=[h.strip() for h in headers]
    if any(not h for h in headers): raise Stop("blank header")
    if len(headers)!=len(set(headers)): raise Stop("duplicate header")

    expected=c["published_expected_headers"]
    missing=[h for h in expected if h not in headers]
    if missing: raise Stop("published expected headers missing: "+",".join(missing))

    lower={h.casefold():h for h in headers}
    group_flags=[h for h in headers if any(t in h.casefold() for t in ("group","redistrib","reconstruct","imput"))]
    effort_flags=[h for h in headers if any(t in h.casefold() for t in ("survey","effort","counted","visited","sampled","observer","method"))]

    out={
      "schema":"structural.finnish_eider_mixed_header_result.v1_152",
      "status":"EXACT_MIXED_FILE_HEADER_FROZEN_DATA_ROWS_UNOPENED",
      "candidate_id":c["candidate_id"],
      "file":{
        "name":src["name"],"size_bytes":a.work_file.stat().st_size,
        "md5":md5,"sha256":sha
      },
      "header":{
        "delimiter_repr":repr(delim),
        "header_byte_count_including_newline":nbytes,
        "column_count":len(headers),
        "columns":headers,
        "published_expected_headers_missing":[],
        "pos2_header_present":"pos2" in headers,
        "group_or_reconstruction_flag_headers":group_flags,
        "survey_or_effort_flag_headers":effort_flags
      },
      "data_row_semantic_values_opened":0,
      "Eider_pairs_values_opened":0,
      "Island_ID_values_opened":0,
      "pos2_values_opened":0,
      "source_loss_events_computed":0,
      "source_leverage_effects_computed":0,
      "raw_file_retained_in_artifact":False,
      "counts_as_empirical_source_loss_evidence":False
    }

    a.header_output.parent.mkdir(parents=True,exist_ok=True)
    a.header_output.write_text(json.dumps(out["header"],indent=2,sort_keys=True)+"\n")
    receipt=dict(out)
    receipt["header_output_sha256"]=digest(a.header_output,"sha256")
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    # Raw mixed file is deleted by caller; never upload it.
    return 0

if __name__=="__main__": raise SystemExit(main())
