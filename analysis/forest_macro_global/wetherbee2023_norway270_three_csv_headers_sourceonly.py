#!/usr/bin/env python3
"""Original Norway Wetherbee2023 270 forest sites: exact 3 CSV HEADER ONLY.
Official publisher source full bytes MD5-verified in runner-private RAM.
Original biological data rows and values never inspected or scored.
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

RECORD=8272489
BASE="https://zenodo.org"
UA="Structural-Wetherbee-2023-Norway-source-header-only/1.0"
SOURCE_FILES={
"GBIFnormalized_SpcSite_matrix_FD_unique.csv":(2759229,"1cc6d3599dccd80b0889b55b5d571eda"),
"GBIFnormalized_Trait_RAW_df.csv":(485427,"da5aa42586fe6994deb039565a782f8a"),
"SiteInfo_Alltaxon_Pred_Detri_SxFD.csv":(403751,"2b0d5e8a7c209a958b6034838d1fd1ee"),
}
MAX_HEADER=65536
CATEGORIES={
 "study_project":{"study","studyid","study_id","project","projectid",
   "project_id","dataset","datasetid","source","sourcestudy","samplingproject"},
 "site_identity":{"site","siteid","site_id","plot","plotid","location",
   "locationid","forest","forestid","forestsite","sample","sampleid","sample_id"},
 "source_time":{"year","sampleyear","samplingyear","collectionyear",
   "date","period","yearsite","samplingdate","season"},
 "method_effort":{"method","trap","trapid","traptype","trapdays",
   "samplingmethod","effort","duration","trapnights","samplingeffort"},
 "original_hostwood":{"treespecies","tree","hosttree","hostspecies",
   "deadwood","deadwoodvolume","woodvolume","dbh","treediversity",
   "treebasalarea","substrate","decay","woody"},
 "management_naturalness":{"managed","management","managementtype",
   "naturalness","near-natural","nearnatural","foresttype","forestclass",
   "oldgrowth","forestage","standage","deadwooddiversity"},
 "original_species_taxon":{"species","speciesid","taxon","taxonid",
   "genus","family","scientificname","spp","sp"},
 "guild_functional_trait":{"guild","feedingguild","predator",
   "predatory","carnivorous","diet","trophic","trophicguild",
   "trait","winglength","roundness","bodyroundness","bodylength"},
 "capture_data":{"count","abundance","individuals","n","abund","biomass"},
 "geography_climate":{"latitude","longitude","lat","lon","region",
   "country","temperature","temp","precipitation","climate"},
}
class SourceStop(Exception):pass

def normalized(x):
    return re.sub(r"[^a-z0-9]","",str(x).casefold())

def fetch_one_original(name,expected_size,digest):
    url=BASE+"/records/"+str(RECORD)+"/files/"+urllib.parse.quote(name,safe="")+"?download=1"
    req=urllib.request.Request(url,method="GET",headers={
         "User-Agent":UA,"Accept":"text/plain,text/csv,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=50) as response:
            raw=response.read(expected_size+1)
            code=response.status
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_ACCESS_STOP_HTTP_"+str(e.code)) from e
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise SourceStop("SOURCE_ACCESS_TRANSPORT_STOP_"+type(e).__name__) from e
    if code!=200 or len(raw)!=expected_size:
        raise SourceStop("SOURCE_STOP_PUBLISHED_ORIGINAL_FILE_LENGTH_CHANGED")
    if hashlib.md5(raw).hexdigest()!=digest:
        raise SourceStop("SOURCE_STOP_PUBLISHER_ORIGINAL_MD5_MISMATCH")
    return raw

def header_only(raw):
    first=io.BytesIO(raw).readline(MAX_HEADER+1)
    if len(first)>MAX_HEADER or not first.endswith((b"\n",b"\r")):
        raise SourceStop("SOURCE_STOP_ORIGINAL_CSV_HEADER_TOO_LONG")
    try:
        text=first.decode("utf-8-sig").rstrip("\r\n")
    except UnicodeError as e:
        raise SourceStop("SOURCE_STOP_HEADER_ENCODING") from e
    delimiters={d:text.count(d) for d in (",",";","\t")}
    d=max(delimiters,key=delimiters.get)
    if delimiters[d]==0:
        raise SourceStop("SOURCE_STOP_CSV_ORIGINAL_DELIMITER")
    try:
        cols=next(csv.reader([text],delimiter=d,strict=True))
    except csv.Error as e:
        raise SourceStop("SOURCE_STOP_ORIGINAL_CSV_HEADER_PARSE") from e
    if len(cols)<2 or len(cols)>20000:
        raise SourceStop("SOURCE_STOP_ORIGINAL_HEADER_WIDTH")
    h=[normalized(c) for c in cols]
    candidates={label:sorted(set(c for c in h if c in
          {normalized(k) for k in vocab}))
          for label,vocab in CATEGORIES.items()}
    return {
        "published_original_header_field_count":len(cols),
        "original_header_delimiter_category":{",":"comma",";":"semicolon","\t":"tab"}[d],
        "only_generic_header_name_categories":{k:v for k,v in candidates.items() if v},
        "original_raw_headers_and_species_column_labels_NOT_EXPORTED":True,
        "original_species_site_trait_environmental_data_rows_READ":0,
    }

def original():
    out={"status":"SOURCE_NOT_OPENED",
         "no_species_site_trait_environmental_values_scored":True}
    results=[]
    try:
        for name,(size,digest) in SOURCE_FILES.items():
            raw=fetch_one_original(name,size,digest)
            results.append({"official_filename":name,
                 "official_original_size_bytes":size,
                 "publisher_original_md5_verified":True,
                 **header_only(raw)})
        out["source_original_header_results"]=results
        out["status"]="THREE_ORIGINAL_CSV_PUBLISHER_MD5_AND_HEADERS_VERIFIED_NO_SOURCE_JOIN"
    except SourceStop as e:
        out["source_original_header_results"]=results
        out["status"]=str(e)
        out["SOURCE_ACCESS_OR_HEADER_STOP_NOT_BIOLOGICAL_NULL"]=True
    return out

def synthetic():
    d=header_only(b"Project;Site;Year;TreeSpecies;FeedingGuild;Species;Abundance;TrapID\n")
    assert d["published_original_header_field_count"]==8
    assert d["original_header_delimiter_category"]=="semicolon"
    assert d["only_generic_header_name_categories"]["study_project"]==["project"]
    assert d["only_generic_header_name_categories"]["original_hostwood"]==["treespecies"]
    assert d["only_generic_header_name_categories"]["guild_functional_trait"]==["feedingguild"]
    assert d["original_species_site_trait_environmental_data_rows_READ"]==0
    assert len(SOURCE_FILES)==3
    assert all(len(digest)==32 for size,digest in SOURCE_FILES.values())
    print("SYNTHETIC_WETHERBEE2023_NORWAY_ORIGINAL_MATRIX_TRAIT_SITEINFO_HEADER_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out needed")
    result={
       "schema":"structural.Wetherbee2023_Norway270_original_three_table_headers_only.v1",
       "precommit":"docs/FOREST_BEETLE_WETHERBEE2023_NORWAY270_THREE_SOURCE_HEADER_PRESPEC_20261117.md",
       "original_source":original(),
       "source_Burner_Norway_lineage_independence_UNVERIFIED":True,
       "no_original_ecological_effect_or_p_computed":True,
       "old_Piccini_Georgia_Finland_Burner_Thai_PREDICTS_NEON_BALA_GEB_UNCHANGED":True,
       "eBird_used":False,"TinyFish_used":False
    }
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Wetherbee2023_Norway270_original_threeCSV_headers_only.json").write_text(
       json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
