#!/usr/bin/env python3
"""Zarges 2026: original publisher manifest and header-only admission.
No abundance, OTU counts, wood values or ecological scores.
The workbook parser loads shared-string metadata; only first-row cell values
are inspected. No claims of original bytes remaining unread.
"""
import argparse,csv,hashlib,io,json,re,urllib.error,urllib.parse,urllib.request
from pathlib import Path

BASE="https://datadryad.org"
DOI="10.5061/dryad.k6djh9wns"
API=BASE+"/api/v2/datasets/"+urllib.parse.quote("doi:"+DOI,safe="")
ROLES={"bacteria_OTU.csv","Bioenergy_Okala_2025.csv","fungi_OTU_FAM.csv","log_data.xlsx","README.md","ste_xylo.xlsx"}
HEADER_FILES=("log_data.xlsx","ste_xylo.xlsx","Bioenergy_Okala_2025.csv","fungi_OTU_FAM.csv")
UA={"User-Agent":"Structural-Zarges2026-temporal-source-only/1.0"}
class Stop(ValueError):pass

def require(p,msg):
    if not p: raise Stop(msg)

def official(href):
    u=urllib.parse.urljoin(BASE,href or "")
    p=urllib.parse.urlsplit(u)
    require(p.scheme=="https" and p.hostname=="datadryad.org" and p.port in (None,443) and p.path.startswith("/api/v2/"),"NONORIGINAL_API_LINK")
    return u

def get(url,cap,accept):
    try:
        req=urllib.request.Request(official(url),headers={**UA,"Accept":accept})
        with urllib.request.urlopen(req,timeout=40) as r:
            require(r.status==200,"HTTP_NON200")
            b=r.read(cap+1)
            require(len(b)<=cap,"BODY_SIZE_STOP")
            return b
    except urllib.error.HTTPError as e:
        raise Stop("PUBLISHER_HTTP_"+str(e.code)) from e
    except (OSError,TimeoutError) as e:
        raise Stop("PUBLISHER_TRANSPORT_"+type(e).__name__) from e

def meta(url):
    return json.loads(get(url,1500000,"application/json"))

def link(obj,rel):
    u=(obj.get("_links",{}).get(rel) or {}).get("href")
    require(isinstance(u,str) and bool(u),"MISSING_PUBLISHER_"+rel)
    return official(u)

def manifest():
    d=meta(API)
    require(DOI in str(d.get("identifier") or d.get("doi") or "").lower(),"DOI_MISMATCH")
    v=meta(link(d,"stash:version"))
    vf=link(v,"stash:files")
    index=meta(vf+("&" if "?" in vf else "?")+"per_page=100")
    rows=index.get("_embedded",{}).get("stash:files")
    require(isinstance(rows,list) and len(rows)==6,"ORIGINAL_SIX_FILE_ROSTER_STOP")
    out={}
    for f in rows:
        path=f.get("path") or f.get("filename") or ""
        name=path.split("/")[-1]
        require(name in ROLES and name not in out,"ORIGINAL_ROLE_MISMATCH")
        fid=f.get("id")
        if not fid:
            m=re.search(r"/files/(\d+)(?:/|$)",(f.get("_links",{}).get("self") or {}).get("href",""))
            if m:fid=int(m.group(1))
        size=f.get("size"); digest=str(f.get("digest") or "").lower()
        require(isinstance(fid,int) and isinstance(size,int) and 0<size<=40_000_000,"ORIGINAL_FILE_ID_OR_SIZE_STOP")
        require(re.fullmatch(r"[0-9a-f]{64}",digest) is not None and str(f.get("digestType") or "").upper().replace("-","")=="SHA256","ORIGINAL_SHA256_MISSING")
        out[name]={"id":fid,"size":size,"sha256":digest}
        # The original official file download relation is read only from the file manifest.
        if name in HEADER_FILES:
            out[name]["download"]=link(f,"stash:download")
    require(set(out)==ROLES,"ORIGINAL_SIX_FILE_COVERAGE_STOP")
    published=str(v.get("publicationDate") or d.get("publicationDate") or "")
    require(published.startswith("2026-06-22"),"VERSION_DATE_NOT_20260622")
    return out,{"version_publication_date":published,"license":d.get("license") or v.get("license"),"original_file_manifest":{k:{i:a[i] for i in ("id","size","sha256")} for k,a in out.items()}}

# Fixed public README labels only; unknown headers never exported.
SAFE={"plot","treat","year","species","number","id","mc","otu","family","fam","dbh.cm","vol.m3","fc","cc","bark.i.intact","bark.i.injured","bark.i.free","totlenght","trees.cut.2022","hv.treat","mm.treat","net_cv","gross_cv","c","n","h"}
for y in (2022,2023,2024):
    SAFE.update((f"beetle.sampl.start.{y}",f"beetle.sampl.end.{y}",f"sample.surface.cm2.{y}"))
