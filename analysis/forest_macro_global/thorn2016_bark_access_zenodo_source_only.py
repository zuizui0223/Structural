#!/usr/bin/env python3
"""Thorn2016 12-paired-windthrow bark access: Zenodo original SOURCE ONLY.

One public publisher metadata GET, one exact original file GET per source file.
Only publisher hashes, CSV header (generic names), byte/line counts inspected.
Original beetle species/abundance, plot/tree/treatment row values NEVER parsed.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RECORD=13905995
DOI="10.5281/zenodo.13905995"
PAPER="10.1016/j.foreco.2015.12.044"
HOST="https://zenodo.org"
EXPECTED={"Babund.csv","Bdist.csv"}
MAX_META=2_000_000
MAX_BYTES=500_000
MAX_HEADER=65536
AGENT="Structural-Thorn2016-Zenodo-original-bark-source-QA/1.0"
GENERIC={
    "site_plot":{"site","siteid","plot","plotid","block","blockid",
                 "windthrow","replicate","replication"},
    "experimental_tree":{"tree","treeid","stem","stemid","log","logid",
                         "individualtree","treeno"},
    "treatment":{"treatment","bark","barktreatment","debarking",
                 "scratch","barkscratch","type","control"},
    "sample_method":{"year","samplingyear","sample","sampleid","run",
                     "period","method","effort","trap","trapid","trapdays"},
    "species_abundance":{"species","taxon","taxonid","abundance",
                         "count","nindividuals","richness"},
}
class SourceStop(Exception):pass

def get_record():
    url=HOST+"/api/records/"+str(RECORD)
    req=urllib.request.Request(url,method="GET",headers={
        "User-Agent":AGENT,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=30) as res:
            body=res.read(MAX_META+1)
            status=res.status
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_METADATA_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise SourceStop("SOURCE_METADATA_TRANSPORT_"+type(e).__name__) from e
    if status!=200 or len(body)>MAX_META:
        raise SourceStop("SOURCE_PUBLISHER_JSON_STATUS_OR_OVERSIZE")
    try:x=json.loads(body.decode("utf-8"))
    except (ValueError,UnicodeError) as e:
        raise SourceStop("SOURCE_PUBLISHER_JSON_INVALID") from e
    if not isinstance(x,dict):raise SourceStop("SOURCE_PUBLISHER_JSON_NOT_OBJECT")
    return x

def manifest(record):
    if str(record.get("id"))!=str(RECORD):
        raise SourceStop("SOURCE_PUBLISHER_RECORD_ID_DRIFT")
    doi=str(record.get("doi") or
            ((record.get("pids") or {}).get("doi") or {}).get("identifier",""))
    if doi.casefold()!=DOI.casefold():
        raise SourceStop("SOURCE_PUBLISHER_EXACT_DOI_NOT_MATCHED")
    files=record.get("files")
    if isinstance(files,list):
        if len(files)!=2:raise SourceStop("SOURCE_FILE_RECORD_COUNT_DRIFT")
        byname={str(f.get("key") or f.get("filename") or ""):f for f in files}
    elif isinstance(files,dict):
        byname=files.get("entries",{})
    else:raise SourceStop("SOURCE_NO_PUBLISHER_FILE_DIRECTORY")
    if not isinstance(byname,dict) or set(byname)!=EXPECTED:
        raise SourceStop("SOURCE_PUBLISHER_TWO_FILE_MANIFEST_DRIFT")
    rows=[]
    for name in sorted(EXPECTED):
        f=byname[name]
        length=f.get("size")
        checksum=str(f.get("checksum",""))
        if not isinstance(length,int) or not (0<length<=MAX_BYTES):
            raise SourceStop("SOURCE_ORIGINAL_BYTES_NOT_ELIGIBLE")
        m=re.fullmatch(r"(?:(md5|sha256|sha-256):)?([a-fA-F0-9]{32}|[a-fA-F0-9]{64})",
                       checksum)
        if not m:raise SourceStop("SOURCE_ORIGINAL_DIGEST_INVALID")
        digest=m.group(2).lower()
        if len(digest) not in (32,64):
            raise SourceStop("SOURCE_ORIGINAL_DIGEST_LENGTH_INVALID")
        rows.append({"name":name,"size":length,
                     "digest":digest,"checksum_algorithm":"md5" if len(digest)==32 else "sha256"})
    meta=record.get("metadata") or {}
    if not isinstance(meta,dict):raise SourceStop("SOURCE_METADATA_RECORD_INVALID")
    access=record.get("access") or {}
    return {"publisher_record":RECORD,"publisher_DOI":DOI,
       "publisher_license":meta.get("license",meta.get("rights")),
       "publisher_access":access,
       "publisher_title_metadata_present":bool(meta.get("title")),
       "original_two_files":rows,
       "original_biological_rows_UNREAD":True}

def fetch_file(entry):
    name=entry["name"]
    url=HOST+"/records/"+str(RECORD)+"/files/"+urllib.parse.quote(name,safe="")+"?download=1"
    req=urllib.request.Request(url,method="GET",headers={
        "User-Agent":AGENT,"Accept":"text/csv,text/plain,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=35) as res:
            raw=res.read(MAX_BYTES+1);status=res.status
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_ORIGINAL_FILE_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise SourceStop("SOURCE_ORIGINAL_FILE_TRANSPORT_"+type(e).__name__) from e
    if status!=200 or len(raw)!=entry["size"]:
        raise SourceStop("SOURCE_ORIGINAL_FILE_LENGTH_OR_STATUS")
    digest=(hashlib.md5(raw).hexdigest() if entry["checksum_algorithm"]=="md5"
            else hashlib.sha256(raw).hexdigest())
    if digest!=entry["digest"]:
        raise SourceStop("SOURCE_ORIGINAL_PUBLISHER_CHECKSUM_MISMATCH")
    return raw

def header_only(raw):
    first=io.BytesIO(raw).readline(MAX_HEADER+1)
    if len(first)>MAX_HEADER or not first.endswith((b"\n",b"\r")):
        raise SourceStop("SOURCE_ORIGINAL_CSV_HEADER_NOT_COMPLETE")
    try:line=first.decode("utf-8-sig").rstrip("\r\n")
    except UnicodeError as e:raise SourceStop("SOURCE_ORIGINAL_CSV_HEADER_NOT_UTF8") from e
    sep=max((",",";","\t"),key=line.count)
    if line.count(sep)==0:raise SourceStop("SOURCE_ORIGINAL_CSV_DELIMITER_NOT_IDENTIFIED")
    try:hdr=next(csv.reader([line],delimiter=sep,strict=True))
    except csv.Error as e:raise SourceStop("SOURCE_ORIGINAL_CSV_HEADER_INVALID") from e
    if len(hdr)<2 or len(hdr)>20000:
        raise SourceStop("SOURCE_ORIGINAL_CSV_HEADER_WIDTH")
    norm=[re.sub("[^a-z0-9]","",s.casefold()) for s in hdr]
    fields={k:sorted(set(n for n in norm if n in allowed))
            for k,allowed in GENERIC.items()}
    return {
      "original_header_columns":len(hdr),
      "header_delimiter_category":{",":"comma",";":"semicolon","\t":"tab"}[sep],
      "exact_safe_generic_header_names_only":{k:v for k,v in fields.items() if v},
      "number_newlines_in_original_source":raw.count(b"\n"),
      "header_first_field_recognized_sample_key":
          norm[0] if norm[0] in {"site","plot","plotid","tree","treeid",
                              "treatment","sample","sampleid","id","code"} else None,
      "first_line_cannot_certify_author_physical_plot_treatment_identity":True,
      "species_labels_and_numerical_beetle_rows_NOT_EXPORTED":True,
      "biological_rows_INSPECTED":0,
    }

def original():
    ans={"status":"SOURCE_NOT_OPENED","new_original_beetle_species_effect":False,
         "previous_Finland_Germany_PREDICTS_BALA_GEB_UNTOUCHED":True}
    try:
        info=manifest(get_record())
        ans["publisher"]=info
        rows=[]
        for item in info["original_two_files"]:
            try:body=fetch_file(item)
            except SourceStop as e:
                rows.append({"source_name":item["name"],"status":str(e)})
                ans["original_source_structure"]=rows
                ans["status"]="SOURCE_PUBLISHER_FILE_ACCESS_STOP_NOT_ECOLOGICAL_NULL"
                return ans
            rows.append({"source_name":item["name"],
                          "publisher_byte_checksum_VERIFIED":True,
                          **header_only(body)})
        ans["original_source_structure"]=rows
        ans["status"]="SOURCE_MANIFEST_HEADERS_AND_LINE_COUNTS_ONLY_PHYSICAL_PLOT_JOIN_UNVERIFIED"
    except SourceStop as e:
        ans["status"]=str(e)
        ans["SOURCE_STOP_NOT_ECOLOGICAL_NULL"]=True
    return ans

def known_truth():
    fake={"id":RECORD,"doi":DOI,
        "metadata":{"title":"Source controlled trees","license":{"id":"cc-by-4.0"}},
        "files":{"entries":{
           n:{"size":100,"checksum":"md5:"+("a" if n=="Babund.csv" else "b")*32}
           for n in EXPECTED}}}
    r=manifest(fake)
    assert r["publisher_record"]==RECORD and len(r["original_two_files"])==2
    x=header_only(b"Plot;TreeID;Treatment;Species;Abundance\n1;T;A;Beetle;1\n")
    assert x["original_header_columns"]==5
    assert x["exact_safe_generic_header_names_only"]["treatment"]==["treatment"]
    assert x["biological_rows_INSPECTED"]==0
    assert x["number_newlines_in_original_source"]==2
    assert all(len(v["digest"])==32 for v in r["original_two_files"])
    print("SYNTHETIC_THORN2016_ZENODO_SOURCE_MD5_AND_HEADER_METHOD_FIREWALL_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    output={"schema":"structural.Thorn2016_12plot_3bark_treatment_Zenodo_sourceonly.v1",
        "precommit":"docs/FOREST_BEETLE_THORN2016_BARK_ACCESS_ORIGINAL_ZENODO_SOURCE_GATE_PRESPEC_20261117.md",
        "original":original(),
        "no_biodiversity_effect_or_p_estimated":True,
        "no_old_original_cohorts_rescored":True,
        "eBird_used":False,"TinyFish_used":False}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Thorn2016_bark_access_12paired_plots_sourceonly.json").write_text(
        json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
