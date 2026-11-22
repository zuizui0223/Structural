#!/usr/bin/env python3
"""Traylor et al 2026 original four-study 356-wood-object CSV first header.

Read original author README/R code as method text only, no source CSV data rows.
Official CC BY published concept→version source, exact 3 files/checksums.
"""
import argparse
import collections
import csv
import hashlib
import io
import json
import re
import urllib.parse
import urllib.error
import urllib.request
from pathlib import Path

CONCEPT=19206036
VERSION=19206037
CONCEPT_DOI="10.5281/zenodo.19206036"
VERSION_DOI="10.5281/zenodo.19206037"
API=f"https://zenodo.org/api/records/{CONCEPT}"
FILES={
 "ambrosia per deadwood object data.csv":(40282,"586df99f7faded8796d26d4143058883"),
 "ambrosia beetle competition script.R":(20797,"05dccb112e503f6436e9fd4641079c8b"),
 "READ ME.txt":(1752,"c12653c9488fd7b9254ec4a086ce218b")
}
UA={"User-Agent":"Structural-Traylor2026-first-header-and-method-only/1.0",
    "Accept":"application/json,text/plain,application/octet-stream,*/*;q=0.2"}
WHITELIST=re.compile(r"(?i)(study|experiment|dataset|site|plot|tree|wood|dead|object|log|bundle|volume|month|time|duration|"
                     r"exposure|native|non.?native|exotic|beetle|species|abund|individual|count|"
                     r"presence|occurrence|origin|diam|length|habitat|sample|method|block|forest|"
                     r"field|date|collection|region|native)")
METHOD_WORDS=("site","plot","study","study id","wood","deadwood","tree species","volume",
              "month","emergence","zero","sample","replicate","forest","species","native",
              "nonnative","competition")

def get(url,cap):
    with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=40) as r:
        b=r.read(cap+1)
        if r.status!=200 or len(b)>cap:
            raise ValueError("SOURCE_ORIGINAL_FILE_HTTP_OR_SIZE_CAP_STOP")
        return b

def source():
    x=json.loads(get(API,400000))
    md=x.get("metadata") or {}
    licence=md.get("license")
    lid=licence.get("id") if isinstance(licence,dict) else licence
    if not(x.get("id")==VERSION and x.get("doi")==VERSION_DOI
           and x.get("conceptdoi")==CONCEPT_DOI
           and str(x.get("conceptrecid"))==str(CONCEPT)
           and lid=="cc-by-4.0"):
        raise ValueError("SOURCE_ORIGINAL_CONCEPT_VERSION_RIGHTS_STOP")
    files=x.get("files") or []
    if isinstance(files,dict):files=list((files.get("entries") or {}).values())
    if {f.get("key") for f in files}!=set(FILES) or len(files)!=3:
        raise ValueError("SOURCE_EXACT_THREE_ORIGINAL_FILES_STOP")
    result={}
    for f in files:
        name=f.get("key")
        size,md5=FILES[name]
        if f.get("size")!=size or f.get("checksum")!="md5:"+md5:
            raise ValueError("SOURCE_OFFICIAL_ORIGINAL_FILE_FINGERPRINT_STOP")
        href=(f.get("links") or {}).get("self") or (f.get("links") or {}).get("download")
        u=urllib.parse.urlparse(href or "")
        if u.scheme!="https" or u.hostname!="zenodo.org" or not (
             u.path.startswith(f"/api/records/{VERSION}/files/") and u.path.endswith("/content")
             or u.path.startswith("/api/files/")):
            raise ValueError("SOURCE_OFFICIAL_FILE_LINK_PATH_STOP")
        raw=get(href,size+1000)
        if len(raw)!=size or hashlib.md5(raw).hexdigest()!=md5:
            raise ValueError("SOURCE_ORIGINAL_DOWNLOADED_FILE_MD5_STOP")
        result[name]=raw
    return result

