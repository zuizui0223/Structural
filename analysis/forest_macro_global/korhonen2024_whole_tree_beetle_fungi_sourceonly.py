#!/usr/bin/env python3
"""Original DOI-only Dryad whole-spruce-tree beetle-fungal metadata source gate.

Zero specimen, taxon or wood resource observations are downloaded/read.
Maximum one publisher-official README file GET, final STOP on 401/403.
"""
import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
import independent_hostwood_source_registry_gate as old

DOI="doi:10.5061/dryad.44j0zpcng"
REQUIRED={
 "Korhonen_et_al_2024_Beetle_species_metadata.csv",
 "Korhonen_et_al_2024_Beetle_species_presabs.csv",
 "Korhonen_et_al_2024_Beetles_raw_data.csv",
 "Korhonen_et_al_2024_Fungal_OTU_presabs.csv",
 "Korhonen_et_al_2024_Fungal_OTU_taxonomy_and_metadata.csv",
 "Korhonen_et_al_2024_Tree_metadata.csv",
 "README.md",
}
BASE="https://datadryad.org"
UA={"User-Agent":"Structural-sourceonly-whole-tree-fungal-beetle/1.0",
    "Accept":"application/octet-stream, text/plain, */*;q=0.1"}

def admission():
    info={
        "doi":"10.5061/dryad.44j0zpcng",
        "study_published_field_tree_n_from_authors":31,
        "author_published_beetle_sample_rows":124,
        "author_published_fungal_sample_rows":93,
        "author_published_tree_part_grain_unharmonized":True,
        "original_fungal_otu_or_beetle_species_rows_read":0,
        "original_tree_compartment_or_location_values_read":0,
        "original_public_files_downloaded":0,
        "status":"SOURCE_DATASET_METADATA_HOLD",
    }
    base=old.get_public(BASE+"/api/v2/datasets/"+urllib.parse.quote(DOI,safe=""))
    info["original_dataset_API_status"]=base["status"]
    if base["status"]!="SOURCE_METADATA_OK":
        info["status"]="SOURCE_DATASET_METADATA_ACCESS_STOP"
        info["original_API_HTTP"]=base.get("http_status")
        return info
    ds=base["data"]
    info["title"]=str(ds.get("title",""))[:220]
    info["visibility"]=ds.get("visibility")
    info["license"]=ds.get("license")
    ver=(ds.get("_links") or {}).get("stash:version",{}).get("href","")
    try:
        url=old.official_dryad_href(ver)
    except ValueError:
        info["status"]="SOURCE_PUBLISHER_VERSION_LINK_STOP"
        return info
    vv=old.get_public(url)
    info["version_API_status"]=vv["status"]
    if vv["status"]!="SOURCE_METADATA_OK":
        info["status"]="SOURCE_VERSION_ACCESS_STOP"
        return info
    version=vv["data"]
    info["published_version_date"]=version.get("publicationDate")
    file_href=(version.get("_links") or {}).get("stash:files",{}).get("href","")
    try:
        file_url=old.official_dryad_href(file_href)
    except ValueError:
        info["status"]="SOURCE_AUTHOR_FILE_LIST_LINK_STOP"
        return info
    if "?" in file_url:file_url+="&per_page=100"
    else:file_url+="?per_page=100"
    index=old.get_public(file_url,max_bytes=300000)
    info["file_index_API_status"]=index["status"]
    if index["status"]!="SOURCE_METADATA_OK":
        info["status"]="SOURCE_PUBLIC_FILE_INDEX_ACCESS_STOP"
        return info
    files=old.file_names_from_dryad(index["data"])
    info["published_file_count"]=len(files)
    info["public_original_file_manifest"]=files
    names={f["name"] for f in files}
    info["all_exact_seven_files_in_required_roster"]=names==REQUIRED
    info["missing_source_files"]=sorted(REQUIRED-names)
    info["unexpected_source_files"]=sorted(names-REQUIRED)
    if names!=REQUIRED:
        info["status"]="SOURCE_EXACT_FILE_ROSTER_MISMATCH_STOP"
        return info
    readme=next(x for x in files if x["name"]=="README.md")
    fid=readme["author_file_id"]
    if not isinstance(fid,int):
        info["status"]="SOURCE_AUTHOR_README_ID_NOT_VERIFIED_HOLD"
        return info
    # One official publisher-listed README GET (no source CSV requests).
    req=urllib.request.Request(BASE+f"/api/v2/files/{fid}/download",headers=UA)
    try:
        with urllib.request.urlopen(req,timeout=34) as response:
            data=response.read(20001)
            if len(data)>20000 or response.status!=200:
                info["status"]="SOURCE_README_RESPONSE_SIZE_OR_STATUS_STOP"
            else:
                info["original_readme_access_HTTP"]=response.status
                info["original_readme_bytes"]=len(data)
                info["original_readme_SHA256"]=hashlib.sha256(data).hexdigest()
                # no text parsed or copied; original method codebook remains unopened
                info["status"]="SOURCE_README_VERIFIABLE_NO_BEETLE_BIOLOGY"
    except urllib.error.HTTPError as exc:
        info["original_readme_access_HTTP"]=exc.code
        info["status"]="SOURCE_README_HTTP_ACCESS_STOP"
    except Exception as exc:
        info["readme_error_type"]=type(exc).__name__
        info["status"]="SOURCE_README_TRANSPORT_STOP"
    return info

def test():
    assert len(REQUIRED)==7
    assert "Korhonen_et_al_2024_Beetle_species_presabs.csv" in REQUIRED
    assert "Korhonen_et_al_2024_Fungal_OTU_presabs.csv" in REQUIRED
    assert DOI!="doi:10.5061/dryad.3j9kd51s7"
    try:
        old.official_dryad_href("https://wronghost.example/api/v2/files/123")
        raise AssertionError("unsafe URL should stop")
    except ValueError:
        pass
    print("WHOLE_TREE_BEETLE_FUNGUS_SOURCE_ONLY_ORIGIN_TEST_PASS")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--test",action="store_true")
    a.add_argument("--out",default="korhonen2024_whole_tree_sourceonly/receipt.json")
    args=a.parse_args()
    test()
    if args.test:return
    x={
      "schema":"structural.korhonen2024_whole_tree_beetle_fungus_sourceonly.v1",
      "result":admission(),
      "original_organism_source_rows_opened":0,
      "new_ecological_predictive_scores":0,
      "old_Sweden2026_Ramberg_scientific_ZERO_CATCH_STOP_preserved":True,
      "old_Frostgard2026_and_Ramberg2025_HTTP401_UNRETRIED":True,
      "eBird_used":False,"TinyFish_used":False,
    }
    p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("WHOLE_TREE_SOURCE_STATUS",x["result"]["status"],
          "FILES",x["result"].get("published_file_count",0))
    print("NO_ORGANISM_RESPONSES_READ",x["original_organism_source_rows_opened"]==0)

if __name__=="__main__":
    main()
