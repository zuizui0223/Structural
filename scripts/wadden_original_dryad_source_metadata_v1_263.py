#!/usr/bin/env python3
"""Dryad Wadden Sea artificial-island source VERSION/FILES metadata only.

Does not fetch CSV data or biological outcomes. The downloaded metadata is not
treated as independent ecological confirmation or an estimate of colonization.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

SCHEMA="structural.wadden_source_metadata_audit.v1_263"
SOURCE_DOI="10.5061/dryad.gxd2547z3"

class SourceStop(Exception):
    pass


def _original_get_json(url):
    info=urllib.parse.urlsplit(url)
    if info.scheme!="https" or info.hostname!="datadryad.org" or not info.path.startswith("/api/v2/"):
        raise SourceStop("Unauthorized Dryad source route")
    req=urllib.request.Request(url,headers={"User-Agent":"Structural-Wadden-source-only/1.0",
                                            "Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=50) as source:
        body=source.read(2_000_001)
    if len(body)>2_000_000:raise SourceStop("Publisher metadata JSON larger than 2 MB")
    try: return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError,json.JSONDecodeError) as e: raise SourceStop("Invalid official metadata JSON") from e


def _versions(v):
    if isinstance(v,list): return v
    if not isinstance(v,dict):raise SourceStop("Dryad versions metadata not dict or list")
    if isinstance(v.get("versions"),list): return v["versions"]
    embedded=v.get("_embedded",{})
    if isinstance(embedded,dict):
        for key,value in embedded.items():
            if "version" in key.casefold() and isinstance(value,list):return value
    raise SourceStop("Dryad response did not expose version collection")


def _choose_latest_version(response):
    items=_versions(response)
    if not items:raise SourceStop("No published versions")
    versions=[]
    for row in items:
        if not isinstance(row,dict): continue
        version_number=row.get("versionNumber",row.get("version_number"))
        ident=row.get("id")
        if ident is None:
            href=(row.get("_links",{}).get("self",{}) or {}).get("href","")
            m=re.search(r"/versions/(\d+)",href)
            ident=int(m.group(1)) if m else None
        try: n=int(version_number);ident=int(ident)
        except (TypeError,ValueError): continue
        versions.append((n,ident))
    if not versions:raise SourceStop("Published version number and file-list id not source-identifiable")
    versions.sort()
    if len({v[0] for v in versions})!=len(versions):
        raise SourceStop("Ambiguous duplicated original published version numbers")
    return versions[-1],len(versions)


def _extract_file_rows(api_object):
    if isinstance(api_object,list):return api_object
    if not isinstance(api_object,dict):raise SourceStop("Unexpected Dryad file-list metadata")
    items=api_object.get("files")
    if isinstance(items,list):return items
    embedded=api_object.get("_embedded",{})
    if isinstance(embedded,dict):
        for key,value in embedded.items():
            if "file" in key.casefold() and isinstance(value,list):return value
    raise SourceStop("Dryad version file-list schema unsupported")


def validate_source(dataset,version_response,file_response,contract):
    if contract["schema"]!="structural.wadden_experimental_island_source_preintake.v1_263":
        raise SourceStop("Protocol was not frozen before response source access")
    raw_doi=dataset.get("doi") or dataset.get("identifier") or ""
    if raw_doi and SOURCE_DOI not in str(raw_doi):
        raise SourceStop("Official source DOI identity changed")
    (version_number,version_id),nversions=_choose_latest_version(version_response)
    rows=_extract_file_rows(file_response)
    required=set(contract["source"]["expected_min_version_files"])
    files={}
    for r in rows:
        filename=str(r.get("path") or r.get("filename") or r.get("name") or "").split("/")[-1]
        if not filename:raise SourceStop("Source file with missing name")
        if filename in files:raise SourceStop("Duplicate published original file name")
        try: length=int(r.get("size",r.get("sizeBytes",0)))
        except (TypeError,ValueError):raise SourceStop("Invalid source file byte size")
        if length<=0 or length>contract["source"]["expected_metadata_max_file_bytes"]:
            raise SourceStop("Unexpected original file size for "+filename)
        ident=r.get("id")
        if ident is None:
            href=(r.get("_links",{}).get("self",{}) or {}).get("href","")
            m=re.search(r"/files/(\d+)",href)
            ident=int(m.group(1)) if m else None
        if ident is None:raise SourceStop("Original published file ID missing: "+filename)
        digest=r.get("digest") or r.get("checksum") or r.get("md5")
        if isinstance(digest,dict):
            digest={str(k):str(v)[:128] for k,v in digest.items()}
        elif digest is not None:
            digest=str(digest)[:128]
        files[filename]={"original_dryad_file_id":ident,
                         "file_bytes":length,"publisher_digest":digest}
    if not required<=set(files):raise SourceStop("Latest Dryad source missing expected companion files: "+str(sorted(required-set(files))))
    return {
        "schema":SCHEMA,
        "status":"ORIGINAL_DRYAD_FILE_METADATA_IDENTIFIED_NO_BIOLOGY",
        "publisher_doi":SOURCE_DOI,
        "dataset_api_version_number":version_number,
        "original_version_id":version_id,
        "number_of_publicly_enumerated_versions":nversions,
        "required_source_files":{name:files[name] for name in sorted(required)},
        "other_published_filenames_only":sorted(set(files)-required),
        "actual_seed_trap_or_plant_presence_rows_read":0,
        "independently_replicated_archipelago_experiments_admitted":0,
        "one_field_landscape_not_twelve_independent_archipelagos":True,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--contract",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    contract=json.loads(args.contract.read_text(encoding="utf-8"))
    base=contract["source"]
    out={"schema":SCHEMA,"status":"SOURCE_METADATA_STOP_NO_NEW_BIOLOGICAL_ROWS",
         "GEB_scientific_HOLD":True,"eBird_used":False}
    try:
        dataset=_original_get_json(base["dataset_api"])
        versions=_original_get_json(base["versions_api"])
        (n,vid),_=_choose_latest_version(versions)
        filelist=_original_get_json(f"https://datadryad.org/api/v2/versions/{vid}/files")
        out=validate_source(dataset,versions,filelist,contract)
        out["source_dataset_url"]=base["dataset_api"]
        out["source_file_metadata_url"]=f"https://datadryad.org/api/v2/versions/{vid}/files"
    except Exception as e:
        out.update({"error_type":type(e).__name__,"reason":str(e)[:450]})
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({key:out.get(key) for key in ("status","original_version_id","dataset_api_version_number","reason")},sort_keys=True))
    if out["status"]!="ORIGINAL_DRYAD_FILE_METADATA_IDENTIFIED_NO_BIOLOGY":
        raise SystemExit(2)


if __name__=="__main__":main()
