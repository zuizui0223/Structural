#!/usr/bin/env python3
"""Audit exactly frozen Hopson author R/README *methods only*, zero biology.

Never open observation or layout rows. Report count-scaling excerpts only;
no outcome/statistic, model fit, or confirmatory claim.
"""
import hashlib
import io
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import quote
import argparse

ARCHIVE="https://zenodo.org/records/4960267/files/"
FILES={
    "author_R":("Thesis Code Experimental - for data dryad.R",
                "dadab72ec94583cdbf7197cc3eb09ea0"),
    "readme":("README_for_Thesis Code Experimental - for data dryad.txt",
              "332b97a8e81ff3eb109dbc7a1b93137b"),
}
ALLOWED_TERMS=re.compile(
    r"(tet|eupl|samp|dilut|dil[.]vol|sub[.]samp|density|densit|per[.]ml)",re.I
)
def fetch_exact(kind):
    name,expected=FILES[kind]
    url=ARCHIVE+quote(name,safe="")+"?download=1"
    req=urllib.request.Request(url,headers={"User-Agent":"StructuralResearch/1.225"})
    with urllib.request.urlopen(req,timeout=35) as f:
        raw=f.read(40000)
    if hashlib.md5(raw).hexdigest()!=expected:
        raise ValueError("Author methods MD5 drift")
    return raw

def audit_source(name,raw):
    if hashlib.md5(raw).hexdigest()!=FILES[name][1]:
        raise ValueError("Methods-source md5 mismatch")
    # Latin-1 is a reversible Unicode fallback for copied author notes;
    # digest verification ensures no alternate version is silently substituted.
    try: content=raw.decode("utf-8-sig")
    except UnicodeDecodeError:content=raw.decode("latin-1")
    lines=content.splitlines()
    excerpts=[{"line":i,"text":line.strip()[:300]}
              for i,line in enumerate(lines,1)
              if ALLOWED_TERMS.search(line)]
    return {"total_lines":len(lines),"method_keyword_lines":excerpts,
            "raw_MD5":hashlib.md5(raw).hexdigest()}

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    d={kind:audit_source(kind,fetch_exact(kind)) for kind in FILES}
    result={"schema":"structural.hopson_prey_assay_source_method_only.v1_225",
       "status":"PASS_FROZEN_AUTHOR_METHODS_NOT_BIOLOGICAL_ANALYSIS",
       "sources":d,
       "original_observation_data_file_fetched":False,
       "ecological_response_rows_opened":0,
       "model_fits":0,
       "source_guidance":"This receipt captures author method source excerpts, not yet an interpreted prey-density formula.",
       "GEB_scientific_HOLD":True,
       "eBird_used":False}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__":main()
