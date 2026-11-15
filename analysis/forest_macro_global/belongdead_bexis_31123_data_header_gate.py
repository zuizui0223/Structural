#!/usr/bin/env python3
"""BExIS officially CC-BY-4.0 original /api/data/31123 first-header-only gate.

Range first 65536 bytes at most; no organismal row data decoded or exported.
Exact one documented endpoint only, no retry or alternate API/host.
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
from pathlib import Path

URL="https://www.bexis.uni-jena.de/api/data/31123"
LIMIT=65536
UA="Structural-BELongDead-31123-published-data-header-prebiology/1.0"
GENERIC={
 "plot","plotid","plot_id","forest","forestid","forest_id",
 "vip","vipid","vip_id","site","siteid","site_id",
 "region","regionid","region_id","exploratory","exploratoryid",
 "tree","treename","treespecies","tree_species","wood","woodid","wood_id",
 "log","logid","log_id","stem","stemid","stem_id","treeid","tree_id",
 "host","hostspecies","host_species","hosttree","host_tree",
 "date","year","yearid","samplingyear","sampling_year",
 "samplingdate","collectiondate","season","exposureage",
 "trap","trapid","trap_id","sample","sampleid","sample_id",
 "effort","traps","samples","trapcount","numberoftraps",
 "decay","decaystage","diameter","dbh","substrate","treatment",
 "id","recordid","record_id","count","abundance",
}
HEADERS="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_0123456789"
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None


def category(ctype:str,first:bytes):
    t=ctype.lower()
    if "json" in t:return "json"
    if "xml" in t:return "xml"
    if "csv" in t:return "csv"
    if "tab-separated" in t or "tsv" in t:return "tsv"
    if "html" in t:return "html"
    stripped=first.lstrip()[:20]
    if stripped.startswith((b"{",b"[")):return "json_like"
    if stripped.startswith(b"<?xml"):return "xml_like"
    if first.count(b"\t")>2:return "tabular_text_tsv_like"
    if first.count(b",")>2:return "tabular_text_csv_like"
    return "unclassified"


def safe_source_header(raw:bytes,ctype:str):
    # No original taxon rows; only split on the first newline if present
    if b"\n" not in raw:
        return {"status":"SOURCE_STOP_FIRST_LINE_INCOMPLETE"}
    first=raw.split(b"\n",1)[0].rstrip(b"\r")
    if len(first)>16384:
        return {"status":"SOURCE_STOP_HEADER_EXCEEDS_16KB"}
    charset="utf-8-sig"
    try:decoded=first.decode(charset)
    except UnicodeDecodeError:
        return {"status":"SOURCE_STOP_NON_UTF8_HEADER"}
    delim=max((",","\t",";"),key=decoded.count)
    if decoded.count(delim)==0:
        return {"status":"SOURCE_STOP_NOT_A_DELIMITED_FIRST_LINE"}
    original_columns=next(csv.reader([decoded],delimiter=delim),[])
    safe=[]
    for i,x in enumerate(original_columns):
        label=str(x).strip().strip('"')
        token=re.sub(r"[^a-z0-9_]","",label.lower())
        if token in GENERIC and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_ .-]{0,50}",label):
            safe.append({"original_source_1based_column_index":i+1,
                         "generic_original_header_label_ONLY":label})
    return {
      "status":"ORIGINAL_CSV_OR_TSV_FIRST_HEADER_PARSED_NO_DATA_ROWS",
      "original_header_column_count":len(original_columns),
      "generic_plot_log_tree_year_effort_fieldnames_only":safe,
      "source_header_delimiter_category":{",":"comma","\t":"tab",";":"semicolon"}[delim],
      "original_species_taxon_column_labels_SUPPRESSED":True,
      "source_species_data_rows_not_decoded_or_scored":True,
    }


def probe():
    out={
      "schema":"structural.BELongDead_BExIS31123_original_public_data_first64KiB_header_gate.v1",
      "official_dataset_ID":31123,
      "original_rights_CC_BY4_verified_in_prior_independent_source_metadata_CI43701688869":True,
      "documented_official_data_API_endpoint":URL,
      "only_one_original_source_endpoint_request_without_auth":True,
      "max_original_body_bytes_requested_for_source_schema":LIMIT,
      "no_species_log_plot_raw_sample_rows_reexported":True,
      "old_Finland_Burner_PREDICTS_NEON_BALA_GEB_scores_unchanged":True,
      "eBird_used":False,
    }
    request=urllib.request.Request(
        URL,headers={"User-Agent":UA,"Accept":"text/csv,application/json;q=0.9,*/*;q=0.5",
                     "Range":f"bytes=0-{LIMIT-1}"})
    try:
        with urllib.request.build_opener(NoRedirect).open(request,timeout=35) as handle:
            ctype=handle.headers.get("Content-Type","")
            cdisp=handle.headers.get("Content-Disposition","")
            clen=handle.headers.get("Content-Length","")
            has_range=handle.headers.get("Content-Range","")
            status=handle.status
            raw=handle.read(LIMIT)
            # The BExIS service may ignore byte Range; abort immediately after
            # first 64KB, no full dataset download.
            out["http_response_code"]=status
            out["content_type_category"]=category(ctype,raw[:2048])
            out["content_disposition_attachment_header_present"]="attachment" in cdisp.lower()
            out["server_content_length_header_bytes_if_numeric"]=int(clen) if clen.isdigit() else None
            out["partial_content_range_header_present"]=bool(has_range)
            out["actual_bytes_received_before_close"]=len(raw)
            out["first_64k_is_not_full_original_archive_if_length_unknown"]=True
            if status not in (200,206):
                out["status"]="SOURCE_STOP_BEXIS_ORIGINAL_DATA_NONSUCCESS"
            elif out["content_type_category"] in ("csv","tsv","tabular_text_tsv_like","tabular_text_csv_like"):
                out["original_tabular_header_schema_only"]=safe_source_header(raw,ctype)
                out["status"]=(
                    "SOURCE_31123_PUBLIC_DATA_API_FIRST_HEADER_ACCESS_OK_BIOLOGY_UNREAD"
                    if out["original_tabular_header_schema_only"]["status"]=="ORIGINAL_CSV_OR_TSV_FIRST_HEADER_PARSED_NO_DATA_ROWS"
                    else "SOURCE_31123_DATA_API_REACHABLE_HEADER_SCHEMA_NOT_PARSED")
            else:
                out["status"]="SOURCE_31123_DATA_API_REACHABLE_UNSUPPORTED_OR_NON_TABULAR_BODY_SCHEMA"
    except urllib.error.HTTPError as e:
        p=urllib.parse.urlparse(e.headers.get("Location","") if e.headers else "")
        out.update({"status":"SOURCE_31123_ACCESS_STOP_HTTP" if e.code in (401,403) else
                    "SOURCE_31123_TRANSPORT_OR_REDIRECT_STOP",
                    "http_response_code":e.code,
                    "redirect_origin_category":"same_original_bexis" if p.hostname=="www.bexis.uni-jena.de"
                    else "other_host" if p.hostname else "none"})
    except (urllib.error.URLError,OSError,TimeoutError) as e:
        out.update({"status":"SOURCE_31123_TRANSPORT_STOP",
                    "exception_class":type(e).__name__})
    return out


def synthetic():
    a=safe_source_header(b"Plot_ID,TreeSpecies,Year,Species_One,abundance\nP001,Picea,2020,0,4\n","text/csv")
    assert a["original_header_column_count"]==5
    assert [x["generic_original_header_label_ONLY"] for x in a["generic_plot_log_tree_year_effort_fieldnames_only"]]==["Plot_ID","TreeSpecies","Year","abundance"]
    assert category("application/json",b'{"a":1}')=="json"
    assert b"Species_One" not in json.dumps(a).encode()
    print("SYNTHETIC_ONE_OFFICIAL_DATA_ENDPOINT_HEADER_ONLY_AND_SPECIES_LABEL_SUPPRESSION_PASS")


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if not a.out:p.error("--out required")
    result=probe()
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"bexis31123_public_data_original_first_header_sourceonly.json").write_text(
       json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":main()
