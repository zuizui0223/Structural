#!/usr/bin/env python3
"""Original Macdonald et al. 2026 190-dataset meta: public Mendeley METADATA.

No individual source study identities, Chao-Jaccard observations, beetle taxa
or biological response values downloaded. Dataset is an anonymized published
SIMILARITY comparator, not plot x wood x beetle original source data.
"""
from __future__ import annotations
import argparse,json,urllib.error,urllib.request
from pathlib import Path

DOI="10.17632/yt42chsskj.1"
ID="yt42chsskj"
VERSION=1
BASE="https://api.data.mendeley.com/datasets/"+ID
LINKS=(BASE+"?version=1",BASE+"/files?version=1")
UA={"Accept":"application/vnd.mendeley-public-dataset.1+json,application/json",
    "User-Agent":"Structural-Macdonald2026-original-mendeley-METADATA/1.0"}

def request(url):
    if url not in LINKS:
        raise ValueError("SOURCE_ORIGINAL_PUBLIC_MENDELEY_URL_NOT_PINNED")
    try:
        req=urllib.request.Request(url,headers=UA)
        with urllib.request.urlopen(req,timeout=32) as response:
            b=response.read(600001)
            if response.status!=200 or len(b)>600000:
                return {"status":"SOURCE_PUBLIC_API_HTTP_OR_SIZE_STOP"}
            try:
                return {"status":"OK","data":json.loads(b)}
            except (UnicodeDecodeError,ValueError):
                return {"status":"SOURCE_PUBLISHER_JSON_STOP"}
    except urllib.error.HTTPError as e:
        return {"status":"SOURCE_PUBLIC_API_HTTP_STOP","http":e.code}
    except Exception as e:
        return {"status":"SOURCE_PUBLIC_API_TRANSPORT_STOP","type":type(e).__name__}

def extract_files(obj):
    if isinstance(obj,list):
        rows=obj
    elif isinstance(obj,dict):
        rows=obj.get("files") or obj.get("results") or obj.get("data") or []
    else:
        rows=[]
    if isinstance(rows,dict):rows=list(rows.values())
    files=[]
    for f in rows[:80]:
        if not isinstance(f,dict):continue
        c=f.get("content_details") or {}
        files.append({
           "name":str(f.get("filename") or f.get("name") or "")[:220],
           "publisher_file_id":f.get("id"),
           "publisher_size_bytes":f.get("size") or c.get("size"),
           "published_SHA256":c.get("sha256_hash") or f.get("sha256_hash"),
           "publisher_file_type":c.get("content_type"),
           "original_file_bytes_GET_count":0,
        })
    return files

def audit():
    o={"publisher": "Mendeley Data","original_version":1,
       "original_DOI":DOI,"original_study_count_from_paper":190,
       "original_primary_papers_from_paper":87,
       "original_unpublished_studies_from_paper":1,
       "original_study_IDs_anonymized_by_author":True,
       "original_wood_resource_or_beetle_taxon_rows_read":0,
       "status":"SOURCE_MENDELEY_API_METADATA_UNOPENED"}
    record=request(LINKS[0])
    o["publisher_dataset_api_status"]=record["status"]
    if record["status"]!="OK":
        o["status"]="SOURCE_MENDELEY_PUBLIC_API_DATASET_ACCESS_STOP"
        o["http"]=record.get("http")
        return o
    x=record["data"]
    if not isinstance(x,dict):
        o["status"]="SOURCE_MENDELEY_API_UNEXPECTED_OBJECT_SCHEMA_STOP"
        return o
    rid=str(x.get("id") or "")
    if rid and rid!=ID:
        o["status"]="SOURCE_MENDELEY_DATASET_ID_MISMATCH_STOP"
        return o
    o["published_title"]=str(x.get("name") or x.get("title") or "")[:220]
    o["returned_dataset_id"]=rid
    o["returned_version"]=x.get("version")
    o["returned_license"]=x.get("license") or x.get("licence")
    o["published_date"]=x.get("publish_date")
    o["published_DOI_metadata"]=x.get("doi")
    if x.get("version") is not None and str(x["version"])!="1":
        o["status"]="SOURCE_MENDELEY_VERSION_NOT_ONE_STOP"
        return o
    files=request(LINKS[1])
    o["publisher_files_API_status"]=files["status"]
    if files["status"]!="OK":
        o["status"]="SOURCE_MENDELEY_FILE_ROSTER_ACCESS_STOP"
        o["file_api_http"]=files.get("http")
        return o
    f=extract_files(files["data"])
    o["original_file_roster"]=f
    o["original_file_count"]=len(f)
    o["has_original_metadata_entity_level"]=any(
        a["name"].lower()=="metadata_entity_level.xlsx" for a in f)
    o["has_anonymized_arthropod_source_comparison"]=any(
        "bugs_arthropods" in a["name"].lower() for a in f)
    o["status"]=(
        "SOURCE_MENDELEY_VERSION1_FILE_NAMES_AND_METADATA_READY_NO_BIOLOGY"
        if len(f)>0 else "SOURCE_MENDELEY_EMPTY_FILE_LIST_STOP")
    return o

def test():
    fake=[{"filename":"Bugs_Arthropods_AllForest_TRTvsREF-anon.csv",
           "id":"a","size":1024,
           "content_details":{"sha256_hash":"a"*64}}]
    s=extract_files(fake)
    assert s[0]["published_SHA256"]=="a"*64 and s[0]["original_file_bytes_GET_count"]==0
    assert LINKS[0].startswith("https://api.data.mendeley.com/")
    assert DOI=="10.17632/yt42chsskj.1"
    print("MACDONALD2026_ANONYMIZED_BOREAL_METADATA_ONLY_KNOWN_TRUTH_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",default="macdonald2026_mendeley190_metadata/receipt.json")
    a=ap.parse_args()
    test()
    if a.test:return
    receipt={
      "schema":"structural.macdonald2026_boreal_recovery_190_dataset_Mendeley_metadata_only.v1",
      "prior_author_chao_jaccard_beetle_recovery_published_not_new":True,
      "source_original_similarity_or_taxon_values_read":0,
      "new_ecological_effects_scored":0,
      "older_DATASAPROX_PREDICTS_Ecuador_Traylor_BALA_GEB_unreopened":True,
      "mendeley_source_original_files_archived":False,
      "status":"SOURCE_MENDELEY_190_STUDY_UNOPENED"}
    try:
        receipt["publisher"]=audit()
        receipt["status"]=receipt["publisher"]["status"]
    except Exception as e:
        receipt["status"]="SOURCE_MENDELEY_API_PROGRAM_RUNTIME_STOP"
        receipt["error_type"]=type(e).__name__
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("BOREAL190_ORIGINAL_PUBLIC_METADATA_STATUS",receipt["status"])
    print("SPECIES_BIOLOGICAL_ROWS",receipt["source_original_similarity_or_taxon_values_read"])
if __name__=="__main__":
    main()
