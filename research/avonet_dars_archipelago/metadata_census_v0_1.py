#!/usr/bin/env python3
"""Response-blind source census for the pre-specified bird/AVONET parallel system.

Reads only repository/file metadata plus README/Dataset_information prose.
It does not download or parse any true-island species presence/absence matrix.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from urllib.request import Request, urlopen

DARS_REPO="txm676/DARs"
DARS_COMMIT="8b381ff26e3d6f4da17730dda0c5ab7dbad12eed"
TREE_URL=f"https://api.github.com/repos/{DARS_REPO}/git/trees/{DARS_COMMIT}?recursive=1"
INFO_URL=f"https://raw.githubusercontent.com/{DARS_REPO}/{DARS_COMMIT}/Dataset_information.txt"
README_URL=f"https://raw.githubusercontent.com/{DARS_REPO}/{DARS_COMMIT}/README.md"
AVONET_ARTICLE_ID=16586228
AVONET_META_URL=f"https://api.figshare.com/v2/articles/{AVONET_ARTICLE_ID}"
PREDICTOR_PATH="Data/Predictors/world_clim_all_ETP.csv"
PREDICTOR_URL=f"https://raw.githubusercontent.com/{DARS_REPO}/{DARS_COMMIT}/{PREDICTOR_PATH}"
GID_LAYER_URL="https://data-gis.unep-wcmc.org/server/rest/services/Hosted/WCMC031_GID2_OSM_2015/FeatureServer/1"
GID_META_URL=GID_LAYER_URL+"?f=json"
GID_COUNT_URL=GID_LAYER_URL+"/query?where=1%3D1&returnCountOnly=true&f=json"

def fetch(url:str):
    req=Request(url,headers={"User-Agent":"Structural-AVONET-DARs-metadata-census/0.1"})
    with urlopen(req,timeout=180) as r:
        raw=r.read()
    return raw,{
        "url":url,
        "bytes":len(raw),
        "sha256":hashlib.sha256(raw).hexdigest(),
    }

def canonical_sha(x)->str:
    return hashlib.sha256(
        json.dumps(x,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    ).hexdigest()

def main()->int:
    tree_raw,tree_meta=fetch(TREE_URL)
    tree=json.loads(tree_raw)
    entries=tree.get("tree",[])
    if not isinstance(entries,list):
        raise RuntimeError("DARs tree response missing tree list")

    true_prefix="Data/Island_datasets/True_island_datasets/"
    true_files=[
        {
            "path":row["path"],
            "blob_sha":row.get("sha"),
            "size":row.get("size"),
        }
        for row in entries
        if row.get("type")=="blob"
        and str(row.get("path","")).startswith(true_prefix)
        and str(row.get("path","")).lower().endswith(".csv")
        and "/Alternative_versions/" not in str(row.get("path",""))
    ]
    true_files.sort(key=lambda x:x["path"])

    predictor_files=[
        {
            "path":row["path"],
            "blob_sha":row.get("sha"),
            "size":row.get("size"),
        }
        for row in entries
        if row.get("type")=="blob"
        and str(row.get("path","")).startswith("Data/Predictors/")
    ]
    predictor_files.sort(key=lambda x:x["path"])

    species_files=[
        {
            "path":row["path"],
            "blob_sha":row.get("sha"),
            "size":row.get("size"),
        }
        for row in entries
        if row.get("type")=="blob"
        and str(row.get("path","")).startswith("Data/Species_datasets/")
    ]
    species_files.sort(key=lambda x:x["path"])

    info_raw,info_meta=fetch(INFO_URL)
    readme_raw,readme_meta=fetch(README_URL)
    info=info_raw.decode("utf-8",errors="replace")
    readme=readme_raw.decode("utf-8",errors="replace")

    # Parse only dataset headings and explicitly stated island counts from prose.
    # Species matrix bytes are never opened here.
    heading_re=re.compile(r"^(.+?)\s*-\s*(\d+)\s*$")
    island_count_re=re.compile(r"\b(\d+)\s+islands?\b",re.I)
    headings=[]
    current=None
    for line in info.splitlines():
        line=line.strip()
        m=heading_re.match(line)
        if m:
            current={"heading":m.group(1).strip(),"dataset_number":int(m.group(2))}
            headings.append(current)
            continue
        if current and "n_islands_text" not in current:
            m=island_count_re.search(line)
            if m:
                current["n_islands_text"]=int(m.group(1))

    pred_raw,pred_meta=fetch(PREDICTOR_URL)
    pred_rows=list(csv.DictReader(io.StringIO(pred_raw.decode("utf-8-sig"))))
    true_names={row["path"].split("/")[-1] for row in true_files}
    true_predictors=[row for row in pred_rows if row.get("Dataset") in true_names]
    if len(true_predictors)!=len(true_files):
        missing=sorted(true_names-{row.get("Dataset") for row in true_predictors})
        raise RuntimeError("predictor rows missing for true-island files: "+", ".join(missing))
    type_counts={}
    for key in ("Type_coarse","Type_V_fine","Type_fine","Type_fine2"):
        counts={}
        for row in true_predictors:
            v=row.get(key,"")
            counts[v]=counts.get(v,0)+1
        type_counts[key]=dict(sorted(counts.items()))
    predictor_summary={
        "source":pred_meta,
        "rows":true_predictors,
        "type_counts":type_counts,
        "missing_iso":sum(row.get("Iso") in ("","NA",None) for row in true_predictors),
        "missing_mean_dist":sum(row.get("MeanDist") in ("","NA",None) for row in true_predictors),
        "content_opened":True,
        "role":"response-independent archipelago-level predictor metadata only",
    }

    gid_raw,gid_meta=fetch(GID_META_URL)
    gid=json.loads(gid_raw)
    gid_count_raw,gid_count_meta=fetch(GID_COUNT_URL)
    gid_count=json.loads(gid_count_raw)
    gid_schema={
        "service_metadata":gid_meta,
        "feature_count_metadata":gid_count_meta,
        "feature_count":gid_count.get("count"),
        "name":gid.get("name"),
        "geometryType":gid.get("geometryType"),
        "objectIdField":gid.get("objectIdField"),
        "maxRecordCount":gid.get("maxRecordCount"),
        "fields":[
            {
                "name":row.get("name"),
                "alias":row.get("alias"),
                "type":row.get("type"),
            }
            for row in gid.get("fields",[])
        ],
        "feature_values_opened":False,
        "geometry_values_opened":False,
    }

    av_raw,av_meta=fetch(AVONET_META_URL)
    av=json.loads(av_raw)
    av_files=[
        {
            "id":f.get("id"),
            "name":f.get("name"),
            "size":f.get("size"),
            "computed_md5":f.get("computed_md5"),
            "download_url":f.get("download_url"),
        }
        for f in av.get("files",[])
    ]

    payload={
        "schema":"structural.avonet_dars_metadata_census.v0_1",
        "status":"RESPONSE_SEALED_METADATA_ONLY",
        "selection_provenance":"bird/AVONET was specified as a parallel system before the GIFT burned pilot was opened",
        "response_values_accessed":False,
        "dars_species_matrix_bytes_opened":False,
        "dars_source":{
            "repository":DARS_REPO,
            "commit":DARS_COMMIT,
            "tree":tree_meta,
            "dataset_information":info_meta,
            "readme":readme_meta,
        },
        "true_island_response_surface":{
            "directory":true_prefix,
            "csv_file_count":len(true_files),
            "files":true_files,
            "files_fingerprint":canonical_sha(true_files),
            "content_opened":False,
        },
        "response_blind_predictor_surface":{
            "files":predictor_files,
            "files_fingerprint":canonical_sha(predictor_files),
            "predictor_content":predictor_summary,
        },
        "global_island_database_schema":gid_schema,
        "avonet_or_trait_surface":{
            "dars_species_files":species_files,
            "dars_species_files_content_opened":False,
            "figshare_article_id":AVONET_ARTICLE_ID,
            "figshare_title":av.get("title"),
            "figshare_doi":av.get("doi"),
            "figshare_version":av.get("version"),
            "figshare_license":av.get("license"),
            "figshare_files":av_files,
            "figshare_metadata":av_meta,
            "trait_values_opened":False,
        },
        "dataset_information_heading_audit":{
            "count":len(headings),
            "rows":headings,
            "source_is_metadata_prose":True,
        },
        "readme_contract":{
            "presence_absence_matrix_declared":"presence-absence matrix" in readme,
            "predictors_declared":all(x in readme for x in ("Bio1_m","Bio12_m","Iso","MeanDist","Type_")),
            "avonet_declared":"AVONET" in readme,
        },
    }
    payload["source_fingerprint"]=canonical_sha({
        "dars_commit":DARS_COMMIT,
        "true_files":true_files,
        "predictor_files":predictor_files,
        "species_files":species_files,
        "info_sha256":info_meta["sha256"],
        "readme_sha256":readme_meta["sha256"],
        "avonet_version":av.get("version"),
        "avonet_doi":av.get("doi"),
        "avonet_files":av_files,
        "predictor_content_sha256":pred_meta["sha256"],
        "gid_schema_sha256":gid_meta["sha256"],
        "gid_count_sha256":gid_count_meta["sha256"],
    })
    print(json.dumps(payload,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
