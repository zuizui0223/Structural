#!/usr/bin/env python3
"""Resolve and download exactly one frozen Dryad workbook during one-shot access.

This script must never run on the pre-response design branch. It validates the
dataset landing page against the committed authorization, resolves only the
anchor whose visible text is exactly Ecological_Data.xlsx, downloads that file
once, records the first-access SHA-256/byte count, and emits a source receipt.
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
MAX_BYTES=1024*1024

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
    headers={"User-Agent":"Structural-murundu-one-shot/0.1"}
    landing=session.get(page,headers=headers,timeout=90)
    landing.raise_for_status()
    html=landing.content
    text=landing.text
    if "10.5061/dryad.612jm64kr" not in text:
        raise RuntimeError("DOI absent from Dryad landing page")
    if "Apr 02, 2026" not in text and "2026-04-02" not in text:
        raise RuntimeError("frozen Dryad version date absent from landing page")
    if "Ecological_Data.xlsx" not in text:
        raise RuntimeError("frozen workbook name absent from landing page")
    if "195.16 KB" not in text:
        raise RuntimeError("frozen workbook display size absent from landing page")

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
    resolved=urljoin(landing.url,href)
    parsed=urlparse(resolved)
    if parsed.scheme!="https" or parsed.netloc!="datadryad.org":
        raise RuntimeError(f"unexpected initial workbook URL: {resolved}")

    with session.get(resolved,headers=headers,timeout=180,stream=True,allow_redirects=True) as response:
        response.raise_for_status()
        chunks=[]
        total=0
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            total+=len(chunk)
            if total>MAX_BYTES:
                raise RuntimeError(f"download exceeded frozen safety ceiling {MAX_BYTES}")
            chunks.append(chunk)
        raw=b"".join(chunks)
        final_url=response.url
        content_type=response.headers.get("Content-Type")
        content_length=response.headers.get("Content-Length")
        etag=response.headers.get("ETag")
        last_modified=response.headers.get("Last-Modified")

    if not raw:
        raise RuntimeError("empty Dryad workbook response")
    if not raw.startswith(b"PK"):
        raise RuntimeError("download does not look like an XLSX/ZIP container")

    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(raw)

    receipt={
        "schema":"structural.murundu_relative_topology_source_access.v0_1",
        "status":"ONE_SHOT_WORKBOOK_DOWNLOADED",
        "authorization_fingerprint":auth.get("authorization_fingerprint"),
        "protocol_fingerprint":EXPECTED_PROTOCOL,
        "source_identity":{
            "doi":"10.5061/dryad.612jm64kr",
            "dataset_page":page,
            "version_date":"2026-04-02",
            "file_name":"Ecological_Data.xlsx",
            "display_size":"195.16 KB",
        },
        "landing_page":{
            "requested_url":page,
            "final_url":landing.url,
            "sha256":sha_bytes(html),
            "doi_present":True,
            "version_date_present":True,
            "file_name_present":True,
            "display_size_present":True,
        },
        "download":{
            "initial_url":resolved,
            "final_url":final_url,
            "bytes":len(raw),
            "sha256":sha_bytes(raw),
            "content_type":content_type,
            "content_length_header":content_length,
            "etag":etag,
            "last_modified":last_modified,
        },
        "response_access":{
            "workbook_downloaded":True,
            "workbook_parsed":False,
            "primary_response_column_parsed":False,
            "herb_or_termite_response_parsed":False,
        },
    }
    receipt["source_access_fingerprint"]=sha_json(receipt)
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
