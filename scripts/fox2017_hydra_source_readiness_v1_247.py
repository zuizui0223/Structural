#!/usr/bin/env python3
"""Fox et al 2017 published spatial-hydra dataset source-metadata gate v1.247.

No biological responses, patch values, treatment effects or original mammal
heldout opened. Public Dryad only. README fetch, if accessible, is publisher
method text. A 401/403 is source technical STOP, not scientific disproof.
"""
import argparse,json,re,hashlib,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urlparse

DOI="10.5061/dryad.2rs23"
ENC="doi%3A10.5061%2Fdryad.2rs23"
BASE="https://datadryad.org/api/v2"
FILES={"data_for_Fox_et_el_2017_nature_ee.csv",
       "README_for_data_for_Fox_et_el_2017_nature_ee.txt"}

def source_json(url):
    if not url.startswith(BASE+"/"):
        raise ValueError("Expected official Dryad API only")
    request=urllib.request.Request(url,headers={"User-Agent":"StructuralResearch/1.247",
                                                "Accept":"application/json"})
    with urllib.request.urlopen(request,timeout=35) as response:
        return json.loads(response.read(150000).decode("utf-8"))
def every_dict(o):
    if isinstance(o,dict):
        yield o
        for v in o.values():yield from every_dict(v)
    elif isinstance(o,list):
        for v in o:yield from every_dict(v)
def published_versions(data):
    out=[]
    for d in every_dict(data):
        if "versionNumber" not in d:continue
        if d.get("curationStatus") not in (None,"Published"):
            continue
        n=d.get("id")
        if not isinstance(n,int):
            href=(d.get("_links") or {}).get("self",{}).get("href","")
            parsed=urlparse(href)
            if parsed.netloc and parsed.netloc!="datadryad.org":
                raise ValueError("Unapproved publisher version link")
            m=re.fullmatch(r"/api/v2/versions/(\d+)",parsed.path)
            if not m:raise ValueError("No exact published version identity")
            n=int(m.group(1))
        out.append((int(d["versionNumber"]),n))
    return sorted(set(out))
def file_id(file):
    href=(file.get("_links") or {}).get("self",{}).get("href","")
    p=urlparse(href)
    if p.netloc and p.netloc!="datadryad.org":
        raise ValueError("Foreign source file")
    m=re.fullmatch(r"/api/v2/files/(\d+)",p.path)
    if m is None:raise ValueError("No source file id")
    return int(m.group(1))
def file_metadata(data):
    e=(data.get("_embedded") or {}).get("stash:files")
    if not isinstance(e,list) or data.get("total")!=len(e):
        raise ValueError("Version file list paginated or malformed")
    files={}
    for o in e:
        name=o.get("path") or o.get("filename") or o.get("name")
        if name in files:raise ValueError("Duplicate source name")
        files[name]=o
    if set(files)!=FILES:
        raise ValueError("Fox source file list differs from original published two")
    return {name:{
         "publisher_file_id":file_id(f),
         "bytes":f.get("size"),
         "sha256":f.get("digest"),
         "download_advertised":bool((f.get("_links") or {}).get("stash:download"))
    } for name,f in files.items()}

def check_readme(name,meta):
    if name not in FILES or not name.startswith("README_"):
        raise ValueError("Only publisher README text authorized")
    id=meta["publisher_file_id"]
    n=meta["bytes"]
    if not isinstance(n,int) or n<0 or n>100000:
        raise ValueError("Method note byte bounds unknown")
    checks=[]
    for url in (f"https://datadryad.org/api/v2/files/{id}/download",
                f"https://datadryad.org/downloads/file_stream/{id}"):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"StructuralResearch/1.247"})
            with urllib.request.urlopen(req,timeout=30) as response:
                raw=response.read(n+1)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as err:
            checks.append({"source_route":url.split("/files/")[0] if "/files/" in url else "public_html",
                           "status":getattr(err,"code",None),"kind":type(err).__name__})
            continue
        if len(raw)!=n or hashlib.sha256(raw).hexdigest()!=meta["sha256"]:
            checks.append({"source_route":"publisher","status":"RAW_NOTE_HASH_MISMATCH"})
            continue
        try:content=raw.decode("utf-8-sig")
        except UnicodeDecodeError:content=raw.decode("latin-1")
        lines=content.splitlines()
        terms=("patch","metapop","disp","extinct","treat","day","repl","synchron","count")
        return {"status":"PASS_PUBLISHER_README_ORIGINAL_BYTES",
            "README_line_count":len(lines),
            "method_semantic_lines":[{"line":i+1,"text":s[:230]}
                for i,s in enumerate(lines) if any(z in s.lower() for z in terms)],
            "source_access_errors":checks}
    return {"status":"TECHNICAL_STOP_README_NOT_ACCESSIBLE",
            "README_line_count":None,
            "method_semantic_lines":[],
            "source_access_errors":checks}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    result={
      "schema":"structural.fox2017_hydra_source_readiness.v1_247",
      "status":"SOURCE_METADATA_NOT_YET_VERIFIED",
      "DOI":DOI,
      "source_paper_DOI":"10.1038/s41559-017-0271-y",
      "file_metadata":{},
      "biological_CSV_downloaded_or_read":False,
      "measured_source_delivery_or_off_event_identified":False,
      "new_confirmatory_system_admitted":False,
      "GEB_scientific_HOLD":True,
      "eBird_used":False
    }
    try:
        dataset=source_json(BASE+"/datasets/"+ENC)
        if str(dataset.get("identifier","")).lower() not in (DOI.lower(),"doi:"+DOI.lower()):
            raise ValueError("Unexpected source DOI")
        versions=published_versions(source_json(BASE+"/datasets/"+ENC+"/versions"))
        if not versions:raise ValueError("No published Fox 2017 dataset version")
        version_id=versions[-1][1]
        fm=file_metadata(source_json(BASE+f"/versions/{version_id}/files?per_page=100"))
        result.update({
           "status":"PASS_SOURCE_METADATA_ONLY",
           "published_versions":versions,
           "version_id":version_id,
           "file_metadata":fm
        })
        readme=next(n for n in FILES if n.startswith("README_"))
        result["readme"]=check_readme(readme,fm[readme])
    except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as exc:
        result["status"]="TECHNICAL_STOP_SOURCE_METADATA_TRANSPORT"
        result["transport_error"]={"type":type(exc).__name__,"http_status":getattr(exc,"code",None)}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
