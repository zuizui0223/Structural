#!/usr/bin/env python3
"""SOURCE ONLY independent forest host-tree/wood x beetle archival intake.

No species, habitat row, individual, site coordinate, environmental measurement
or trait value is downloaded/read. Only official published metadata, source
filename/checksum and one optional Dryad README source-download status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DRYAD_DOI = "doi:10.5061/dryad.k3j9kd5m4"
ZENODO_IDS = (21486790, 21535672)
REQUIRED_SWEDEN = {
    "README.md", "Beetlespecies_data.xlsx", "deadwood_local.xlsx",
    "site_coordinate.xlsx",
}
BASE_DRYAD = "https://datadryad.org"
UA = {"User-Agent": "Structural-author-source-intake/1.0 research archive verification",
      "Accept": "application/json"}


def get_public(url: str, max_bytes: int=900000):
    p = urllib.parse.urlparse(url)
    if p.scheme != "https" or p.hostname not in ("datadryad.org","zenodo.org"):
        raise ValueError("SOURCE_STOP_UNAUTHORIZED_EXTERNAL_HOST")
    if not (p.path.startswith("/api/v2/") or p.path.startswith("/api/records/")):
        raise ValueError("SOURCE_STOP_NOT_AN_OFFICIAL_ARCHIVE_API_ENDPOINT")
    req=urllib.request.Request(url,headers=UA)
    try:
        with urllib.request.urlopen(req,timeout=24) as f:
            data=f.read(max_bytes+1)
            if len(data)>max_bytes:
                return {"status":"SOURCE_STOP_METADATA_TOO_LARGE","bytes":len(data)}
            if f.status != 200:
                return {"status":"SOURCE_STOP_NON200","http_status":f.status}
            try:
                obj=json.loads(data.decode("utf-8"))
                return {"status":"SOURCE_METADATA_OK","data":obj}
            except (UnicodeDecodeError,json.JSONDecodeError):
                return {"status":"SOURCE_STOP_METADATA_NOT_JSON"}
    except urllib.error.HTTPError as exc:
        return {"status":"SOURCE_ACCESS_HTTP_STOP","http_status":exc.code}
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        return {"status":"SOURCE_ACCESS_TRANSPORT_STOP","error_class":type(exc).__name__}


def official_dryad_href(path: str):
    parsed=urllib.parse.urlparse(path)
    if parsed.scheme or parsed.netloc or not path.startswith("/api/v2/"):
        raise ValueError("SOURCE_STOP_UNSAFE_ORIGIN_DRYAD_API_LINK")
    return BASE_DRYAD+path


def file_names_from_dryad(j):
    v=((j.get("_embedded") or {}).get("stash:files") or [])
    if not isinstance(v,list):
        return []
    out=[]
    for f in v:
        name=f.get("path") or f.get("filename") or ""
        if name:
            # Dryad's public file-list JSON omits numeric "id" on some
            # records, but official HAL self/download links can carry it.
            # Resolve ID ONLY from an exact official file metadata path.
            fid=f.get("id")
            linkkeys=sorted((f.get("_links") or {}).keys())
            if not isinstance(fid,int):
                for kind in ("stash:download","self","stash:file"):
                    href=((f.get("_links") or {}).get(kind) or {}).get("href","")
                    p=urllib.parse.urlparse(href)
                    if p.scheme and (p.scheme!="https" or p.hostname!="datadryad.org"):
                        continue
                    m=re.fullmatch(r"/api/v2/files/(\d+)(?:/download)?",p.path)
                    if m:
                        fid=int(m.group(1))
                        break
            out.append({
                "name":str(name),
                "size_bytes":f.get("size"),
                "md5_or_other_digest":f.get("digest"),
                "digest_type":f.get("digestType"),
                "author_file_id":fid if isinstance(fid,int) else None,
                "source_official_hal_link_kinds":linkkeys,
                "source_mime_type":f.get("mimeType"),
            })
    return out


def dryad_source():
    url=BASE_DRYAD+"/api/v2/datasets/"+urllib.parse.quote(DRYAD_DOI,safe="")
    output={"original_DOI":DRYAD_DOI, "author_publication_year":2025,
      "original_author_field_sites_from_publication":23,
      "original_field_regions_from_publication":3,
      "original_beetle_survey_year":2022,
      "original_local_deadwood_measurement_year":2020,
      "study_time_gap_not_same_year":True,
      "required_original_files":sorted(REQUIRED_SWEDEN),
      "no_source_beetle_taxa_or_field_values_read":True}
    base=get_public(url)
    output["dataset_api_status"]=base["status"]
    if base["status"]!="SOURCE_METADATA_OK":
        if "http_status" in base:output["dataset_api_http_status"]=base["http_status"]
        output["status"]="SOURCE_ACCESS_STOP_SWEDEN_ORIGINAL_ARCHIVE_METADATA"
        return output
    ds=base["data"]
    output["source_title"]=str(ds.get("title",""))[:160]
    output["original_license"]=ds.get("license")
    output["original_visibility"]=ds.get("visibility")
    ver=(ds.get("_links") or {}).get("stash:version") or {}
    try:
        vurl=official_dryad_href(ver["href"])
    except (KeyError,ValueError):
        output["status"]="SOURCE_STOP_SWEDEN_MISSING_AUTHOR_VERSION_LINK"
        return output
    vv=get_public(vurl)
    output["published_version_metadata_status"]=vv["status"]
    if vv["status"]!="SOURCE_METADATA_OK":
        output["status"]="SOURCE_STOP_SWEDEN_AUTHOR_VERSION_UNAVAILABLE"
        return output
    vdata=vv["data"]
    output["version_original_published_date"]=vdata.get("publicationDate")
    file_href=(vdata.get("_links") or {}).get("stash:files",{}).get("href")
    if not file_href:
        output["status"]="SOURCE_STOP_SWEDEN_NO_SOURCE_FILE_INDEX_LINK"
        return output
    try:
        furl=official_dryad_href(file_href)
    except ValueError:
        output["status"]="SOURCE_STOP_SWEDEN_BAD_FILE_INDEX_ORIGIN"
        return output
    separator="&" if "?" in furl else "?"
    ff=get_public(furl+separator+"per_page=100",max_bytes=700000)
    output["original_file_index_api_status"]=ff["status"]
    if ff["status"]!="SOURCE_METADATA_OK":
        output["status"]="SOURCE_STOP_SWEDEN_ORIGINAL_FILE_INDEX_UNAVAILABLE"
        return output
    files=file_names_from_dryad(ff["data"])
    # Diagnose *public* original HAL link shape, rather than inventing file IDs
    # after two metadata-only attempts found no IDs in the published records.
    raw=((ff["data"].get("_embedded") or {}).get("stash:files") or [])
    readme_public=next((row for row in raw if row.get("path")=="README.md"),None)
    if readme_public is not None:
        output["readme_public_HAL_link_paths_for_file_identity_diagnosis"]={
            kind:((readme_public.get("_links") or {}).get(kind) or {}).get("href")
            for kind in ("self","stash:download","stash:file")
        }
    files=file_names_from_dryad(ff["data"])
    output["original_public_file_metadata"]=files
    output["original_file_total_returned"]=len(files)
    names={r["name"].rsplit("/",1)[-1] for r in files}
    output["original_required_files_metadata_present"]=sorted(REQUIRED_SWEDEN&names)
    output["required_files_missing_from_original_index"]=sorted(REQUIRED_SWEDEN-names)
    if REQUIRED_SWEDEN-names:
        output["status"]="SOURCE_STOP_MISSING_SOURCE_NATIVE_BEETLE_WOOD_IDENTITY_FILES"
        return output
    # Only original publicly published README permitted; do not download Excel.
    r=next((e for e in files if e["name"].rsplit("/",1)[-1]=="README.md"),None)
    if not r or not isinstance(r.get("author_file_id"),int):
        output["status"]="SOURCE_STOP_AUTHOR_README_SOURCE_FILE_ID_UNAVAILABLE"
        return output
    readme=BASE_DRYAD+f"/api/v2/files/{r['author_file_id']}/download"
    req=urllib.request.Request(readme,headers={"User-Agent":UA["User-Agent"]})
    try:
        with urllib.request.urlopen(req,timeout=28) as h:
            body=h.read(100000)
            output["readme_original_source_http_status"]=h.status
            output["readme_original_source_bytes_read_max100kb"]=len(body)
            output["readme_original_source_sha256"]=hashlib.sha256(body).hexdigest()
            # Never print original author README content.
            output["status"]="SOURCE_SWEDEN_ARCHIVE_METADATA_AND_README_ACCESS_OK"
    except urllib.error.HTTPError as exc:
        output["readme_original_source_http_status"]=exc.code
        output["status"]="SOURCE_STOP_SWEDEN_README_DOWNLOAD_ACCESS"
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        output["readme_transport_exception_class"]=type(exc).__name__
        output["status"]="SOURCE_STOP_SWEDEN_README_TRANSPORT"
    return output


def zenodo_sources():
    out={}
    for record in ZENODO_IDS:
        z=get_public("https://zenodo.org/api/records/"+str(record))
        item={"original_record_DOI":"10.5281/zenodo."+str(record),
              "status":z["status"],"no_original_biological_source_file_downloaded":True}
        if z["status"]=="SOURCE_METADATA_OK":
            j=z["data"]
            md=j.get("metadata",{})
            item["published_title"]=str(md.get("title",""))[:170]
            item["rights_license"]=md.get("license")
            item["access_right"]=md.get("access_right") or md.get("access_status")
            item["version"]=md.get("version")
            arr=j.get("files") or []
            if isinstance(arr,dict): arr=list((arr.get("entries") or {}).values())
            item["original_data_file_metadata"]=[]
            for f in arr:
                if not isinstance(f,dict):continue
                item["original_data_file_metadata"].append({
                    "name":f.get("key") or f.get("filename"),
                    "size_bytes":f.get("size"),
                    "checksum":f.get("checksum"),
                })
            item["original_file_count"]=len(item["original_data_file_metadata"])
            item["status"]="SOURCE_ZENODO_RECORD_METADATA_ONLY_OK"
        elif "http_status" in z:
            item["http_status"]=z["http_status"]
        out[str(record)]=item
    return out


def synthetic():
    good={"_embedded":{"stash:files":[{"path":"Beetlespecies_data.xlsx","size":20,"digest":"md5abc","id":42},{"path":"deadwood_local.xlsx","size":15,"id":43}]}}
    out=file_names_from_dryad(good)
    assert len(out)==2 and out[0]["name"]=="Beetlespecies_data.xlsx"
    assert official_dryad_href("/api/v2/files/123/download").startswith(BASE_DRYAD)
    try:
        official_dryad_href("https://random.example.com/metadata")
        raise AssertionError("unsafe origin accepted")
    except ValueError:
        pass
    assert str(urllib.parse.quote(DRYAD_DOI,safe="")).startswith("doi%3A10.5061%2F")
    print("SYNTHETIC_OFFICIAL_ARCHIVE_METADATA_ONLY_AND_ORIGIN_GATES_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    synthetic()
    if a.test:return
    if not a.out:ap.error("--out required")
    result={
      "schema":"structural.independent_hostwood_2025_Sweden_and_2026_Poland_sourceonly.v1",
      "primary_original_Sweden":dryad_source(),
      "secondary_distinct_Poland_archives":zenodo_sources(),
      "original_biodiversity_response_abundance_or_wood_amount_rows_unread":True,
      "no_new_ecological_effect_estimated":True,
      "original_Finland142site_guild_spatial_deadwood_positive_frozen":True,
      "original_threecountry_PREDICTS_NEON_BALA_GEB_scorers_unchanged":True,
      "eBird_used":False,
    }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"independent_forest_hostwood_archival_sourceonly.json").write_text(
       json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8"
    )
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
