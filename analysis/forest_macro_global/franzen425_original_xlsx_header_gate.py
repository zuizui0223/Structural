#!/usr/bin/env python3
"""Franzén2026 CC0 Dryad original 425-beetle XLSX: exact-byte/first-header only.

Never decode an original species name, feeding-guild row, body length or
Carpathian beetle matrix. ZIP/XML parser only reaches first worksheet row.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

URL="https://datadryad.org/api/v2/files/4851331/download"
SHA="68d9c10f70174f2166c664ca6e549d8731ed8ffdbe5f912b02269402aa2c3b08"
SIZE=26345
PRESPEC="docs/FOREST_MACRO_FRANZEN425_ORIGINAL_XLSX_STRUCTURE_PRESPEC_20261118.md"
FIELDS=("Species","Family","Trophic_group","Body_length")
MAIN="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
MAX_ZIP_PART=3000000

class SourceStop(RuntimeError):pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def exact_publisher_bytes():
    req=urllib.request.Request(URL,headers={
        "User-Agent":"Structural-Franzen2026-original-Dryad-425-guild-header-only/1.0",
        "Accept":"*/*",
    })
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=45) as r:
            if r.status!=200:raise SourceStop("SOURCE_DRYAD_XLSX_NOT_HTTP200")
            data=r.read(SIZE+1)
    except urllib.error.HTTPError as ex:
        raise SourceStop("SOURCE_DRYAD_XLSX_HTTP_"+str(ex.code)) from None
    except (urllib.error.URLError,OSError,TimeoutError) as ex:
        raise SourceStop("SOURCE_DRYAD_XLSX_TRANSPORT_"+type(ex).__name__) from None
    if len(data)!=SIZE or hashlib.sha256(data).hexdigest()!=SHA:
        raise SourceStop("SOURCE_DRYAD_ORIGINAL_XLSX_SHA256_SIZE_STOP")
    return data

def parse_source_worksheet_first_row(sheet_xml):
    """Read XML elements only through first row; do not inspect following rows."""
    header=[]
    seen=False
    try:
        it=ET.iterparse(io.BytesIO(sheet_xml),events=("start","end"))
        in_first=False
        for ev,el in it:
            tag=el.tag.rsplit("}",1)[-1]
            if ev=="start" and tag=="row":
                if seen:break
                if el.attrib.get("r") not in ("1",None):
                    raise SourceStop("SOURCE_XLSX_HEADER_NOT_FIRST_ROW")
                in_first=True
            elif ev=="end" and tag=="c" and in_first:
                if len(header)>=12:raise SourceStop("SOURCE_XLSX_FIRST_HEADER_GT12")
                rawref=el.attrib.get("r","")
                if not re.fullmatch(r"[A-L]1",rawref):
                    raise SourceStop("SOURCE_XLSX_HEADER_COLUMN_REF_STOP")
                code=el.attrib.get("t","")
                children=list(el)
                one=next((x for x in children if x.tag.endswith("}v")),None)
                if code=="s" and one is not None:
                    if one.text is None or not one.text.isdigit():
                        raise SourceStop("SOURCE_XLSX_FIRST_ROW_SHARED_INDEX_BAD")
                    header.append(("shared",int(one.text)))
                elif code=="inlineStr":
                    texts=[e.text or "" for e in el.iter() if e.tag.endswith("}t")]
                    header.append(("inline","".join(texts)))
                elif one is not None:
                    header.append(("raw",one.text or ""))
                else:
                    raise SourceStop("SOURCE_XLSX_HEADER_CELL_VALUE_UNSUPPORTED")
                el.clear()
            elif ev=="end" and tag=="row" and in_first:
                seen=True
                break
    except ET.ParseError:
        raise SourceStop("SOURCE_XLSX_SHEET_XML_UNREADABLE") from None
    if len(header)!=4:raise SourceStop("SOURCE_XLSX_FOUR_FIRST_ROW_FIELDS_NOT_FOUND")
    return header

def first_shared_string_items(xml_data, max_index):
    """Only parse shared-string entries needed by first row; no later taxa."""
    if max_index>15:raise SourceStop("SOURCE_XLSX_HEADER_SHARED_STRINGS_TOO_DEEP")
    result=[]
    try:
        it=ET.iterparse(io.BytesIO(xml_data),events=("end",))
        for ev,el in it:
            if el.tag==f"{{{MAIN}}}si":
                result.append("".join(t.text or "" for t in el.iter(f"{{{MAIN}}}t")))
                el.clear()
                if len(result)>max_index:break
    except ET.ParseError:
        raise SourceStop("SOURCE_XLSX_SHARED_STRINGS_XML_UNREADABLE") from None
    if len(result)<=max_index:raise SourceStop("SOURCE_XLSX_ORIGINAL_FIRST_ROW_SHARED_STRING_MISSING")
    return result

def source_structure(original):
    try:
        z=zipfile.ZipFile(io.BytesIO(original))
    except (zipfile.BadZipFile,OSError):
        raise SourceStop("SOURCE_DRYAD_ORIGINAL_XLSX_BAD_ZIP") from None
    with z:
        files=z.namelist()
        if not 1<=len(files)<=120:
            raise SourceStop("SOURCE_XLSX_ARCHIVE_ENTRIES_OUT_OF_BOUNDS")
        if any(".." in s or s.startswith("/") or "\\" in s for s in files):
            raise SourceStop("SOURCE_XLSX_ARCHIVE_INVALID_ENTRY_PATH")
        sheets=sorted(f for f in files if re.fullmatch(r"xl/worksheets/sheet[0-9]+\.xml",f))
        if len(sheets)!=1:
            raise SourceStop("SOURCE_XLSX_ORIGINAL_MULTIPLE_OR_MISSING_WORKSHEETS")
        if any(z.getinfo(s).file_size>MAX_ZIP_PART for s in sheets):
            raise SourceStop("SOURCE_XLSX_ORIGINAL_SHEET_TOO_LARGE")
        data=z.read(sheets[0])
        header=parse_source_worksheet_first_row(data)
        if any(k=="shared" for k,_ in header):
            path="xl/sharedStrings.xml"
            if path not in files or z.getinfo(path).file_size>MAX_ZIP_PART:
                raise SourceStop("SOURCE_XLSX_ORIGINAL_SHARED_STRINGS_NOT_AVAILABLE")
            names=first_shared_string_items(z.read(path),max(x for k,x in header if k=="shared"))
        else:names=[]
        final=[names[v] if k=="shared" else v for k,v in header]
        if tuple(final)!=FIELDS:
            raise SourceStop("SOURCE_ORIGINAL_FOUR_FIELD_SCHEMA_DIFFERENT_FROM_PUBLISHER_README")
        return {
            "original_data_file_SHA256_verified":SHA,
            "original_data_file_bytes_verified":SIZE,
            "original_xlsx_archive_entry_count":len(files),
            "original_workbook_worksheet_count":len(sheets),
            "only_original_first_header_fields_verified":list(final),
            "original_all_species_trophic_group_body_size_VALUES_NOT_OPENED":True,
            "original_any_subsequent_worksheet_row_PARSED":False,
            "original_Gloor_species_names_or_observation_rows_ACCESSED":False,
            "source_taxon_coverage_NOT_INFERRED_FROM_FIELD_COUNT":True,
            "status":"ORIGINAL_GUILD_XLSX_FIRST_HEADER_SCHEMA_VERIFIED_ONLY",
        }

def synthetic():
    # In-memory OOXML first row only. Does not contain a source beetle name.
    row=(
      '<?xml version="1.0"?><worksheet xmlns="'+MAIN+
      '"><sheetData><row r="1">'+
      ''.join(f'<c r="{c}1" t="inlineStr"><is><t>{name}</t></is></c>'
         for c,name in zip("ABCD",FIELDS))+
      '</row><row r="2"><c r="A2" t="inlineStr"><is><t>SECRET_DO_NOT_OPEN</t></is></c></row></sheetData></worksheet>'
    ).encode()
    first=parse_source_worksheet_first_row(row)
    assert [v for k,v in first]==list(FIELDS)
    assert "SECRET_DO_NOT_OPEN" not in repr(first)
    print("SYNTHETIC_FRANZEN425_ORIGINAL_XLSX_FIRST_HEADER_ONLY_NO_SPECIES_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    synthetic()
    if a.test:return
    if a.out is None:p.error("--out required")
    result={
      "schema":"structural.Franzen425_Dryad_original_guild_xlsx_header_only.v1",
      "prespec":PRESPEC,
      "guild_species_row_values_READ":False,
      "original_Carpathian_response_species_labels_or_abundance_READ":False,
      "original_other_Finland_Chiu_Piccini_BELongDead_PREDICTS_NEON_BALA_GEB_UNCHANGED":True,
      "new_ecological_effect_scored":False,
      "eBird_used":False,
      "TinyFish_used":False,
    }
    try:
        result["source_verified_first_header_only"]=source_structure(exact_publisher_bytes())
        result["status"]=result["source_verified_first_header_only"]["status"]
    except SourceStop as ex:
        result["status"]=str(ex)
        result["publisher_source_STOP_not_ecological_non_support"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Franzen425_original_Dryad_guild_XLSX_first_header_only.json").write_text(
       json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("FRANZEN425_ORIGINAL_PUBLISHER_GUILD_XLSX_SCHEMA",result["status"])

if __name__=="__main__":
    main()
