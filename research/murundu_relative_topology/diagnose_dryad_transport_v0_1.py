#!/usr/bin/env python3
"""Response-free Dryad transport diagnostic for the frozen murundu workbook.

This script reads only public landing/API metadata and HTTP response headers.
It NEVER downloads or iterates any file body from a download endpoint.
"""
from __future__ import annotations

import json
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DOI="10.5061/dryad.612jm64kr"
DATASET_PAGE="https://datadryad.org/dataset/doi:10.5061/dryad.612jm64kr"
FILE_NAME="Ecological_Data.xlsx"
FILE_ID=4686245
API_VERSION="2.1.0"
BROWSER_UA=(
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)

def safe_headers(response):
    keys=("Content-Type","Content-Length","Location","WWW-Authenticate","ETag","Last-Modified","X-API-Version","X-API-Deprecation")
    return {k:response.headers.get(k) for k in keys if response.headers.get(k) is not None}

def probe(session,method,url,headers):
    if method=="HEAD":
        r=session.head(url,headers=headers,timeout=90,allow_redirects=False)
    else:
        # stream=True and never touch .content/.text/.raw.read: headers/status only.
        r=session.get(url,headers=headers,timeout=90,allow_redirects=False,stream=True)
    out={
        "method":method,
        "url":url,
        "status_code":r.status_code,
        "reason":r.reason,
        "headers":safe_headers(r),
    }
    r.close()
    return out

