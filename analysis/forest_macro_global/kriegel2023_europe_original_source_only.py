#!/usr/bin/env python3
"""Kriegel et al. 2023 original 8-country beetle Dryad: publisher-source ONLY.

Publisher DOI + version + file manifest + up to one HEADER per 3 CSV files.
3 small text codebooks scanned for safe general method-words (not republished).
No actual biodiversity, environmental, resource or individual source rows scored.
No nonpublisher host, authentication escalation or retry.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

DOI="10.5061/dryad.brv15dvch"
ARTICLE="10.1111/ele.14227"
BASE="https://datadryad.org"
SOURCE_FILES={
    "Analyses.html","Analyses.rmd","data_legend.csv","README.md",
    "saproxylic_beetles_europe.csv","trait_legend.csv",
    "traits_corrected.csv","traits.csv"
}
HEADERS_READ={"saproxylic_beetles_europe.csv","traits_corrected.csv","traits.csv"}
CODEBOOKS={"data_legend.csv","trait_legend.csv","README.md"}
MAX_API_BYTES=2_000_000
MAX_HEADER_BYTES=16_384
MAX_CODEBOOK_BYTES=16_384
MAX_FILE_COUNT=20
SOURCE_UA="Structural-Kriegel-2023-Original-Publisher-Source-Only/1.0"

CATEGORIES={
    "study_source":{"study","studyid","study_id","dataset","datasetid","dataset_id",
                    "project","projectid","source","sourceid","cohort","experiment"},
    "country_region":{"country","countrycode","region","realm","site",
                      "siteid","location","locationid","latitude","longitude"},
    "wood_object":{"object","objectid","woodobject","deadwoodid","log",
                   "logid","stem","stemid","plot","plotid","sampleid","eventid"},
    "host_identity":{"tree","treespecies","treesp","host","hosttree",
                     "hosttreespecies","hostspecies","substrate","substratespecies"},
    "time_effort":{"year","collectionyear","samplingyear","date","method",
                   "samplingmethod","trap","trapid","effort","trapdays","duration"},
    "climate":{"temperature","temp","bio1","bio2","bio5","bio12","solar",
               "solarradiation","radiation","precipitation","climate"},
    "substrate_resource":{"carbohydrates","xylem","phloem","nitrogen","carbon",
                          "decay","diameter","dbh","woodvolume","woodtrait","wooddensity"},
    "guild_trait":{"guild","feedingguild","feedingtype","feeding","diet",
                   "trophic","trophicguild","trophiclevel","trait"},
    "species_taxon":{"species","speciesid","taxon","taxonid","sp",
                     "beetlespecies","beetletaxon"},
    "abundance":{"abundance","count","individuals","nindividuals",
                 "observed","number","biomass"},
}
CODEBOOK_TERMS=(
    "study","country","object","host","tree","year","guild",
    "site","trap","effort","species","method","abundance"
)

class SourceStop(Exception):
    pass

def source_url(href:str):
    """Only published official same-origin API endpoint links."""
    if not isinstance(href,str) or not href.startswith("/api/v2/"):
        raise SourceStop("SOURCE_STOP_NONCANONICAL_PUBLISHER_API_LINK")
    if "//" in href or ".." in href or "?" in href or "#" in href:
        raise SourceStop("SOURCE_STOP_UNSAFE_PUBLISHER_API_LINK")
    return BASE+href

def publisher_get(url:str,maxbytes:int):
    if not url.startswith(BASE+"/api/v2/"):
        raise SourceStop("SOURCE_STOP_NOT_OFFICIAL_PUBLISHER_URL")
    req=urllib.request.Request(url,method="GET",headers={
        "User-Agent":SOURCE_UA,"Accept":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=30) as response:
            raw=response.read(maxbytes+1)
            status=response.status
    except urllib.error.HTTPError as exc:
        raise SourceStop("SOURCE_ACCESS_STOP_HTTP_"+str(exc.code)) from exc
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise SourceStop("SOURCE_TRANSPORT_STOP_"+type(exc).__name__) from exc
    if status!=200 or len(raw)>maxbytes:
        raise SourceStop("SOURCE_STOP_PUBLISHER_API_STATUS_OR_OVERSIZE")
    try:
        obj=json.loads(raw.decode("utf-8"))
    except (ValueError,UnicodeError) as exc:
        raise SourceStop("SOURCE_STOP_PUBLISHER_API_INVALID_JSON") from exc
    if not isinstance(obj,dict):
        raise SourceStop("SOURCE_STOP_PUBLISHER_API_NOT_OBJECT")
    return obj

def one_public_file_get(href:str,filename:str):
    """Publisher official file path. One normal GET; header-only or bounded codebook."""
    url=source_url(href)
    # No URL variants, credentials, or forced alternate access routes.
    is_header=filename in HEADERS_READ
    cap=MAX_HEADER_BYTES if is_header else MAX_CODEBOOK_BYTES
    headers={"User-Agent":SOURCE_UA,"Accept":"text/plain,text/csv,*/*"}
    if is_header:
        headers["Range"]="bytes=0-"+str(cap-1)
    req=urllib.request.Request(url,method="GET",headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=30) as response:
            status=response.status
            raw=response.readline(cap+1) if is_header else response.read(cap+1)
    except urllib.error.HTTPError as exc:
        raise SourceStop("SOURCE_FILE_ACCESS_STOP_HTTP_"+str(exc.code)) from exc
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        raise SourceStop("SOURCE_FILE_TRANSPORT_STOP_"+type(exc).__name__) from exc
    if status not in (200,206) or len(raw)>cap:
        raise SourceStop("SOURCE_FILE_BAD_STATUS_OR_OVERSIZE")
    if is_header and not raw.endswith((b"\n",b"\r")):
        raise SourceStop("SOURCE_FILE_HEADER_NOT_FULL_LINE_WITHIN_16KB")
    return raw,status

def normalized(s):
    return re.sub(r"[^a-z0-9]","",str(s).casefold())

def header_qualification(content:bytes):
    try:
        line=content.decode("utf-8-sig").rstrip("\r\n")
    except UnicodeError as exc:
        raise SourceStop("SOURCE_FILE_NONUTF8_HEADER") from exc
    # No source row: a single first header line only.
    counts={d:line.count(d) for d in (";",",","\t")}
    sep=max(counts,key=counts.get)
    if counts[sep]==0:
        raise SourceStop("SOURCE_FILE_HEADER_DELIMITER_UNDETERMINED")
    try:
        cols=next(csv.reader([line],delimiter=sep,strict=True))
    except csv.Error as exc:
        raise SourceStop("SOURCE_FILE_HEADER_INVALID_CSV") from exc
    if len(cols)<2 or len(cols)>15000:
        raise SourceStop("SOURCE_FILE_HEADER_COLUMN_COUNT_UNEXPECTED")
    cols=[normalized(x) for x in cols]
    matches={kind:sorted(set(x for x in cols if x in {
          normalized(y) for y in vocabulary}))
             for kind,vocabulary in CATEGORIES.items()}
    return {"header_columns":len(cols),
            "header_delimiter":{";":"semicolon",",":"comma","\t":"tab"}[sep],
            "recognized_generic_field_categories":{
                k:v for k,v in matches.items() if v},
            "header_all_raw_field_names_NOT_EXPORTED":True,
            "biological_data_row_count_read":0}

def safe_codebook_counts(raw:bytes):
    try:
        s=raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise SourceStop("SOURCE_CODEBOOK_NOT_UTF8") from exc
    lower=s.casefold()
    return {"source_codebook_utf8_readable":True,
            "source_codebook_line_count":len(s.splitlines()),
            "generic_method_word_occurrences":{
               k:len(re.findall(r"\b"+k+r"\b",lower)) for k in CODEBOOK_TERMS},
            "original_codebook_text_NOT_EXPORTED":True}

def manifest_metadata():
    doi_endpoint=BASE+"/api/v2/datasets/"+urllib.parse.quote("doi:"+DOI,safe="")
    dataset=publisher_get(doi_endpoint,MAX_API_BYTES)
    identity=str(dataset.get("identifier","")).casefold()
    if identity not in ("doi:"+DOI,DOI):
        raise SourceStop("SOURCE_STOP_ORIGINAL_DOI_IDENTITY")
    version_link=((dataset.get("_links") or {}).get("stash:version") or {}).get("href")
    version_href=source_url(version_link)
    m=re.fullmatch(r"/api/v2/versions/([1-9][0-9]*)",version_link)
    if m is None:
        raise SourceStop("SOURCE_STOP_PUBLISHER_VERSION_LINK_NOT_CANONICAL")
    version_id=m.group(1)
    # Use authoritative publisher-linked ID; versionNumber is NOT this ID.
    v=publisher_get(version_href,MAX_API_BYTES)
    source_files_href="/api/v2/versions/"+version_id+"/files"
    f=publisher_get(source_url(source_files_href),MAX_API_BYTES)
    items=((f.get("_embedded") or {}).get("stash:files"))
    if not isinstance(items,list) or len(items)>MAX_FILE_COUNT:
        raise SourceStop("SOURCE_STOP_PUBLISHER_VERSION_FILE_LIST")
    if f.get("total") is not None and int(f["total"])!=len(items):
        raise SourceStop("SOURCE_STOP_FILE_LIST_PAGINATION")
    actual={str(x.get("path","")):x for x in items}
    if len(items)!=8 or set(actual)!=SOURCE_FILES:
        raise SourceStop("SOURCE_STOP_ORIGINAL_EIGHT_FILE_MANIFEST_DRIFT")
    result={"doi":DOI,
      "publisher_article_DOI":ARTICLE,
      "publisher_latest_version_id":int(version_id),
      "publisher_version_number":v.get("versionNumber"),
      "publisher_curation_status":v.get("versionStatus",v.get("curationStatus")),
      "publisher_dataset_visibility":dataset.get("visibility"),
      "publisher_license":dataset.get("license"),
      "official_eight_published_files_verified":True,
      "file_manifest":[]}
    for name in sorted(actual):
        item=actual[name]
        sz=item.get("size")
        sha=item.get("digest")
        alg=item.get("digestType")
        if not isinstance(sz,int) or sz<1 or not isinstance(sha,str) or len(sha)<32:
            raise SourceStop("SOURCE_STOP_PUBLISHED_FILE_SIZE_OR_CHECKSUM")
        dl=((item.get("_links") or {}).get("stash:download") or {}).get("href")
        # Strict publisher official path validation BEFORE any content read
        source_url(dl)
        result["file_manifest"].append({
          "publisher_filename":name,
          "publisher_bytes":sz,
          "publisher_digest":sha,
          "publisher_digest_type":alg,
          "publisher_file_status":item.get("status")})
    return result,actual

def original_gate():
    out={"status":"SOURCE_ONLY_NOT_RUN","raw_original_biological_values_opened":False,
         "species_country_object_data_row_values_scored":False,
         "no_heldout_reopened":True}
    try:
        metadata,files=manifest_metadata()
        out["publisher_metadata"]=metadata
        headers=[]
        for filename in sorted(HEADERS_READ):
            dl=files[filename]["_links"]["stash:download"]["href"]
            try:
                blob,status=one_public_file_get(dl,filename)
                headers.append({"publisher_filename":filename,
                                "http_status":status,**header_qualification(blob)})
            except SourceStop as e:
                headers.append({"publisher_filename":filename,"status":str(e)})
                out["headers"]=headers
                out["status"]="ORIGINAL_FIRSTLINE_ACCESS_STOP_NOT_ECOLOGICAL_NULL"
                return out
        out["headers"]=headers
        cb=[]
        for filename in sorted(CODEBOOKS):
            dl=files[filename]["_links"]["stash:download"]["href"]
            try:
                blob,status=one_public_file_get(dl,filename)
                cb.append({"publisher_filename":filename,"http_status":status,
                           **safe_codebook_counts(blob)})
            except SourceStop as e:
                cb.append({"publisher_filename":filename,"status":str(e)})
                out["codebooks"]=cb
                out["status"]="ORIGINAL_CODEBOOK_ACCESS_STOP_NOT_ECOLOGICAL_NULL"
                return out
        out["codebooks"]=cb
        out["status"]="ORIGINAL_PUBLISHER_HEADER_CODEBOOK_RECORDED_AWAIT_AUTHOR_GRAIN"
    except SourceStop as exc:
        out["status"]=str(exc)
        out["scientific_access_STOP_not_ecological_null"]=True
    return out

def known_truth():
    h=header_qualification(b"Study;Country;ObjectID;TreeSpecies;year;Guild;species;Count\n")
    assert h["header_columns"]==8
    assert h["header_delimiter"]=="semicolon"
    assert h["recognized_generic_field_categories"]["study_source"]==["study"]
    assert h["recognized_generic_field_categories"]["host_identity"]==["treespecies"]
    assert h["biological_data_row_count_read"]==0
    c=safe_codebook_counts(b"Study and country and host tree. Guild of species.\n")
    assert c["source_codebook_utf8_readable"]
    assert c["original_codebook_text_NOT_EXPORTED"]
    assert all(k in CATEGORIES for k in h["recognized_generic_field_categories"])
    assert set(HEADERS_READ|CODEBOOKS)<SOURCE_FILES
    assert re.fullmatch(r"/api/v2/versions/([1-9][0-9]*)",
                        "/api/v2/versions/26724").group(1)=="26724"
    assert not re.fullmatch(r"/api/v2/versions/([1-9][0-9]*)",
                            "/api/v2/versions/26724/../wrong")
    print("SYNTHETIC_KRIEGEL2023_PUBLISHER_HEADER_ONLY_GUILD_COUNTRY_OBJECT_READINESS_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    out={"schema":"structural.Kriegel2023_Europe_8country_source_only_prebiology.v1",
      "precommit":"docs/FOREST_BEETLE_KRIEGEL_EUROPE_SOURCE_QUALIFICATION_PRESPEC_20261117.md",
      "publisher_original":original_gate(),
      "new_biological_effect_estimated":False,
      "original_2026_Piccini_Finland_Thai_PREDICTS_NEON_BALA_GEB_SEALED":True,
      "eBird_used":False,"TinyFish_used":False}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Kriegel2023_europe_8country_source_only.json").write_text(
        json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
