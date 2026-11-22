#!/usr/bin/env python3
"""Two novel Swedish forest-beetle original publisher metadata gates (NO biology).

Frostgard et al. 2026: Dryad 10.5061/dryad.gqnk98t49
Ramberg et al. 2026: Zenodo 23021809.
No author CSV, species, stand or stump file download whatsoever.
"""
import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DRYAD_DOI="doi:10.5061/dryad.gqnk98t49"
ZENODO_ID=23021809
D_ORIGIN="https://datadryad.org"
Z_ORIGIN="https://zenodo.org"
REQUIRED={"ModelData.csv","Speciesdata.csv","README.md"}
UA={"User-Agent":"Structural-forest-beetle-original-source-metadata/1.0",
    "Accept":"application/json"}

def official_url(url, domain):
    p=urllib.parse.urlparse(url)
    if p.scheme!="https" or p.netloc!=domain or p.username or p.password:
        raise ValueError("SOURCE_BAD_OFFICIAL_ORIGIN")
    if domain=="datadryad.org" and not p.path.startswith("/api/v2/"):
        raise ValueError("SOURCE_BAD_DRYAD_API_PATH")
    if domain=="zenodo.org" and not p.path.startswith("/api/records/"):
        raise ValueError("SOURCE_BAD_ZENODO_API_PATH")
    return url

def dryad_href(href):
    p=urllib.parse.urlparse(href)
    if not p.scheme and not p.netloc and href.startswith("/api/v2/"):
        return official_url(D_ORIGIN+href,"datadryad.org")
    return official_url(href,"datadryad.org")

def get(url,domain):
    official_url(url,domain)
    try:
        r=urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=28)
        with r:
            b=r.read(900001)
            if len(b)>900000:
                return {"status":"STOP_METADATA_CAP"}
            if r.status!=200:
                return {"status":"STOP_HTTP","http":r.status}
            try:
                return {"status":"PASS","object":json.loads(b)}
            except (UnicodeDecodeError,ValueError):
                return {"status":"STOP_JSON"}
    except urllib.error.HTTPError as e:
        return {"status":"STOP_HTTP","http":e.code}
    except Exception as e:
        return {"status":"STOP_TRANSPORT","error_type":type(e).__name__}

def dryad_file_index(j):
    entries=(j.get("_embedded") or {}).get("stash:files") or []
    out=[]
    for f in entries:
        filename=f.get("path") or f.get("filename") or ""
        if not filename:continue
        fid=f.get("id") if isinstance(f.get("id"),int) else None
        for k in ["self","stash:download"]:
            u=((f.get("_links") or {}).get(k) or {}).get("href","")
            if not u:continue
            try:
                src=dryad_href(u)
                p=urllib.parse.urlparse(src)
                m=re.fullmatch(r"/api/v2/files/([0-9]+)(?:/download)?",p.path)
                if m:
                    fid=int(m.group(1))
            except ValueError:
                continue
        out.append({
            "filename":filename.split("/")[-1],
            "size_bytes":f.get("size"),
            "checksum":f.get("digest"),
            "digest_type":f.get("digestType"),
            "publisher_file_id":fid
        })
    return out

def source_dryad():
    out={"doi":"10.5061/dryad.gqnk98t49",
         "required_original_files":sorted(REQUIRED),
         "source_original_species_or_tree_records_read":0,
         "study_count":1,
         "author_reported_trees":{"birch":60,"pine":60},
         "author_reported_stands":3,
         "status":"SOURCE_METADATA_HOLD"}
    d=get(D_ORIGIN+"/api/v2/datasets/"+urllib.parse.quote(DRYAD_DOI,safe=""),"datadryad.org")
    out["dataset_request_status"]=d["status"]
    if d["status"]!="PASS":
        out["status"]="SOURCE_DRYAD_API_STOP"
        out["http"]=d.get("http")
        return out
    x=d["object"]
    out["title"]=str(x.get("title",""))[:210]
    out["license"]=x.get("license")
    out["visibility"]=x.get("visibility")
    v=(x.get("_links") or {}).get("stash:version",{}).get("href")
    if not v:
        out["status"]="SOURCE_VERSION_LINK_HOLD"
        return out
    z=get(dryad_href(v),"datadryad.org")
    out["version_status"]=z["status"]
    if z["status"]!="PASS":
        out["status"]="SOURCE_VERSION_ACCESS_STOP"
        return out
    x=z["object"]
    out["version_publication_date"]=x.get("publicationDate")
    f=(x.get("_links") or {}).get("stash:files",{}).get("href")
    if not f:
        out["status"]="SOURCE_FILE_INDEX_LINK_HOLD"
        return out
    u=dryad_href(f)
    f=get(u+("&" if "?" in u else "?")+"per_page=100","datadryad.org")
    out["file_index_status"]=f["status"]
    if f["status"]!="PASS":
        out["status"]="SOURCE_FILE_INDEX_ACCESS_STOP"
        return out
    files=dryad_file_index(f["object"])
    out["original_files"]=files
    names={row["filename"] for row in files}
    out["required_files_present"]=sorted(names & REQUIRED)
    out["required_files_missing"]=sorted(REQUIRED-names)
    out["status"]="SOURCE_METADATA_FILES_READY" if not REQUIRED-names else "SOURCE_REQUIRED_FILES_MISSING_HOLD"
    return out

