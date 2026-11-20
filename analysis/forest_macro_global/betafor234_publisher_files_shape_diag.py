#!/usr/bin/env python3
"""BETA-FOR234 record JSON descriptor-SHAPE ONLY after frozen v1 metadata STOP."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from betafor234_original_zenodo_metadata_only import (
    URL,RECORD,DOI,LICENSE,SourceStop,published_record_GET_only,
)
PRESPEC="docs/FOREST_MACRO_BETAFOR234_FILES_SHAPE_DIAGNOSTIC_PREFREEZE_20261120.md"

def audit(doc):
    if not isinstance(doc,dict) or doc.get("id")!=RECORD:
        raise SourceStop("SOURCE_WRONG_RECORD_ID")
    md=doc.get("metadata")
    if not isinstance(md,dict):
        raise SourceStop("SOURCE_METADATA_NOT_OBJECT")
    if doc.get("doi",md.get("doi"))!=DOI or doc.get("status")!="published":
        raise SourceStop("SOURCE_WRONG_DOI_OR_PUBLICATION_STATE")
    license=md.get("license")
    lic=license.get("id") if isinstance(license,dict) else license
    if lic!=LICENSE:
        raise SourceStop("SOURCE_PUBLISHER_LICENSE_CHANGED")
    if "files" not in doc:
        dtype="absent";length=None;counts=None
    elif doc["files"] is None:
        dtype="null";length=None;counts=None
    elif isinstance(doc["files"],list):
        dtype="list";length=len(doc["files"])
        counts={k:sum(isinstance(f,dict) and k in f for f in doc["files"])
                for k in ("key","checksum","size")}
    else:
        dtype="other";length=None;counts=None
    raw=json.dumps(doc,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()
    return {
        "source_publisher_record":RECORD,
        "source_publisher_versioned_DOI":DOI,
        "publisher_original_license":LICENSE,
        "original_record_JSON_canonical_sha256_NOT_file_digest":hashlib.sha256(raw).hexdigest(),
        "source_files_field_shape_ONLY":dtype,
        "source_files_entry_count_ONLY":length,
        "source_nonvalue_descriptor_key_presence_counts_ONLY":counts,
        "source_access_field_present":("access" in doc),
        "source_links_field_present":("links" in doc),
        "source_original_file_downloads":0,
        "source_original_names_digests_ID_values_EXPORTED":False,
        "not_original_file_MD5_verified":True,
        "no_response_or_sample_data_READ":True,
        "new_ecological_effects":0,
        "v1_original_STOP_preserved":True,
        "status":(
            "SOURCE_DIAGNOSTIC_FILE_LIST_PRESENT_NOT_ADMITTED"
            if dtype=="list" and length and length>0 else
            "SOURCE_PUBLISHER_NO_PUBLIC_FILE_DESCRIPTOR"
        ),
    }

def synthetic():
    doc={"id":RECORD,"doi":DOI,"status":"published",
         "metadata":{"license":{"id":LICENSE}},"files":[]}
    r=audit(doc)
    assert r["status"]=="SOURCE_PUBLISHER_NO_PUBLIC_FILE_DESCRIPTOR"
    assert r["source_files_entry_count_ONLY"]==0
    d=json.loads(json.dumps(doc));d["files"]=[{"key":"NONEXPORT_TEST","size":15,"checksum":"md5:1"}]
    r=audit(d)
    assert r["source_files_entry_count_ONLY"]==1
    assert "NONEXPORT_TEST" not in json.dumps(r)
    d["metadata"]["license"]={"id":"restricted"}
    try:audit(d)
    except SourceStop:pass
    else:raise AssertionError("wrong publisher license admitted")
    print("SYNTHETIC_BETAFOR234_NOFILE_DESCRIPTOR_SHAPE_FIREWALL_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:p.error("--out required")
    out={"schema":"structural.BETAFOR234_public_record_descriptor_shape_diagnostic.v1",
         "prespec":PRESPEC,"v1_STOP_unchanged":True,
         "source_file_GET":0,"source_OTU_rows_READ":0,
         "new_biodiversity_effects":0}
    try:
        out["source"]=audit(published_record_GET_only())
        out["status"]=out["source"]["status"]
    except SourceStop as ex:
        out["status"]="SOURCE_DIAGNOSTIC_STOP_"+str(ex)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("BETAFOR234_FILES_SHAPE_ONLY",out["status"])
    if "source" in out:
        print("PUBLISHER_FILES_FIELD_TYPE",out["source"]["source_files_field_shape_ONLY"])
        print("PUBLISHER_DESCRIPTOR_COUNT",out["source"]["source_files_entry_count_ONLY"])
    print("NO_NEW_ECOLOGICAL_SCORE_NO_ORIGINAL_FILE_MEMBER_GET")

if __name__=="__main__":main()
