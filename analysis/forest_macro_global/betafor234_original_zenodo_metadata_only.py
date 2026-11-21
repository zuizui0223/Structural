#!/usr/bin/env python3
"""BETA-FOR 234-patch parent record metadata discovery, NO original file GET.

This is a different SOURCE VERSION from the earlier 99-patch 2025 seasonal
panel, but the SAME 11 parent forests (not independent ecology replication).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

URL="https://zenodo.org/api/records/18467123"
RECORD=18467123
DOI="10.5281/zenodo.18467123"
LICENSE="cc-by-4.0"
PRESPEC="docs/FOREST_MACRO_BETAFOR234_PAIRED_ALPHA_BETA_SOURCE_PREINTAKE_20261120.md"
SAFE_NAME=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_. -]{0,140}$")
SAFE_VERSION=re.compile(r"^[A-Za-z0-9_.-]{1,40}$")
HASH=re.compile(r"^(?:md5:[0-9a-fA-F]{32}|sha256:[0-9a-fA-F]{64})$")


class SourceStop(Exception): pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None


def parse_record_only(doc):
    if not isinstance(doc,dict) or doc.get("id")!=RECORD:
        raise SourceStop("SOURCE_PUBLISHER_RECORD_ID_MISMATCH")
    metadata=doc.get("metadata")
    if not isinstance(metadata,dict) or doc.get("doi",metadata.get("doi"))!=DOI:
        raise SourceStop("SOURCE_PUBLISHER_VERSIONED_DOI_MISMATCH")
    if doc.get("status")!="published":
        raise SourceStop("SOURCE_PUBLICATION_STATUS_NOT_PUBLISHED")
    lic=metadata.get("license")
    lid=lic.get("id") if isinstance(lic,dict) else lic
    if not isinstance(lid,str) or lid.casefold()!=LICENSE:
        raise SourceStop("SOURCE_PUBLISHER_LICENSE_NOT_EXPECTED_PUBLIC_CC_BY")
    items=doc.get("files")
    if not isinstance(items,list) or not items or len(items)>100:
        raise SourceStop("SOURCE_PUBLISHER_FILE_DESCRIPTORS_INVALID_COUNT")
    rows=[];seen=set()
    for f in items:
        if not isinstance(f,dict):
            raise SourceStop("SOURCE_PUBLISHER_ORIGINAL_FILE_DESCRIPTOR_INVALID")
        name=f.get("key")
        if not isinstance(name,str) or not SAFE_NAME.fullmatch(name) or name in seen:
            raise SourceStop("SOURCE_PUBLISHER_ORIGINAL_FILE_NAME_INVALID_OR_DUPLICATE")
        seen.add(name)
        digest=f.get("checksum")
        if not isinstance(digest,str) or not HASH.fullmatch(digest):
            raise SourceStop("SOURCE_PUBLISHER_ORIGINAL_FILE_CHECKSUM_INVALID")
        size=f.get("size")
        if type(size) is not int or not 0<size<=10**10:
            raise SourceStop("SOURCE_PUBLISHER_ORIGINAL_FILE_SIZE_INVALID")
        rows.append({"publisher_original_filename":name,
                     "publisher_reported_bytes":size,
                     "publisher_published_checksum":digest})
    rows.sort(key=lambda x:x["publisher_original_filename"])
    version=metadata.get("version")
    if version is not None and (not isinstance(version,str) or not SAFE_VERSION.fullmatch(version)):
        raise SourceStop("SOURCE_PUBLISHER_VERSION_LITERAL_UNSAFE")
    return {
        "status":"BETAFOR234_PUBLISHER_FILE_MANIFEST_METADATA_ONLY_PASS_NOT_BIOLOGICAL",
        "published_record":RECORD,
        "version_specific_original_doi":DOI,
        "publisher_version_literal":version,
        "publisher_public_license":lid,
        "original_file_count":len(rows),
        "publisher_original_file_roster":rows,
        "publisher_manifest_sha256":hashlib.sha256(
            json.dumps(rows,sort_keys=True,separators=(",",":")).encode()
        ).hexdigest(),
        "original_file_member_GET_count":0,
        "original_physical_patch_IDs_or_sample_ROWS_read":0,
        "original_OTU_counts_OR_taxon_ids_READ":0,
        "new_biodiversity_effect_estimates":0,
        "234_patch_count_AUTHOR_REPORTED_not_verified":True,
        "11_parent_forests_shared_with_BETAFOR99":True,
        "not_independent_external_forest_replication":True,
    }


def published_record_GET_only():
    req=urllib.request.Request(
        URL,headers={"Accept":"application/json",
                     "User-Agent":"Structural-BETAFOR234-original-index-only/1.0"})
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=45) as q:
            if q.status!=200:
                raise SourceStop("SOURCE_PUBLISHER_INDEX_HTTP_NOT200")
            raw=q.read(1024*1024+1)
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_PUBLISHER_INDEX_HTTP_"+str(e.code)) from None
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise SourceStop("SOURCE_PUBLISHER_INDEX_TRANSPORT_"+type(e).__name__) from None
    if len(raw)>1024*1024:
        raise SourceStop("SOURCE_PUBLISHER_INDEX_TOO_LARGE")
    try:return json.loads(raw.decode("utf-8"))
    except (ValueError,UnicodeError):
        raise SourceStop("SOURCE_PUBLISHER_INDEX_JSON_PARSE_STOP") from None


def synthetic():
    doc={"id":RECORD,"doi":DOI,"status":"published",
         "metadata":{"license":{"id":LICENSE}},
         "files":[{"key":"method.csv","size":12345,"checksum":"md5:"+"a"*32}]}
    q=parse_record_only(doc)
    assert q["original_file_count"]==1
    bad=json.loads(json.dumps(doc));bad["files"][0]["checksum"]="bad"
    try: parse_record_only(bad)
    except SourceStop: pass
    else:raise AssertionError("Original checksum corruption accepted")
    bad=json.loads(json.dumps(doc));bad["metadata"]["license"]={"id":"cc-by-sa-4.0"}
    try: parse_record_only(bad)
    except SourceStop: pass
    else:raise AssertionError("Changed public source license accepted")
    print("SYNTHETIC_BETAFOR234_ORIGINAL_ZENODO_INDEX_METADATA_ONLY_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out required")
    obj={"schema":"structural.BETAFOR234_original_publisher_first_index_v1",
         "prespec":PRESPEC,
         "original_biological_response_rows_opened":0,
         "new_ecological_effects":0,
         "original_99patch_v1_v2_v3_gates_unchanged":True,
         "eBird_used":False,"TinyFish_used":False}
    try:
        obj["source_publisher"]=parse_record_only(published_record_GET_only())
        obj["status"]=obj["source_publisher"]["status"]
    except SourceStop as e:
        obj["status"]="BETAFOR234_SOURCE_METADATA_STOP_"+str(e)
        obj["does_not_mean_biological_null"]=True
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("BETAFOR234_ORIGINAL_INDEX_ONLY",obj["status"])
    print("PARENT_DATA_FILE_GET=0; OTU_BIOLOGICAL_ROWS=0; FITS=0")


if __name__=="__main__":
    main()
