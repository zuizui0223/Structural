#!/usr/bin/env python3
"""Read only exact-original Ranke (2021) file metadata and first header.
No numerical geography or biological source records decoded in this gate.
"""
import argparse,csv,hashlib,io,json,re,urllib.error,urllib.request
from pathlib import Path

BASE="https://datadryad.org/api/v2"
VERSION=136299
LOCK={
"description.txt":(3266,"a8dbce0f8d9f84dbf13b0a1197143cfde83feefb2ff93518655dbcb1959aaa4f"),
"island-pairs.txt":(527964,"c5d4f44a3f3f0987ad2202d66737754238cf199a51eca07d31af46ee48e2226e"),
}
def file_id(entry):
    s=entry["_links"]["self"]["href"]
    if re.fullmatch(r"(?:https://datadryad.org)?/api/v2/files/(\d+)",s) is None:
        raise ValueError("Non-publisher Dryad file self-link")
    return int(s.rsplit("/",1)[-1])

def file_list(api):
    data=api.get("_embedded",{}).get("stash:files",[])
    if len(data)!=api.get("total"):raise ValueError("Incomplete file metadata")
    indexed={x.get("path") or x.get("filename") or x.get("name"):x for x in data}
    for name,(size,sha) in LOCK.items():
        entry=indexed.get(name)
        if entry is None or entry.get("size")!=size or entry.get("digest")!=sha:
            raise ValueError("Original source file name/sha/size drift")
    return {n:file_id(indexed[n]) for n in LOCK}

def urls(source_id):
    return [f"https://datadryad.org/api/v2/files/{source_id}/download",
            f"https://datadryad.org/downloads/file_stream/{source_id}",
            f"https://datadryad.org/stash/downloads/file_stream/{source_id}"]

def try_original(name,source_id):
    size,sha=LOCK[name];attempts=[]
    for url in urls(source_id):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"StructuralResearch/1.243"})
            with urllib.request.urlopen(req,timeout=25) as response:
                raw=response.read(size+1)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as ex:
            attempts.append({"url":url,"status":getattr(ex,"code",None),"kind":type(ex).__name__})
            continue
        if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=sha:
            attempts.append({"url":url,"status":"ORIGINAL_SHA256_OR_SIZE_MISMATCH"})
            continue
        if name=="island-pairs.txt":
            line=raw.splitlines()[0].decode("utf-8-sig",errors="replace")
            delim=max(("\t",";",","),key=lambda x:line.count(x))
            fields=next(csv.reader(io.StringIO(line),delimiter=delim))
            meta={"header":fields,"separator":repr(delim),"numerical_rows_read":0}
        else:
            txt=raw.decode("utf-8-sig",errors="replace")
            meta={"source_documentation_excerpt":txt[:2200],"numerical_rows_read":0}
        return meta,attempts
    return None,attempts

def main():
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    req=urllib.request.Request(BASE+f"/versions/{VERSION}/files?per_page=100",
         headers={"User-Agent":"StructuralResearch/1.243","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=25) as response:
        data=json.loads(response.read(100000))
    ids=file_list(data)
    result={"schema":"structural.ranke2021_original_pair_headers.v1_243",
      "status":"SOURCE_DOWNLOAD_STOP","original_Dryad_version_id":VERSION,
      "verified_original_file_ids":ids,"headers_or_source_documentation":{},"access_failures":{},
      "numeric_distance_rows_decoded":0,"original_529_mammal_heldout_read":False,
      "GEB_scientific_HOLD":True,"eBird_used":False}
    for name in sorted(LOCK):
        content,failures=try_original(name,ids[name])
        if content is None:
            result["access_failures"][name]=failures
            break
        result["headers_or_source_documentation"][name]=content
    else:
        result["status"]="PASS_ORIGINAL_SHA256_FILE_HEADERS_ONLY"
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
