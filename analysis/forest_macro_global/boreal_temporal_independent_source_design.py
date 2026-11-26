#!/usr/bin/env python3
"""Independent repeated forest cohorts, publisher/source-design gates only.
No species identity, count, abundance, or coordinate values are interpreted.
Public files only. STOP independently on access or schema error.
"""
import argparse,csv,io,json,re,hashlib,urllib.request,urllib.parse,urllib.error
from pathlib import Path
import openpyxl
from macdonald2026_boreal190_mendeley_original_metadata_only import extract_files
from sweden2024_restoration_original_dryad_metadata_only import fetch as dryad_meta,href

class Stop(ValueError):pass
def require(x,m):
    if not x: raise Stop(m)

def get(url,host,cap,accept="*/*"):
    p=urllib.parse.urlsplit(url)
    require(p.scheme=="https" and p.hostname==host,"SOURCE_ORIGIN_INVALID")
    req=urllib.request.Request(url,headers={"User-Agent":"Structural-forest-source-design-only/1.0","Accept":accept})
    with urllib.request.urlopen(req,timeout=40) as r:
        p=urllib.parse.urlsplit(r.url)
        require(p.scheme=="https" and p.hostname==host and r.status==200,"SOURCE_REDIRECT_OR_HTTP_STOP")
        b=r.read(cap+1)
        require(len(b)<=cap,"SOURCE_SIZE_STOP")
        return b

def jsonget(url,host):
    return json.loads(get(url,host,2000000,"application/json"))

def canada(o):
    doi="10.5061/dryad.msbcc2fvq"
    d=dryad_meta("https://datadryad.org/api/v2/datasets/"+urllib.parse.quote("doi:"+doi,safe=""))
    require(doi in str(d.get("identifier") or d.get("doi") or "").casefold(),"EMEND_DOI_DRIFT")
    v=dryad_meta(href(d["_links"]["stash:version"]["href"]))
    require(str(v.get("publicationDate","")).startswith("2020-05-27"),"EMEND_VERSION_DRIFT")
    url=href(v["_links"]["stash:files"]["href"])
    f=dryad_meta(url+("&" if "?" in url else "?")+"per_page=100")
    arr=f.get("_embedded",{}).get("stash:files",[])
    require(len(arr)==1,"EMEND_FILE_COUNT_DRIFT")
    a=arr[0]; name=a.get("path") or a.get("filename")
    require(name=="EMEND_Carabids_15.csv","EMEND_FILENAME_DRIFT")
    o.update(original_doi=doi,publication_date=v.get("publicationDate"),license=d.get("license") or v.get("license"),
             file={"name":name,"id":a.get("id"),"size":a.get("size"),"digest":a.get("digest"),"digest_type":a.get("digestType")},
             original_data_file_GETs=0,status="EMEND_ORIGINAL_MANIFEST_ONLY")
    # Do not download yet: Dryad file API access previously denied for other
    # datasets. Freeze the actual official manifest first, no bypass/retry.

def finland(o):
    base="https://api.data.mendeley.com/datasets/dkwgwnbtb7"
    a="application/vnd.mendeley-public-dataset.1+json,application/json"
    m=json.loads(get(base+"?version=1","api.data.mendeley.com",600000,a))
    require(isinstance(m,dict) and str(m.get("id"))=="dkwgwnbtb7" and str(m.get("version"))=="1","FINLAND_ID_VERSION_DRIFT")
    title=str(m.get("name") or m.get("title") or "")
    require("boreal ground beetles" in title.casefold(),"FINLAND_TITLE_DRIFT")
    o.update(original_doi="10.17632/dkwgwnbtb7.1",title=title,license=m.get("license") or m.get("licence"))
    rows=extract_files(json.loads(get(base+"/files?version=1","api.data.mendeley.com",600000,a)))
    require(bool(rows),"FINLAND_EMPTY_MANIFEST")
    o.update(files=rows,original_data_file_GETs=0,status="FINLAND_ORIGINAL_MANIFEST_ONLY")

EST_RECORD="20348149"
EST_FILES={
    "0.0_README_v2.txt":"bedb6ba464d2755510127da8aa85313f",
    "0.1_taxonomy_v2.xlsx":"95a5c899edfb4fd8abe9881b0478b83f",
    "1_subsets_stands_v3.xlsx":"39fd695aeeafec38941a0bda36da4372",
    "2_details_v2.xlsx":"9cfa2bca05fc2ad9df482466f1b67ed2",
    "stands_shapefile.zip":"93623f4a9401c102fea63894df9ba8df"
}
def generic(v):
    return re.sub(r"[^a-z0-9]","",str(v or "").casefold())
def est_file(name,size):
    require(name in EST_FILES and isinstance(size,int) and 0<size<=14000000,"EST_FILE_ID_OR_SIZE")
    raw=get("https://zenodo.org/records/"+EST_RECORD+"/files/"+urllib.parse.quote(name)+"?download=1","zenodo.org",size)
    require(len(raw)==size and hashlib.md5(raw).hexdigest()==EST_FILES[name],"EST_FILE_DIGEST_DRIFT")
    return raw

