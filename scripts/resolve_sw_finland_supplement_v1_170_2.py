#!/usr/bin/env python3
"""Resolve SW Finland supplement transport candidates from landing HTML only."""
from __future__ import annotations
import argparse,hashlib,json,re
from html import unescape
from pathlib import Path
from urllib.parse import urljoin,urlparse

class Stop(RuntimeError): pass

def resolve(raw:bytes, *, final_url:str, content_type:str, contract:dict)->dict:
    if contract.get("schema")!="structural.sw_finland_supplement_resolver_contract.v1_170_2":
        raise Stop("contract schema drift")
    ctype=(content_type or "").split(";",1)[0].strip().lower()
    allowed=set(contract["resolver"]["accepted_content_types"])
    if ctype not in allowed: raise Stop(f"unexpected landing content type: {ctype}")
    candidates=[]
    if ctype=="application/pdf" or raw.startswith(b"%PDF"):
        candidates=[final_url]
        body_kind="pdf"
    else:
        text=raw.decode("utf-8","strict")
        body_kind="html"
        hrefs=re.findall(r"""href\s*=\s*["']([^"']+)["']""",text,flags=re.I)
        for href in hrefs:
            href=unescape(href.strip())
            absolute=urljoin(final_url,href)
            low=absolute.lower()
            if not ("ecog-05013" in low or "ecog05013" in low): continue
            path=urlparse(absolute).path.lower()
            if not any(path.endswith(s) for s in contract["resolver"]["allowed_link_suffixes"]):
                continue
            candidates.append(absolute)
        candidates=sorted(set(candidates))
    return {
      "schema":"structural.sw_finland_supplement_resolver_result.v1_170_2",
      "status":contract["success_ceiling"]["status"] if candidates else "HOLD_NO_SUPPLEMENT_FILE_CANDIDATE_FOUND",
      "candidate_id":contract["candidate_id"],
      "landing_final_url":final_url,
      "landing_content_type":ctype,
      "landing_body_kind":body_kind,
      "landing_sha256":hashlib.sha256(raw).hexdigest(),
      "candidate_urls":candidates,
      "candidate_count":len(candidates),
      "landing_body_persisted":False,
      "link_text_persisted":False,
      "supplement_table_values_parsed":0,
      "future_summary_values_parsed":0,
      "future_summary_values_persisted":0,
      "row_level_recent_outcome_opened":False,
      "counts_as_empirical_evidence":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("body",type=Path)
    p.add_argument("--metadata",type=Path,required=True)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        meta=json.loads(a.metadata.read_text())
        contract=json.loads(a.contract.read_text())
        r=resolve(a.body.read_bytes(),final_url=meta["final_url"],content_type=meta["content_type"],contract=contract);code=0
    except (OSError,UnicodeDecodeError,KeyError,ValueError,json.JSONDecodeError,Stop) as exc:
        r={
          "schema":"structural.sw_finland_supplement_resolver_result.v1_170_2",
          "status":"STOP_SUPPLEMENT_LANDING_RESOLUTION",
          "reason":str(exc),
          "supplement_table_values_parsed":0,
          "future_summary_values_parsed":0,
          "future_summary_values_persisted":0,
          "row_level_recent_outcome_opened":False,
          "counts_as_empirical_evidence":False
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True));return code

if __name__=="__main__": raise SystemExit(main())
