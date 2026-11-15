#!/usr/bin/env python3
"""Original source-rights and accessibility gates for external forest beetles.

Swedish 2026 paired 120 trap trees: Dryad official record, file manifest,
one README GET only. European 2026 99 plots: Zenodo metadata RIGHTS only.
No organism, wood, trap, taxon, vegetation, coordinates or RData rows read.
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

DRYAD_DOI="doi:10.5061/dryad.gqnk98t49"
ZENODO_ID="17927769"
DRYAD_ROOT="https://datadryad.org"
REQUIRED={"README.md","ModelData.csv","Speciesdata.csv"}
HEADERS={"User-Agent":"Structural-original-forest-source-2026/1.0","Accept":"application/json"}

class SourceStop(Exception):pass


def get_official_json(url, allowed):
    parsed=urllib.parse.urlparse(url)
    if parsed.scheme!="https" or parsed.hostname not in allowed:
        return {"status":"SOURCE_STOP_WRONG_ORIGIN"}
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=30) as f:
            if f.status!=200:
                return {"status":"SOURCE_STOP_HTTP","http_status":f.status}
            b=f.read(1500000)
        if len(b)>=1500000:
            return {"status":"SOURCE_STOP_TOO_LARGE"}
        return {"status":"ORIGINAL_PUBLISHED_METADATA_OK","data":json.loads(b.decode("utf-8"))}
    except urllib.error.HTTPError as e:
        return {"status":"SOURCE_ACCESS_STOP_HTTP","http_status":e.code}
    except (urllib.error.URLError,TimeoutError,OSError,ValueError) as e:
        return {"status":"SOURCE_ACCESS_STOP_TRANSPORT","class":type(e).__name__}


def make_original_dryad_url(href):
    if not isinstance(href,str): raise SourceStop("SOURCE_STOP_MISSING_OFFICIAL_LINK")
    p=urllib.parse.urlparse(href)
    if p.scheme or p.netloc or not p.path.startswith("/api/v2/"):
        raise SourceStop("SOURCE_STOP_UNTRUSTED_DRYAD_LINK_ORIGIN")
    return DRYAD_ROOT+href


def dryad_access():
    info={
      "original_doi":DRYAD_DOI,
      "author_reported_2024_tree_traps":120,
      "author_reported_paired_plots":30,
      "author_reported_birch_traps":60,
      "author_reported_pine_traps":60,
      "author_reported_burned_stand_groups":3,
      "author_beetle_collection_calendar_year":2024,
      "original_species_rows_and_tree_biology_not_read":True,
      "swedish_sampling_grain_author_reported_NOT_SOURCE_RECONCILED":True,
    }
    res=get_official_json(DRYAD_ROOT+"/api/v2/datasets/"+
              urllib.parse.quote(DRYAD_DOI,safe=""),{"datadryad.org"})
    info["dataset_original_api_status"]=res["status"]
    if res["status"]!="ORIGINAL_PUBLISHED_METADATA_OK":
        info["status"]="SOURCE_STOP_SWEDEN_DATASET_METADATA_UNAVAILABLE"
        if "http_status" in res:info["dataset_http_status"]=res["http_status"]
        return info
    ds=res["data"]
    info["publisher_title"]=str(ds.get("title",""))[:190]
    info["publisher_license"]=ds.get("license")
    info["publisher_visibility"]=ds.get("visibility")
    info["original_dataset_metadata_public"]=True
    try:
        vurl=make_original_dryad_url(ds["_links"]["stash:version"]["href"])
    except (SourceStop,KeyError,TypeError):
        info["status"]="SOURCE_STOP_NO_PUBLISHED_ORIGINAL_VERSION"
        return info
    vv=get_official_json(vurl,{"datadryad.org"})
    info["original_version_api_status"]=vv["status"]
    if vv["status"]!="ORIGINAL_PUBLISHED_METADATA_OK":
        info["status"]="SOURCE_STOP_SWEDEN_ORIGINAL_VERSION_METADATA_UNAVAILABLE"
        return info
    version=vv["data"]
    info["version_published_date"]=version.get("publicationDate")
    try:
        filesurl=make_original_dryad_url(version["_links"]["stash:files"]["href"])
    except (SourceStop,KeyError,TypeError):
        info["status"]="SOURCE_STOP_NO_AUTHOR_FILE_LIST"
        return info
    res=get_official_json(filesurl+("&" if "?" in filesurl else "?")+"per_page=100",{"datadryad.org"})
    info["file_index_original_api_status"]=res["status"]
    if res["status"]!="ORIGINAL_PUBLISHED_METADATA_OK":
        info["status"]="SOURCE_STOP_FILE_METADATA_NOT_ACCESSIBLE"
        return info
    raw=((res["data"].get("_embedded") or {}).get("stash:files") or [])
    info["original_files_metadata"]=[]
    readme_id=None
    for f in raw:
        if not isinstance(f,dict):continue
        name=(f.get("path") or "").split("/")[-1]
        if not name:continue
        meta={
          "published_file":name,
          "published_bytes":f.get("size"),
          "publisher_digest":f.get("digest"),
          "publisher_digest_type":f.get("digestType"),
        }
        info["original_files_metadata"].append(meta)
        if name=="README.md":
            for kind in ("stash:download","self"):
                href=((f.get("_links") or {}).get(kind) or {}).get("href","")
                if not href:continue
                p=urllib.parse.urlparse(href)
                if p.scheme or p.netloc:continue
                match=re.fullmatch(r"/api/v2/files/(\d+)(?:/download)?",p.path)
                if match:
                    readme_id=int(match.group(1))
                    break
    names={f["published_file"] for f in info["original_files_metadata"]}
    info["required_original_files_present"]=sorted(names&REQUIRED)
    info["required_original_files_missing"]=sorted(REQUIRED-names)
    if REQUIRED-names:
        info["status"]="SOURCE_STOP_SWEDEN_PUBLISHED_FILES_INCOMPLETE"
        return info
    if readme_id is None:
        info["status"]="SOURCE_STOP_SWEDEN_README_FILE_ID_NOT_VERIFIED"
        return info
    # A single normal public GET, not authentication bypass.
    readmeurl=f"{DRYAD_ROOT}/api/v2/files/{readme_id}/download"
    try:
        req=urllib.request.Request(readmeurl,headers={"User-Agent":HEADERS["User-Agent"]})
        with urllib.request.urlopen(req,timeout=30) as h:
            content=h.read(100000)
            if h.status!=200:
                info["source_readme_http_status"]=h.status
                info["status"]="SOURCE_STOP_README_NON200"
                return info
        info["source_readme_http_status"]=200
        info["source_readme_bytes"]=len(content)
        info["source_readme_sha256"]=hashlib.sha256(content).hexdigest()
        info["status"]="SWEDEN_RESEARCH_METADATA_AND_README_PUBLISHER_ACCESS_OK"
    except urllib.error.HTTPError as e:
        info["source_readme_http_status"]=e.code
        info["status"]="SOURCE_STOP_SWEDEN_README_HTTP_ACCESS"
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        info["source_readme_transport_class"]=type(e).__name__
        info["status"]="SOURCE_STOP_SWEDEN_README_TRANSPORT"
    return info


def european_context_metadata():
    out={
     "original_zenodo_doi":"10.5281/zenodo.17927769",
     "original_paper_doi":"10.1111/1365-2664.70483",
     "author_reported_original_fir_forest_plots":56,
     "author_reported_original_spruce_forest_plots":28,
     "author_reported_original_oak_forest_plots":15,
     "author_reported_original_total_plots":99,
     "fir_and_spruce_flight_interception_near_1p5m_oak_baited_and_unbaited_canopy_about15m":True,
     "author_original_sampling_design_context_fully_confounded_with_trap_height_and_method":True,
     "original_beetle_and_tree_biodiversity_data_NOT_DOWNLOADED":True,
    }
    r=get_official_json("https://zenodo.org/api/records/"+ZENODO_ID,{"zenodo.org"})
    out["source_record_metadata_status"]=r["status"]
    if r["status"]!="ORIGINAL_PUBLISHED_METADATA_OK":
        if "http_status" in r:out["http_status"]=r["http_status"]
        out["status"]="SOURCE_STOP_ZENODO_RECORD_NOT_ACCESSIBLE"
        return out
    m=r["data"].get("metadata",{})
    out["record_original_title"]=str(m.get("title",""))[:190]
    out["record_date"]=m.get("publication_date")
    out["original_rights_metadata"]=m.get("license")
    out["source_access_right"]=m.get("access_right") or m.get("access_status")
    arr=r["data"].get("files") or []
    if isinstance(arr,dict):
        arr=list((arr.get("entries") or {}).values())
    out["original_published_files"]=[
       {"filename":f.get("key") or f.get("filename"),
        "bytes":f.get("size"),
        "source_checksum":f.get("checksum")}
       for f in arr if isinstance(f,dict)]
    lic=out["original_rights_metadata"]
    lic_id=str(lic.get("id","") if isinstance(lic,dict) else lic).lower()
    out["license_is_standard_CC_BY_OR_CC0"]=lic_id.startswith("cc-by") or lic_id.startswith("cc0")
    out["status"]=(
      "ZENODO_ORIGINAL_METADATA_ONLY_RIGHTS_AND_SOURCE_PRESENT"
      if out["original_published_files"] else "SOURCE_STOP_ZENODO_NO_FILES"
    )
    return out


def synthetic():
    assert make_original_dryad_url("/api/v2/files/1234/download").endswith("/download")
    for bad in ("https://example.org/api/v2/files/10","/../api/v2/files/11"):
        try:
            make_original_dryad_url(bad)
            raise AssertionError("unsafe href accepted")
        except SourceStop:
            pass
    assert sum((56,28,15))==99
    print("SYNTHETIC_DRYAD_HAL_ORIGIN_AND_PUBLISHED_ZENODO_NO_BIOLOGY_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    synthetic()
    if a.test:return
    if not a.out:ap.error("--out required")
    out={
      "schema":"structural.Swedish_2026_birch_pine_paired_tree_v_European_2026_99plot_original_source_gate.v1",
      "source_Sweden_paired_tree":dryad_access(),
      "source_99plot_Europe_3forest_contexts":european_context_metadata(),
      "no_original_taxa_wood_environment_rows_or_species_abundances_read":True,
      "no_new_ecological_effect_scored":True,
      "original_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_results_unchanged":True,
      "eBird_used":False,
    }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"forest_120tree_Sweden_99plot_Europe_original_access_only.json").write_text(
       json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(out,indent=2,ensure_ascii=False))


if __name__=="__main__":main()
