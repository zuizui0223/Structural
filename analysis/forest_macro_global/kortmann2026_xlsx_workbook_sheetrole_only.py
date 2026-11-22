#!/usr/bin/env python3
"""Source-original Kortmann 17775805 XLSX workbook STRUCTURAL sheet names only.

Verifies the fixed original ZIP and one XLSX member, but reads only
xl/workbook.xml inside XLSX. NO worksheets, shared strings, taxa or OTU cells.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.error
import xml.etree.ElementTree as ET
import zipfile

from kortmann2026_17775805_original_zip_directory_only import (
    SourceStop, original_file_metadata, official_get_one_zip,
    inspect_central_directory_only,
)

MEMBER = ("data_public/FT_Retz_RV-UniWue-2022-003_"
          "COI_w-1-tons_results_AIMIDs.xlsx")
SIZE = 73378007
XML = "xl/workbook.xml"
XML_MAX = 512 * 1024
MAX_INNER_FILES = 5000
MAX_SHEETS = 1000
METHOD = re.compile(r"sample|collect|trap|bottle|event|field|metadata|method",re.I)
BIOLOGY = re.compile(r"otu|taxon|specie|ident|aim|match",re.I)
MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
PRESPEC = ("docs/FOREST_MACRO_KORTMANN2026_AUTHOR_XLSX_"
           "WORKBOOK_SHEETROLE_PREFREEZE_20261122.md")

def scan_workbook_structural_sheet_names(workbook: bytes) -> dict:
    try:
        f=zipfile.ZipFile(io.BytesIO(workbook), "r")
    except (zipfile.BadZipFile,zipfile.LargeZipFile,ValueError):
        raise SourceStop("SOURCE_AUTHOR_WORKBOOK_NOT_OPENXML_ZIP") from None
    with f:
        info=f.infolist()
        if not info or len(info)>MAX_INNER_FILES:
            raise SourceStop("SOURCE_AUTHOR_WORKBOOK_INNER_DIRECTORY_TOO_LARGE")
        seen=set()
        for z in info:
            name=z.filename
            if (not isinstance(name,str) or name.startswith("/")
                or "\\" in name or any(x==".." for x in name.split("/"))
                or name in seen or z.flag_bits&1):
                raise SourceStop("SOURCE_AUTHOR_WORKBOOK_INNER_PATH_UNSAFE")
            seen.add(name)
        if XML not in seen:
            raise SourceStop("SOURCE_AUTHOR_WORKBOOK_XML_MISSING")
        if f.getinfo(XML).file_size>XML_MAX:
            raise SourceStop("SOURCE_AUTHOR_WORKBOOK_XML_OVERSIZED")
        try:
            with f.open(XML,"r") as stream:
                only_xml=stream.read(XML_MAX+1)
        except (OSError,zipfile.BadZipFile,RuntimeError):
            raise SourceStop("SOURCE_AUTHOR_WORKBOOK_XML_READ_STOP") from None
    if not only_xml or len(only_xml)>XML_MAX:
        raise SourceStop("SOURCE_AUTHOR_WORKBOOK_XML_EMPTY_OR_OVERSIZED")
    try:
        root=ET.fromstring(only_xml)
    except ET.ParseError:
        raise SourceStop("SOURCE_AUTHOR_WORKBOOK_XML_PARSE_STOP") from None
    if root.tag!=MAIN+"workbook":
        raise SourceStop("SOURCE_AUTHOR_WORKBOOK_XML_WRONG_NAMESPACE")
    sheets=root.find(MAIN+"sheets")
    if sheets is None:
        raise SourceStop("SOURCE_AUTHOR_WORKBOOK_SHEET_SET_MISSING")
    sheet_tags=list(sheets)
    if not sheet_tags or len(sheet_tags)>MAX_SHEETS:
        raise SourceStop("SOURCE_AUTHOR_WORKBOOK_SHEET_COUNT_UNSAFE")
    stats=Counter()
    names=set()
    for e in sheet_tags:
        if e.tag!=MAIN+"sheet":
            raise SourceStop("SOURCE_AUTHOR_WORKBOOK_UNEXPECTED_SHEET_TAG")
        title=e.get("name")
        if (not isinstance(title,str) or not 1<=len(title)<=200
            or title.casefold() in names):
            raise SourceStop("SOURCE_AUTHOR_WORKBOOK_INVALID_OR_DUP_SHEET_TITLE")
        names.add(title.casefold())
        stats["sheets"]+=1
        if METHOD.search(title):stats["possible_sampling_method_title"]+=1
        if BIOLOGY.search(title):stats["possible_biology_pipeline_title"]+=1
        if not METHOD.search(title) and not BIOLOGY.search(title):
            stats["unclassified_title"]+=1
    return {
      "status":("SOURCE_AUTHOR_WORKBOOK_SHEETROLE_CANDIDATE_ONLY_NO_CELL_READ"
                if stats["possible_sampling_method_title"] else
                "SOURCE_AUTHOR_WORKBOOK_SHEETROLE_NOT_EVIDENCED_NO_CELL_READ"),
      "original_inner_XLSX_file_count_not_extracted":len(info),
      "source_worksheet_count":stats["sheets"],
      "method_like_sheet_title_count_not_verified_content":
           stats["possible_sampling_method_title"],
      "taxonomy_or_lab_like_sheet_title_count_not_verified_content":
           stats["possible_biology_pipeline_title"],
      "other_sheet_title_count":stats["unclassified_title"],
      "source_sheet_titles_NOT_EXPORTED":True,
      "original_worksheet_XML_contents_NOT_OPENED":True,
      "sharedStrings_XML_NOT_OPENED":True,
      "original_taxon_OTU_abundance_fields_NOT_READ":True,
      "new_ecological_effects_scored":0,
      "sample_to_method_join_remains_HOLD":True,
    }

def synthetic():
    out=io.BytesIO()
    xml=('<?xml version="1.0" encoding="utf-8"?>'
         '<workbook xmlns="http://schemas.openxmlformats.org/'
         'spreadsheetml/2006/main"><sheets>'
         '<sheet name="collection_metadata" sheetId="1"/>'
         '<sheet name="AIM_ids" sheetId="2"/>'
         '</sheets></workbook>').encode("utf8")
    with zipfile.ZipFile(out,"w") as z:
        z.writestr(XML,xml)
        z.writestr("xl/worksheets/sheet1.xml",
                   b"SECRET_PRIVATE_SAMPLE_AND_BIOLOGY_VALUE_DO_NOT_READ")
        z.writestr("xl/sharedStrings.xml",
                   b"SECRET_ORIGINAL_TAXON_NAMES_DO_NOT_READ")
    a=scan_workbook_structural_sheet_names(out.getvalue())
    assert a["source_worksheet_count"]==2
    assert a["method_like_sheet_title_count_not_verified_content"]==1
    assert a["taxonomy_or_lab_like_sheet_title_count_not_verified_content"]==1
    assert "SECRET" not in json.dumps(a)
    for attack in ("../xl/private.xml","xl/../secret.xml"):
        bad=io.BytesIO()
        with zipfile.ZipFile(bad,"w") as z:
            z.writestr(XML,xml)
            z.writestr(attack,"SECRET")
        try:
            scan_workbook_structural_sheet_names(bad.getvalue())
        except SourceStop:
            pass
        else:
            raise AssertionError("unsafe original workbook path accepted")
    print("SYNTHETIC_KORTMANN_XLSX_SHEETNAMES_ONLY_NO_DATA_PASS")

def run():
    source_url=original_file_metadata()
    archive=official_get_one_zip(source_url)
    d=inspect_central_directory_only(archive)
    if d["status"]!="SOURCE_ZIP_CENTRAL_DIRECTORY_READY_METADATA_ONLY":
        raise SourceStop("SOURCE_PUBLISHER_ARCHIVE_DIRECTORY_STOP")
    with zipfile.ZipFile(io.BytesIO(archive),"r") as z:
        info=z.getinfo(MEMBER)
        if info.file_size!=SIZE or info.flag_bits&1:
            raise SourceStop("SOURCE_AUTHOR_WORKBOOK_ORIGINAL_MEMBER_SIZE_DRIFT")
        with z.open(info,"r") as stream:
            raw=stream.read(SIZE+1)
    if len(raw)!=SIZE:
        raise SourceStop("SOURCE_AUTHOR_WORKBOOK_ORIGINAL_MEMBER_BYTE_DRIFT")
    scan=scan_workbook_structural_sheet_names(raw)
    return {
      "original_publisher_record":17775805,
      "source_original_full_archive_MD5_verified":
          "41f9a8428d80e833e4785be198a5c886",
      "source_XLSX_uncompressed_member_size_verified":SIZE,
      "source_XLSX_member_SHA256_new_fingerprint_only":
          hashlib.sha256(raw).hexdigest(),
      "original_workbook_structural_sheet_role_only":scan,
      "no_original_RData_or_OTU_member_reopened":True,
      "no_source_OTU_numeric_taxon_or_sample_ID_values":True,
      "status":scan["status"],
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:p.error("--out required")
    out={
        "schema":"structural.Kortmann17775805_original_XLSX_workbook_sheetroles_only.v1",
        "prespec":PRESPEC,
        "historical_40_original_triplet_HOLD_unchanged":True,
        "existing_OTU_SAMPLE_LINK_HOLD_unchanged":True,
        "original_20k_x_702_OTU_RData_PREVIOUSLY_DESERIALIZED_SCHEMA_ONLY":True,
        "no_new_biodiversity_models":True,
        "eBird_used":False,"TinyFish_used":False,
    }
    try:
        out["source"]=run()
        out["status"]=out["source"]["status"]
    except (SourceStop,KeyError) as ex:
        # These only emit stable source diagnostic codes. No publisher row values.
        reason=str(ex)
        if not re.fullmatch("[A-Z0-9_]{6,130}",reason):
            reason="SOURCE_WORKBOOK_UNEXPECTED_SCHEMA_OR_FILE_STOP"
        out["status"]="SOURCE_WORKBOOK_SHEETROLE_STOP_"+reason
        out["not_ecological_null"]=True
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print("KORTMANN_SOURCE_WORKBOOK_SHEETROLES",out["status"])
    print("ORIGINAL_XLSX_WORKSHEETS_AND_OTU_VALUES_UNREAD; SAMPLE_LINK_HOLD_UNCHANGED")

if __name__=="__main__":
    main()
