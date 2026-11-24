#!/usr/bin/env python3
"""EnviDat455 source original four CSV files: each FIRST HEADER ROW only.

Publisher original UUID/size-gated bytes may be downloaded only by unchanged
links returned in exact public CKAN metadata. Biological and environmental
rows are never parsed. Original file bytes never redistributed.
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

import haeler2023_envidat455_original_publisher_metadata_only as prior

ORIGINAL={
 "Community matrix (saproxylic beetles)":("1873211d-631c-493e-a998-103395d5de43",23120),
 "Community matrix (all beetles)":("30938085-43a4-43f0-bdde-2f57dd557064",34872),
 "Forest and environmental variables":("66dbaff5-2b06-4e82-9f92-9e40d298f938",158262),
 "Variable description":("8113973a-149d-4514-8b03-11201870881c",3005),
}
CATEGORY=re.compile(
 r"(?i)(site|plot|id|trap|event|species|taxon|beetle|treatment|wood|"
 r"branch|bundle|number|size|area|volume|dead|decay|bark|light|"
 r"temperature|temp|landscape|surround|isolation|dist|year|date|"
 r"local|abund|rich|inciden|canopy|snag|log|depth|diam|type|"
 r"stand|flight|effort|habitat|saproxy|forest|month|grid)")
SAFE_LABEL=re.compile(r"^[A-Za-zÀ-ÿ0-9_ .:/()+\-]{1,130}$")
HEADERS={
 "User-Agent":"Structural-forest-Swiss2023-original-four-headers-only/1.0",
 "Accept":"text/csv,application/octet-stream,*/*;q=0.2",
}
def exact_public_urls():
    req=urllib.request.Request(prior.API,headers={"Accept":"application/json","User-Agent":HEADERS["User-Agent"]})
    try:
        with urllib.request.urlopen(req,timeout=32) as h:
            body=h.read(500001)
            if h.status!=200 or len(body)>500000:
                raise ValueError("SOURCE_PUBLIC_CKAN_METADATA_SIZE_STOP")
    except urllib.error.HTTPError as e:
        raise ValueError("SOURCE_CKAN_HTTP_"+str(e.code))
    d=json.loads(body)
    if d.get("success") is not True or not isinstance(d.get("result"),dict):
        raise ValueError("SOURCE_OFFICIAL_CKAN_NOT_SUCCESS")
    x=d["result"]
    if (x.get("name")!=prior.SLUG or x.get("private") is True
        or x.get("state")!="active" or x.get("license_id")!="cc-by-sa"):
        raise ValueError("SOURCE_ORIGINAL_ID_OR_LICENSE_ACTIVE_STOP")
    rr=x.get("resources") or []
    if len(rr)!=4:
        raise ValueError("SOURCE_ORIGINAL_FOUR_RESOURCE_ROSTER_STOP")
    got={}
    for f in rr:
        title=f.get("name")
        if title not in ORIGINAL or title in got:
            raise ValueError("SOURCE_EXACT_ROLE_TITLE_STOP")
        id_,size=ORIGINAL[title]
        if f.get("id")!=id_ or f.get("size")!=size:
            raise ValueError("SOURCE_PUBLISHER_RESOURCE_ID_OR_SIZE_DRIFT")
        if str(f.get("format","")).upper()!="CSV":
            raise ValueError("SOURCE_ORIGINAL_FILE_FORMAT_NOT_CSV")
        url=f.get("url")
        p=urllib.parse.urlparse(url or "")
        if p.scheme!="https" or p.hostname!="www.envidat.ch":
            raise ValueError("SOURCE_ORIGINAL_URL_NON_OFFICIAL_HOST")
        got[title]={"url":url,"id":id_,"size":size,"publisher_hash":f.get("hash")}
    if set(got)!=set(ORIGINAL):
        raise ValueError("SOURCE_FOUR_RESOURCE_COVERAGE_STOP")
    return got

def one_download(url,size):
    # DO NOT construct resource URL or retry denied originals.
    p=urllib.parse.urlparse(url)
    if p.scheme!="https" or p.hostname!="www.envidat.ch":
        raise ValueError("SOURCE_RESOURCE_URL_NOT_OFFICIAL")
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS),timeout=48) as h:
            final=urllib.parse.urlparse(h.url)
            if final.scheme!="https" or not (
              final.hostname=="www.envidat.ch" or
              final.hostname=="envidat.ch" or
              str(final.hostname).endswith(".envidat.ch")):
                raise ValueError("SOURCE_ORIGINAL_FILE_REDIRECT_DOMAIN_STOP")
            data=h.read(size+1)
            if h.status!=200:
                raise ValueError("SOURCE_ORIGINAL_FILE_NON200")
    except urllib.error.HTTPError as e:
        raise ValueError("SOURCE_ORIGINAL_FILE_HTTP_"+str(e.code))
    if len(data)!=size:
        raise ValueError("SOURCE_ORIGINAL_RESOURCE_EXACT_BYTE_SIZE_MISMATCH")
    return data

def first_header(data,title):
    # Open FIRST newline, nothing else. Do not parse any organism row.
    raw=io.BytesIO(data).readline(26001)
    if len(raw)>26000 or not raw:
        raise ValueError("SOURCE_FIRST_HEADER_SIZE_OR_EMPTY_STOP")
    txt=raw.decode("utf-8-sig",errors="replace").strip("\r\n")
    delimiter=max((",", ";","\t"),key=lambda x:txt.count(x))
    row=next(csv.reader([txt],delimiter=delimiter))
    if len(row)<2 or len(row)>2000:
        raise ValueError("SOURCE_HEADER_WIDTH_STOP")
    role="wood_method" if title in ("Forest and environmental variables","Variable description") else "beetle_matrix"
    labels=[x.strip() for x in row]
    generic=sorted(set(x[:130] for x in labels if CATEGORY.search(x) and SAFE_LABEL.match(x)))
    # Species matrix WIDE columns may be literal plot IDs; report generic
    # field count only, not original site or species identifiers.
    if role=="beetle_matrix":
        generic=[x for x in generic if x.casefold() in {
           "species","speciesid","species_id","taxon","taxon_id",
           "plot","plotid","plot_id","trap","trapid","trap_id",
           "site","siteid","site_id","id","name","abundance",
           "saproxylic","saproxylic_beetles"}]
    return {
       "role":role,
       "first_header_column_count":len(row),
       "delimiter_label":{",":"COMMA",";":"SEMICOLON","\t":"TAB"}[delimiter],
       "first_header_generic_method_field_names_only":generic[:120],
       "all_original_columns_are_field_names_not_observations":False if role=="beetle_matrix" else True,
       "original_source_rows_after_header_read":0,
       "original_numeric_beetle_or_wood_values_read":0
    }

def audit():
    rr=exact_public_urls()
    files=[]
    for title in sorted(ORIGINAL):
        r=rr[title]
        b=one_download(r["url"],r["size"])
        h=r.get("publisher_hash")
        digest=hashlib.sha256(b).hexdigest()
        if h and isinstance(h,str) and re.fullmatch(r"[0-9a-fA-F]{64}",h) and h.lower()!=digest:
            raise ValueError("SOURCE_PUBLISHER_SHA256_MISMATCH")
        row={
          "original_resource_title":title,
          "official_resource_id":r["id"],
          "exact_source_file_bytes":len(b),
          "source_sha256":digest,
          "publisher_hash_verified_if_sha256":bool(h and re.fullmatch(r"[0-9a-fA-F]{64}",str(h))),
          "source_original_biological_file_redistributed":False,
          "first_header_only":first_header(b,title),
        }
        files.append(row)
    return {
      "status":"SOURCE_FOUR_AUTHENTIC_CSV_FIRST_HEADERS_OPENED_NO_BIOLOGY",
      "original_files":files,
      "source_original_files_downloaded":4,
      "original_data_rows_read":0,
      "original_taxon_wood_numeric_values_read":0,
      "original_plot_keys_crosswalk_verified":False,
      "source_original_resource_file_bytes_archived":False}

def synthetic():
    assert len(ORIGINAL)==4
    assert first_header(b"PlotID,bundle_size,wood_volume,beetle_abundance\nA,1,2,3\n",
                        "Forest and environmental variables")["first_header_column_count"]==4
    assert first_header(b"Species,Trap_1,Trap_2\nA,4,5\n",
                        "Community matrix (saproxylic beetles)")["original_source_rows_after_header_read"]==0
    print("ENVIDAT455_FIRST_FOUR_CSV_HEADER_SOURCEFREE_KNOWN_TRUTH_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="envidat455_four_csv_firstheader/receipt.json")
    a=p.parse_args()
    synthetic()
    if a.test:return
    result={
      "schema":"structural.haeler2023_envidat455_4_source_CSV_FIRST_HEADER.v1",
      "original_source_data_doi":"10.16904/envidat.455",
      "original_publisher_license":"CC BY-SA",
      "original_experiment_plots_from_publication":62,
      "original_monitoring_plots_from_catalogue":69,
      "original_plot_identity_conflict_still_unresolved":True,
      "new_beetle_ecological_effects_fitted":0,
      "source_original_numeric_organism_or_wood_values_read":0,
      "status":"SOURCE_ORIGINAL_FIRST_HEADERS_UNOPENED"}
    try:
        result["original_file_schema"]=audit()
        result["status"]=result["original_file_schema"]["status"]
    except Exception as e:
        result["status"]="SOURCE_ORIGINAL_ENVIDAT_RESOURCE_ACCESS_OR_SCHEMA_STOP"
        result["scientific_stop_type"]=type(e).__name__
        result["scientific_stop_reason"]=str(e)[:175] if isinstance(e,ValueError) else ""
    dest=Path(a.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("SWISS_ENVIDAT_ORIGINAL_CSV_HEADER_STATUS",result["status"])
    print("NEW_BIOLOGICAL_EFFECTS",result["new_beetle_ecological_effects_fitted"])
if __name__=="__main__":
    main()
