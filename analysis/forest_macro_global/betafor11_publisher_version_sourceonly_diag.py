#!/usr/bin/env python3
"""Source-only BETA-FOR publisher REST version literal diagnostic; no data-file GET."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from betafor11_publisher_metadata_preintake_only import (
    FILES, RECORD, DOI, SourceStop, get_official_metadata_only,
)

SAFE_LITERAL = re.compile(r"^[A-Za-z0-9_.-]{1,40}$")
EXPECTED_LICENSE = "cc-by-sa-4.0"


def safe_scalar(value):
    if value is None:
        return None
    if isinstance(value, str) and SAFE_LITERAL.fullmatch(value):
        return value
    raise SourceStop("SOURCE_METADATA_VERSION_NON_SCALAR_OR_UNSAFE")


def audit(doc):
    if not isinstance(doc, dict) or doc.get("id") != RECORD:
        raise SourceStop("SOURCE_ORIGINAL_RECORD_WRONG")
    md = doc.get("metadata")
    if not isinstance(md, dict):
        raise SourceStop("SOURCE_ORIGINAL_METADATA_INVALID")
    if doc.get("doi", md.get("doi")) != DOI:
        raise SourceStop("SOURCE_ORIGINAL_VERSIONED_DOI_WRONG")
    if doc.get("status") != "published":
        raise SourceStop("SOURCE_ORIGINAL_NOT_PUBLISHED")
    lic = md.get("license")
    value = lic.get("id") if isinstance(lic,dict) else lic
    if value != EXPECTED_LICENSE:
        raise SourceStop("SOURCE_ORIGINAL_LICENSE_CHANGED")
    original = doc.get("files")
    if not isinstance(original, list) or len(original)!=len(FILES):
        raise SourceStop("SOURCE_ORIGINAL_FILE_COUNT_DRIFT")
    names=set()
    for f in original:
        if not isinstance(f,dict):
            raise SourceStop("SOURCE_PUBLISHER_FILE_ENTRY_INVALID")
        name=f.get("key")
        if name not in FILES or name in names:
            raise SourceStop("SOURCE_ORIGINAL_FILE_NAME_CHANGE_OR_DUPLICATE")
        if f.get("checksum")!="md5:"+FILES[name]:
            raise SourceStop("SOURCE_ORIGINAL_PUBLISHER_MD5_CHANGED")
        if type(f.get("size")) is not int or f["size"]<=0:
            raise SourceStop("SOURCE_ORIGINAL_PUBLISHER_SIZE_INVALID")
        names.add(name)
    versions=doc.get("versions")
    keys=[]
    if versions is not None:
        if not isinstance(versions,dict):
            raise SourceStop("SOURCE_VERSION_OBJECT_UNEXPECTED_TYPE")
        keys=sorted(k for k in versions if isinstance(k,str) and SAFE_LITERAL.fullmatch(k))
    return {
        "status":"SOURCE_ONLY_ORIGINAL_SIX_FILE_ID_DOI_LICENSE_CHECKSUM_PASS_VERSION_DIAG_UNRESOLVED",
        "publisher_record":RECORD,
        "published_versioned_doi":DOI,
        "six_fixed_source_filename_checksum_matches":len(names),
        "metadata_version_FIELD_PRESENT": "version" in md,
        "metadata_version_literal":safe_scalar(md.get("version")),
        "versions_object_safe_field_names_ONLY":keys,
        "no_original_source_data_member_GET":True,
        "no_original_info_or_OTU_header_or_row_READ":True,
        "original_biological_effects_scored":0,
        "original_v1_STOP_untouched":True,
        "not_a_v2_source_admission":True,
    }


def synthetic():
    case={
        "id": RECORD,"doi":DOI,"status":"published",
        "metadata":{"license":{"id":EXPECTED_LICENSE},"version":"1"},
        "files":[{"key":n,"checksum":"md5:"+md5,"size":10}
                 for n,md5 in FILES.items()],
        "versions":{"index":1}
    }
    r=audit(case)
    assert r["metadata_version_literal"]=="1"
    assert r["not_a_v2_source_admission"]
    bad=json.loads(json.dumps(case))
    bad["files"][0]["checksum"]="md5:"+("0"*32)
    try:
        audit(bad)
    except SourceStop:
        pass
    else:
        raise AssertionError("Unexpected source checksum accepted")
    print("SYNTHETIC_BETAFOR11_REST_VERSION_LITERAL_DIAGNOSTIC_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    synthetic()
    if args.test:
        return
    if args.out is None:
        p.error("--out required")
    result={
        "schema":"structural.BETAFOR11_20261119_original_publisher_rest_version_diag.v1",
        "source_get_url":"https://zenodo.org/api/records/15371332",
        "scientific_status":"SOURCE_ONLY_DIAGNOSTIC_NOT_BIOLOGICAL",
        "original_v1_version_STOP_preserved":True,
        "new_original_organism_or_community_effects":0,
        "original_source_data_files_requested":0,
    }
    try:
        result["publisher"]=audit(get_official_metadata_only())
        result["status"]=result["publisher"]["status"]
    except SourceStop as e:
        result["status"]="SOURCE_DIAG_STOP_"+str(e)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("BETAFOR11_PUBLISHER_VERSION_ONLY",result["status"])
    if result.get("publisher"):
        print("ORIGINAL_REST_METADATA_VERSION_LITERAL",repr(result["publisher"]["metadata_version_literal"]))
    print("NO_BIOLOGICAL_SOURCE_MEMBER_OR_EFFECT")


if __name__=="__main__":
    main()
