#!/usr/bin/env python3
"""Original Kortmann2026 Zenodo 17775805 publisher index ONLY: no insect data."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

URL="https://zenodo.org/api/records/17775805"
RECORD=17775805
DOI="10.5281/zenodo.17775805"
PRESPEC="docs/FOREST_MACRO_KORTMANN2026_17775805_CANONICAL_SOURCE_INDEX_PREFREEZE_20261120.md"
LICENSES={"cc-by-4.0","cc0-1.0","cc-by-sa-4.0"}
FILE=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._() +\-]{0,150}$")
HASH=re.compile(r"^(md5:[a-fA-F0-9]{32}|sha256:[a-fA-F0-9]{64})$")
VERSION=re.compile(r"^[a-zA-Z0-9._\-]{1,40}$")

class SourceStop(Exception):pass
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def parse(doc):
    if not isinstance(doc,dict) or doc.get("id")!=RECORD:
        raise SourceStop("SOURCE_ORIGINAL_RECORD_WRONG")
    md=doc.get("metadata")
    if not isinstance(md,dict):
        raise SourceStop("SOURCE_ORIGINAL_METADATA_SCHEMA")
    if doc.get("doi",md.get("doi"))!=DOI or doc.get("status")!="published":
        raise SourceStop("SOURCE_ORIGINAL_DOI_OR_PUBLICATION_STATUS")
    lic=md.get("license")
    lid=lic.get("id") if isinstance(lic,dict) else lic
    if not isinstance(lid,str) or lid.casefold() not in LICENSES:
        raise SourceStop("SOURCE_ORIGINAL_LICENSE_NOT_PREDECLARED")
    ver=md.get("version")
    if ver is not None and (not isinstance(ver,str) or not VERSION.fullmatch(ver)):
        raise SourceStop("SOURCE_ORIGINAL_PUBLISHER_VERSION_UNSAFE")
    fs=doc.get("files")
    if not isinstance(fs,list) or not 1<=len(fs)<=100:
        raise SourceStop("SOURCE_ORIGINAL_FILE_DESCRIPTOR_EMPTY_OR_INVALID")
    seen=set();rows=[]
    for v in fs:
        if not isinstance(v,dict):
            raise SourceStop("SOURCE_ORIGINAL_FILE_DESCRIPTOR_NOT_OBJECT")
        name=v.get("key");size=v.get("size");digest=v.get("checksum")
        if not isinstance(name,str) or not FILE.fullmatch(name) or name in seen:
            raise SourceStop("SOURCE_ORIGINAL_FILENAME_UNSAFE_OR_DUPLICATE")
        if type(size) is not int or not 0<size<=10**10:
            raise SourceStop("SOURCE_ORIGINAL_FILE_SIZE_INVALID")
        if not isinstance(digest,str) or not HASH.fullmatch(digest):
            raise SourceStop("SOURCE_ORIGINAL_DIGEST_UNSUPPORTED")
        seen.add(name)
        rows.append({"publisher_file_name":name,
                     "publisher_reported_bytes":size,
                     "publisher_original_checksum_UNVERIFIED_BYTES":digest})
    rows.sort(key=lambda z:z["publisher_file_name"])
    return{
        "status":"SOURCE_CANONICAL_INDEX_READY_NO_BIOLOGY",
        "original_record":RECORD,"versioned_doi":DOI,"publisher_version_literal":ver,
        "publisher_public_license":lid,"source_file_count":len(rows),
        "original_publisher_files_UNVERIFIED_BYTES":rows,
        "original_publisher_manifest_SHA256":hashlib.sha256(json.dumps(
            rows,separators=(",",":"),sort_keys=True).encode()).hexdigest(),
        "independence_from_BETAFOR_not_yet_tested":True,
        "no_original_file_GET":True,
        "no_organism_data_or_plot_ID_READ":True,
        "original_physical_sampling_denominator_NOT_VERIFIED":True,
        "sample_coverage_metadata_NOT_VERIFIED":True,
        "new_organismal_models_fitted":0,
    }

def download_index_only():
    req=urllib.request.Request(URL,headers={
        "Accept":"application/json",
        "User-Agent":"Structural-Kortmann2026-Official-Zenodo-Publisher-IndexOnly/1.0"
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=45) as r:
            if r.status!=200:raise SourceStop("SOURCE_PUBLISHER_HTTP_NOT200")
            raw=r.read(1024*1024+1)
    except urllib.error.HTTPError as ex:
        raise SourceStop("SOURCE_PUBLISHER_HTTP_"+str(ex.code)) from None
    except (urllib.error.URLError,TimeoutError,OSError) as ex:
        raise SourceStop("SOURCE_PUBLISHER_TRANSPORT_"+type(ex).__name__) from None
    if not raw or len(raw)>1024*1024:
        raise SourceStop("SOURCE_PUBLISHER_EMPTY_OR_LARGE_JSON")
    try:return json.loads(raw.decode("utf8"))
    except (UnicodeError,ValueError):
        raise SourceStop("SOURCE_PUBLISHER_JSON_DECODING_FAILED") from None

def synthetic():
    d={"id":RECORD,"doi":DOI,"status":"published",
       "metadata":{"license":{"id":"cc-by-4.0"}},
       "files":[{"key":"meta.csv","checksum":"md5:"+"a"*32,"size":123}]}
    assert parse(d)["source_file_count"]==1
    for edit in [
        lambda x: x["files"].clear(),
        lambda x: x["metadata"].update(license={"id":"restricted"}),
        lambda x: x["files"][0].update(checksum="wrong"),
        lambda x: x.update(doi="10.5281/zenodo.other"),
    ]:
        v=json.loads(json.dumps(d))
        edit(v)
        try:parse(v)
        except SourceStop:pass
        else:raise AssertionError("source safety drift accepted")
    print("SYNTHETIC_KORTMANN2026_ORIGINAL_INDEX_ONLY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:p.error("--out required")
    result={
        "schema":"structural.Kortmann2026_canonical_17775805_zenodo_first_public_index.v1",
        "prespec":PRESPEC,"new_ecological_effect":False,
        "biological_data_member_download_count":0,
        "source_species_or_OTU_response_rows_READ":0,
        "shared_BETAFOR_sources_UNTOUCHED":True,
        "historical_17775804_http302_STOP_unchanged": True,
        "canonical_target_17775805_diagnosed_before_this_GET": True,
    }
    try:
        result["publisher"]=parse(download_index_only())
        result["status"]=result["publisher"]["status"]
    except SourceStop as e:
        result["status"]="SOURCE_CANONICAL_PUBLISHER_STOP_"+str(e)
        result["not_biological_zero"]=True
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("KORTMANN2026_PUBLISHER_INDEX_ONLY",result["status"])
    print("NO_ORIGINAL_SOURCE_MEMBER_OTU_ROWS_OR_BIOLOGICAL_EFFECTS")

if __name__=="__main__":main()
