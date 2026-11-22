#!/usr/bin/env python3
"""Cours et al 2026 three-context forest beetle original author Rmd method audit.

Fetch exact one Zenodo-publisher native original Rmd and verify MD5/size.
Never fetch RData, execute R code, parse any organism/site observation or fit.
"""
import argparse
import collections
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REC=17927769
DOI="10.5281/zenodo.17927769"
INDEX=f"https://zenodo.org/api/records/{REC}"
NAME="Analysis_Cascade_Decline_Salvage.Rmd"
MD5="083c1aef2e0acb519675f52dcbbf92f7"
SIZE=80911
UA={"User-Agent":"Structural-Cours2026-author-method-only/1.0","Accept":"*/*"}

def request(url,maxbytes):
    with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=35) as h:
        b=h.read(maxbytes+1)
        if h.status!=200 or len(b)>maxbytes:
            raise ValueError("SOURCE_ORIGINAL_ZENODO_HTTP_OR_SIZE_STOP")
        return b

def original_method():
    j=json.loads(request(INDEX,300000))
    if j.get("id")!=REC or j.get("doi")!=DOI:
        raise ValueError("SOURCE_ORIGINAL_ZENODO_ID_STOP")
    md=j.get("metadata") or {}
    lic=md.get("license")
    lic_id=lic.get("id") if isinstance(lic,dict) else lic
    if lic_id!="cc-by-4.0":
        raise ValueError("SOURCE_ORIGINAL_LICENSE_NOT_PUBLIC_CC_BY_STOP")
    fs=j.get("files") or []
    if isinstance(fs,dict):
        fs=list((fs.get("entries") or {}).values())
    if len(fs)!=2 or {r.get("key") for r in fs}!={NAME,"Decline_Data.RData"}:
        raise ValueError("SOURCE_ORIGINAL_FILE_ROSTER_STOP")
    f=next(r for r in fs if r.get("key")==NAME)
    if f.get("size")!=SIZE or f.get("checksum")!="md5:"+MD5:
        raise ValueError("SOURCE_ORIGINAL_METHOD_PUBLISHED_MD5_STOP")
    href=(f.get("links") or {}).get("self") or (f.get("links") or {}).get("download")
    u=urllib.parse.urlparse(href or "")
    if (u.scheme!="https" or u.hostname!="zenodo.org" or
        not re.fullmatch(r"/api/records/17927769/files/[^/]+/content",u.path)):
        raise ValueError("SOURCE_ORIGINAL_METHOD_LINK_ORIGIN_STOP")
    b=request(href,110000)
    if len(b)!=SIZE or hashlib.md5(b).hexdigest()!=MD5:
        raise ValueError("SOURCE_ORIGINAL_RMD_MD5_MISMATCH_STOP")
    return b.decode("utf-8-sig",errors="replace")

def method_only(src):
    # The author script is Rmd: never execute it or evaluate model formulas.
    terms=re.findall(r"\b(?:load|read\.csv|readRDS|read\.table|read_csv|glmmTMB|lmer|glmer|psem|sem|inext|iNEXT|rda|adonis2|vegdist|lm|glm|gam|scale|select|left_join|merge)\s*\(",src)
    source_members=sorted(set(x[:120] for x in re.findall(
        r"(?:load|readRDS|read\.csv|read_csv)\s*\(\s*['\"]([^'\"]{1,160})['\"]",src)))
    # Bounded field-name inventory from $-access only, ASCII/R identifier grammar.
    match=re.findall(r"\b[A-Za-z][A-Za-z0-9_.]*\$([A-Za-z][A-Za-z0-9_.]*)",src)
    pattern=re.compile(r"(site|plot|forest|type|species|wood|dead|decay|mort|declin|salvag|volume|"
                       r"trem|height|diam|dbh|region|guild|trait|rich|soil|longitude|latitude|"
                       r"area|density|cover|effort|sample|trap|year|env|abun|site)",re.I)
    semantic=sorted({x[:70] for x in match if pattern.search(x)})
    return {
        "source_author_Rmd_original_bytes":SIZE,
        "source_file_original_md5":MD5,
        "original_script_executed":False,
        "source_data_RData_downloaded":False,
        "script_line_count":len(src.splitlines()),
        "direct_import_argument_basenames_from_author_source_ONLY":source_members[:20],
        "referenced_dataframe_field_candidates_method_tokens_ONLY":semantic[:110],
        "candidate_dataframe_field_token_total":len(semantic),
        "fixed_R_method_function_counts":dict(collections.Counter(
            s.split("(")[0].strip() for s in terms)),
        "original_population_or_beetle_numeric_values_read":0,
        "new_ecological_effects_estimated":0,
        "status":"SOURCE_ORIGINAL_METHOD_RMD_CHECKSUM_AND_CODE_TOKENS_ONLY"
    }

def known_truth():
    example='load("Decline_Data.RData")\n asd$Site plot$DEADWOOD_v0 glmmTMB(a~b)\n'
    r=method_only(example)
    assert r["direct_import_argument_basenames_from_author_source_ONLY"]==["Decline_Data.RData"]
    assert "Site" in r["referenced_dataframe_field_candidates_method_tokens_ONLY"]
    assert r["original_population_or_beetle_numeric_values_read"]==0
    print("COURS2026_AUTHOR_RMD_METHOD_ONLY_KNOWN_TRUTH_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="cours2026_original_Rmd_methodonly/receipt.json")
    a=p.parse_args()
    known_truth()
    if a.test:return
    obj={"schema":"structural.cours2026_original_author_Rmd_method_only.v1",
         "prior_Cours_publisher_CC_BY_rights_verified":True,
         "original_RData_file_contents_read":0,
         "original_scientific_organism_scores":0,
         "prior_Ramberg2026_scientific_STOP_preserved":True,
         "prior_Ecuador_BALA_GEB_Finland_sealed":True,
         "eBird_used":False,"TinyFish_used":False,
         "status":"SOURCE_ORIGINAL_RMD_METHOD_UNOPENED"}
    try:
        obj["source_method_vocabulary"]=method_only(original_method())
        obj["status"]="SOURCE_ORIGINAL_RMD_METHOD_AUDIT_PASS"
    except Exception as e:
        obj["status"]="SOURCE_ORIGINAL_RMD_ACCESS_OR_PARSE_STOP"
        obj["error_type"]=type(e).__name__
        obj["error_code"]=str(e)[:150] if isinstance(e,ValueError) else ""
    f=Path(a.out);f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("COURS2026_METHOD_GATE",obj["status"])
    print("RDATA_OPENED",obj["original_RData_file_contents_read"])
    print("NEW_ECOLOGY",obj["original_scientific_organism_scores"])

if __name__=="__main__":
    main()
