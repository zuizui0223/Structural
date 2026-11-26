#!/usr/bin/env python3
"""Pilis public OSF exact folder roster, license and first-header audit.
Follow only publisher-supplied API relationships. Bounded traversal, no
author code execution, no numerical ecological response scoring.
"""
import argparse,csv,hashlib,io,json,re,urllib.parse,urllib.request,urllib.error,zipfile
from pathlib import Path
from pilis2022_fp2b8_full_community_source import ROOT,NODE,metadata,roster,public_file,header,Stop,req

FOLDER="60a754aca480c600370d33c6"
TITLE="Pilis experiment - long-term response of ground beetles"
MAX_PAGES=14
MAX_FOLDERS=5
MAX_FILES=35
MAX_BYTES=6_000_000
GENERIC={"plot","plotid","plotcode","stand","standid","block","blockid","rep","replicate","replication","treatment","treat","trt","year","samplingyear","time","date","season","sample","sampleid","site","siteid","trap","trapid","species","taxon","speciesname","abundance","count","effort","trapdays","activitydensity","management","samplingperiod","period","session","yearperiod","month"}
def link_value(x):
    if isinstance(x,str):return x
    if isinstance(x,dict) and isinstance(x.get("href"),str):return x["href"]
    return None
def related(item,key):
    return link_value((item.get("relationships",{}).get(key) or {}).get("links",{}).get("related"))
def api_url(url,allowed_path):
    p=urllib.parse.urlsplit(url or "")
    req(p.scheme=="https" and p.hostname=="api.osf.io" and p.port in (None,443) and not p.username and not p.password and p.path==allowed_path,"PUBLISHER_RELATION_PATH_STOP")
    return url
def get_json(url,allowed_path):
    url=api_url(url,allowed_path)
    r=urllib.request.Request(url,headers={"Accept":"application/vnd.api+json, application/json","User-Agent":"Structural-Pilis-author-folder-source/1.0"})
    with urllib.request.urlopen(r,timeout=40) as h:
        api_url(h.url,allowed_path);req(h.status==200,"METADATA_STATUS_STOP")
        b=h.read(2000001);req(len(b)<=2000000,"METADATA_CAP")
    a=json.loads(b);req(isinstance(a,dict),"METADATA_OBJECT_REQUIRED")
    return a
def folder_path(item):
    req(item.get("attributes",{}).get("kind")=="folder","FOLDER_RELATION_KIND")
    fid=item.get("id") or ""
    req(re.fullmatch(r"[0-9a-f]{24}",fid) is not None,"FOLDER_ID_GRAMMAR")
    u=related(item,"files")
    # OSF may supply a node-storage or file-resource children relation.
    p=urllib.parse.urlsplit(u or "")
    allowed=(
        "/v2/files/"+fid+"/files/",
        "/v2/nodes/"+NODE+"/files/osfstorage/"+fid+"/",
        "/v2/nodes/"+NODE+"/files/osfstorage/"+fid+"/files/",
    )
    req(p.path in allowed,"AUTHOR_FOLDER_CHILD_LINK_NOT_RECOGNIZED")
    return api_url(u,p.path),p.path
def license_info(node):
    u=related(node,"license")
    if not u:return {"status":"NO_LICENSE_RELATION","allow_header_read":False}
    p=urllib.parse.urlsplit(u)
    req(re.fullmatch(r"/v2/licenses/[A-Za-z0-9_-]+/",p.path) is not None,"LICENSE_RELATION_PATH_STOP")
    q=get_json(u,p.path).get("data",{})
    req(q.get("type")=="licenses","LICENSE_RESOURCE_TYPE_STOP")
    a=q.get("attributes",{})
    name=str(a.get("name") or a.get("title") or "")
    low=name.casefold()
    denied=bool(re.search(r"non.?commercial|no.?derivatives|by.nc|by.nd|all rights reserved|no license",low))
    permitted=not denied and bool(re.search(r"\bcc0\b|creative commons.*attribution|^cc.by\b|^mit license$|^mit$|^apache license|^bsd",low))
    return {"name":name,"status":"EXPLICIT_PERMISSIVE_NAME" if permitted else "LICENSE_REVIEW_HOLD","allow_header_read":permitted}
