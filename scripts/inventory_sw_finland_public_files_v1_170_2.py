#!/usr/bin/env python3
"""Inventory public SW Finland archive metadata without downloading data files."""
from __future__ import annotations
import argparse,json,urllib.request
from pathlib import Path
from urllib.parse import quote

UA={"User-Agent":"Structural-v1.170.2","Accept":"application/json"}

def get(url:str):
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def zenodo():
    x=get("https://zenodo.org/api/records/4942881")
    files=[]
    for f in x.get("files",[]) or []:
        files.append({
            "key":f.get("key"),
            "size":f.get("size"),
            "checksum":f.get("checksum"),
            "download":(f.get("links") or {}).get("self"),
        })
    return {
        "record_id":x.get("id"),
        "doi":(x.get("metadata") or {}).get("doi"),
        "file_count":len(files),
        "files":files,
    }

def dryad():
    doi="doi:10.5061/dryad.ffbg79cr6"
    dataset_url="https://datadryad.org/api/v2/datasets/"+quote(doi,safe="")
    d=get(dataset_url)
    links=d.get("_links") or {}
    version_url=None
    for key in ("stash:version","stash:latest-version","latestVersion","latest-version"):
        v=links.get(key)
        if isinstance(v,dict) and v.get("href"):
            version_url=v["href"];break
    if not version_url:
        version_url=d.get("latestVersion")
    version=None
    files=[]
    errors=[]
    candidates=[]
    if version_url:
        candidates.append(version_url)
    # Dryad also commonly exposes /versions on the dataset endpoint.
    candidates += [dataset_url+"/versions"]
    seen=set()
    for url in candidates:
        if not url or url in seen:continue
        seen.add(url)
        try:
            obj=get(url)
        except Exception as exc:
            errors.append({"url":url,"error":type(exc).__name__})
            continue
        # If a versions collection, pick embedded latest.
        emb=obj.get("_embedded") if isinstance(obj,dict) else None
        versions=[]
        if isinstance(emb,dict):
            for value in emb.values():
                if isinstance(value,list):
                    versions.extend(v for v in value if isinstance(v,dict))
        version=max(versions,key=lambda v:v.get("versionNumber",0)) if versions else obj
        break
    if isinstance(version,dict):
        vlinks=version.get("_links") or {}
        file_url=None
        for key in ("stash:files","files"):
            v=vlinks.get(key)
            if isinstance(v,dict) and v.get("href"):
                file_url=v["href"];break
        if not file_url and version.get("id"):
            file_url=f"https://datadryad.org/api/v2/versions/{version['id']}/files"
        if file_url:
            try:
                fo=get(file_url)
                emb=fo.get("_embedded") or {}
                raw=[]
                for value in emb.values():
                    if isinstance(value,list):
                        raw.extend(v for v in value if isinstance(v,dict))
                for f in raw:
                    flinks=f.get("_links") or {}
                    download=None
                    for key in ("stash:download","download"):
                        z=flinks.get(key)
                        if isinstance(z,dict) and z.get("href"):
                            download=z["href"];break
                    files.append({
                        "id":f.get("id"),
                        "path":f.get("path") or f.get("name"),
                        "size":f.get("size"),
                        "digest":f.get("digest"),
                        "download":download,
                    })
            except Exception as exc:
                errors.append({"url":file_url,"error":type(exc).__name__})
    return {
        "dataset_doi":doi,
        "dataset_id":d.get("id"),
        "version_id":version.get("id") if isinstance(version,dict) else None,
        "version_number":version.get("versionNumber") if isinstance(version,dict) else None,
        "file_count":len(files),
        "files":files,
        "errors":errors,
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    out={
      "schema":"structural.sw_finland_public_file_inventory.v1_170_2",
      "status":"PUBLIC_METADATA_ONLY_FILE_INVENTORY",
      "zenodo":zenodo(),
      "dryad":dryad(),
      "file_content_downloads":0,
      "row_level_recent_outcome_opened":False,
      "future_summary_values_parsed":0,
      "counts_as_empirical_evidence":False,
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(out,sort_keys=True))
if __name__=="__main__":main()