SAFE|={"wp.ii.bark","wp.ii.xylem","lat","long","treat.person","treat.time.sec"}
PLOTS=set("AU BB BR BU DI EB GO HU LA LE NH NR RE RO RW SE SO TH WI WU".split())
TREATS=set("KON GES HV1 HV2 MEN HEN".split())
TIMES={"I","II","III","IV","V"}

def profile_header(fields):
    clean=[str(x).strip() if x is not None else "" for x in fields]
    low=[x.casefold() for x in clean]
    # Strict documented site/treatment/time pattern for diagnostics only:
    # not an authorization to join until actual grammar and author semantics confirmed.
    times={t:0 for t in TIMES}
    recognized=set()
    for x in clean:
        p=re.split(r"[_\-.]",x)
        if len(p)==3 and p[0] in PLOTS and p[1] in TREATS and p[2] in TIMES:
            times[p[2]]+=1; recognized.add(tuple(p))
    return {"header_count":len(clean),"blank_count":sum(not x for x in clean),
            "duplicate_nonblank":sum(n-1 for n in __import__("collections").Counter(x for x in clean if x).values()),
            "exact_public_method_field_matches":sorted(set(low)&SAFE),
            "documented_pattern_counts_by_time":times,
            "unique_documented_pattern_tokens":len(recognized),
            "nonempty_headers_outside_allowlist_or_pattern":sum(bool(x) for x in clean)-sum(x.casefold() in SAFE for x in clean)-sum(times.values())}

def header_only(blob,name):
    if name.endswith(".xlsx"):
        import openpyxl
        wb=openpyxl.load_workbook(io.BytesIO(blob),read_only=True,data_only=False,keep_links=False)
        try:
            return {"format":"xlsx","sheet_count":len(wb.worksheets),
                    "sheets":[{"sheet_index":i+1,**profile_header(next(ws.iter_rows(min_row=1,max_row=1,values_only=True),()))} for i,ws in enumerate(wb.worksheets)],
                    "shared_string_metadata_may_be_deserialized":True}
        finally:wb.close()
    first=io.BytesIO(blob).readline(500001)
    require(bool(first) and len(first)<=500000,"CSV_FIRST_HEADER_LIMIT")
    txt=first.decode("utf-8-sig",errors="strict").rstrip("\r\n")
    dlm=max((",", ";","\t"),key=txt.count)
    return {"format":"csv","separator":{",":"comma",";":"semicolon","\t":"tab"}[dlm],**profile_header(next(csv.reader([txt],delimiter=dlm)))}

def test():
    p=profile_header(["OTU","AU_KON_II","AU_GES_II","AU_KON_III","unrecognized"])
    assert p["documented_pattern_counts_by_time"]["II"]==2 and p["unique_documented_pattern_tokens"]==3
    assert p["nonempty_headers_outside_allowlist_or_pattern"]==1
    assert header_only(b"plot;treat;year;species;number\nA;B;2023;X;123\n","x.csv")["header_count"]==5
    for bad in ("https://example.com/api/v2/files/1","https://datadryad.org/private/x"):
        try:official(bad)
        except Stop:continue
        raise AssertionError("nonofficial link accepted")
    print("ZARGES_HEADER_ONLY_SYNTHETIC_PASS")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--test",action="store_true")
    a.add_argument("--out",default="zarges_source/receipt.json")
    args=a.parse_args();test()
    if args.test:return
    r={"schema":"structural.zarges2026.temporal_source_manifest_and_header_only.v1","original_doi":DOI,
       "status":"SOURCE_UNOPENED","headers":{},"original_numeric_biology_cells_scored":0,
       "original_data_rows_semantically_inspected":0,"new_ecological_effects_scored":0,"raw_source_exported":False}
    try:
        files,m=manifest();r["publisher"]=m
        r["status"]="MANIFEST_PASS"
        for name in HEADER_FILES:
            f=files[name]
            blob=get(f["download"],f["size"],"application/octet-stream")
            require(len(blob)==f["size"] and hashlib.sha256(blob).hexdigest()==f["sha256"],"ORIGINAL_FILE_SHA_OR_SIZE_DRIFT")
            r["headers"][name]={"source_sha256_verified":True,**header_only(blob,name)}
            del blob
        r["status"]="ORIGINAL_FOUR_HEADERS_READ_NO_BIOLOGICAL_ROWS_SCORED"
    except Stop as e:r["status"]="SOURCE_ACCESS_OR_SCHEMA_STOP";r["reason"]=str(e)
    except Exception as e:r["status"]="SOURCE_EXECUTION_STOP";r["error_class"]=type(e).__name__
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