def crawl(root_folder):
    queue=[(root_folder,"R-archive-for-analyses")]
    all_items=[];seen=set();pages=0;folders=0;folder_paths=set()
    while queue:
        f,path=queue.pop(0)
        fid=f["id"]
        req(fid not in folder_paths and folders<MAX_FOLDERS,"FOLDER_LOOP_OR_LIMIT")
        folder_paths.add(fid);folders+=1
        u,allowed_path=folder_path(f)
        visited=set()
        while u:
            req(u not in visited and pages<MAX_PAGES,"PAGINATION_LOOP_OR_LIMIT")
            visited.add(u);pages+=1
            q=get_json(u,allowed_path)
            arr=q.get("data")
            req(isinstance(arr,list),"FOLDER_FILE_LIST_REQUIRED")
            for item in arr:
                a=item.get("attributes",{});iid=item.get("id")
                name=a.get("name");kind=a.get("kind")
                req(iid and iid not in seen and isinstance(name,str) and name and "/" not in name and "\\" not in name and name not in {".",".."},"FILE_ID_OR_NAME_STOP")
                seen.add(iid);req(len(seen)<=MAX_FILES+MAX_FOLDERS,"CATALOG_LIMIT")
                if kind=="folder":queue.append((item,path+"/"+name));continue
                req(kind=="file" and isinstance(a.get("size"),int) and a["size"]>=0,"FILE_KIND_OR_SIZE_STOP")
                hashes=a.get("extra",{}).get("hashes") or {}
                req(isinstance(hashes,dict),"FILE_HASH_METADATA_INVALID")
                all_items.append({"id":iid,"kind":kind,"name":name,"path":path+"/"+name,"size":a["size"],"published_hashes":hashes,"download":link_value(item.get("links",{}).get("download"))})
            u=link_value(q.get("links",{}).get("next"))
    return all_items,{"folders":folders,"pages":pages}
def csv_header(raw):
    b=io.BytesIO(raw).readline(100001)
    req(0<len(b)<=100000,"HEADER_LIMIT")
    s=b.decode("utf-8-sig",errors="strict").rstrip("\r\n")
    d=max((",",";","\t"),key=s.count)
    h=next(csv.reader([s],delimiter=d))
    req(2<=len(h)<=10000,"HEADER_WIDTH_STOP")
    norm=lambda v:re.sub(r"[^a-z0-9]","",v.casefold())
    return {"width":len(h),"separator":{",":"comma",";":"semicolon","\t":"tab"}[d],"role_fields":[{"column":i+1,"literal":x} for i,x in enumerate(h) if norm(x) in GENERIC],"duplicate_nonblank_headers":sum(n-1 for n in __import__("collections").Counter(x for x in h if x).values())}
def method_code(raw,known_names):
    s=raw.decode("utf-8-sig",errors="strict")
    # Never execute original author code. Report source file references and
    # counts of generic operations only; not source lines or numerical values.
    return {"line_count":len(s.splitlines()),"known_catalog_file_references":sorted(n for n in known_names if n in s),
            "method_token_counts":{k:len(re.findall(p,s,re.I)) for k,p in {
                "read_table":r"\b(read\.csv2?|read\.table|read_delim|read_csv|read_excel)\s*\(",
                "load_object":r"\b(load|readRDS)\s*\(",
                "aggregation":r"\b(aggregate|group_by|summari[sz]e|rowsum|dcast|pivot_wider)\s*\(",
                "plot_block":r"\b(plot|block|plotid|blockid)\b",
                "treatment":r"\b(treatment|treat|trt)\b",
                "year":r"\b(year|season|date|period)\b"}.items()}}
