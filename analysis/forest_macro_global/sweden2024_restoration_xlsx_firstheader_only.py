#!/usr/bin/env python3
"""Exact author 2024 restoration XLSX: one original official GET, HEADER ONLY.

Source is a CC0 Dryad published 2024 forest restoration analysis TABLE,
not an independent 2026 study or a species×trap composition matrix.
No original measured wood, beetle values or site IDs are opened/extracted.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import posixpath
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

URL="https://datadryad.org/api/v2/files/2826007/download"
SIZE=30080
SHA="5a29e92e95a0efec671f110a292a61b412e592a5004092d99c181658439e2967"
N_MAIN=("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}",
        "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}")
MAIN, DOCREL=N_MAIN
WHITELIST={
    "Plotid","Trap","Plot","Treatment","trapid","ab","spr","trt",
    "declog","decsnag","conlog","consnag","log","snag","dw","decdw",
    "condw","rlab","rlspr","wbab","wbspr","sxab","sxspr",
    "predab","predspr","fungab","fungspr","woodab","woodspr",
    "conab","conspr","decab","decspr","bothab","bothspr",
    "earlyab","earlyspr","midab","midspr","lateab","latespr",
    "generab","generspr"
}

class SourceStop(ValueError):pass

def official_one_request():
    req=urllib.request.Request(URL,headers={
      "User-Agent":"Structural-original-Sweden2024-exact-XLSX-sourceonly/1.0",
      "Accept":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=36) as r:
            if r.status!=200:
                raise SourceStop("SOURCE_PUBLISHER_ORIGINAL_GET_NOT_200")
            u=r.url
            # Dryad public original endpoint may redirect to an official
            # cloud object. Do not derive alternate URL or retry anything.
            if not u.startswith("https://"):
                raise SourceStop("SOURCE_PUBLISHER_ORIGINAL_REDIRECT_INSECURE")
            blob=r.read(100001)
    except urllib.error.HTTPError as e:
        raise SourceStop("SOURCE_ORIGINAL_DRYAD_XLSX_HTTP_"+str(e.code))
    except (urllib.error.URLError,OSError,TimeoutError) as e:
        raise SourceStop("SOURCE_ORIGINAL_DRYAD_XLSX_TRANSPORT_"+type(e).__name__)
    if len(blob)!=SIZE or hashlib.sha256(blob).hexdigest()!=SHA:
        raise SourceStop("SOURCE_ORIGINAL_XLSX_BYTES_SHA_OR_SIZE_MISMATCH_STOP")
    return blob

def sharedstrings(z, wanted):
    if not wanted:return {}
    if "xl/sharedStrings.xml" not in z.namelist():
        raise SourceStop("SOURCE_HEADER_SHAREDSTRING_FILE_MISSING")
    found={}
    with z.open("xl/sharedStrings.xml") as f:
        i=0
        for event,element in ET.iterparse(f,events=("end",)):
            if element.tag==MAIN+"si":
                if i in wanted:
                    found[i]="".join(x.text or "" for x in element.iter(MAIN+"t"))
                i+=1
                element.clear()
    if len(found)!=len(wanted):raise SourceStop("SOURCE_FIRST_HEADER_SST_INDEX_MISSING")
    return found

def worksheet_first_row(z,name):
    # Stops at end of first row, never reads subsequent biological rows.
    dim=None
    fields=[]
    with z.open(name) as f:
        for _,element in ET.iterparse(f,events=("end",)):
            if element.tag==MAIN+"dimension":
                dim=element.attrib.get("ref","")[:50]
            if element.tag!=MAIN+"row":continue
            if element.attrib.get("r","")!="1":
                raise SourceStop("SOURCE_HEADER_NOT_ROW_1")
            for cell in element.findall(MAIN+"c"):
                typ=cell.attrib.get("t","n")
                v=cell.find(MAIN+"v")
                if typ=="s" and v is not None and (v.text or "").isdigit():
                    fields.append(("s",int(v.text)))
                elif typ=="inlineStr":
                    fields.append(("inline","".join(x.text or "" for x in cell.iter(MAIN+"t"))))
                elif typ=="str" and v is not None:
                    fields.append(("str",str(v.text or "")))
                else:
                    fields.append(("unknown",""))
            break
    if not fields:raise SourceStop("SOURCE_EXCEL_FIRST_ROW_EMPTY")
    return dim,fields

def sheet_manifest(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=z.namelist()
        if len(set(names))!=len(names) or len(names)>150:
            raise SourceStop("SOURCE_EXCEL_CENTRAL_DIRECTORY_UNEXPECTED")
        if "xl/workbook.xml" not in names or "xl/_rels/workbook.xml.rels" not in names:
            raise SourceStop("SOURCE_WORKBOOK_XML_MISSING")
        wb=ET.fromstring(z.read("xl/workbook.xml"))
        rel=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        aliases={r.attrib.get("Id"):r.attrib.get("Target","") for r in rel}
        listed=[]
        refs={}
        for sheet in wb.iter(MAIN+"sheet"):
            shname=sheet.attrib.get("name","")[:90]
            rid=sheet.attrib.get(DOCREL+"id")
            target=aliases.get(rid,"")
            if target.startswith("/xl/"):
                member=target.lstrip("/")
            else:
                member=posixpath.normpath(posixpath.join("xl",target))
            if member not in names or not member.startswith("xl/worksheets/"):
                raise SourceStop("SOURCE_EXCEL_SHEET_PATH_NOT_IN_ARCHIVE")
            dimension,head=worksheet_first_row(z,member)
            refs[shname]=(dimension,head)
        all_sst={value for _,(dim,cols) in refs.items() for typ,value in cols if typ=="s"}
        strings=sharedstrings(z,all_sst)
        for sheet,(dim,cols) in refs.items():
            names0=[
                strings.get(val,"") if typ=="s" else val if typ in ("inline","str") else ""
                for typ,val in cols
            ]
            known=sorted(set(names0)&WHITELIST)
            listed.append({
                "source_original_sheet_title":sheet if re.fullmatch(r"[A-Za-z0-9._ -]{1,90}",sheet) else "MASKED_SHEET",
                "source_worksheet_dimensions_metadata":dim,
                "source_first_header_row_columns":len(cols),
                "source_documented_original_method_columns_present":known,
                "unknown_nonwhitelisted_first_header_count":len(names0)-len(known),
                "original_data_row_values_read":0,
                "original_beetle_count_or_taxon_cells_read":0
            })
    return listed

def test():
    assert len(SHA)==64 and SIZE==30080
    assert {"declog","decsnag","decspr","latespr","Plotid","Treatment"}<=WHITELIST
    assert "scientificName" not in WHITELIST
    sample=io.BytesIO()
    with zipfile.ZipFile(sample,"w") as z:
        z.writestr("xl/workbook.xml",(
           '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
           '<sheets><sheet name="Method" sheetId="1" r:id="rId1"/></sheets></workbook>'))
        z.writestr("xl/_rels/workbook.xml.rels",(
           '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
           '<Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>'))
        z.writestr("xl/worksheets/sheet1.xml",(
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
           '<dimension ref="A1:B3"/><sheetData><row r="1">'
           '<c r="A1" t="inlineStr"><is><t>Plotid</t></is></c>'
           '<c r="B1" t="inlineStr"><is><t>decdw</t></is></c>'
           '</row><row r="2"><c r="A2"><v>1</v></c></row></sheetData></worksheet>'))
    s=sheet_manifest(sample.getvalue())
    assert s[0]["source_documented_original_method_columns_present"]==["Plotid","decdw"]
    assert s[0]["original_data_row_values_read"]==0
    print("SWEDEN2024_SOURCE_ONLY_EXCEL_FIRST_HEADER_SYNTHETIC_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",default="sweden2024_original_xlsx_firstheader/receipt.json")
    a=p.parse_args()
    test()
    if a.test:return
    result={
       "schema":"structural.sweden2024_restoration_original_2021_XLSX_FIRST_HEADER.v1",
       "original_source_doi":"10.5061/dryad.c2fqz61gv",
       "original_expected_file_sha256":SHA,
       "original_expected_file_bytes":SIZE,
       "2024_2026_study_lineage_treated_as_potentially_shared":True,
       "original_workbook_or_beetle_source_rows_exported":False,
       "new_beetle_or_resource_ecological_effects":0,
       "original_taxon_guild_or_site_record_values_read":0,
       "status":"SOURCE_OFFICIAL_WORKBOOK_NOT_FETCHED"}
    try:
        result["source_workbook_header_method_only"]=sheet_manifest(official_one_request())
        result["status"]="SOURCE_OFFICIAL_WORKBOOK_XLSX_HEADERS_VERIFIED_NO_BIOLOGY"
    except SourceStop as e:
        result["status"]="SOURCE_OFFICIAL_XLSX_FILE_ACCESS_OR_SCHEMA_STOP"
        result["scientific_source_stop"]=str(e)
    except Exception as e:
        result["status"]="SOURCE_ORIGINAL_WORKBOOK_RUNTIME_STOP"
        result["error_type"]=type(e).__name__
    f=Path(a.out);f.parent.mkdir(parents=True,exist_ok=True)
    f.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("SWEDEN_RESTORATION_SOURCE_XLSX",result["status"])
    print("ORIGINAL_BIOLOGICAL_VALUES_READ",result["original_taxon_guild_or_site_record_values_read"])

if __name__=="__main__":
    main()
