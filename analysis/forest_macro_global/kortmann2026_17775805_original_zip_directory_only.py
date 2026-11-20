#!/usr/bin/env python3
"""Exact-publisher Kortmann 2026 ZIP central-directory inventory ONLY.

Download exact source bytes to verify publisher size/MD5, then access ZIP
central directory metadata; NEVER extract or decode a single original member.
No original site keys, OTU values, species rows, or model fit.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from kortmann2026_17775805_canonical_publisher_index_only import (
    URL, RECORD, DOI, parse, download_index_only, NoRedirect, SourceStop,
)

PRESPEC = "docs/FOREST_MACRO_KORTMANN2026_17775805_ORIGINAL_ZIP_CENTRAL_DIRECTORY_PREFREEZE_20261120.md"
ARCHIVE = "data_code.zip"
SIZE = 46205253
MD5 = "41f9a8428d80e833e4785be198a5c886"
MANIFEST_SHA = "278910cf7c284eeb55a11fc45f4fa8b7af77530c73b059ac606410d3e5224dd2"
LIC = "cc-by-sa-4.0"
CAP_FILES = 500
CAP_UNCOMPRESSED = 2 * 10**9
CAP_DISCLOSED_FILE_ROLES = 100
ZIP_SAFE_PATH = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./() +\-]{0,200}$")
DISCLOSED_EXTENSIONS = {".csv",".tsv",".xlsx",".xls",".r",".rds",".rdata",".txt",".md",".json"}


def original_file_metadata():
    source = download_index_only()
    receipt = parse(source)
    if receipt.get("status") != "SOURCE_CANONICAL_INDEX_READY_NO_BIOLOGY":
        raise SourceStop("SOURCE_CANONICAL_VERSION_NOT_READY")
    if receipt.get("source_file_count") != 1:
        raise SourceStop("SOURCE_CANONICAL_FILE_COUNT_DRIFT")
    if receipt.get("original_publisher_manifest_SHA256") != MANIFEST_SHA:
        raise SourceStop("SOURCE_CANONICAL_ORIGINAL_MANIFEST_DRIFT")
    if receipt.get("publisher_public_license") != LIC:
        raise SourceStop("SOURCE_CANONICAL_ORIGINAL_LICENSE_DRIFT")
    if receipt.get("versioned_doi") != DOI or receipt.get("original_record") != RECORD:
        raise SourceStop("SOURCE_CANONICAL_ID_DOI_DRIFT")
    f = source["files"][0]
    if f.get("key") != ARCHIVE or f.get("size") != SIZE or f.get("checksum") != "md5:"+MD5:
        raise SourceStop("SOURCE_CANONICAL_ORIGINAL_ARCHIVE_FILE_DRIFT")
    links=f.get("links",{})
    if not isinstance(links,dict):
        raise SourceStop("SOURCE_ZIP_PUBLISHER_FILE_LINK_MISSING")
    url=links.get("content") or links.get("self")
    return url


def validate_file_url(url):
    if not isinstance(url,str):
        raise SourceStop("SOURCE_ZIP_DOWNLOAD_LINK_NOT_PUBLISHER_STRING")
    p=urllib.parse.urlsplit(url)
    if (p.scheme!="https" or p.netloc!="zenodo.org"
        or p.username or p.password or p.query or p.fragment):
        raise SourceStop("SOURCE_ZIP_DOWNLOAD_NOT_EXACT_ZENODO")
    record_path=f"/api/records/{RECORD}/files/{ARCHIVE}/content"
    uuid_path=r"/api/files/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/"+re.escape(ARCHIVE)
    if p.path!=record_path and not re.fullmatch(uuid_path,p.path):
        raise SourceStop("SOURCE_ZIP_DOWNLOAD_PATH_NOT_AUTHOR_PUBLISHER")
    return url


def official_get_one_zip(url):
    validate_file_url(url)
    request=urllib.request.Request(
        url,headers={"Accept":"*/*",
            "User-Agent":"Structural-Kortmann17775805-ZIP-CentralDirectory-ONLY/1.0"})
    try:
        with urllib.request.build_opener(NoRedirect).open(request,timeout=65) as q:
            if q.status!=200:
                raise SourceStop("SOURCE_ZIP_DOWNLOAD_NON200")
            binary=q.read(SIZE+1)
    except urllib.error.HTTPError as ex:
        raise SourceStop("SOURCE_ZIP_DOWNLOAD_HTTP_"+str(ex.code)) from None
    except (urllib.error.URLError,OSError,TimeoutError) as ex:
        raise SourceStop("SOURCE_ZIP_DOWNLOAD_TRANSPORT_"+type(ex).__name__) from None
    if len(binary)!=SIZE or hashlib.md5(binary).hexdigest()!=MD5:
        raise SourceStop("SOURCE_ZIP_FULL_BYTES_SIZE_OR_DIGEST_DRIFT")
    return binary


def inspect_central_directory_only(binary):
    # ZipFile.infolist() reads ZIP directory records only, not member content.
    try:
        with zipfile.ZipFile(io.BytesIO(binary),"r") as z:
            entries=z.infolist()
    except (zipfile.BadZipFile,zipfile.LargeZipFile,ValueError):
        raise SourceStop("SOURCE_ZIP_CENTRAL_DIRECTORY_UNREADABLE") from None
    if not entries or len(entries)>CAP_FILES:
        raise SourceStop("SOURCE_ZIP_DIRECTORY_ENTRY_COUNT_UNSAFE")
    names=set();ext_counts=Counter();readable=[]
    total_size=0
    for info in entries:
        name=info.filename
        if (not isinstance(name,str) or not ZIP_SAFE_PATH.fullmatch(name)
            or name.startswith("/") or ".." in name.split("/")
            or "\\" in name or ":" in name or name in names
            or (info.flag_bits & 1)):
            raise SourceStop("SOURCE_ZIP_DIRECTORY_MEMBER_NAME_DUPLICATE_OR_UNSAFE")
        names.add(name)
        if not info.is_dir():
            if info.file_size < 0 or info.compress_size < 0:
                raise SourceStop("SOURCE_ZIP_MEMBER_DIRECTORY_SIZE_INVALID")
            total_size += info.file_size
            if total_size>CAP_UNCOMPRESSED:
                raise SourceStop("SOURCE_ZIP_ADVERTISED_UNCOMPRESSED_CAP_EXCEEDED")
            extension=Path(name).suffix.lower()
            ext_counts[extension if extension else "(none)"]+=1
            if extension in DISCLOSED_EXTENSIONS:
                readable.append({
                   "original_safe_publisher_ZIP_member_path":name,
                   "advertised_member_file_bytes_NOT_OPENED":info.file_size,
                })
    if len(readable)>CAP_DISCLOSED_FILE_ROLES:
        raise SourceStop("SOURCE_ZIP_TOO_MANY_ROLE_CANDIDATES_FOR_SAFE_DISCLOSURE")
    return {
        "status":"SOURCE_ZIP_CENTRAL_DIRECTORY_READY_METADATA_ONLY",
        "archive_publisher_file_size_verified":SIZE,
        "archive_original_publisher_MD5_verified":MD5,
        "central_directory_entry_count":len(entries),
        "central_directory_file_count":sum(ext_counts.values()),
        "central_directory_extension_counts":dict(sorted(ext_counts.items())),
        "advertised_total_uncompressed_bytes_NOT_EXTRACTED":total_size,
        "safe_method_or_table_file_role_candidates_ONLY":readable,
        "no_original_member_extracted_or_opened":True,
        "no_original_member_crc_test_or_decompression":True,
        "no_source_site_or_OTU_values_read":True,
        "ecological_models_fitted":0,
    }


def synthetic():
    archive=io.BytesIO()
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("methods/README.md","SYNTHETIC_ONLY_SOURCE_CONTENT_SECRET")
        z.writestr("data/taxa.csv","taxon,abundance\nfake,1\n")
    r=inspect_central_directory_only(archive.getvalue())
    assert r["central_directory_file_count"]==2
    assert r["no_original_member_extracted_or_opened"]
    assert "SYNTHETIC_ONLY_SOURCE_CONTENT_SECRET" not in json.dumps(r)
    try:
        validate_file_url("https://example.org/api/records/17775805/files/data_code.zip/content")
        raise AssertionError("cross-origin source link accepted")
    except SourceStop:pass
    try:
        validate_file_url("https://zenodo.org/api/records/17775805/files/data_code.zip/content?token=X")
        raise AssertionError("query-credential link accepted")
    except SourceStop:pass
    bad=io.BytesIO()
    with zipfile.ZipFile(bad,"w") as z:
        z.writestr("../bad.csv","unopened")
    try:
        inspect_central_directory_only(bad.getvalue())
        raise AssertionError("zip slip path accepted")
    except SourceStop:pass
    print("SYNTHETIC_KORTMANN_2026_CENTRAL_DIRECTORY_NOT_MEMBER_READ_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out required")
    report={
        "schema":"structural.Kortmann17775805_one_original_ZIP_central_directory_only.v1",
        "prespec":PRESPEC,
        "original_publisher_record":RECORD,
        "historical_17775804_HTTP302_STOP_unchanged":True,
        "historical_BETAFOR234_no_files_STOP_unchanged":True,
        "biological_source_rows_read":0,
        "new_organismal_effects":0,
        "eBird_used":False,
        "TinyFish_used":False,
    }
    try:
        url=original_file_metadata()
        raw=official_get_one_zip(url)
        report["source_zip_directory"]=inspect_central_directory_only(raw)
        report["status"]=report["source_zip_directory"]["status"]
    except SourceStop as ex:
        report["status"]="SOURCE_ZIP_STOP_"+str(ex)
        report["not_biological_null"]=True
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("KORTMANN2026_ZIP_CENTRAL_DIRECTORY_ONLY",report["status"])
    print("NO_SOURCE_ZIP_MEMBER_READ; NO_ORGANISM_MODELS")


if __name__=="__main__":main()
