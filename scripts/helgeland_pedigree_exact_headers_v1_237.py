#!/usr/bin/env python3
"""Source-locked published Dryad files v1.237: verify bytes and HEADERS only.
Do not analyze any breeder/pedigree observations.
"""
import argparse,csv,hashlib,io,json,re,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urlparse
BASE="https://datadryad.org/api/v2"
DOI="doi%3A10.5061%2Fdryad.qfttdz0sx"
def get_json(url):
    if not url.startswith(BASE+"/"):raise ValueError("Only Dryad official API")
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"StructuralEcology/1.237"})
    with urllib.request.urlopen(req,timeout=35) as r:
        return json.loads(r.read(100000).decode("utf-8"))
def file_id(x):
    href=(x.get("_links") or {}).get("self",{}).get("href","")
    u=urlparse(href)
    if u.netloc and u.netloc!="datadryad.org":raise ValueError("Foreign Dryad file authority")
    m=re.fullmatch(r"/api/v2/files/(\d+)",u.path)
    if not m:raise ValueError("File self-link shape not verified: "+u.path[:90])
    return int(m.group(1))
def download_href(x,expected_id):
    links=(x.get("_links") or {})
    h=(links.get("stash:download") or {}).get("href")
    if not isinstance(h,str) or not h:
        raise ValueError("No advertised file download link")
    u=urlparse(h)
    if u.netloc and u.netloc!="datadryad.org":
        raise ValueError("Unapproved file transport")
    expected=f"/api/v2/files/{expected_id}/download"
    if u.path!=expected or u.query:
        raise ValueError("Unexpected advertised Dryad file download route")
    return "https://datadryad.org"+u.path
def source_files(data):
    items=data.get("_embedded",{}).get("stash:files")
    if not isinstance(items,list):raise ValueError("No Dryad file list")
    if data.get("total")!=len(items):raise ValueError("Truncated Dryad file list")
    result={}
    for x in items:
        name=x.get("path") or x.get("filename") or x.get("name")
        if not name or name in result:raise ValueError("Missing or duplicate source name")
        result[name]=x
    return result
def header_line(raw):
    # Do not decode biological records. Read exactly first line after hashes.
    first=raw.splitlines()[0].decode("utf-8-sig")
    delim="\t" if first.count("\t")>0 else ";" if first.count(";")>0 else ","
    cols=next(csv.reader(io.StringIO(first),delimiter=delim))
    return {"delimiter":"TAB" if delim=="\t" else delim,
        "fields":[v.strip().strip('"') for v in cols],
        "field_count":len(cols)}
def audit_metadata(data,expected):
    f=source_files(data)
    if set(f)!=set(expected["file_sha256"]):raise ValueError("Five source file names drift")
    out={}
    for name,item in sorted(f.items()):
        if int(item.get("size",-1))!=expected["bytes"][name]:
            raise ValueError("Source byte size differs from pinned v1.236")
        if item.get("digest")!=expected["file_sha256"][name]:
            raise ValueError("Source digest differs from pinned v1.236")
        id=file_id(item)
        out[name]={"file_id":id,"expected_bytes":expected["bytes"][name],
                  "expected_sha256":expected["file_sha256"][name],
                  "verified_advertised_download_link":download_href(item,id)}
    return out
def main():
    p=argparse.ArgumentParser()
    p.add_argument("contract",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    c=json.loads(a.contract.read_text(encoding="utf-8"))
    if c.get("schema")!="structural.helgeland_pedigree_exact_version_header_access.v1_237":
        raise ValueError("Wrong predeclared source")
    expected=c["source"]
    data=get_json(BASE+"/versions/"+str(expected["version_id"])+"/files?per_page=100")
    files=audit_metadata(data,expected)
    receipt={"schema":"structural.helgeland_pedigree_immutable_headers.v1_237",
             "version_id":expected["version_id"],
             "status":"SOURCE_NOT_YET_ATTEMPTED",
             "published_file_metadata":{k:{key:v for key,v in item.items() if key!="verified_advertised_download_link"} for k,item in files.items()},
             "verified_raw_headers":{},
             "readme_variable_terms":[],
             "raw_biological_observation_rows_parsed":0,
             "new_confirmatory_systems":0,
             "GEB_scientific_HOLD":True,
             "eBird_used":False}
    for name,item in sorted(files.items()):
        try:
            req=urllib.request.Request(item["verified_advertised_download_link"],
                 headers={"User-Agent":"StructuralEcology/1.237"})
            with urllib.request.urlopen(req,timeout=35) as r:
                raw=r.read(item["expected_bytes"]+1)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as exc:
            receipt["status"]="TECHNICAL_STOP_SOURCE_DOWNLOAD_ACCESS"
            receipt["technical_failure"]={"name":name,"exception_type":type(exc).__name__,
                    "http_status":getattr(exc,"code",None)}
            break
        if len(raw)!=item["expected_bytes"] or hashlib.sha256(raw).hexdigest()!=item["expected_sha256"]:
            raise ValueError("Source original bytes do not match v1.236 digest")
        if name.endswith(".txt"):
            receipt["verified_raw_headers"][name]=header_line(raw)
        else:
            txt=raw.decode("utf-8-sig")
            terms=("natal.island","adult.island","lastobs.island","dam","sire","recruit")
            receipt["readme_variable_terms"]=[t for t in terms if t.lower() in txt.lower()]
    else:
        receipt["status"]="PASS_FIVE_SOURCE_FILE_SHA256_AND_HEADERS_ONLY"
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,sort_keys=True))
if __name__=="__main__":main()
