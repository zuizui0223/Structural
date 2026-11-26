#!/usr/bin/env python3
"""Pilis FP2B8 public OSF manifest and bounded first-header source audit only."""
import argparse,csv,io,json,hashlib,re,urllib.request,urllib.parse,urllib.error
from pathlib import Path
from collections import Counter
NODE="fp2b8"
ROOT="https://api.osf.io/v2/nodes/"+NODE
class Stop(ValueError):pass
def req(x,m):
    if not x:raise Stop(m)
def metadata(url):
    p=urllib.parse.urlsplit(url)
    req(p.scheme=="https" and p.hostname=="api.osf.io" and (p.path=="/v2/nodes/"+NODE+"/" or p.path.startswith("/v2/nodes/"+NODE+"/files/")),"OFFICIAL_NODE_PATH_REQUIRED")
    r=urllib.request.Request(url,headers={"Accept":"application/vnd.api+json, application/json","User-Agent":"Structural-Pilis-public-metadata/1.0"})
    with urllib.request.urlopen(r,timeout=40) as h:
        q=urllib.parse.urlsplit(h.url)
        req(q.scheme=="https" and q.hostname=="api.osf.io" and h.status==200,"OFFICIAL_METADATA_RESPONSE_REQUIRED")
        b=h.read(2000001)
        req(len(b)<=2000000 and "html" not in h.headers.get("Content-Type","").casefold(),"METADATA_SIZE_OR_TYPE_STOP")
    return json.loads(b),hashlib.sha256(b).hexdigest()
def roster(pages):
    known=set();out=[]
    for page in pages:
        req(isinstance(page.get("data"),list),"INVALID_FILE_LIST")
        for x in page["data"]:
            a=x.get("attributes",{});fid=x.get("id")
            req(isinstance(fid,str) and fid and fid not in known,"FILE_ID_DUPLICATE_OR_MISSING")
            known.add(fid)
            kind=a.get("kind");name=a.get("name")
            req(kind in {"file","folder"} and isinstance(name,str) and bool(name),"FILE_METADATA_INVALID")
            size=a.get("size")
            if kind=="file":req(isinstance(size,int) and size>=0,"FILE_SIZE_INVALID")
            hashes=a.get("extra",{}).get("hashes",{})
            out.append({"kind":kind,"name":name,"size":size,"published_hashes":hashes if isinstance(hashes,dict) else {},"id":fid,"download":x.get("links",{}).get("download")})
    return out
def public_file(x):
    u=x["download"] or "";p=urllib.parse.urlsplit(u)
    req(p.scheme=="https" and (p.hostname=="osf.io" or (p.hostname or "").endswith(".osf.io")),"OFFICIAL_FILE_LINK_REQUIRED")
    req(0<x["size"]<=2000000,"FILE_SIZE_LIMIT")
    with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":"Structural-Pilis-source-header/1.0"}),timeout=45) as h:
        # Permit normal publisher file-storage redirect, never alternative guessed URL.
        req(urllib.parse.urlsplit(h.url).scheme=="https" and h.status==200,"PUBLIC_FILE_RESPONSE_STOP")
        b=h.read(x["size"]+1)
    req(len(b)==x["size"],"PUBLISHED_SIZE_DRIFT")
    verified={}
    for k in ("md5","sha256"):
        v=x["published_hashes"].get(k)
        if v:
            req(hashlib.new(k,b).hexdigest()==v.lower(),"PUBLISHED_HASH_DRIFT")
            verified[k]=True
    return b,verified
GENERIC={"plot","plotid","stand","standid","block","blockid","rep","replicate","replication","treatment","treat","trt","year","samplingyear","time","date","season","sample","sampleid","site","siteid","trap","trapid","species","taxon","abundance","count","effort","trapdays","activitydensity","cc","c","r","g","p"}
def header(b):
    first=io.BytesIO(b).readline(100001)
    req(bool(first) and len(first)<=100000,"FIRST_HEADER_LIMIT")
    s=first.decode("utf-8-sig",errors="strict").rstrip("\r\n")
    sep=max((",",";","\t"),key=s.count)
    a=next(csv.reader([s],delimiter=sep))
    req(len(a)>=2,"HEADER_NOT_TABULAR")
    return {"header_width":len(a),"recognized_role_fields":[{"column":i+1,"field":x} for i,x in enumerate(a) if re.sub(r"[^a-z0-9]","",x.casefold()) in GENERIC]}
def test():
    a=header(b"block;Treatment;Year;species_a;species_b\n1;CC;2014;2;3\n")
    assert a["header_width"]==5 and len(a["recognized_role_fields"])==3
    fake={"data":[{"id":"1","attributes":{"kind":"file","name":"data.csv","size":10},"links":{"download":"https://osf.io/download/x"}}]}
    assert roster([fake])[0]["size"]==10
    print("PILIS_MANIFEST_AND_HEADER_SYNTHETIC_PASS")
def main():
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--out",default="pilis_source/receipt.json");args=p.parse_args();test()
    if args.test:return
    out={"schema":"structural.pilis_fp2b8.public_source_only.v1","doi":"10.17605/OSF.IO/FP2B8","original_response_cells_interpreted":0,"ecological_effects_scored":0,"raw_data_exported":False}
    try:
        node,h=metadata(ROOT+"/")
        d=node.get("data",{});a=d.get("attributes",{})
        req(d.get("id")==NODE and d.get("type")=="nodes" and a.get("public") is True,"PUBLIC_NODE_IDENTITY_STOP")
        title=str(a.get("title",""))
        out.update(project_title=title,node_sha256=h,public=True)
        req(bool(re.search("carabid|beetle|pilis|forestr",title,re.I)),"SOURCE_TITLE_REVIEW_REQUIRED")
        lr=(d.get("relationships",{}).get("license") or {}).get("links",{}).get("related")
        out["license_relationship_present"]=bool(lr)
        # If licence is explicitly linked, only accept official OSF licence metadata.
        # No original table access before manual source-rights review in this run.
        pages=[];seen=set();next_url=ROOT+"/files/osfstorage/"
        while next_url:
            req(next_url not in seen and len(pages)<5,"PAGINATION_LIMIT")
            seen.add(next_url);q,digest=metadata(next_url);pages.append(q)
            next_url=q.get("links",{}).get("next")
        files=roster(pages)
        out["root_roster"]=[{k:x[k] for k in ("kind","name","size","published_hashes","id")} for x in files]
        out["data_file_bytes_read"]=0
        out["status"]="PILIS_PUBLIC_NODE_MANIFEST_ONLY"
    except urllib.error.HTTPError as e:out.update(status="SOURCE_HTTP_STOP",http=e.code)
    except Stop as e:out.update(status="SOURCE_SCHEMA_STOP",reason=str(e))
    except Exception as e:out.update(status="SOURCE_EXECUTION_STOP",error_type=type(e).__name__)
    q=Path(args.out);q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+"\n");print(json.dumps(out,ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
