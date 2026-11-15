#!/usr/bin/env python3
"""Lettenmaier et al. original 12-year host-tree experiment: metadata gate only.

Only original Zenodo 17337484 REST JSON, NO archive/source biological files
downloaded. The original observation grain of logs/sites/years stays UNKNOWN.
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

DOI="10.5281/zenodo.17337484"
URL="https://zenodo.org/api/records/17337484"

def source_metadata():
    out={
        "schema":"structural.Lettenmaier_three_host_deadwood12year_original_Zenodo_sourceonly.v1",
        "original_record_DOI":DOI,
        "original_Article_DOI":"10.1111/1365-2656.70183",
        "reported_beetle_individuals_author_article_not_recomputed":35059,
        "reported_beetle_species_author_article_not_recomputed":297,
        "reported_original_tree_species_author_article":["Picea abies","Abies alba","Fagus sylvatica"],
        "reported_original_longitudinal_years_author_article":12,
        "site_plot_log_year_independence_NOT_established":True,
        "published_spruce_start_offset_and_emergence_trap_repositioning_require_source_crosswalk":True,
        "original_biological_rows_tree_wood_and_species_values_NOT_READ":True,
        "original_Finland_PREDICTS_NEON_BALA_GEB_results_UNCHANGED":True,
        "eBird_used":False,
    }
    try:
        with urllib.request.urlopen(urllib.request.Request(
            URL,headers={"User-Agent":"Structural-official-Zenodo-source-only-2026/1.0","Accept":"application/json"}
        ),timeout=28) as resp:
            body=resp.read(800000)
            if resp.status!=200 or len(body)>=800000:
                out["status"]="SOURCE_STOP_ZENODO_RECORD_NON200_OR_SIZE"
                out["status_code"]=resp.status
                return out
        obj=json.loads(body.decode("utf-8"))
    except urllib.error.HTTPError as e:
        out["status"]="SOURCE_STOP_ZENODO_RECORD_HTTP"
        out["status_code"]=e.code
        return out
    except (urllib.error.URLError, OSError, TimeoutError,ValueError) as e:
        out["status"]="SOURCE_STOP_ZENODO_RECORD_TRANSPORT"
        out["error_class"]=type(e).__name__
        return out
    md=obj.get("metadata") or {}
    out["original_source_record_metadata_ok"]=True
    out["published_data_title"]=str(md.get("title",""))[:210]
    out["record_publication_date"]=md.get("publication_date")
    out["record_version"]=md.get("version")
    out["record_access_right"]=md.get("access_right") or md.get("access_status") or obj.get("access",{}).get("record")
    out["record_license"]=md.get("license")
    out["record_DOI"]=obj.get("doi")
    out["published_file_metadata_only"]=[]
    arr=obj.get("files") or []
    if isinstance(arr,dict):
        arr=list((arr.get("entries") or {}).values())
    for q in arr:
        if not isinstance(q,dict): continue
        out["published_file_metadata_only"].append({
            "original_filename":q.get("key") or q.get("filename"),
            "size_bytes":q.get("size"),
            "checksum":q.get("checksum") or q.get("checksum_sha256"),
            "file_mime_type":q.get("mimetype") or q.get("mime_type"),
        })
    out["published_original_file_count"]=len(out["published_file_metadata_only"])
    legal=out["record_license"]
    license_id=(legal.get("id") or legal.get("title") or "") if isinstance(legal,dict) else str(legal)
    isopen=("cc-by" in license_id.lower() or "cc0" in license_id.lower() or
            "cc-by-sa" in license_id.lower())
    # Do not assume "open access" automatically permits raw redistributions;
    # only print published original license metadata, no original payload.
    out["published_license_recognized_standard_research_reuse"]=isopen
    out["status"]=(
      "SOURCE_PUBLISHED_OPEN_RECORD_METADATA_READY_FOR_ORIGINAL_LOG_GRAIN_AUDIT"
      if out["published_original_file_count"]>0 and isopen else
      "SOURCE_METADATA_RECEIVED_RIGHTS_OR_FILES_REQUIRE_REVIEW"
    )
    return out


def known_truth():
    m={"license":{"id":"cc-by-4.0"}}
    assert m["license"]["id"].lower().startswith("cc-by-")
    assert URL.endswith("/17337484")
    print("SYNTHETIC_ZENODO_12YEAR_METADATA_ONLY_RIGHTS_AND_FILE_GATES_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if not a.out:p.error("need --out")
    result=source_metadata()
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"longterm_12year_three_host_saproxylic_original_Zenodo_sourceonly.json").write_text(
       json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":main()