def source_zenodo():
    out={"record":ZENODO_ID,"expected_doi":"10.5281/zenodo.23021809",
         "species_or_stump_values_read":0,"new_biological_scores":0,
         "status":"SOURCE_METADATA_HOLD"}
    z=get(Z_ORIGIN+"/api/records/"+str(ZENODO_ID),"zenodo.org")
    out["api_status"]=z["status"]
    if z["status"]!="PASS":
        out["status"]="SOURCE_ZENODO_API_STOP"
        out["http"]=z.get("http")
        return out
    x=z["object"]
    md=x.get("metadata") or {}
    out["returned_record_id"]=x.get("id")
    out["returned_doi"]=x.get("doi") or md.get("doi")
    out["title"]=str(md.get("title",""))[:200]
    out["publication_date"]=md.get("publication_date")
    out["license"]=md.get("license")
    out["access_right"]=md.get("access_right") or md.get("access_status")
    files=x.get("files") or []
    if isinstance(files,dict):
        files=list((files.get("entries") or {}).values())
    out["original_files"]=[{"filename":f.get("key"),"size_bytes":f.get("size"),
                             "checksum":f.get("checksum")}
                            for f in files if isinstance(f,dict)][:50]
    out["status"]=("SOURCE_ZENODO_FILE_METADATA_READY"
       if x.get("id")==ZENODO_ID and
          str(out["returned_doi"]).lower()==out["expected_doi"]
          and bool(out["original_files"]) else "SOURCE_ZENODO_IDENTITY_OR_FILES_HOLD")
    return out

def test():
    fake={"_embedded":{"stash:files":[{"path":"ModelData.csv","size":70,
            "_links":{"self":{"href":"/api/v2/files/333"}}}]}}
    x=dryad_file_index(fake)
    assert len(x)==1 and x[0]["publisher_file_id"]==333
    for bad,host in [("https://random.example/api/v2/a","datadryad.org"),
                     ("https://zenodo.org/private/data","zenodo.org")]:
        try:
            official_url(bad,host)
            raise AssertionError("bad URL must fail")
        except ValueError:
            pass
    assert REQUIRED=={"ModelData.csv","Speciesdata.csv","README.md"}
    print("SOURCE_ONLY_OFFICIAL_METADATA_KNOWN_TRUTH_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",default="sweden2026_sourceonly_metadata/receipt.json")
    a=ap.parse_args()
    test()
    if a.test:return
    receipt={"schema":"structural.sweden2026_beetle_two_sources_metadata_only.v1",
      "Frostgard_2026_Dryad":source_dryad(),
      "Ramberg_2026_Zenodo":source_zenodo(),
      "original_source_specimen_or_site_values_read":0,
      "original_source_file_bytes_downloaded":0,
      "ecological_effects_fitted":0,
      "previous_2025_Sweden_401_hold_unchanged":True,
      "prior_Ecuador_Finland_Germany_BALA_GEB_sealed":True,
      "eBird_used":False,"TinyFish_used":False}
    p=Path(a.out);p.parent.mkdir(exist_ok=True,parents=True)
    p.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    for n,x in [("FROSTGARD",receipt["Frostgard_2026_Dryad"]),
                ("RAMBERG",receipt["Ramberg_2026_Zenodo"])]:
        print(n+"_SOURCE_ONLY_STATUS",x["status"],"FILES_N",len(x.get("original_files",[])))
    print("ORIGINAL_BIOLOGICAL_ROWS_READ",receipt["original_source_specimen_or_site_values_read"])

if __name__=="__main__":
    main()
