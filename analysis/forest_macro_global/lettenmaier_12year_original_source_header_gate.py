#!/usr/bin/env python3
"""Lettenmaier 12-year beetle/hostwood ORIGINAL source-only schema gate.

Two published CSV first lines and one XLSX original workbook sheet inventory.
No original organism rows, tree measurements, species/trait values, or source
log/site identifiers are inspected, published or scored.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

RECORD=17337484
MANIFEST={
 "original_beetle_community":{
   "filename":"Beetle_Community_JAE-2025-00357.csv",
   "size":329736,"md5":"a5d8a26d932594ce40dc6b5aba269c19"},
 "original_beetle_sampling":{
   "filename":"Beetle_Data_JAE-2025-00357.csv",
   "size":852649,"md5":"ae7254baac19934a75242defce6ada59"},
 "original_trait_workbook":{
   "filename":"Trait_Table_JAE-2025-00357.xlsx",
   "size":58578,"md5":"3a5b226e35d75cd3ed7501dff3c15bc1"},
}
GENERIC_META={
 "sample_id","sampleid","sample","samplingunit","observation","observationid",
 "trap","trapid","trap_id","event","eventid","plot","plotid","plot_id",
 "site","siteid","site_id","region","regionid","region_id","forest","forestid",
 "tree","treespecies","tree_species","wood","woodtype","wood_type","trunk",
 "trunkid","trunk_id","log","logid","log_id","stem","stemid","stem_id","branch",
 "year","samplingyear","sampling_year","calendar_year","date","collectiondate",
 "period","age","woodage","wood_age","exposureyear","exposure_year",
 "elapsedage","decay","decaystage","decay_stage","host","hosttree","host_tree",
 "hostspecies","host_species","treatment","replicate","numberoftraps","effort",
 "taxon","taxonid","species","speciesname","scientificname","abundance",
 "individualcount","count","number","plots","lognumber","treenumber",
 "altitude","elevation","dbh","diameter"
}
FIELDS_EXPOSE_ONLY={
 "log_site_structure": {
   "plot","plotid","plot_id","site","siteid","site_id","forest","forestid",
   "region","regionid","region_id","trunk","trunkid","trunk_id","log","logid",
   "log_id","stem","stemid","stem_id","tree","treenumber","lognumber"},
 "time_sampling":{
   "year","samplingyear","sampling_year","calendar_year","date","collectiondate",
   "period","age","woodage","wood_age","exposureyear","exposure_year",
   "elapsedage","decay","decaystage","decay_stage"},
 "hostwood_measurement":{
   "wood","woodtype","wood_type","treespecies","tree_species","host","hosttree",
   "host_tree","hostspecies","host_species","dbh","diameter"},
 "method_effort":{
   "sample_id","sampleid","sample","samplingunit","observation","observationid",
   "trap","trapid","trap_id","event","eventid","treatment","replicate",
   "numberoftraps","effort"},
 "taxon_data_field_only":{
   "taxon","taxonid","species","speciesname","scientificname","abundance",
   "individualcount","count"}
}
XLSX_NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"

class SourceStop(Exception):pass


def source_pub_bytes(meta):
    name=meta["filename"]
    req=urllib.request.Request(
      f"https://zenodo.org/records/{RECORD}/files/{name}?download=1",
      headers={"User-Agent":"Structural-source-identity-prebiology/1.0"})
    try:
      with urllib.request.urlopen(req,timeout=40) as f:
        data=f.read(meta["size"]+1)
        status=f.status
    except urllib.error.HTTPError as exc:
      raise SourceStop(f"SOURCE_STOP_ZENODO_ARCHIVE_HTTP_{exc.code}") from exc
    except (urllib.error.URLError,TimeoutError,OSError) as exc:
      raise SourceStop("SOURCE_STOP_ZENODO_ARCHIVE_TRANSPORT_"+type(exc).__name__) from exc
    if status!=200 or len(data)!=meta["size"]:
      raise SourceStop("SOURCE_STOP_ORIGINAL_PUBLISHED_BYTECOUNT_CHANGED")
    if hashlib.md5(data).hexdigest()!=meta["md5"]:
      raise SourceStop("SOURCE_STOP_PUBLISHED_ORIGINAL_MD5_CHANGED")
    return data


def approved_field_name(x):
    label=str(x).strip()
    if not label or len(label)>48:
        return None
    if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_ .-]*",label):
        return None
    token=re.sub(r"[^a-z0-9_]","",label.lower())
    if token not in GENERIC_META:
        return None
    for key,v in FIELDS_EXPOSE_ONLY.items():
        if token in v:
            return {"generic_source_field_category":key,
                    "generic_original_field_label_only":label}
    return None


def csv_first_header(binary):
    # Header only; original data rows intentionally NOT parsed. Physical
    # newline count is a byte-level diagnostic, not a sample denominator.
    head=binary.split(b"\n",1)[0].decode("utf-8-sig","replace").rstrip("\r")
    sep=max((",",";","\t"),key=head.count)
    values=next(csv.reader([head],delimiter=sep),[])
    if len(values)<2:
        raise SourceStop("SOURCE_STOP_ORIGINAL_CSV_NOT_TABULAR")
    accepted=[]
    for i,name in enumerate(values):
        hit=approved_field_name(name)
        if hit:
            accepted.append({"source_column_index_1based":i+1,**hit})
    counts={}
    for item in accepted:
        category=item["generic_source_field_category"]
        counts[category]=counts.get(category,0)+1
    return {
       "original_csv_header_field_count":len(values),
       "original_csv_physical_lines_including_header_NOT_VALIDATED_SAMPLE_COUNT":binary.count(b"\n")+
         (0 if binary.endswith(b"\n") else 1),
       "source_file_delimiter_class":{",":"comma",";":"semicolon","\t":"tab"}[sep],
       "source_safe_generic_metadata_field_names_only":accepted,
       "source_generic_header_category_counts":counts,
       "original_response_taxon_names_and_biology_values_UNREAD":True,
       "source_sample_year_log_hierarchy_NOT_VERIFIED":True,
    }


def trait_xlsx_workbook_header_only(binary):
    if not binary.startswith(b"PK"):
        raise SourceStop("SOURCE_STOP_AUTHOR_TRAIT_XLSX_NOT_ZIP")
    with zipfile.ZipFile(io.BytesIO(binary),"r") as z:
        if "xl/workbook.xml" not in z.namelist():
            raise SourceStop("SOURCE_STOP_TRAIT_WORKBOOK_METADATA_MISSING")
        xml=ET.fromstring(z.read("xl/workbook.xml"))
        sheets=[n.attrib.get("name","") for n in xml.findall(f".//{{{XLSX_NS}}}sheet")]
        if not sheets or any(not s for s in sheets):
            raise SourceStop("SOURCE_STOP_AUTHOR_TRAIT_WORKBOOK_SHEET_NAMES_UNAVAILABLE")
        return {
           "source_original_sheet_count":len(sheets),
           "source_original_sheet_names":sheets,
           "source_original_workbook_packages":len(z.namelist()),
           "taxon_traits_cells_and_species_names_UNREAD":True,
           "author_source_traits_not_automatically_Host_tree_affinity":True,
        }


def known_truth():
    assert approved_field_name("logID")["generic_source_field_category"]=="log_site_structure"
    assert approved_field_name("Year")["generic_source_field_category"]=="time_sampling"
    assert approved_field_name("host_tree")["generic_source_field_category"]=="hostwood_measurement"
    assert approved_field_name("Bolitochara pulchra") is None
    t=csv_first_header(b"logID,Year,Fagus sylvatica,Abundance\nLOG4,2018,10,20\n")
    assert t["source_safe_generic_metadata_field_names_only"][0]["generic_original_field_label_only"]=="logID"
    assert len(t["source_safe_generic_metadata_field_names_only"])==3
    assert t["original_csv_physical_lines_including_header_NOT_VALIDATED_SAMPLE_COUNT"]==2
    assert t["original_response_taxon_names_and_biology_values_UNREAD"]
    print("SYNTHETIC_12YEAR_CSV_HEADER_ONLY_AND_TAXON_REDACTION_PASS")


def audit():
    receipt={
        "schema":"structural.Lettenmaier2025_original_12year_beetle_hostwood_source_schema_only.v1",
        "original_zenodo_DOI":"10.5281/zenodo.17337484",
        "original_Article_DOI":"10.1111/1365-2656.70183",
        "original_three_pinned_files_MD5_and_size_verified":False,
        "original_wood_tree_species_taxa_abundance_and_functional_trait_values_NOT_READ":True,
        "source_original_site_log_year_records_NOT_REEXPORTED":True,
        "authors_original_12year_independent_log_count_NOT_INFERRED":True,
        "reported_author_tree_hosts":["spruce","fir","beech"],
        "original_Finland142site_VD10_guild_PREDICTS_NEON_BALA_GEB_original_results_unchanged":True,
        "eBird_used":False,
    }
    try:
        files={k:source_pub_bytes(v) for k,v in MANIFEST.items()}
        receipt["original_three_pinned_files_MD5_and_size_verified"]=True
        receipt["original_source_schema"]={
            "Beetle_Community":csv_first_header(files["original_beetle_community"]),
            "Beetle_Data":csv_first_header(files["original_beetle_sampling"]),
            "Trait_Table":trait_xlsx_workbook_header_only(files["original_trait_workbook"]),
        }
        receipt["status"]="SOURCE_ORIGINAL_CSV_AND_TRAIT_HEADER_RECEIVED_LOG_TREE_YEAR_JOIN_UNVERIFIED"
    except SourceStop as e:
        receipt["status"]=str(e)
        receipt["source_access_or_schema_STOP_not_ecological_non_support"]=True
    return receipt


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    known_truth()
    if args.test:return
    if not args.out:ap.error("--out required")
    r=audit()
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Lettenmaier12y_original_header_sourceonly.json").write_text(
       json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))


if __name__=="__main__":main()
