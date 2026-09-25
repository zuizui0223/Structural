#!/usr/bin/env python3
"""Resolve and download the exact frozen Dryad workbook during one-shot access v0.2.

v0.2 changes transport only. It verifies the landing-page anchor and anonymous
Dryad REST file metadata for file id 4686245, then attempts the documented REST
download route and the same-origin UI file_stream route. Only bytes matching the
Dryad-published SHA-256/size and an XLSX ZIP signature are accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

AUTH_SCHEMA="structural.murundu_relative_topology_one_shot_authorization.v0_1"
EXPECTED_PROTOCOL="83b6a2539acc7983bb75648eb6c53a913917d5ea50dffdaefceceb3ac8fb6512"
FILE_ID=4686245
MAX_BYTES=1024*1024
BROWSER_UA=(
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/140.0.0.0 Safari/537.36"
)

def load(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict):
        raise RuntimeError(f"{path} must contain a JSON object")
    return x

def sha_bytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def sha_json(value)->str:
    return hashlib.sha256(
        json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def read_binary_response(response, strategy:str):
    response.raise_for_status()
    chunks=[]
    total=0
    for chunk in response.iter_content(chunk_size=65536):
        if not chunk:
            continue
        total+=len(chunk)
        if total>MAX_BYTES:
            raise RuntimeError(
                f"{strategy}: download exceeded frozen safety ceiling {MAX_BYTES}"
            )
        chunks.append(chunk)
    return b"".join(chunks)

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--authorization",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()

    auth=load(a.authorization)
    if auth.get("schema")!=AUTH_SCHEMA:
        raise RuntimeError("unexpected authorization schema")
    if auth.get("status")!="AUTHORIZED_FOR_ONE_SHOT_WORKBOOK_ACCESS":
        raise RuntimeError("one-shot workbook access not authorized")
    if auth.get("protocol_fingerprint")!=EXPECTED_PROTOCOL:
        raise RuntimeError("protocol fingerprint drift")
    if auth.get("response_values_accessed") is not False:
        raise RuntimeError("authorization already records response access")
    if auth.get("failed_v01",{}).get("workbook_bytes_downloaded") != 0:
        raise RuntimeError("v0.1 failure was not response-free")
    if int(auth.get("source",{}).get("dryad_file_id",-1))!=FILE_ID:
        raise RuntimeError("Dryad file-id drift")

    source=auth.get("source",{})
    if source.get("identity_mode")!="dryad_doi_version_filename_first_access_hash":
        raise RuntimeError("source identity mode drift")
    if source.get("doi")!="10.5061/dryad.612jm64kr":
        raise RuntimeError("Dryad DOI drift")
    page=source.get("dataset_page")
    if page!="https://datadryad.org/dataset/doi:10.5061/dryad.612jm64kr":
        raise RuntimeError("Dryad dataset page drift")
    if source.get("version_date")!="2026-04-02":
        raise RuntimeError("version date drift")
    if source.get("file_name")!="Ecological_Data.xlsx":
        raise RuntimeError("file name drift")
    if source.get("display_size")!="195.16 KB":
        raise RuntimeError("display size identity drift")

    session=requests.Session()
    common={
        "User-Agent":BROWSER_UA,
        "Accept-Language":"en-US,en;q=0.9",
    }
    landing=session.get(page,headers={**common,"Accept":"text/html,application/xhtml+xml"},timeout=90)
    landing.raise_for_status()
    html=landing.content
    text=landing.text
    for token,label in [
        ("10.5061/dryad.612jm64kr","DOI"),
        ("Ecological_Data.xlsx","file name"),
        ("195.16 KB","display size"),
    ]:
        if token not in text:
            raise RuntimeError(f"frozen {label} absent from landing page")
    if "Apr 02, 2026" not in text and "2026-04-02" not in text:
        raise RuntimeError("frozen Dryad version date absent from landing page")

    soup=BeautifulSoup(html,"html.parser")
    matches=[
        tag for tag in soup.find_all("a")
        if tag.get_text(" ",strip=True)=="Ecological_Data.xlsx"
    ]
    if len(matches)!=1:
        raise RuntimeError(f"expected exactly one Ecological_Data.xlsx anchor, got {len(matches)}")
    href=matches[0].get("href")
    if not href:
        raise RuntimeError("Dryad workbook anchor has no href")
    ui_url=urljoin(landing.url,href)
    parsed=urlparse(ui_url)
    if parsed.scheme!="https" or parsed.netloc!="datadryad.org":
        raise RuntimeError(f"unexpected workbook anchor URL: {ui_url}")
    if parsed.path!=f"/downloads/file_stream/{FILE_ID}":
        raise RuntimeError(f"landing-page file id drift: {parsed.path}")

    api_meta_url=f"https://datadryad.org/api/v2/files/{FILE_ID}"
    meta_response=session.get(
        api_meta_url,
        headers={**common,"Accept":"application/json","X-API-Version":"2.1.0"},
        timeout=90,
    )
    meta_response.raise_for_status()
    meta=meta_response.json()
    if str(meta.get("path"))!="Ecological_Data.xlsx":
        raise RuntimeError(f"API file path drift: {meta.get('path')}")
    if str(meta.get("digestType","")).lower()!="sha-256":
        raise RuntimeError(f"unexpected Dryad digest type: {meta.get('digestType')}")
    expected_digest=str(meta.get("digest","")).lower()
    expected_size=int(meta.get("size",-1))
    if len(expected_digest)!=64:
        raise RuntimeError("Dryad API did not provide a SHA-256 digest")
    if expected_size<=0 or expected_size>MAX_BYTES:
        raise RuntimeError(f"unexpected Dryad API file size: {expected_size}")

    strategies=[
        (
            "api_v2_file_download",
            f"https://datadryad.org/api/v2/files/{FILE_ID}/download",
            {**common,"Accept":"application/octet-stream,*/*","X-API-Version":"2.1.0"},
        ),
        (
            "ui_same_origin_file_stream",
            ui_url,
            {
                **common,
                "Accept":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream,*/*",
                "Referer":landing.url,
                "Sec-Fetch-Site":"same-origin",
                "Sec-Fetch-Mode":"navigate",
                "Sec-Fetch-Dest":"document",
                "Upgrade-Insecure-Requests":"1",
            },
        ),
    ]
    attempts=[]
    raw=None
    winning=None
    response_headers={}
    final_url=None
    for name,url,headers in strategies:
        with session.get(url,headers=headers,timeout=180,stream=True,allow_redirects=True) as response:
            attempts.append({
                "strategy":name,
                "initial_url":url,
                "status_code":response.status_code,
                "final_url":response.url,
                "content_type":response.headers.get("Content-Type"),
                "content_length":response.headers.get("Content-Length"),
            })
            if response.status_code in (401,403):
                continue
            candidate=read_binary_response(response,name)
            if not candidate.startswith(b"PK"):
                raise RuntimeError(f"{name}: response is not an XLSX/ZIP container")
            if len(candidate)!=expected_size:
                raise RuntimeError(
                    f"{name}: byte-size mismatch {len(candidate)} != {expected_size}"
                )
            observed=sha_bytes(candidate)
            if observed!=expected_digest:
                raise RuntimeError(
                    f"{name}: SHA-256 mismatch {observed} != {expected_digest}"
                )
            raw=candidate
            winning=name
            final_url=response.url
            response_headers={
                "content_type":response.headers.get("Content-Type"),
                "content_length":response.headers.get("Content-Length"),
                "etag":response.headers.get("ETag"),
                "last_modified":response.headers.get("Last-Modified"),
            }
            break

    if raw is None:
        raise RuntimeError(
            "all frozen Dryad download transports were denied before any workbook byte "
            f"was accepted; attempts={attempts}"
        )

    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(raw)
    receipt={
        "schema":"structural.murundu_relative_topology_source_access.v0_2",
        "status":"ONE_SHOT_WORKBOOK_DOWNLOADED",
        "authorization_fingerprint":auth.get("authorization_fingerprint"),
        "protocol_fingerprint":EXPECTED_PROTOCOL,
        "source_identity":{
            "doi":"10.5061/dryad.612jm64kr",
            "dataset_page":page,
            "version_date":"2026-04-02",
            "file_name":"Ecological_Data.xlsx",
            "display_size":"195.16 KB",
            "dryad_file_id":FILE_ID,
            "dryad_api_file_sha256":expected_digest,
            "dryad_api_file_bytes":expected_size,
        },
        "landing_page":{
            "requested_url":page,
            "final_url":landing.url,
            "sha256":sha_bytes(html),
        },
        "api_file_metadata":{
            "url":api_meta_url,
            "path":meta.get("path"),
            "size":expected_size,
            "digest":expected_digest,
            "digestType":meta.get("digestType"),
        },
        "download":{
            "winning_strategy":winning,
            "attempts":attempts,
            "final_url":final_url,
            "bytes":len(raw),
            "sha256":sha_bytes(raw),
            **response_headers,
        },
        "response_access":{
            "workbook_downloaded":True,
            "workbook_parsed":False,
            "primary_response_column_parsed":False,
            "herb_or_termite_response_parsed":False,
        },
    }
    receipt["source_access_fingerprint"]=sha_json(receipt)
    a.receipt.write_text(
        json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8"
    )
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
