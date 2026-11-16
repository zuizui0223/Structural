#!/usr/bin/env python3
"""2026 Piccini GRO.data: one first-line HEADER of each official 2026 file.
No species/abundance row, original site value, tree data or model is read.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

from piccini2026_gro_three_strata_source_only_gate import (
    HOST, HEADERS, get_public_json, gro_only, datacite_only, SourceStop
)

DOI="10.25625/H8EMJS"
MAX_HEADER=8192
MAX_FILE=4_000_000
CATEGORIES={
 "physical_site":{"site","siteid","plot","plotid","stand","standid","location","locationid","forestsite","sitecode","standcode"},
 "vertical_layer":{"stratum","layer","forestlayer","verticalstratum","heightstratum","canopy","subcanopy","understorey","understory","floor","forestfloor","samplingheight","trapheight"},
 "sample_year":{"year","sampleyear","samplingyear","collectionyear","date","period","season","samplingperiod"},
 "method_effort":{"trap","trapid","trapnumber","method","samplingmethod","effort","duration","trapdays","sample","sampleid"},
 "taxon":{"species","speciesid","speciesname","taxon","taxonid","abundance","individuals","count","speciescode"},
 "guild_affiliation":{"guild","feedingguild","guildcode","hosttree","hosts","host","foodguild","feedingtype","diet"},
 "tree_forest_resource":{"tree","treespecies","foresttype","standtype","treediversity","dbh","deadwood","woodvolume","basalarea","foreststructure"},
}
DELIMS={"\t":"tab",",":"comma",";":"semicolon"}
class HeaderStop(RuntimeError): pass

def normalized(x):
    return re.sub("[^a-z0-9]","",str(x).casefold())

def summarized_header(raw):
    """Never output raw source fields, species names, row/sample values."""
    if len(raw)>MAX_HEADER or not raw.endswith((b"\n",b"\r")):
        raise HeaderStop("SOURCE_STOP_FIRST_HEADER_LINE_EXCEEDS_BOUND_OR_NO_NEWLINE")
    try:
        t=raw.decode("utf-8-sig").strip("\r\n")
    except UnicodeError as e:
        raise HeaderStop("SOURCE_STOP_SOURCE_HEADER_NOT_UTF8") from e
    delim=max(DELIMS,key=lambda d:t.count(d))
    cells=t.split(delim)
    if len(cells)<2 or len(cells)>20000:
        return {"status":"HEADER_FORMAT_NOT_RESOLVED",
                "header_column_count":len(cells),
                "generic_field_categories":[]}
    found=sorted(k for k,values in CATEGORIES.items()
                 if any(normalized(c) in values for c in cells))
    return {
       "status":"FIRST_LINE_READ_SCHEMA_ONLY",
       "header_column_count":len(cells),
       "header_delimiter_category":DELIMS[delim],
       "generic_field_categories":found,
       "generic_categories_count":len(found),
       "original_header_text_NOT_EXPORTED":True,
       "original_taxa_species_names_NOT_EXPORTED":True,
       "NO_species_abundances_or_field_rows_processed":True,
    }

def legitimate_first_line(fid):
    if not isinstance(fid,int) or fid<=0:
        return {"status":"SOURCE_STOP_INVALID_OFFICIAL_DATAFILE_ID"}
    url=HOST+"/api/access/datafile/"+str(fid)
    req=urllib.request.Request(url,method="GET",
        headers={**HEADERS,"Range":"bytes=0-8191"})
    try:
        with urllib.request.urlopen(req,timeout=24) as response:
            status=response.status
            if status not in (200,206):
                return {"status":"SOURCE_STOP_FILE_RESPONSE_NON200_NON206",
                        "http_status":status}
            first_line=response.readline(MAX_HEADER+1)
    except urllib.error.HTTPError as exc:
        return {"status":"SOURCE_ACCESS_RESTRICTED" if exc.code in (401,403)
                else "SOURCE_FILE_HTTP_STOP","http_status":exc.code}
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
        return {"status":"SOURCE_FILE_TRANSPORT_STOP",
                "exception_class":type(exc).__name__}
    try:
        h=summarized_header(first_line)
        h["source_file_first_line_http_status"]=status
        return h
    except HeaderStop as exc:
        return {"status":str(exc)}

def source_2026_header_gate():
    url_dc="https://api.datacite.org/dois/"+urllib.parse.quote(DOI,safe="/")
    url_gro=HOST+"/api/datasets/:persistentId/?" + urllib.parse.urlencode({"persistentId":"doi:"+DOI})
    dc_status,dc=get_public_json(url_dc)
    ds_status,ds=get_public_json(url_gro)
    result={"doi":DOI,"status":"NOT_RUN",
            "official_datacite_http":dc_status["status"],
            "official_gro_http":ds_status["status"],
            "original_file_content_read":"FIRST_LINE_ONLY_IF_ELIGIBLE",
            "original_2024_canopy_file_content_read":False,
            "original_2026_species_counts_or_site_data_rows_read":False,
            "original_source_filenames_file_ids_and_headers_NOT_EXPORTED":True}
    if dc is None or ds is None:
        result["status"]="SOURCE_STOP_PUBLIC_PUBLISHER_METADATA_NOT_AVAILABLE"
        return result
    try:
        bib=datacite_only(DOI,dc)
        meta=gro_only(DOI,ds)
    except SourceStop:
        result["status"]="SOURCE_STOP_METADATA_SCHEMA_UNQUALIFIED"
        return result
    bib_ok=all(bib.get(k,False) for k in (
        "published_DOI_exact_match","publisher_metadata_present",
        "title_metadata_present","published_publication_year_metadata_present"))
    if not bib_ok or not meta["source_DOI_exact_match"] or not meta["published_version_exists"]:
        result["status"]="SOURCE_STOP_DOI_IDENTITY_OR_PUBLISHED_VERSION_NOT_VALIDATED"
        return result
    if meta["metadata_file_record_count"]!=2 or meta["metadata_restricted_file_count"]!=0:
        result["status"]="SOURCE_STOP_PUBLISHED_ORIGINAL_FILE_COUNT_OR_RESTRICTION"
        return result
    files=ds["data"]["latestVersion"]["files"]
    file_rows=[]
    for f in files:
        d=f.get("dataFile") or {}
        fid=d.get("id");size=d.get("filesize")
        mime=str(d.get("contentType","")).lower()
        allowed=(isinstance(fid,int) and fid>0
                 and isinstance(size,int) and 0<size<=MAX_FILE
                 and mime.startswith("text/") and not f.get("restricted",False))
        if not allowed:
            result["status"]="SOURCE_STOP_FILE_ID_SIZE_MIME_OR_RIGHTS_UNQUALIFIED"
            return result
        file_rows.append((fid,size))
    summary=[]
    for fid,size in file_rows:
        response=legitimate_first_line(fid)
        response["source_file_advertised_size_binned"]="<=4MB"
        summary.append(response)
        if response["status"]!="FIRST_LINE_READ_SCHEMA_ONLY":
            # One-shot: no alternate URL/file variant or metadata workaround.
            result["status"]="SOURCE_STOP_ORIGINAL_FILE_HEADER_ACCESS_OR_FORMAT"
            result["original_file_header_results"]=summary
            return result
    result["original_file_header_results"]=summary
    result["status"]="SOURCE_HEADER_ONLY_TWO_OFFICIAL_FILES_READ_SOURCE_GRAIN_STILL_UNRESOLVED"
    return result

def known_truth():
    h=summarized_header(b"PlotID\tLayer\tSpecies\tFeedingGuild\tCount\n")
    assert h["header_column_count"]==5
    assert h["generic_field_categories"]==[
       "guild_affiliation","physical_site","taxon","vertical_layer"]
    assert "PlotID" not in json.dumps(h)
    assert not any("taxon_name" in x for x in h)
    x=summarized_header(b"Abies alba\tQuercus robur\n")
    assert x["generic_categories_count"]==0
    assert summarized_header(b"Site,Year,Tree species\n")["header_delimiter_category"]=="comma"
    try:
        summarized_header(b"PlotID\tSpecies")
        raise AssertionError("must fail missing header newline")
    except HeaderStop:
        pass
    assert legitimate_first_line(0)["status"]=="SOURCE_STOP_INVALID_OFFICIAL_DATAFILE_ID"
    print("SYNTHETIC_GRO_2026_HEADER_REDACTION_AND_MISSING_NEWLINE_STOP_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:ap.error("--out required")
    r={"schema":"structural.Piccini2026_original_GRO_firstline_headeronly_source_gate.v1",
       "source_publication_DOI":"10.1111/1365-2664.70472",
       "protocol":"docs/FOREST_BEETLE_PICCINI2026_ORIGINAL_HEADER_SOURCE_GATE_PRESPEC_20261116.md",
       "source":source_2026_header_gate(),
       "previous_original_forest_beta_guild_mammal_heldouts_UNCHANGED":True,
       "NOT_new_ecological_positive_or_independent_country_replication":True,
       "eBird_used":False,"TinyFish_used":False}
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Piccini2026_GRO_original_file_firstline_headeronly.json").write_text(
       json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
