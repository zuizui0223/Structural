#!/usr/bin/env python3
"""US Georgia original 40-forest Traylor 2023 beetles: Zenodo source-only gate.
Exact official files, MD5 integrity, ORIGINAL HEADER ONLY and README vocabulary.
No original biological species, guild, abundance, site, forest/covariate row
values selected, scored, uploaded or exported.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RECORD=8246615
DOI="10.5281/zenodo.8246615"
HOST="https://zenodo.org"
FILES={
 "READ ME metadata.txt":"8aaaf3b725d9c30fbd46f02a85d157d1",
 "site_forest_variables.csv":"5c4b8c449b5a2f483b4f17df3b54a8fd",
 "species_list_abundance_per_site_functional_group.csv":"4f187aa816ffa72dcc618c6c99feec2b",
}
LIMIT=130000
UA="Structural-Traylor-Georgia-40forest-original-source-only/1.0"

CATEGORIES={
    "site_grain":{"site","siteid","sitecode","site_id","location",
                  "plot","plotid","forest","forestid","studyarea","habitat"},
    "sampling_method_time":{"date","period","samplingdate","collectiondate",
        "year","month","fortnight","collectionperiod","samplingperiod",
        "sampleid","sample","method","trap","trapid","traptype","trapdays",
        "effort","litter","flightsample","flightinterception"},
    "taxon":{"species","speciesname","sp","speciesid","taxon","taxonid",
             "speciescode","family","genus"},
    "guild":{"guild","functionalgroup","feedingguild","feedingtype","fg",
             "saproxylic","saproxylicstatus","trophicgroup","sap_group"},
    "capture_quantity":{"abundance","count","individuals","number",
                        "n","abund","total"},
    "forest_age":{"age","standage","forestage","old","young","foresthistory",
                  "year1938","forestclass","forest_age"},
    "forest_resources":{"deadwood","deadwoodvolume","tree","treevolume",
        "treebasalarea","basalarea","dbh","treecover","treecomposition",
        "treespecies","pinus","quercus","woody","canopy","wood"},
    "landscape":{"landscapeforestcover","lfc","forestcover","cover1km",
                 "cover2km","habitatcover","fragmentation","landcover",
                 "forestamount","forestcover500m","forestcover1000m"},
    "geography":{"lat","lon","latitude","longitude","utm","easting","northing",
                 "x","y","region","county"},
}
TERMS=("site","forest","age","wood","landscape","cover","plot","trap","period",
       "sampling","method","guild","functional","abundance","species",
       "flight","litter","zero","effort","basal")

class SourceStop(Exception): pass

def get(url,max_bytes,accept="*/*"):
    if not url.startswith(HOST+"/"):
        raise SourceStop("SOURCE_STOP_NON_OFFICIAL_ZENODO_URL")
    try:
        req=urllib.request.Request(url,method="GET",headers={
            "User-Agent":UA,"Accept":accept})
        with urllib.request.urlopen(req,timeout=45) as r:
            raw=r.read(max_bytes+1)
            status=r.status
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_ACCESS_STOP_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise SourceStop("SOURCE_TRANSPORT_STOP_"+type(e).__name__) from e
    if status!=200 or len(raw)>max_bytes:
        raise SourceStop("SOURCE_STOP_ZENODO_OVERSIZE_OR_HTTP_NOT200")
    return raw

def official_manifest():
    raw=get(HOST+"/api/records/"+str(RECORD),2000000,"application/json")
    try:
        ob=json.loads(raw.decode("utf-8"))
    except (UnicodeError,ValueError) as e:
        raise SourceStop("SOURCE_STOP_ZENODO_JSON_INVALID") from e
    if str(ob.get("id"))!=str(RECORD):
        raise SourceStop("SOURCE_STOP_ZENODO_RECORD_ID_DRIFT")
    doi=str(ob.get("doi") or (ob.get("pids") or {}).get("doi",{}).get("identifier",""))
    if doi.casefold()!=DOI.casefold():
        raise SourceStop("SOURCE_STOP_PUBLISHED_ORIGINAL_DOI_DRIFT")
    rawfiles=ob.get("files")
    if isinstance(rawfiles,dict):
        fs=rawfiles.get("entries",{})
    elif isinstance(rawfiles,list):
        # Zenodo legacy REST API uses a list of file objects with 'key'.
        if any(not isinstance(item,dict) for item in rawfiles):
            raise SourceStop("SOURCE_STOP_ZENODO_FILE_RECORD_NOT_OBJECT")
        keys=[item.get("key") or item.get("filename") for item in rawfiles]
        if any(not isinstance(k,str) or not k for k in keys):
            raise SourceStop("SOURCE_STOP_ZENODO_FILE_KEY_INVALID")
        if len(keys)!=len(set(keys)):
            raise SourceStop("SOURCE_STOP_ZENODO_DUPLICATE_PUBLISHER_FILE_NAME")
        fs=dict(zip(keys,rawfiles))
    else:
        raise SourceStop("SOURCE_STOP_ZENODO_FILE_LIST_SCHEMA_UNKNOWN")
    if not isinstance(fs,dict) or len(fs)!=3 or set(fs)!=set(FILES):
        raise SourceStop("SOURCE_STOP_AUTHOR_THREE_FILE_MANIFEST_DRIFT")
    md=ob.get("metadata") or {}
    if not isinstance(md,dict):
        raise SourceStop("SOURCE_STOP_ZENODO_METADATA_NOT_OBJECT")
    lic=md.get("rights") or md.get("license") or []
    out={"record":RECORD,"doi":DOI,
         "original_publisher":ob.get("metadata",{}).get("publisher","Zenodo"),
         "source_licence_metadata_present":bool(lic),
         "file_manifest":[]}
    sizes={}
    for name in sorted(fs):
        e=fs[name]
        if not isinstance(e,dict):
            raise SourceStop("SOURCE_STOP_ZENODO_FILE_METADATA_NOT_OBJECT")
        checksum=str(e.get("checksum") or "").lower()
        if checksum not in ("md5:"+FILES[name],"md5-"+FILES[name],FILES[name]):
            raise SourceStop("SOURCE_STOP_ZENODO_FILE_MD5_DRIFT")
        size=e.get("size")
        if not isinstance(size,int) or not 0<size<=LIMIT:
            raise SourceStop("SOURCE_STOP_ZENODO_FILE_SIZE_NOT_BOUNDED")
        sizes[name]=size
        out["file_manifest"].append({
            "publisher_filename":name,"bytes":size,
            "original_published_checksum_md5":FILES[name],
            "source_bytes_NOT_EXPORTED":True})
    return out,sizes

def normalized(x):
    return re.sub("[^a-z0-9]","",x.strip().casefold())

def only_header_summary(raw):
    # FIRST line only: csv file full bytes were hashed but all source data
    # records remain uninterpreted. Never materialize the full data table.
    first=io.BytesIO(raw).readline(32000)
    if not first.endswith((b"\n",b"\r")):
        raise SourceStop("SOURCE_STOP_ORIGINAL_CSV_HEADER_TOO_LONG")
    try: txt=first.decode("utf-8-sig").rstrip("\r\n")
    except UnicodeError as e:raise SourceStop("SOURCE_STOP_ORIGINAL_HEADER_NONUTF8") from e
    nums={d:txt.count(d) for d in (",",";","\t")}
    sep=max(nums,key=nums.get)
    if nums[sep]==0:raise SourceStop("SOURCE_STOP_CSV_DELIMITER_NOT_FOUND")
    try:hdr=next(csv.reader([txt],delimiter=sep,strict=True))
    except csv.Error as e:raise SourceStop("SOURCE_STOP_INVALID_CSV_HEADER") from e
    if not 2<=len(hdr)<=3000:
        raise SourceStop("SOURCE_STOP_HEADER_FIELD_COUNT")
    n=[normalized(z) for z in hdr]
    matches={k:sorted({s for s in n if s in {normalized(z) for z in options}})
             for k,options in CATEGORIES.items()}
    return {"header_field_count":len(hdr),
            "original_header_delimiter":{",":"comma",";":"semicolon","\t":"tab"}[sep],
            "generic_safe_original_column_roles":{
                k:v for k,v in matches.items() if v},
            "original_all_unrecognized_header_text_NOT_EXPORTED":True,
            "source_species_site_guild_environment_rows_scored":0}

def readme_method_words(raw):
    try: s=raw.decode("utf-8-sig")
    except UnicodeError as e:raise SourceStop("SOURCE_STOP_AUTHOR_README_NOT_UTF8") from e
    lower=s.casefold()
    return {
        "original_author_README_utf8":True,
        "original_README_lines":len(s.splitlines()),
        "safe_method_word_counts":{
            k:len(re.findall(r"\b"+k+r"\b",lower)) for k in TERMS},
        "original_readme_text_NOT_EXPORTED":True}

def actual_source_gate():
    result={"status":"ORIGINAL_NOT_READ",
       "new_species_guild_environment_BIOLOGICAL_VALUES_SCORED":False,
       "all_prior_German_Finnish_BALA_GEB_biology_SEALED":True}
    try:
        meta,sizes=official_manifest()
        result["publisher_original_metadata"]=meta
        source_headers=[]
        for name in sorted(FILES):
            url=HOST+"/records/"+str(RECORD)+"/files/"+urllib.parse.quote(name,safe="")+"?download=1"
            raw=get(url,LIMIT)
            if len(raw)!=sizes[name] or hashlib.md5(raw).hexdigest()!=FILES[name]:
                raise SourceStop("SOURCE_STOP_PUBLISHER_FILE_HASH_OR_SIZE_DRIFT_"+("README" if name.startswith("READ") else "CSV"))
            if name.endswith(".csv"):
                source_headers.append({"original_file":name,**only_header_summary(raw)})
            else:
                result["readme_method_only"]=readme_method_words(raw)
        result["source_header_metadata"]=source_headers
        result["status"]="ORIGINAL_THREE_FILES_MD5_AND_HEADERS_VERIFIED_FIELD_CROSSWALK_STILL_UNTESTED"
    except SourceStop as e:
        result["status"]=str(e)
        result["source_access_or_schema_STOP_not_ecological_null"]=True
    return result

def known_truth():
    h=only_header_summary(b"site_id,tree basal area,forest_age,LFC,deadwood,Species,functional_group,Abundance\n")
    assert h["header_field_count"]==8
    assert h["generic_safe_original_column_roles"]["site_grain"]==["siteid"]
    assert h["generic_safe_original_column_roles"]["guild"]==["functionalgroup"]
    assert h["generic_safe_original_column_roles"]["landscape"]==["lfc"]
    assert h["source_species_site_guild_environment_rows_scored"]==0
    read=readme_method_words(b"site forest age sample period, trap effort. Functional group and guild.\n")
    assert read["original_author_README_utf8"] and read["original_readme_text_NOT_EXPORTED"]
    assert len(FILES)==3 and all(len(x)==32 for x in FILES.values())
    old_manifest=[{"key":k,"checksum":"md5:"+v,"size":8000}
                  for k,v in FILES.items()]
    assert len({x["key"] for x in old_manifest})==3
    duplicated=old_manifest+[old_manifest[0]]
    assert len(duplicated)!=len({x["key"] for x in duplicated})
    print("SYNTHETIC_GEORGIA40_ZENODO_MD5_HEADER_AND_METHOD_SOURCE_ONLY_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:ap.error("--out required")
    out={"schema":"structural.Traylor2023_Georgia_40forest_original_source_only.v1",
         "prespec":"docs/FOREST_BEETLE_TRAYLOR_US40_ORIGINAL_SOURCE_PRESPEC_20261117.md",
         "source":actual_source_gate(),"new_ecological_effect_scored":False,
         "prior_Piccini_Kriegel_Finland_Burner_Thai_PREDICTS_NEON_BALA_GEB_sealed":True,
         "eBird_used":False,"TinyFish_used":False}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Traylor2023_Georgia_40forest_original_source_only.json").write_text(
        json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
