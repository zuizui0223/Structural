#!/usr/bin/env python3
"""v1.242 read ONLY 2021 Ranke et al. published Dryad file META.

Checks potential native exact island-distance data/geo files without guessing
breeding-site centroids or downloading any biology/source file.
"""
import argparse,json,re,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urlparse
BASE="https://datadryad.org/api/v2"
ENC="doi%3A10.5061%2Fdryad.v41ns1rx1"
DOI="10.5061/dryad.v41ns1rx1"
def get(url):
    if not url.startswith(BASE+"/"):raise ValueError("Unapproved source host")
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"StructuralEcology/1.242"})
    with urllib.request.urlopen(req,timeout=35) as response:
        return json.loads(response.read(250000).decode("utf-8"))
def objects(x):
    if isinstance(x,dict):
        yield x
        for z in x.values():yield from objects(z)
    if isinstance(x,list):
        for z in x:yield from objects(z)
def version_ids(v):
    out=[]
    for z in objects(v):
        if not isinstance(z,dict) or "versionNumber" not in z:continue
        status=z.get("curationStatus")
        if status not in (None,"Published"):continue
        vid=z.get("id")
        if not isinstance(vid,int):
            href=(z.get("_links") or {}).get("self",{}).get("href","")
            u=urlparse(href)
            if u.netloc and u.netloc!="datadryad.org":
                raise ValueError("Unexpected Dryad version host")
            match=re.fullmatch(r"/api/v2/versions/(\d+)",u.path)
            if match is None:raise ValueError("Version self link does not identify frozen source")
            vid=int(match.group(1))
        out.append((int(z["versionNumber"]),vid))
    return sorted(set(out))
def headers_only(dataset,versions,files):
    ident=str(dataset.get("identifier","")).lower()
    if ident not in (DOI.lower(),"doi:"+DOI.lower()):
        raise ValueError("Metadata DOI not original Ranke 2021")
    vv=version_ids(versions)
    if not vv:raise ValueError("No published Dryad version metadata")
    highest=vv[-1]
    fl=(files.get("_embedded") or {}).get("stash:files")
    if not isinstance(fl,list) or files.get("total")!=len(fl):
        raise ValueError("Source file list is missing or paginated")
    names=[]
    for row in fl:
        path=row.get("path") or row.get("filename") or row.get("name")
        if not isinstance(path,str) or not path or path in {f["filename"] for f in names}:
            raise ValueError("Ambiguous original Ranke source file name")
        names.append({"filename":path,
                      "bytes":row.get("size"),
                      "checksum":row.get("digest"),
                      "potential_distance_or_spatial_metadata":
                          bool(re.search("distance|coord|location|site|geograph|island|spatial",
                                         path,re.IGNORECASE))})
    return {"schema":"structural.helgeland_rank2021_distance_source_preflight.v1_242",
            "status":"PASS_ONLY_AUTHOR_2021_DRYAD_FILE_METADATA_NO_DISTANCE_MATRIX_VERIFIED",
            "source_DOI":DOI,
            "all_published_versions":vv,
            "selected_published_version_id":highest[1],
            "selected_published_version_number":highest[0],
            "file_count":len(names),
            "file_metadata":names,
            "candidate_filenames":sorted(x["filename"] for x in names if x["potential_distance_or_spatial_metadata"]),
            "distance_matrix_or_breeding_location_coordinates_ACTUALLY_VERIFIED":False,
            "biological_outcome_rows_read":0,
            "eBird_used":False,"GEB_scientific_HOLD":True}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result={"schema":"structural.helgeland_rank2021_distance_source_preflight.v1_242",
            "status":"SOURCE_METADATA_ACCESS_NOT_YET_CONFIRMED",
            "source_DOI":DOI,
            "biological_outcome_rows_read":0,"distance_matrix_or_breeding_location_coordinates_ACTUALLY_VERIFIED":False,
            "eBird_used":False,"GEB_scientific_HOLD":True}
    try:
        dataset=get(BASE+"/datasets/"+ENC)
        v=get(BASE+"/datasets/"+ENC+"/versions")
        vv=version_ids(v)
        if not vv:raise ValueError("No source version")
        files=get(BASE+"/versions/"+str(vv[-1][1])+"/files?per_page=100")
        result=headers_only(dataset,v,files)
    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as exc:
        result["status"]="STOP_ORIGINAL_PUBLISHED_DRYAD_METADATA_TRANSPORT"
        result["transport_error"]={"name":type(exc).__name__,"http_status":getattr(exc,"code",None)}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