# Only an explicitly identified author metadata sheet may disclose field names
# and short descriptions about years, sampling, stand ID or management.
FIELD_WORDS=re.compile(r"stand|subset|year|date|survey|inventory|sampling|trap|management|treatment|forest|effort|method|succession|beetl",re.I)
def method_sheet(ws):
    out=[]
    for i,row in enumerate(ws.iter_rows(values_only=True),1):
        if i>300:raise Stop("EST_METADATA_SHEET_ROW_CAP")
        vals=[str(x).strip() for x in row if isinstance(x,str) and x.strip()]
        if vals and FIELD_WORDS.search(vals[0]):
            out.append({"metadata_row":i,"first_field":vals[0][:160],
                        "method_description":" | ".join(vals[1:])[:400]})
    return out

def first_header(ws,allowed):
    # Only row 1; unknown strings not exported (could be taxon labels).
    row=next(ws.iter_rows(min_row=1,max_row=1,values_only=True),())
    matches=[]
    for i,x in enumerate(row,1):
        if isinstance(x,str) and generic(x) in allowed:
            matches.append({"field":x,"column":i})
    return {"header_width":len(row),"recognized_method_fields":matches,
            "other_nonblank_header_cells":sum(x is not None and str(x).strip()!="" for x in row)-len(matches)}
SAFE={"standid","subsetid","year","surveyyear","inventoryyear","beetleyear","yearbeetles","beetlesyear","yearofsurvey","yearofinventory","trapid","trap","method","samplingmethod","management","managementhistory","managementbackground","treatment","foresttype","sitetype","successionalstage","standage","date","samplingyear","beetlesurveyyear","beetlesurveyyears","beetlesurvey","beetles","speciesgroup","taxongroup","group","samplingeffort","effort"}
def estonia(o):
    d=jsonget("https://zenodo.org/api/records/"+EST_RECORD,"zenodo.org")
    m=d.get("metadata",{})
    require(str(d.get("id"))==EST_RECORD and d.get("doi")=="10.5281/zenodo."+EST_RECORD,"EST_RECORD_DRIFT")
    require("hemiboreal forests" in str(m.get("title","")).casefold(),"EST_TITLE_DRIFT")
    require(m.get("access_right")=="open","EST_ACCESS_NOT_OPEN")
    files={x["key"]:x for x in d.get("files",[])}
    require(set(files)==set(EST_FILES),"EST_FIVE_FILE_ROSTER_DRIFT")
    for name,x in files.items():
        require(x.get("checksum","").casefold()=="md5:"+EST_FILES[name],"EST_PUBLISHER_MD5_DRIFT")
    o.update(original_doi=d.get("doi"),title=m.get("title"),license=m.get("license"),
        manifest=[{"name":n,"size":f.get("size"),"md5":EST_FILES[n]} for n,f in sorted(files.items())])
    # Workbook bytes are retrieved, but only metadata sheets and first header
    # rows interpreted. openpyxl can deserialize shared strings. No claim that
    # all biological bytes remain unopened.
    o["workbooks"]={}
    for name,meta_name,data_name in (
        ("1_subsets_stands_v3.xlsx","1.0_metadata_subsets_stands","1.2_stands"),
        ("2_details_v2.xlsx","2.0_metadata_detailed","2.4_beetle_detailed")):
        raw=est_file(name,files[name]["size"])
        wb=openpyxl.load_workbook(io.BytesIO(raw),read_only=True,data_only=False,keep_links=False)
        try:
            o["workbooks"][name]={"source_md5_verified":True,"sheet_names":wb.sheetnames}
            require(meta_name in wb.sheetnames and data_name in wb.sheetnames,"EST_DOCUMENTED_SHEET_NAME_DRIFT")
            rec=o["workbooks"][name]
            rec["author_method_metadata"]=method_sheet(wb[meta_name])
            rec["first_header"]=first_header(wb[data_name],SAFE)
        finally:wb.close()
    o["status"]="EST_AUTHENTIC_METHOD_AND_HEADER_ONLY"
    o["beetle_repeated_stand_count_verified"]=False

def test():
    w=openpyxl.Workbook();s=w.active
    s.append(["stand_ID","year","SpeciesX"]);s.append(["sample_A",2001,100])
    q=first_header(s,SAFE)
    assert len(q["recognized_method_fields"])==2 and q["other_nonblank_header_cells"]==1
    s=w.create_sheet("metadata");s.append(["stand_ID","plot identity"]);s.append(["year","survey year"])
    assert len(method_sheet(s))==2
    assert generic("Stand_ID")=="standid"
    print("BOREAL_SOURCE_DESIGN_SYNTHETIC_PASS")

def main():
    p=argparse.ArgumentParser();p.add_argument("--test",action="store_true");p.add_argument("--out",default="boreal_temporal_source/receipt.json");a=p.parse_args();test()
    if a.test:return
    r={"schema":"structural.boreal_temporal_independent_source_design.v1","original_response_cells_interpreted":0,
       "ecological_effects_scored":0,"raw_source_exported":False,"sources":{}}
    for label,fn in (("Canada_EMEND",canada),("Finland_Koivula",finland),("Estonia_Lohmus",estonia)):
        o={};r["sources"][label]=o
        try:fn(o)
        except urllib.error.HTTPError as e:o.update(status="PUBLISHER_HTTP_STOP",http=e.code)
        except Exception as e:o.update(status="SOURCE_DESIGN_STOP",error_class=type(e).__name__,reason=str(e) if isinstance(e,ValueError) else None)
    path=Path(a.out);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps(r,sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
