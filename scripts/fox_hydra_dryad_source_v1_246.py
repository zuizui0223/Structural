#!/usr/bin/env python3
"""Published Fox et al 2017 spatial hydra experiment: Dryad metadata ONLY."""
import argparse,json,re,urllib.request
from pathlib import Path
from urllib.parse import urlparse
API="https://datadryad.org/api/v2"
DOI="10.5061/dryad.2rs23"
ENC="doi%3A10.5061%2Fdryad.2rs23"
NAMES={"data_for_Fox_et_el_2017_nature_ee.csv",
       "README_for_data_for_Fox_et_el_2017_nature_ee.txt"}
def source_json(url):
    if not url.startswith(API+"/"):raise ValueError("Only original Dryad API")
    req=urllib.request.Request(url,headers={"Accept":"application/json",
                                            "User-Agent":"StructuralEcology/1.246"})
    with urllib.request.urlopen(req,timeout=35) as response:
        return json.loads(response.read(300000).decode("utf-8"))
def walk(obj):
    if isinstance(obj,dict):
        yield obj
        for val in obj.values():yield from walk(val)
    elif isinstance(obj,list):
        for val in obj:yield from walk(val)
def original_id(doc,kind):
    if isinstance(doc.get("id"),int):return doc["id"]
    link=((doc.get("_links") or {}).get("self") or {}).get("href","")
    u=urlparse(link)
    if u.netloc not in ("","datadryad.org"):
        raise ValueError("Foreign source host")
    pattern=r"/api/v2/"+kind+r"/(\d+)"
    m=re.fullmatch(pattern,u.path)
    if m is None:raise ValueError("Unrecognized source ID")
    return int(m.group(1))
def published_versions(response):
    matches=set()
    for obj in walk(response):
        if not isinstance(obj,dict) or "versionNumber" not in obj:continue
        if obj.get("curationStatus") not in (None,"Published"):continue
        matches.add((int(obj["versionNumber"]),original_id(obj,"versions")))
    if not matches:raise ValueError("No published Dryad source version")
    return sorted(matches)
def receipt(dataset,ver,filedata):
    if str(dataset.get("identifier","")).lower() not in (DOI.lower(),"doi:"+DOI.lower()):
        raise ValueError("Unexpected original DOI")
    vv=published_versions(ver)
    items=(filedata.get("_embedded") or {}).get("stash:files")
    if not isinstance(items,list) or len(items)!=2 or filedata.get("total")!=2:
        raise ValueError("Original two-file publisher listing missing")
    out={}
    for item in items:
        name=item.get("path") or item.get("filename") or item.get("name")
        sha=item.get("digest")
        size=item.get("size")
        if name not in NAMES or name in out:
            raise ValueError("Unexpected source filename")
        if not isinstance(size,int) or size<1000:
            raise ValueError("Unverified source size")
        # Original archive may expose MD5, SHA256 or no digest. Metadata
        # cannot be promoted to original-byte verification without a check.
        digest=(sha or "").strip().lower() if isinstance(sha,str) else ""
        if re.fullmatch(r"[0-9a-f]{64}",digest):
            algorithm="publisher_sha256"
        elif re.fullmatch(r"[0-9a-f]{32}",digest):
            algorithm="publisher_md5"
        else:
            algorithm="UNVERIFIED_SOURCE_DIGEST"
        out[name]={"id":original_id(item,"files"),"bytes":size,
                   "source_digest_if_present":digest or None,
                   "digest_class":algorithm,
                   "original_file_bytes_read":False}
    return {"schema":"structural.fox_spatial_hydra_published_source_metadata.v1_246",
            "status":("SOURCE_DIGEST_NOT_VERIFIED_HOLD_METADATA_ONLY" if any(x["digest_class"]=="UNVERIFIED_SOURCE_DIGEST" for x in out.values()) else "PASS_PUBLISHED_FOX_DATASET_DIGEST_METADATA_ONLY"),
            "article_DOI":"10.1038/s41559-017-0271-y","data_DOI":DOI,
            "source_version":vv[-1][0],"source_version_id":vv[-1][1],
            "source_files":out,
            "biological_data_rows_read":0,
            "published_spatial_hydra_result_is_prior_art":True,
            "new_independent_confirmatory_systems":0,
            "original_GEB_scientific_HOLD":True,"eBird_used":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    ds=source_json(API+"/datasets/"+ENC)
    v=source_json(API+"/datasets/"+ENC+"/versions")
    vi=published_versions(v)[-1][1]
    files=source_json(API+"/versions/"+str(vi)+"/files?per_page=100")
    r=receipt(ds,v,files)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
