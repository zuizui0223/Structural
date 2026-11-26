#!/usr/bin/env python3
"""Larsson Ekström et al. 2024 original Swedish forest restoration Dryad.

Publisher-official dataset VERSION and FILE MANIFEST only. No original workbook,
trap outcomes, trees, beetle species or site IDs are fetched. 2024 JAE and 2026
Restoration Ecology are treated as potentially overlapping 2021 field cohorts.
"""
from __future__ import annotations
import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DOI="doi:10.5061/dryad.c2fqz61gv"
BASE="https://datadryad.org"
API=BASE+"/api/v2/datasets/"+urllib.parse.quote(DOI,safe="")
FILES={"README.md","wbwdatajappl.xlsx"}
UA={"User-Agent":"Structural-restoration-sourceonly-2026-11-24",
    "Accept":"application/json"}

class SourceStop(ValueError):
    pass

def official(url):
    p=urllib.parse.urlparse(url)
    if p.scheme!="https" or p.hostname!="datadryad.org" or p.port not in (None,443):
        raise SourceStop("SOURCE_ORIGIN_NOT_ORIGINAL_DRYAD")
    if not p.path.startswith("/api/v2/"):
        raise SourceStop("SOURCE_PUBLIC_DRYAD_API_PATH_MISSING")
    return url

def href(s):
    if not s:raise SourceStop("SOURCE_ORIGINAL_API_HREF_MISSING")
    if s.startswith("/api/v2/"):return official(BASE+s)
    return official(s)

def fetch(url):
    try:
        req=urllib.request.Request(official(url),headers=UA)
        with urllib.request.urlopen(req,timeout=35) as r:
            if r.status!=200:
                raise SourceStop("SOURCE_OFFICIAL_DRYAD_STATUS_NON200")
            b=r.read(400001)
            if len(b)>400000:raise SourceStop("SOURCE_METADATA_BODY_CAP_STOP")
            return json.loads(b)
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_ORIGINAL_DRYAD_METADATA_HTTP_"+str(e.code))
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise SourceStop("SOURCE_DRYAD_TRANSPORT_"+type(e).__name__)

def original():
    d=fetch(API)
    # Confirm the source identity by publisher native fields, not the
    # paper title alone, which may be a normalized reprint string.
    doi=str(d.get("identifier") or d.get("doi") or "").casefold()
    if doi and DOI not in doi and "10.5061/dryad.c2fqz61gv" not in doi:
        raise SourceStop("SOURCE_DATASET_DOI_MISMATCH")
    links=d.get("_links") or {}
    v=(links.get("stash:version") or {}).get("href")
    version=fetch(href(v))
    file_href=((version.get("_links") or {}).get("stash:files") or {}).get("href")
    url=href(file_href)
    url+="&per_page=100" if "?" in url else "?per_page=100"
    file_index=fetch(url)
    arr=(file_index.get("_embedded") or {}).get("stash:files") or []
    if not isinstance(arr,list):raise SourceStop("SOURCE_FILE_LIST_OBJECT_BAD")
    roster=[]
    for f in arr:
        if not isinstance(f,dict):raise SourceStop("SOURCE_FILE_ENTRY_BAD")
        name=f.get("path") or f.get("filename") or ""
        fid=f.get("id")
        if not fid:
            link=((f.get("_links") or {}).get("self") or {}).get("href","")
            mm=re.search(r"/files/(\d+)(?:/|$)",link)
            if mm:fid=int(mm.group(1))
        roster.append({
            "original_file_name":name.split("/")[-1],
            "original_publisher_file_id":fid,
            "original_file_size_bytes":f.get("size"),
            "published_file_digest":f.get("digest"),
            "published_file_digest_type":f.get("digestType"),
        })
    names={x["original_file_name"] for x in roster}
    if len(roster)!=2 or names!=FILES:
        raise SourceStop("SOURCE_2024_EXACT_TWO_AUTHOR_FILES_MISMATCH")
    if any(not isinstance(x["original_publisher_file_id"],int) or not
           isinstance(x["original_file_size_bytes"],int) for x in roster):
        raise SourceStop("SOURCE_ORIGINAL_FILE_ID_SIZE_MISSING")
    return {
        "status":"ORIGINAL_2024_DRYAD_METADATA_AND_FILE_IDENTIFIERS_PASS_NO_BIOLOGY",
        "source_dataset_doi":"10.5061/dryad.c2fqz61gv",
        "original_publication_date":version.get("publicationDate"),
        "original_dataset_license":d.get("license") or version.get("license"),
        "original_dataset_title":str(d.get("title") or "")[:190],
        "original_exact_two_publisher_files":sorted(roster,key=lambda x:x["original_file_name"]),
        "source_original_workbook_GETs":0,
        "source_species_richness_and_guild_values_read":0,
        "2024_2026_same_field_cohort_independence_NOT_assumed":True,
        "source_data_object_or_tree_response_measured":False,
    }

def synthetic():
    assert href("/api/v2/files/123")=="https://datadryad.org/api/v2/files/123"
    for bad in ["http://datadryad.org/api/v2/files/123",
                "https://example.org/api/v2/files/123",
                "https://datadryad.org/private/file"]:
        try:official(bad);raise AssertionError("must reject")
        except SourceStop:pass
    assert DOI=="doi:10.5061/dryad.c2fqz61gv"
    assert len(FILES)==2
    print("SWEDEN2024_RESTORATION_SOURCE_METADATA_KNOWN_TRUTH_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",default="sweden2024_restoration_source_metadata/receipt.json")
    a=ap.parse_args()
    synthetic()
    if a.test:return
    receipt={
        "schema":"structural.sweden2024_restoration_Dryad_2026_overlap_SOURCE_METADATA_ONLY.v1",
        "original_2024_DOI":"10.5061/dryad.c2fqz61gv",
        "associated_original_2024_article_DOI":"10.1111/1365-2664.14586",
        "related_2026_functional_article_DOI":"10.1111/rec.70592",
        "original_source_species_taxon_or_guild_cells_read":0,
        "source_original_workbook_or_full_archive_downloaded":False,
        "ecological_effects_scored":0,
        "old_Ecuador_Finland_Chiu_Ramberg_Traylor_BALA_GEB_unreopened":True,
        "status":"SOURCE_ORIGINAL_DATASET_UNOPENED"}
    try:
        receipt["original_publisher_file_manifest"]=original()
        receipt["status"]=receipt["original_publisher_file_manifest"]["status"]
    except SourceStop as e:
        receipt["status"]="SOURCE_PUBLISHER_METADATA_ACCESS_OR_FILE_SCHEMA_STOP"
        receipt["source_stop_code"]=str(e)
    except Exception as e:
        receipt["status"]="SOURCE_ORIGINAL_METADATA_RUNTIME_STOP"
        receipt["error_class"]=type(e).__name__
    path=Path(a.out)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(receipt,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print("SWEDEN2024_SOURCE_METADATA_STATUS",receipt["status"])
    print("ORIGINAL_BEETLE_GUILD_RESPONSE_READ",receipt["original_source_species_taxon_or_guild_cells_read"])

if __name__=="__main__":
    main()
