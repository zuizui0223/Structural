#!/usr/bin/env python3
"""Read ONLY first physical headers of 3 original OSF CSVs + source R code grammar.

Official OSF 9dhzw four-file root source. Whole file raw bytes are fetched
only for exact original byte-length/SHA attestation and discarded.
No CSV data rows are parsed. Original R code is NEVER executed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import urllib.error

from haack2022_leipzig_osf_source_manifest_only import (
    API_NODE, API_STORAGE, NODE_ID, source_json, verify_project, SourceStop,
)

PRESPEC="docs/FOREST_LEIPZIG2022_OSF_9DHZW_ORIGINAL_CSV_HEADER_AND_AUTHOR_R_METHOD_GATE_PRESPEC_20261119.md"
EXPECTED_FILES={".csv":3,".r":1}
EXPECTED_TOTAL=813317
MAX_FILE_BYTES=1024*1024
MAX_TOTAL_BYTES=2*1024*1024
MAX_FIRST_LINE=128*1024
CSV_FAMILIES={
 "site_or_plot_ID_candidate":r"(?i)(plot|site|station|location|transect|sample.?id|tree.?id)",
 "host_tree_or_deadwood_identity_candidate":r"(?i)(tree|host|dead.?wood|decay|wood|substrat|dbh|bark)",
 "trap_method_stratum_height_candidate":r"(?i)(trap|window|intercept|height|strat|layer|level|canopy|ground|understor|ethanol|glycol|preserv)",
 "date_year_effort_candidate":r"(?i)(date|year|month|period|campaign|effort|week|expos|collect|event|time)",
 "microclimate_candidate_UNVERIFIED":r"(?i)(microclimat|temperature|temp|humid|light|lux|radiat|thermal|logger)",
 "species_guild_count_candidate":r"(?i)(species|taxon|richness|individual|count|abund|guild|family|genus)",
 "geographic_OR_dataset_metadata_candidate":r"(?i)(latitude|longitude|coordinate|easting|northing|method|reference|version|source)",
}
R_FAMILIES={
 "source_csv_import":r"(?i)(read[._]csv|read[._]table|readr::read|fread\s*\(|read\.delim)",
 "joins_or_merge":r"(?i)(\bmerge\s*\(|\bjoin\b|left_join|inner_join|match\s*\(|rbind\s*\(|cbind\s*\()",
 "source_sample_grain":r"(?i)(\btrap\b|\bsample\b|\bsite\b|\bplot\b|transect|replicat)",
 "source_height_stratum":r"(?i)(height|strat|vertical|canopy|understor|ground|meter)",
 "source_host_tree":r"(?i)(tree|host|wood|quercus|tilia|fraxinus)",
 "source_temperature_or_climate":r"(?i)(microclimat|temperature|temp|therm|humidity|logger|lux)",
 "source_preservative":r"(?i)(ethanol|glycol|preservative|solvent)",
 "original_time":r"(?i)(\byear\b|\bdate\b|period|collection|week|season)",
}
def official_file_manifest(source_payload):
    data=source_payload.get("data")
    if not isinstance(data,list):
        raise SourceStop("SOURCE_LEIPZIG_OSF_ROOT_FILE_MANIFEST_NOT_LIST")
    result=[]
    seen=set()
    extensions=Counter()
    total=0
    for ent in data:
        if not isinstance(ent,dict):
            raise SourceStop("SOURCE_LEIPZIG_OSF_ORIGINAL_FILE_OBJECT_INVALID")
        fid=ent.get("id")
        if not isinstance(fid,str) or not fid or fid in seen:
            raise SourceStop("SOURCE_LEIPZIG_OSF_ORIGINAL_FILE_ID_MISSING_OR_DUPLICATE")
        seen.add(fid)
        a=ent.get("attributes") or {}
        if not isinstance(a,dict) or a.get("kind")!="file":
            raise SourceStop("SOURCE_LEIPZIG_OSF_ORIGINAL_NOT_ALL_FILES")
        name=a.get("name")
        if not isinstance(name,str) or "." not in name:
            raise SourceStop("SOURCE_LEIPZIG_OSF_ORIGINAL_FILE_EXTENSION_INVALID")
        ext="."+name.rsplit(".",1)[-1].casefold()
        if ext not in EXPECTED_FILES:
            raise SourceStop("SOURCE_LEIPZIG_OSF_ORIGINAL_FILE_EXTENSION_DRIFT")
        count=a.get("size")
        if not isinstance(count,int) or isinstance(count,bool) or count<1 or count>MAX_FILE_BYTES:
            raise SourceStop("SOURCE_LEIPZIG_OSF_ORIGINAL_FILE_SIZE_MISSING_OR_TOO_LARGE")
        link=(ent.get("links") or {}).get("download")
        if not isinstance(link,str):
            raise SourceStop("SOURCE_LEIPZIG_OSF_NO_OFFICIAL_FILE_DOWNLOAD_LINK")
        u=urllib.parse.urlsplit(link)
        host=(u.hostname or "").lower()
        if u.scheme!="https" or not (host=="osf.io" or host.endswith(".osf.io")):
            raise SourceStop("SOURCE_LEIPZIG_OSF_DOWNLOAD_NOT_ISSUED_OSF_HOST")
        result.append({"_private_id":fid,"_private_original_name":name,
                       "_private_official_url":link,"_private_extension":ext,"_private_size":count})
        total+=count
        extensions[ext]+=1
    if len(result)!=4 or dict(extensions)!=EXPECTED_FILES or total!=EXPECTED_TOTAL or total>MAX_TOTAL_BYTES:
        raise SourceStop("SOURCE_LEIPZIG_OSF_PINNED_3CSV_1R_813317B_METADATA_DRIFT")
    return sorted(result,key=lambda r:(r["_private_size"],r["_private_id"]))

def file_bytes(metadata):
    u=metadata["_private_official_url"]
    req=urllib.request.Request(
       u,headers={"User-Agent":"Structural-forest-leipzig-OSF-official/1.0",
                  "Accept":"text/csv,text/plain,application/octet-stream;q=0.8,*/*;q=0.2"},
       method="GET"
    )
    try:
        with urllib.request.urlopen(req,timeout=65) as response:
            typ=(response.headers.get("Content-Type") or "").lower()
            if "text/html" in typ:
                raise SourceStop("SOURCE_LEIPZIG_OSF_FILE_DOWNLOAD_HTML_NOT_ORIGINAL")
            raw=response.read(metadata["_private_size"]+1)
    except urllib.error.HTTPError as exc:
        raise SourceStop(f"SOURCE_LEIPZIG_OSF_ORIGINAL_FILE_DOWNLOAD_HTTP_{exc.code}_STOP") from None
    except (urllib.error.URLError,TimeoutError,OSError):
        raise SourceStop("SOURCE_LEIPZIG_OSF_ORIGINAL_FILE_DOWNLOAD_TRANSPORT_STOP") from None
    if len(raw)!=metadata["_private_size"]:
        raise SourceStop("SOURCE_LEIPZIG_OSF_ORIGINAL_FILE_BYTES_DIFFER_FROM_CATALOG")
    return raw

def first_header_schema(original):
    # First newline only. No original CSV data row is decoded or interpreted.
    raw=original.split(b"\n",1)[0].rstrip(b"\r")
    if not raw or len(raw)>MAX_FIRST_LINE or b"\x00" in raw:
        raise SourceStop("SOURCE_LEIPZIG_OSF_ORIGINAL_FIRST_CSV_HEADER_NOT_TEXT")
    try:
        txt=raw.decode("utf-8-sig")
        enc="UTF8"
    except UnicodeError:
        txt=raw.decode("latin-1")
        enc="LATIN1"
    candidates=[]
    for delimiter in (",",";","\t"):
        try:
            vals=next(csv.reader([txt],delimiter=delimiter,strict=True))
        except (csv.Error,StopIteration):
            continue
        if len(vals)>=2 and len(vals)<=10000 and all(str(x).strip() for x in vals):
            candidates.append((len(vals),delimiter,vals))
    if not candidates:
        raise SourceStop("SOURCE_LEIPZIG_OSF_ORIGINAL_CSV_HEADER_PARSE_STOP")
    count,delimiter,headers=max(candidates,key=lambda x:x[0])
    if len({h.strip() for h in headers})!=len(headers):
        raise SourceStop("SOURCE_LEIPZIG_OSF_ORIGINAL_CSV_HEADER_DUPLICATED")
    flags={k:sum(bool(re.search(pattern,h)) for h in headers)
           for k,pattern in CSV_FAMILIES.items()}
    return {
        "original_csv_FIRST_HEADER_only_semantically_INSPECTED":True,
        "original_csv_FIRST_HEADER_fields_count":count,
        "original_csv_first_header_encoding":enc,
        "original_csv_delimiter_family":{",":"comma",";":"semicolon","\t":"tab"}[delimiter],
        "original_csv_header_candidate_family_count_only":flags,
        "original_csv_data_rows_READ":0,
        "original_csv_raw_field_names_NOT_EXPORTED":True,
        "original_species_sample_plot_site_values_NOT_EXPORTED":True,
    }

def r_source_code_grammar(original):
    # Only published author R script CODE inspected; never executed.
    text=original.decode("utf-8-sig",errors="replace")
    return {
        "author_original_R_script_code_BYTES":len(original),
        "author_original_R_script_NOT_EXECUTED":True,
        "author_original_R_keyword_occurrences_code_only":{
            name:len(re.findall(regex,text)) for name,regex in R_FAMILIES.items()
        },
        "author_original_R_raw_code_species_lines_NOT_EXPORTED":True,
        "no_R_source_external_targets_OR_original_CSV_values_OPENED":True,
    }

def original_once():
    node,node_rcpt=source_json(API_NODE)
    project=verify_project(node)
    manifest,manifest_rcpt=source_json(API_STORAGE)
    files=official_file_manifest(manifest)
    original=[]
    for record in files:
        raw=file_bytes(record)
        entry={
            "original_source_file_byte_count":len(raw),
            "original_source_file_sha256":hashlib.sha256(raw).hexdigest(),
            "original_file_type":record["_private_extension"],
            "original_catalog_byte_count_verified":True,
            "original_file_source_is_OSF_official_metadata_link":True,
        }
        if record["_private_extension"]==".csv":
            entry.update(first_header_schema(raw))
        else:
            entry.update(r_source_code_grammar(raw))
        original.append(entry)
    csvs=[x for x in original if x["original_file_type"]==".csv"]
    scripts=[x for x in original if x["original_file_type"]==".r"]
    if len(csvs)!=3 or len(scripts)!=1:
        raise SourceStop("SOURCE_LEIPZIG_OSF_AFTER_DOWNLOAD_ORIGINAL_FILE_TYPE_DRIFT")
    return {
       "source_publisher_OSF_id":NODE_ID,
       "original_OSF_project_public":project["source_original_node_explicit_public"],
       "original_OSF_node_json_sha256":node_rcpt["original_publisher_metadata_sha256"],
       "original_OSF_storage_catalog_json_sha256":manifest_rcpt["original_publisher_metadata_sha256"],
       "source_original_exact_total_downloaded_4files_bytes":sum(x["original_source_file_byte_count"] for x in original),
       "source_original_file_structure_count":{"original_csv":3,"original_R":1},
       "source_original_file_first_headers_and_R_method_aggregates":original,
       "original_source_sample_or_beetle_biological_response_rows_READ":0,
       "original_R_scripts_executed":0,
       "new_regional_prediction_or_guild_effect_computed":False,
       "original_files_filenames_URIs_fileIDs_or_raw_headers_NOT_EXPORTED":True,
       "status":"SOURCE_LEIPZIG2022_ORIGINAL_3CSV_1R_FIRST_HEADERS_PASS",
    }

def known_truth():
    fake_meta=[]
    for i,(name,siz) in enumerate([
       ("PRIVATE_A.csv",1000),("PRIVATE_B.csv",800),("PRIVATE_C.csv",1300),("PRIVATE_R.R",810217)]):
       fake_meta.append({"id":f"private_{i}","attributes":{
        "kind":"file","name":name,"size":siz},
        "links":{"download":f"https://osf.io/download/private_{i}/"}})
    fixed=official_file_manifest({"data":fake_meta})
    assert len(fixed)==4
    assert sum(r["_private_size"] for r in fixed)==813317
    fields=first_header_schema(
        b"plotid,tree,trapheight,temp,species,count\nPRIVATE_BIOLOGY_SAMPLE_NOT_READ,Oak,20,15,Carabus,33\n"
    )
    assert fields["original_csv_FIRST_HEADER_fields_count"]==6
    assert fields["original_csv_data_rows_READ"]==0
    assert "PRIVATE_BIOLOGY" not in json.dumps(fields)
    r=r_source_code_grammar(b'dat <- read.csv("PRIVATE_TAXA.csv")\nmerge(dat,by="site")\n')
    assert r["author_original_R_keyword_occurrences_code_only"]["source_csv_import"]>=1
    assert "PRIVATE_TAXA" not in json.dumps(r)
    print("SYNTHETIC_OSF_3CSV_1R_FIXED_SOURCE_HEADER_AND_CODE_ONLY_GATE_PASS")

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--test",action="store_true")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    known_truth()
    if args.test:return
    if args.out is None:parser.error("--out required")
    result={
       "schema":"structural.haack2022_leipzig_OSF3CSV1R_firstheaders_Rscript_only.v1",
       "precommit":PRESPEC,
       "source_original_DOI":"10.3390/insects13020161",
       "source_OSF_node":"9dhzw",
       "source_field_forest_count_NOT_multiregion":1,
       "source_original_canopy_2levels_published_20m_25m":True,
       "original_ground_vs_canopy_preservative_CONFOUNDED":True,
       "original_field_microclimate_and_host_deadwood_quantity_MEASURED_UNVERIFIED":True,
       "original_species_taxon_trap_OR_community_value_rows_ACCESSED":0,
       "all_earlier_England_Carpathian_Finland_Thai_PREDICTS_NEON_BALA_GEB_biology_UNCHANGED":True,
       "eBird_used":False,"TinyFish_used":False,
    }
    try:
        d=original_once()
        result["original_publisher_file_header_and_R_code_only_receipts"]=d
        result["status"]=d["status"]
    except SourceStop as exc:
        result["status"]=str(exc)
        result["source_access_or_schema_STOP_not_ecological_null"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Haack2022_OSF9dhzw_original3CSV1R_headers_R_method_only.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"
    )
    print("ORIGINAL_LEIPZIG_3CSV1R_METHOD_SOURCE_ONLY",result["status"])
    print("NO_BEETLE_SPECIES_ORIGINAL_ABUNDANCE_MATRIX_ROWS_OPENED")
if __name__=="__main__":
    main()