def method(filebytes):
    csvraw=filebytes["ambrosia per deadwood object data.csv"]
    # HEADER ONLY; do not tokenize any subsequent line
    head=io.BytesIO(csvraw).readline(65536)
    if len(head)>14000 or not head:
        raise ValueError("SOURCE_ORIGINAL_CSV_HEADER_SIZE_STOP")
    delim=max([",",";","\t"],key=lambda x:head.count(x.encode()))
    row=next(csv.reader([head.decode("utf-8-sig",errors="replace").rstrip("\r\n")],
                        delimiter=delim))
    unique=len(set(row))==len(row)
    if not unique or len(row)>150:
        raise ValueError("SOURCE_ORIGINAL_HEADER_DUPLICATE_OR_WIDE_STOP")
    allowed=[name[:90] for name in row if WHITELIST.search(name)]
    readme=filebytes["READ ME.txt"].decode("utf-8-sig","replace")
    code=filebytes["ambrosia beetle competition script.R"].decode("utf-8-sig","replace")
    funcs=collections.Counter(re.findall(
      r"\b(?:read\.csv|read_csv|glmmTMB|glm|glmer|lmer|lm|scale|relevel|fit|predict|"
      r"ggplot|anova|AIC|emmeans|rbind|table|aggregate|filter|select|left_join|merge)\s*\(",
      code))
    var_names=sorted(set(
      n[:85] for n in re.findall(r"\b[A-Za-z][A-Za-z0-9_.]*\$([A-Za-z][A-Za-z0-9_.]*)",code)
      if WHITELIST.search(n)
    ))
    return {
       "source_original_three_file_MD5_verified":True,
       "csv_first_header_physical_lines_read":1,
       "csv_source_subsequent_data_rows_read":0,
       "csv_source_first_header_delimiter":{"\t":"TAB",",":"COMMA",";":"SEMICOLON"}[delim],
       "csv_source_first_header_field_count":len(row),
       "generic_source_header_field_names_only":allowed[:110],
       "unclassified_first_header_field_count":len(row)-len(allowed),
       "source_original_README_line_count":len(readme.splitlines()),
       "README_method_vocabulary_presence":{w:readme.lower().count(w) for w in METHOD_WORDS},
       "original_R_script_line_count":len(code.splitlines()),
       "original_R_script_static_function_counts":dict(funcs),
       "original_R_script_generic_field_references":var_names[:90],
       "source_original_method_code_executed":False,
       "original_species_beetle_abundance_values_inspected":0,
       "ecological_models_fit":0,
       "status":"SOURCE_ORIGINAL_FIRST_CSV_HEADER_AND_METHOD_CODE_ONLY"
    }

def test():
    assert len(FILES)==3 and all(len(m)==32 for _,m in FILES.values())
    assert WHITELIST.search("native_abundance")
    assert WHITELIST.search("study_ID")
    assert not WHITELIST.search("something_unknown_Q")
    print("TRAYLOR_2026_HEADER_ONLY_SYNTHETIC_TESTS_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="traylor2026_firstheader_methodonly/receipt.json")
    a=p.parse_args()
    test()
    if a.test:return
    x={"schema":"structural.traylor2026_original_3file_CSV_header_R_method_only.v1",
       "source_concept_doi":CONCEPT_DOI,"source_version_doi":VERSION_DOI,
       "original_field_sample_or_taxon_values_read":0,
       "original_biological_effects":0,
       "source_raw_files_distributed":False,
       "prior_Ramberg2026_sci_STOP_preserved":True,
       "prior_Finland_Ecuador_BALA_GEB_sealed":True,
       "eBird_used":False,"TinyFish_used":False,
       "status":"SOURCE_ORIGINAL_METHOD_UNOPENED"}
    try:
        x["method_only"]=method(source())
        x["status"]="SOURCE_ORIGINAL_METHOD_HEADER_ONLY_PASS"
    except Exception as e:
        x["status"]="SOURCE_ORIGINAL_METHOD_DOWNLOAD_OR_SCHEMA_STOP"
        x["error_type"]=type(e).__name__
        x["error_code"]=str(e)[:150] if isinstance(e,ValueError) else ""
    pth=Path(a.out);pth.parent.mkdir(parents=True,exist_ok=True)
    pth.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("TRAYLOR_2026_ORIGINAL_METHOD_STATUS",x["status"])
    print("ORGANISM_VALUES_READ",x["original_field_sample_or_taxon_values_read"])

if __name__=="__main__":
    main()
