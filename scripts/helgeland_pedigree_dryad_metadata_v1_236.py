#!/usr/bin/env python3
"""v1.236 Dryad 2025 pedigree dataset SOURCE METADATA ONLY.

Query exact DOI/version/file-list via documented Dryad REST API.
DO NOT download, decode or score published offspring/reproduction values.
"""
import argparse,json,urllib.request,urllib.parse
from pathlib import Path

DOI="10.5061/dryad.qfttdz0sx"
ENC="doi%3A10.5061%2Fdryad.qfttdz0sx"
BASE="https://datadryad.org/api/v2"
FILES={"LRS.txt","ARS_Survival.txt","Rectype_LRS.txt",
       "Rectype_ARS_Survival.txt","README.md"}

def get_json(url):
    if not url.startswith(BASE+"/"):
        raise ValueError("Source endpoint outside documented Dryad API")
    request=urllib.request.Request(url,headers={"User-Agent":"StructuralScience/1.236",
                                                  "Accept":"application/json"})
    with urllib.request.urlopen(request,timeout=35) as resp:
        data=resp.read(300000)
    return json.loads(data.decode("utf-8"))

def objects(data):
    """Walk JSON recursively; never interpret any phenotype or response."""
    if isinstance(data,dict):
        yield data
        for value in data.values():yield from objects(value)
    elif isinstance(data,list):
        for value in data:yield from objects(value)

def versions(data):
    # Dryad HAL versions may expose their ID in _links.self.href and not
    # in an 'id' key. The collection must still have versionNumber.
    options=[]
    for x in objects(data):
        if not isinstance(x,dict) or "versionNumber" not in x:
            continue
        vid=x.get("id")
        if not isinstance(vid,int):
            href=(x.get("_links") or {}).get("self",{}).get("href","")
            from urllib.parse import urlparse
            import re
            parsed=urlparse(href)
            if parsed.netloc and parsed.netloc!="datadryad.org":
                raise ValueError("Version links outside pinned Dryad host")
            m=re.fullmatch(r"/api/v2/versions/(\d+)",parsed.path)
            if not m:
                raise ValueError("Unrecognized version HAL self link")
            vid=int(m.group(1))
        if x.get("curationStatus") not in (None,"Published"):
            continue
        options.append({**x,"id":vid})
    return list({int(x["id"]):x for x in options}.values())

def files(data):
    found=[]
    for x in objects(data):
        if not isinstance(x,dict):continue
        name=x.get("path") or x.get("filename") or x.get("name")
        if isinstance(name,str) and name.rsplit("/",1)[-1] in FILES:
            found.append(x)
    return {str(x.get("path") or x.get("filename") or x.get("name")).rsplit("/",1)[-1]:x
            for x in found}

def audit(dataset,versions_json,file_json):
    if str(dataset.get("identifier","")).lower() not in (
            DOI.lower(),"doi:"+DOI.lower()):
        raise ValueError("Unexpected dataset DOI in Dryad metadata")
    vv=versions(versions_json)
    if not vv:raise ValueError("No discoverable Published Dryad version object")
    latest=sorted(vv,key=lambda x:(int(x.get("versionNumber",0)),int(x["id"])))[-1]
    found=files(file_json)
    if set(found)!=FILES:
        raise ValueError("Dryad file-list differs from five predeclared files")
    file_receipt={}
    for name in sorted(FILES):
        x=found[name]
        file_receipt[name]={"file_id":x.get("id"),"byte_size":x.get("size"),
             "digest_metadata":x.get("digest"),
             "url_present":bool(x.get("downloadUrl") or x.get("_links")),
             "name":name}
    return {
        "schema":"structural.helgeland_pedigree_dryad_metadata_preflight.v1_236",
        "status":"PASS_DRYAD_PUBLISHED_FIVE_FILE_METADATA_ONLY",
        "dataset_DOI":DOI,
        "publication_date_from_web":"2025-03-25",
        "version_id":latest["id"],"version_number":latest.get("versionNumber"),
        "available_version_IDs":sorted(x["id"] for x in vv),
        "exact_five_file_metadata":file_receipt,
        "downloaded_raw_reproductive_file_bodies":False,
        "biological_rows_semantically_read":0,
        "paper_prior":"Saatoglu et al. 2025 already reports immigrant annual/lifetime fitness and exported recruit advantages",
        "same_Helgeland_archipelago_as_2021_2026":True,
        "new_independent_confirmatory_system_admitted":False,
        "GEB_scientific_HOLD":True,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    ds=get_json(BASE+"/datasets/"+ENC)
    version_json=get_json(BASE+"/datasets/"+ENC+"/versions")
    vv=versions(version_json)
    if not vv:
        # Only metadata keys and primitive metadata types; no biological rows.
        print("VERSION_METADATA_TOP_TYPE",type(version_json).__name__)
        if isinstance(version_json,dict):
            print("VERSION_METADATA_TOP_KEYS",sorted(version_json.keys()))
            for key,val in version_json.items():
                if isinstance(val,dict):
                    print("VERSION_METADATA_CHILD",key,"keys",sorted(val.keys()))
                elif isinstance(val,list):
                    print("VERSION_METADATA_CHILD",key,"list_length",len(val),
                          "first_type",type(val[0]).__name__ if val else None,
                          "first_keys",sorted(val[0].keys()) if val and isinstance(val[0],dict) else None)
        embedded=version_json.get("_embedded",{}) if isinstance(version_json,dict) else {}
        entries=embedded.get("stash:versions",[])
        if entries and isinstance(entries[0],dict):
            print("VERSION_ENTRY_KEYS",sorted(entries[0].keys()))
            print("VERSION_ENTRY_METADATA", {k:entries[0].get(k) for k in ("versionNumber","versionStatus","curationStatus")})
            print("VERSION_SELF_LINK",entries[0].get("_links",{}).get("self",{}))
        raise ValueError("No Dryad version ID available; source metadata shape requires explicit repair")
    latest=sorted(vv,key=lambda x:(int(x.get("versionNumber",0)),int(x["id"])))[-1]
    fl=get_json(BASE+"/versions/"+str(latest["id"])+"/files")
    r=audit(ds,version_json,fl)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,sort_keys=True,indent=2)+"\n")
    print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
