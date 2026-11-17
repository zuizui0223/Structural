#!/usr/bin/env python3
"""Wetherbee et al 2023 Norway 270 forest sites: publisher manifest SOURCE ONLY.

Zenodo original file metadata only, no source file content, taxa, guild or
field values. Never claim project independence from Burner Norway without ID QA.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

RECORD=8272489
DOI="10.5281/zenodo.8272489"
HOST="https://zenodo.org"
MAX_JSON=2_000_000
MAX_FILES=50
MAX_FILE_BYTES=1_000_000_000
UA="Structural-Wetherbee2023-Norway-270forest-publisher-lineage-QA/1.0"

class SourceStop(Exception):pass

def original_record_only():
    req=urllib.request.Request(
       HOST+"/api/records/"+str(RECORD),
       headers={"User-Agent":UA,"Accept":"application/json"},
       method="GET")
    try:
        with urllib.request.urlopen(req,timeout=35) as response:
            data=response.read(MAX_JSON+1)
            code=response.status
    except urllib.error.HTTPError as exc:
        raise SourceStop("SOURCE_ACCESS_STOP_HTTP_"+str(exc.code)) from exc
    except (urllib.error.URLError,OSError,TimeoutError) as exc:
        raise SourceStop("SOURCE_TRANSPORT_STOP_"+type(exc).__name__) from exc
    if code!=200 or len(data)>MAX_JSON:
        raise SourceStop("SOURCE_STOP_ZENODO_PUBLISHER_OVERSIZE_OR_STATUS")
    try:
        obj=json.loads(data.decode("utf-8"))
    except (ValueError,UnicodeError) as exc:
        raise SourceStop("SOURCE_STOP_PUBLISHER_ORIGINAL_JSON_INVALID") from exc
    return obj

def normalize_manifest(obj):
    if not isinstance(obj,dict) or str(obj.get("id"))!=str(RECORD):
        raise SourceStop("SOURCE_STOP_ORIGINAL_ZENODO_RECORD_ID")
    doi=str(obj.get("doi") or (obj.get("pids") or {}).get("doi",{}).get("identifier",""))
    if doi.casefold()!=DOI.casefold():
        raise SourceStop("SOURCE_STOP_ORIGINAL_PUBLISHER_DOI")
    fields=obj.get("files")
    if isinstance(fields,list):
        if not all(isinstance(r,dict) for r in fields):
            raise SourceStop("SOURCE_STOP_LEGACY_FILE_RECORD")
        names=[r.get("key") or r.get("filename") for r in fields]
        if any(not isinstance(k,str) or not k for k in names):
            raise SourceStop("SOURCE_STOP_ZENODO_FILE_NAME_MISSING")
        if len(set(names))!=len(names):
            raise SourceStop("SOURCE_STOP_DUPLICATE_AUTHOR_FILE_NAME")
        fs=dict(zip(names,fields))
    elif isinstance(fields,dict):
        fs=fields.get("entries",{})
    else:
        raise SourceStop("SOURCE_STOP_UNKNOWN_ZENODO_FILE_LIST")
    if not isinstance(fs,dict) or not 1<=len(fs)<=MAX_FILES:
        raise SourceStop("SOURCE_STOP_ORIGINAL_FILE_MANIFEST_COUNT")
    safe=[]
    for n,item in sorted(fs.items()):
        if not isinstance(n,str) or not n or len(n)>255 or not isinstance(item,dict):
            raise SourceStop("SOURCE_STOP_SOURCE_FILE_OBJECT")
        size=item.get("size")
        checksum=str(item.get("checksum",""))
        if not isinstance(size,int) or not 0<size<=MAX_FILE_BYTES:
            raise SourceStop("SOURCE_STOP_PUBLISHER_FILE_SIZE_UNQUALIFIED")
        if not re.fullmatch(r"(?:(?:md5|sha256|sha-256):)?[0-9a-fA-F]{32,64}",checksum):
            raise SourceStop("SOURCE_STOP_PUBLISHER_DIGEST_UNQUALIFIED")
        safe.append({
            "original_publisher_filename":n,
            "original_publisher_file_size_bytes":size,
            "original_publisher_checksum":checksum,
            "source_file_BODY_not_downloaded":True,
        })
    meta=obj.get("metadata")
    if not isinstance(meta,dict):
        raise SourceStop("SOURCE_STOP_ORIGINAL_METADATA_NOT_OBJECT")
    license_obj=meta.get("license") or (meta.get("rights") or [])
    access_obj=obj.get("access") or meta.get("access_right") or {}
    name_candidates={n:[] for n in ("community_species","traits_guild",
                                   "study_project_site_effort","forest_resources",
                                   "source_methods_codebook")}
    terms={
      "community_species":r"beetle|species|community|abundan|capture|occurr",
      "traits_guild":r"trait|morph|guild|predator|diet|feed",
      "study_project_site_effort":r"site|plot|study|project|trap|effort|method|period",
      "forest_resources":r"deadwood|stand|forest|wood|tree|habitat|environment|climat",
      "source_methods_codebook":r"readme|metadata|legend|codebook|dictionary|method"
    }
    for f in safe:
        lowered=f["original_publisher_filename"].lower()
        for label,regex in terms.items():
            if re.search(regex,lowered):
                name_candidates[label].append(f["original_publisher_filename"])
    return {
       "original_record_id":RECORD,
       "original_publisher_DOI":doi,
       "original_publisher_title_exists":bool(meta.get("title")),
       "original_publisher_license_metadata_present":bool(license_obj),
       "original_access_metadata_present":bool(access_obj),
       "original_files_count":len(safe),
       "original_file_manifest":safe,
       "source_FILENAME_ONLY_candidate_roles":name_candidates,
       "source_filename_CANNOT_ESTABLISH_BIOLOGICAL_JOIN":True,
       "original_270_site_ids_NOT_EXAMINED":True,
       "original_8_project_lineages_NOT_IDENTIFIED_FROM_CONTENT":True,
       "overlap_with_prior_Burner_Norway_original_NOT_ESTABLISHED":True,
       "source_contents_original_NOT_DOWNLOADED":True,
    }

def synthetic():
    fake={"id":RECORD,"doi":DOI,
          "metadata":{"title":"Forest beetles","license":{"id":"cc-by-4.0"}},
          "files":[
            {"key":"community.csv","size":9000,"checksum":"md5:"+"a"*32},
            {"key":"traits.csv","size":8000,"checksum":"md5:"+"b"*32},
            {"key":"README.txt","size":3000,"checksum":"md5:"+"c"*32},
          ]}
    x=normalize_manifest(fake)
    assert x["original_files_count"]==3
    assert x["source_contents_original_NOT_DOWNLOADED"]
    assert x["overlap_with_prior_Burner_Norway_original_NOT_ESTABLISHED"]
    assert len(x["source_FILENAME_ONLY_candidate_roles"]["community_species"])==1
    try:
        normalize_manifest({**fake,"files":fake["files"]+[fake["files"][0]]})
    except SourceStop:
        pass
    else:raise AssertionError("duplicate original names were not rejected")
    assert normalize_manifest({**fake,"files":{
      "entries":{x["key"]:x for x in fake["files"]}}})["original_files_count"]==3
    print("SYNTHETIC_NORWAY270_ZENODO_PUBLISHER_MANIFEST_AND_LINEAGE_FIREWALL_PASS")

def original():
    out={"status":"SOURCE_NOT_READ",
         "original_species_site_guild_environmental_BIOLOGICAL_VALUES_READ":False}
    try:
        src=normalize_manifest(original_record_only())
        out["metadata"]=src
        out["status"]="ORIGINAL_PUBLISHER_FILE_MANIFEST_QUALIFIED_BIOLOGY_AND_LINEAGE_UNVERIFIED"
    except SourceStop as exc:
        out["status"]=str(exc)
        out["SOURCE_STOP_NOT_ECOLOGICAL_NULL"]=True
    return out

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    opts=p.parse_args()
    synthetic()
    if opts.test:return
    if opts.out is None:p.error("--out required")
    out={
       "schema":"structural.Wetherbee2023_Norway_270forest_original_manifest_sourceonly.v1",
       "precommit":"docs/FOREST_BEETLE_WETHERBEE_NORWAY270_SOURCE_AND_LINEAGE_PRESPEC_20261117.md",
       "original_publisher":original(),
       "new_ecological_result_produced":False,
       "prior_Piccini_Georgia_Finland_Burner_Kriegel_PREDICTS_NEON_BALA_GEB_biology_UNOPENED":True,
       "eBird_used":False,"TinyFish_used":False
    }
    opts.out.mkdir(parents=True,exist_ok=True)
    (opts.out/"Wetherbee2023_Norway270_Zenodo_original_manifest_sourceonly.json").write_text(
      json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
