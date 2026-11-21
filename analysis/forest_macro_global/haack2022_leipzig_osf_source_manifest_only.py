#!/usr/bin/env python3
"""Haack et al. 2022 OSF node 9dhzw metadata-only input gate.

Never downloads original species/count/trap/temperature/tree data files.
Runs once on official OSF public API; emits anonymous file inventories only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request

NODE_ID="9dhzw"
API_NODE="https://api.osf.io/v2/nodes/9dhzw/"
API_PROVIDER="https://api.osf.io/v2/nodes/9dhzw/files/"
API_STORAGE="https://api.osf.io/v2/nodes/9dhzw/files/osfstorage/"
MAX_JSON_BYTES=2*1024*1024
MAX_PAGES=5
PRESPEC="docs/FOREST_LEIPZIG2022_OSF_9DHZW_SOURCE_ONLY_GATE_PRESPEC_20261119.md"
SOURCE_DATA_FORMATS={".csv",".tsv",".xlsx",".xls",".rds",".rdata",".txt",".zip",".ods"}
USER_AGENT="Structural-forest-leipzig-source-only/1.0"
class SourceStop(Exception):
    pass

def source_json(url):
    u=urllib.parse.urlsplit(url)
    if u.scheme!="https" or u.hostname!="api.osf.io":
        raise SourceStop("SOURCE_OSF_NOT_EXACT_OFFICIAL_API_HOST")
    if not (u.path in ("/v2/nodes/9dhzw/","/v2/nodes/9dhzw/files/")
            or u.path.startswith("/v2/nodes/9dhzw/files/osfstorage/")):
        raise SourceStop("SOURCE_OSF_NOT_FROZEN_PROJECT_OR_STORAGE_PATH")
    req=urllib.request.Request(
        url,headers={"User-Agent":USER_AGENT,"Accept":"application/vnd.api+json, application/json"},
        method="GET"
    )
    try:
        with urllib.request.urlopen(req,timeout=65) as response:
            final=urllib.parse.urlsplit(response.geturl())
            if final.scheme!="https" or final.hostname!="api.osf.io":
                raise SourceStop("SOURCE_OSF_ORIGINAL_API_REDIRECT_DIFFERENT_HOST")
            length=response.headers.get("Content-Length")
            if length:
                try:
                    if int(length)>MAX_JSON_BYTES:
                        raise SourceStop("SOURCE_OSF_METADATA_JSON_TOO_LARGE")
                except ValueError:
                    pass
            raw=response.read(MAX_JSON_BYTES+1)
            ctype=(response.headers.get("Content-Type") or "").lower()
            if "text/html" in ctype or len(raw)>MAX_JSON_BYTES:
                raise SourceStop("SOURCE_OSF_METADATA_NONJSON_OR_OVERSIZE_STOP")
    except urllib.error.HTTPError as e:
        raise SourceStop(f"SOURCE_OSF_OFFICIAL_API_HTTP_{e.code}_STOP") from None
    except (urllib.error.URLError,TimeoutError,OSError):
        raise SourceStop("SOURCE_OSF_ORIGINAL_PUBLIC_API_TRANSPORT_STOP") from None
    try:
        result=json.loads(raw)
    except (ValueError,UnicodeError):
        raise SourceStop("SOURCE_OSF_ORIGINAL_API_RESPONSE_NOT_VALID_JSON") from None
    if not isinstance(result,dict):
        raise SourceStop("SOURCE_OSF_ORIGINAL_METADATA_NOT_JSON_OBJECT")
    return result,{"original_publisher_metadata_bytes":len(raw),
                   "original_publisher_metadata_sha256":hashlib.sha256(raw).hexdigest()}

def verify_project(payload):
    data=payload.get("data")
    if not isinstance(data,dict):
        raise SourceStop("SOURCE_OSF_ORIGINAL_NODE_OBJECT_UNAVAILABLE")
    if data.get("id")!=NODE_ID or data.get("type")!="nodes":
        raise SourceStop("SOURCE_OSF_ORIGINAL_NODE_ID_OR_TYPE_DRIFT")
    attrs=data.get("attributes") or {}
    if not isinstance(attrs,dict) or attrs.get("public") is not True:
        raise SourceStop("SOURCE_OSF_ORIGINAL_NODE_NOT_EXPLICITLY_PUBLIC")
    return {"source_node_id":NODE_ID,"source_OSF_api_resource_type_verified":True,
            "source_original_node_explicit_public":True,
            "source_project_title_public_metadata_only":str(attrs.get("title") or "")[:180],
            "source_publisher_original_node_created_time_available":bool(attrs.get("date_created")),
            "source_publisher_original_node_modified_time_available":bool(attrs.get("date_modified"))}

def inventory_provider(payload):
    data=payload.get("data")
    if not isinstance(data,list):
        raise SourceStop("SOURCE_OSF_ORIGINAL_STORAGE_DATA_NOT_LIST")
    providers=[]
    for ent in data:
        if not isinstance(ent,dict):
            raise SourceStop("SOURCE_OSF_ORIGINAL_PROVIDER_RECORD_MALFORMED")
        fields=(ent.get("attributes") or {})
        if not isinstance(fields,dict):
            raise SourceStop("SOURCE_OSF_ORIGINAL_PROVIDER_ATTR_MALFORMED")
        providers.append(str(fields.get("name") or "").strip())
    return {"official_node_public_file_provider_count":len(data),
            "official_node_storage_provider_NAME_OSFSTORAGE_present":
                "osfstorage" in [x.casefold() for x in providers]}

def safe_file_ext(name):
    if not isinstance(name,str):
        return "<unknown>"
    name=name.rsplit("/",1)[-1].lower()
    suffix="."+name.rsplit(".",1)[-1] if "." in name else "<none>"
    if len(suffix)>12 or any(x in suffix for x in ("\r","\n")):
        return "<other>"
    return suffix

def inventory_storage(pages):
    known=set()
    formats=Counter()
    sizes=[]
    files=0
    folders=0
    blank_ids=0
    for page in pages:
        arr=page.get("data")
        if not isinstance(arr,list):
            raise SourceStop("SOURCE_OSF_STORAGE_ORIGINAL_DATA_NOT_LIST")
        for item in arr:
            if not isinstance(item,dict):
                raise SourceStop("SOURCE_OSF_ORIGINAL_STORAGE_RECORD_NOT_JSON")
            idval=item.get("id")
            if not idval or idval in known:
                blank_ids+=1
                continue
            known.add(idval)
            attrs=item.get("attributes") or {}
            if not isinstance(attrs,dict):
                raise SourceStop("SOURCE_OSF_ORIGINAL_FILE_METADATA_ATTR_INVALID")
            kind=str(attrs.get("kind") or "").casefold()
            if kind=="folder":
                folders+=1
                continue
            if kind!="file":
                continue
            files+=1
            name=attrs.get("name")
            formats[safe_file_ext(name)]+=1
            v=attrs.get("size")
            if isinstance(v,int) and not isinstance(v,bool) and v>=0:
                sizes.append(v)
    original_data_candidates=sum(v for k,v in formats.items() if k in SOURCE_DATA_FORMATS)
    return {
      "original_root_STORAGE_files":files,
      "original_root_STORAGE_folders_not_recursively_opened":folders,
      "original_root_STORAGE_duplicate_or_blank_file_ids":blank_ids,
      "original_root_STORAGE_file_extensions_COUNTS":dict(sorted(formats.items())),
      "original_root_STORAGE_file_size_nonmissing_n":len(sizes),
      "original_root_STORAGE_file_sizes_SUM":sum(sizes),
      "original_root_STORAGE_candidate_data_files_BY_SUFFIX_ONLY":original_data_candidates,
      "original_folder_children_UNKNOWN_not_zero":folders>0,
      "original_file_names_or_file_IDs_NOT_EXPORTED":True,
      "original_species_or_trap_ORIGINAL_FILE_CONTENT_ROWS_OPENED":0,
      "original_source_region_tree_height_microclimate_columns_IDENTIFIED":False,
    }

def original_once():
    result={}
    node,node_sha=source_json(API_NODE)
    result["original_OSF_verified_project"]=verify_project(node)
    result["original_OSF_node_json_receipt"]=node_sha
    providers,providers_sha=source_json(API_PROVIDER)
    provider=inventory_provider(providers)
    result["original_OSF_official_public_providers"]=provider
    result["original_OSF_provider_json_receipt"]=providers_sha
    if not provider["official_node_storage_provider_NAME_OSFSTORAGE_present"]:
        raise SourceStop("SOURCE_OSF_ORIGINAL_OSFSTORAGE_NOT_IN_PUBLIC_PROVIDER_LIST")
    pages=[]
    seen=set()
    url=API_STORAGE
    page_receipts=[]
    while url and len(pages)<MAX_PAGES:
        if url in seen:
            raise SourceStop("SOURCE_OSF_ORIGINAL_STORAGE_PAGINATION_CYCLE")
        seen.add(url)
        p,receipt=source_json(url)
        pages.append(p)
        page_receipts.append(receipt)
        nxt=(p.get("links") or {}).get("next")
        if nxt and not isinstance(nxt,str):
            raise SourceStop("SOURCE_OSF_ORIGINAL_NEXT_PAGE_URL_INVALID")
        if nxt:
            split=urllib.parse.urlsplit(nxt)
            if (split.scheme!="https" or split.hostname!="api.osf.io"
                or not split.path.startswith("/v2/nodes/9dhzw/files/osfstorage/")):
                raise SourceStop("SOURCE_OSF_ORIGINAL_NEXT_PAGE_NOT_SAME_STORAGE")
        url=nxt
    if url is not None:
        raise SourceStop("SOURCE_OSF_ORIGINAL_STORAGE_PAGINATION_GT5_PAGES")
    result["original_OSF_STORAGE_pagination_pages_opened"]=len(pages)
    result["original_OSF_STORAGE_page_metadata_sha_receipts"]=page_receipts
    result["original_OSF_storage_root_inventory"]=inventory_storage(pages)
    x=result["original_OSF_storage_root_inventory"]
    if x["original_root_STORAGE_candidate_data_files_BY_SUFFIX_ONLY"]>0:
        result["status"]="SOURCE_HAACK2022_OSF_PUBLIC_FILE_MANIFEST_PASS"
    elif x["original_root_STORAGE_folders_not_recursively_opened"]>0:
        result["status"]="SOURCE_HAACK2022_OSF_ROOT_ONLY_FOLDER_CHILDREN_UNKNOWN_HOLD"
    else:
        result["status"]="SOURCE_HAACK2022_OSF_NO_ELIGIBLE_TABLE_METADATA_HOLD"
    return result

def known_truth():
    node={"data":{"type":"nodes","id":"9dhzw","attributes":
        {"public":True,"title":"Test","date_created":"2020-01-01"}}}
    assert verify_project(node)["source_original_node_explicit_public"]
    providers={"data":[{"attributes":{"name":"osfstorage"}}]}
    assert inventory_provider(providers)["official_node_storage_provider_NAME_OSFSTORAGE_present"]
    pages=[{"data":[
        {"id":"private_a","attributes":{"kind":"file","name":"PRIVATE_SPECIES.csv","size":60}},
        {"id":"private_b","attributes":{"kind":"file","name":"PRIVATE_SITE.xlsx","size":90}},
        {"id":"private_folder","attributes":{"kind":"folder","name":"secret"}}]}]
    result=inventory_storage(pages)
    assert result["original_root_STORAGE_candidate_data_files_BY_SUFFIX_ONLY"]==2
    assert result["original_root_STORAGE_files"]==2
    assert result["original_root_STORAGE_folders_not_recursively_opened"]==1
    assert "PRIVATE_SPECIES" not in json.dumps(result)
    assert "PRIVATE_SITE" not in json.dumps(result)
    assert result["original_species_or_trap_ORIGINAL_FILE_CONTENT_ROWS_OPENED"]==0
    print("SYNTHETIC_OSF_PUBLIC_METADATA_ONLY_SOURCE_MANIFEST_NO_BIOLOGY_PASS")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--test",action="store_true")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:parser.error("--out required")
    result={
      "schema":"structural.forest_haack2022_OSF9dhzw_official_public_root_metadata_only.v1",
      "precommit":PRESPEC,
      "original_paper_DOI":"10.3390/insects13020161",
      "original_OSF_project_identifier":"9dhzw",
      "source_original_field_study_Leipzig_one_forest":True,
      "source_original_canopy_understory_preservative_confound":True,
      "source_original_canopy_20m_25m_windows_same_preservative_AUTHOR_REPORTED":True,
      "source_original_logged_temperature_or_deadwood_resource_UNVERIFIED":True,
      "source_original_species_OTU_OR_trap_measurement_DATA_ROWS_READ":0,
      "source_previous_England_NFI_Carpathian_Finland_PREDICTS_Thai_NEON_BALA_GEB_scores_UNCHANGED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    try:
        v=original_once()
        result["source_original_publisher_public_root_metadata_receipts_ONLY"]=v
        result["status"]=v["status"]
    except SourceStop as exc:
        result["status"]=str(exc)
        result["source_metadata_access_OR_schema_STOP_not_ecological_null"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Haack2022_Leipzig_OSF9dhzw_original_public_metadata_only.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("ORIGINAL_LEIPZIG_OSF9DHZW_SOURCE_METADATA_ONLY",result["status"])
    print("NO_BEETLE_SPECIES_ORIGINAL_RESPONSES_OR_SAMPLE_VALUES_OPENED")
if __name__=="__main__":
    main()