def zip_directory(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        files=z.infolist();req(len(files)<=200,"ZIP_ENTRY_LIMIT")
        # Archive members are listed only; none extracted or executed.
        return {"members":[{"name":x.filename,"bytes":x.file_size,"compressed_bytes":x.compress_size} for x in files if not x.is_dir()],"member_contents_read":0}
def diagnostic(x,raw):
    return {"file_bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}
def test():
    f={"id":FOLDER,"attributes":{"kind":"folder"},"relationships":{"files":{"links":{"related":{"href":"https://api.osf.io/v2/files/"+FOLDER+"/files/"}}}}}
    u,p=folder_path(f);assert p.endswith("/files/") and u.startswith("https://api.osf.io/")
    assert len(csv_header(b"Plot;block;year;TaxonX\n1;1;2015;98\n")["role_fields"])==3
    assert method_code(b"d <- read.csv('example.csv')\n",["example.csv"])["known_catalog_file_references"]==["example.csv"]
    try:api_url("https://example.org/v2/files/a/","/v2/files/a/");raise AssertionError("origin accepted")
    except Stop:pass
    print("PILIS_FOLDER_ROLE_AND_RELATION_SYNTHETIC_PASS")
def main():
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--out",default="pilis_folder/receipt.json");a=p.parse_args();test()
    if a.test:return
    r={"schema":"structural.pilis_fp2b8.folder_roles.v1","original_biological_values_interpreted":0,"new_ecological_effects_scored":0,"raw_source_exported":False,"original_author_code_executed":False,"files":{}}
    try:
        q,nodehash=metadata(ROOT+"/");node=q["data"]
        req(node.get("id")==NODE and node.get("type")=="nodes" and node.get("attributes",{}).get("public") is True and node["attributes"].get("title")==TITLE,"NODE_DRIFT")
        r["public_node_verified"]=True
        root,_=metadata(ROOT+"/files/osfstorage/")
        arr=root.get("data",[])
        req(isinstance(arr,list) and len(arr)==1 and not root.get("links",{}).get("next"),"ROOT_ROSTER_DRIFT")
        f=arr[0];req(f.get("id")==FOLDER and f.get("attributes",{}).get("name")=="R-archive-for-analyses","ROOT_FOLDER_DRIFT")
        files,scope=crawl(f)
        r["folder_catalog"]=scope
        r["file_roster"]=[{k:x[k] for k in ("id","path","size","published_hashes")} for x in files]
        r["license"]=license_info(node)
        r["status"]="PUBLIC_FOLDER_ROSTER_COMPLETE"
        if r["license"]["allow_header_read"]:
            budget=0
            names=[x["name"] for x in files]
            for f in files:
                ext=Path(f["name"]).suffix.casefold()
                if ext not in {".csv",".tsv",".r",".rmd",".zip"}:continue
                if not 0<f["size"]<=2_000_000 or budget+f["size"]>MAX_BYTES:
                    r["files"][f["path"]]={"status":"SIZE_BUDGET_HOLD"};continue
                budget+=f["size"]
                try:
                    b,verified=public_file(f);s=diagnostic(f,b);s["publisher_hashes_verified"]=verified
                    if ext in {".csv",".tsv"}:s["first_header"]=csv_header(b)
                    elif ext in {".r",".rmd"}:s["method_code_diagnostics"]=method_code(b,names)
                    else:s["archive_directory"]=zip_directory(b)
                    s["status"]="SOURCE_ROLE_ONLY_PASS";r["files"][f["path"]]=s
                except urllib.error.HTTPError as e:
                    r["files"][f["path"]]={"status":"SOURCE_FILE_HTTP_STOP","http":e.code}
                    if e.code in {401,403}:break
                except Exception as e:r["files"][f["path"]]={"status":"SOURCE_ROLE_STOP","error":type(e).__name__,"reason":str(e) if isinstance(e,Stop) else None}
            r["status"]="PUBLIC_FOLDER_ROSTER_AND_BOUNDED_ROLES_COMPLETE"
    except urllib.error.HTTPError as e:r.update(status="SOURCE_HTTP_STOP",http=e.code)
    except Stop as e:r.update(status="SOURCE_SCHEMA_STOP",reason=str(e))
    except Exception as e:r.update(status="SOURCE_EXECUTION_STOP",error_type=type(e).__name__)
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps(r,sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