def main():
    session=requests.Session()
    common={"User-Agent":BROWSER_UA,"Accept-Language":"en-US,en;q=0.9"}

    landing=session.get(
        DATASET_PAGE,
        headers={**common,"Accept":"text/html,application/xhtml+xml"},
        timeout=90,
    )
    landing.raise_for_status()
    html=landing.content
    text=landing.text
    if DOI not in text or FILE_NAME not in text or "195.16 KB" not in text:
        raise RuntimeError("frozen landing-page identity not present")

    soup=BeautifulSoup(html,"html.parser")
    matches=[a for a in soup.find_all("a") if a.get_text(" ",strip=True)==FILE_NAME]
    if len(matches)!=1:
        raise RuntimeError(f"expected one workbook anchor, got {len(matches)}")
    ui_url=urljoin(landing.url,matches[0].get("href"))
    parsed=urlparse(ui_url)
    if parsed.path!=f"/downloads/file_stream/{FILE_ID}":
        raise RuntimeError(f"file-id drift in anchor: {ui_url}")

    encoded=quote(f"doi:{DOI}",safe="")
    dataset_api=f"https://datadryad.org/api/v2/datasets/{encoded}"
    versions_api=f"{dataset_api}/versions"
    file_api=f"https://datadryad.org/api/v2/files/{FILE_ID}"
    file_download=f"{file_api}/download"
    dataset_download=f"{dataset_api}/download"
    stash_file_stream=f"https://datadryad.org/stash/downloads/file_stream/{FILE_ID}"
    api_headers={**common,"Accept":"application/json","X-API-Version":API_VERSION}

    dataset=session.get(dataset_api,headers=api_headers,timeout=90)
    dataset.raise_for_status()
    dataset_json=dataset.json()

    versions=session.get(versions_api,headers=api_headers,timeout=90)
    versions.raise_for_status()
    versions_json=versions.json()
    embedded=versions_json.get("_embedded",{})
    version_rows=embedded.get("stash:versions",[])
    if not version_rows:
        raise RuntimeError("no Dryad versions returned")
    # The landing page is frozen to Apr 02, 2026; inspect all public versions.
    version_ids=[]
    files_by_version=[]
    for v in version_rows:
        vid=v.get("id")
        if vid is None:
            href=(v.get("_links",{}).get("self",{}) or {}).get("href","")
            if "/versions/" in href:
                vid=href.rsplit("/",1)[-1]
        if vid is None:
            continue
        vid=int(vid)
        version_ids.append(vid)
        files_url=f"https://datadryad.org/api/v2/versions/{vid}/files"
        fr=session.get(files_url,headers=api_headers,timeout=90)
        fr.raise_for_status()
        fj=fr.json()
        items=(fj.get("_embedded",{}) or {}).get("stash:files",[])
        target=[x for x in items if x.get("path")==FILE_NAME]
        files_by_version.append({
            "version_id":vid,
            "version_status":v.get("versionStatus"),
            "version_number":v.get("versionNumber"),
            "last_modification_date":v.get("lastModificationDate"),
            "target_files":[{
                "id":x.get("id"),
                "path":x.get("path"),
                "size":x.get("size"),
                "digest":x.get("digest"),
                "digestType":x.get("digestType"),
                "links":x.get("_links"),
            } for x in target],
        })

    fm=session.get(file_api,headers=api_headers,timeout=90)
    fm.raise_for_status()
    file_json=fm.json()
    if file_json.get("path")!=FILE_NAME:
        raise RuntimeError("file metadata path drift")
    if int(file_json.get("id",FILE_ID))!=FILE_ID:
        raise RuntimeError("file metadata id drift")

    browser_download_headers={
        **common,
        "Accept":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream,*/*",
        "Referer":landing.url,
        "Sec-Fetch-Site":"same-origin",
        "Sec-Fetch-Mode":"navigate",
        "Sec-Fetch-Dest":"document",
        "Upgrade-Insecure-Requests":"1",
    }
    probes=[]
    for method,url,headers in [
        ("HEAD",file_download,{**common,"Accept":"application/octet-stream,*/*","X-API-Version":API_VERSION}),
        ("GET",file_download,{**common,"Accept":"application/octet-stream,*/*","X-API-Version":API_VERSION}),
        ("HEAD",ui_url,browser_download_headers),
        ("GET",ui_url,browser_download_headers),
        ("HEAD",stash_file_stream,browser_download_headers),
        ("GET",stash_file_stream,browser_download_headers),
        ("HEAD",dataset_download,{**common,"Accept":"application/zip,*/*","X-API-Version":API_VERSION}),
        ("GET",dataset_download,{**common,"Accept":"application/zip,*/*","X-API-Version":API_VERSION}),
    ]:
        probes.append(probe(session,method,url,headers))

    out={
        "schema":"structural.murundu_dryad_transport_diagnostic.v0_1",
        "status":"RESPONSE_BODY_UNREAD_TRANSPORT_DIAGNOSTIC",
        "response_values_accessed":False,
        "workbook_bytes_read":0,
        "source":{
            "doi":DOI,
            "dataset_page":DATASET_PAGE,
            "file_name":FILE_NAME,
            "file_id":FILE_ID,
            "landing_anchor":ui_url,
        },
        "dataset_api":{
            "id":dataset_json.get("id"),
            "identifier":dataset_json.get("identifier"),
            "versionNumber":dataset_json.get("versionNumber"),
            "versionStatus":dataset_json.get("versionStatus"),
            "lastModificationDate":dataset_json.get("lastModificationDate"),
            "storageSize":dataset_json.get("storageSize"),
            "links":dataset_json.get("_links"),
        },
        "versions":{
            "count":len(version_rows),
            "version_ids":version_ids,
            "files_by_version":files_by_version,
        },
        "file_api":{
            "id_field":file_json.get("id"),
            "self_href":(file_json.get("_links",{}).get("self",{}) or {}).get("href"),
            "path":file_json.get("path"),
            "size":file_json.get("size"),
            "mimeType":file_json.get("mimeType"),
            "digest":file_json.get("digest"),
            "digestType":file_json.get("digestType"),
            "links":file_json.get("_links"),
        },
        "header_only_probes":probes,
        "claim":"no response-body bytes from any download endpoint were consumed",
    }
    print(json.dumps(out,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
