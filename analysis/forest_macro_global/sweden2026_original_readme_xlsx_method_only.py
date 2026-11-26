#!/usr/bin/env python3
"""One source-only file-access gate for TWO newly authenticated Sweden 2026 studies.

Allowed: single Dryad 2026 exact README GET (author file id 4898760);
single Zenodo 2026 exact published Beetles_data.xlsx (56,235B, MD5 checked).
For Excel, inspect OpenXML ZIP central directory and workbook sheet TITLES
only. No worksheet cells, field keys, species, abundance or ecological fits.
"""
import argparse, hashlib, io, json, urllib.parse, urllib.error, urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

DRYAD_URL="https://datadryad.org/api/v2/files/4898760/download"
README_SHA="8c2ca30286df4ec4c0cd9c2e7c56e5aabc8184662027090d61c5a97c76db603d"
README_SIZE=4705
ZENODO_API="https://zenodo.org/api/records/23021809"
BOOK_NAME="Beetles_data.xlsx"
BOOK_SIZE=56235
BOOK_MD5="42b6ba1d401cf77fc70efcfa91bf7adf"
UA={"User-Agent":"Structural-forest-beetle-sourceonly-method/1.0",
    "Accept":"application/json,application/octet-stream,*/*;q=0.2"}

def get_bytes(url,limit):
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=38) as r:
            b=r.read(limit+1)
            if len(b)>limit:
                return {"status":"SIZE_CAP_STOP","http":r.status},None
            if r.status!=200:
                return {"status":"HTTP_STOP","http":r.status},None
            return {"status":"BYTES_DELIVERED","http":r.status},b
    except urllib.error.HTTPError as e:
        return {"status":"HTTP_STOP","http":e.code},None
    except Exception as e:
        return {"status":"TRANSPORT_STOP","error_type":type(e).__name__},None

def workbook_xml_metadata(blob):
    if not zipfile.is_zipfile(io.BytesIO(blob)):
        raise ValueError("SOURCE_NOT_OPENXML")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names=z.namelist()
        if ("xl/workbook.xml" not in names or "[Content_Types].xml" not in names
            or len(names)>1000 or any(s.startswith("/") or ".." in s.split("/") for s in names)):
            raise ValueError("OPENXML_DIRECTORY_STOP")
        root=ET.fromstring(z.read("xl/workbook.xml"))
        ns="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
        sheets=[e.attrib.get("name","") for e in root.iter(ns+"sheet")]
        if not sheets or len(sheets)!=len(set(sheets)):
            raise ValueError("EXCEL_SHEET_TITLES_STOP")
        return {"file_count_OpenXML_central_directory":len(names),
                "sheet_titles_from_workbook_xml_only":sheets,
                "n_original_sheets":len(sheets),
                "read_worksheet_xml_cell_values":False,
                "read_original_beetle_or_stump_values":False}

def source_dryad():
    o={"original_doi":"10.5061/dryad.gqnk98t49",
       "publisher_file_id":4898760,"author_public_file":"README.md",
       "read_original_csv_values":False,"read_specimen_data":False}
    result,data=get_bytes(DRYAD_URL,12000)
    o["publisher_readme_get_status"]=result["status"]
    o["http"]=result.get("http")
    if data is None:
        o["status"]="DRYAD_README_FILE_ACCESS_HOLD"
    elif len(data)!=README_SIZE or hashlib.sha256(data).hexdigest()!=README_SHA:
        o["status"]="DRYAD_SOURCE_README_FINGERPRINT_STOP"
    else:
        # Original README text explicitly NOT logged or analyzed in this gate
        o["status"]="DRYAD_README_BYTES_AUTHENTICATED_NO_CSV"
        o["README_size"]=len(data)
        o["README_sha256"]=README_SHA
    return o

def source_zenodo():
    o={"original_doi":"10.5281/zenodo.23021809","original_record":23021809,
       "expected_exact_file":BOOK_NAME,"original_beetle_cells_read":0,
       "original_stump_environment_values_read":0}
    s,record=get_bytes(ZENODO_API,250000)
    o["record_api_status"]=s["status"]
    if record is None:
        o["status"]="ZENODO_RECORD_SOURCE_STOP"
        o["http"]=s.get("http")
        return o
    try: j=json.loads(record)
    except ValueError:
        o["status"]="ZENODO_RECORD_JSON_STOP"
        return o
    md=j.get("metadata",{})
    if (j.get("id")!=23021809 or j.get("doi")!=o["original_doi"] or
            md.get("access_right") not in (None,"open") and md.get("access_status")!="open"):
        o["status"]="ZENODO_SOURCE_ID_OR_ACCESS_STOP"
        return o
    arr=j.get("files") or []
    if isinstance(arr,dict):arr=list((arr.get("entries") or {}).values())
    if len(arr)!=1 or not isinstance(arr[0],dict):
        o["status"]="ZENODO_SOURCE_MANIFEST_STOP"
        return o
    f=arr[0]
    if (f.get("key")!=BOOK_NAME or f.get("size")!=BOOK_SIZE or
         f.get("checksum")!="md5:"+BOOK_MD5):
        o["status"]="ZENODO_ORIGINAL_BOOK_FINGERPRINT_IN_INDEX_STOP"
        return o
    href=(f.get("links") or {}).get("self") or (f.get("links") or {}).get("download")
    if not href:
        o["status"]="ZENODO_ORIGINAL_FILE_OFFICIAL_LINK_MISSING"
        return o
    p=urllib.parse.urlparse(href)
    # Link is copied byte-for-byte from the canonical Zenodo record's exact
    # checksum-pinned original file entry. Never construct or guess a URL.
    o["publisher_authorized_link_host"]=p.hostname
    o["publisher_authorized_link_path_without_query"]=p.path[:220]
    allowed_path=(
        p.path.startswith("/api/files/") or
        p.path.startswith("/api/records/23021809/files/") or
        p.path.startswith("/records/23021809/files/")
    )
    if p.scheme!="https" or p.hostname!="zenodo.org" or not allowed_path:
        o["status"]="ZENODO_ORIGINAL_FILE_URL_HOST_OR_PATH_STOP"
        return o
    status,data=get_bytes(href,150000)
    o["file_original_public_get_status"]=status["status"]
    o["http"]=status.get("http")
    if data is None:
        o["status"]="ZENODO_ORIGINAL_FILE_ACCESS_HOLD"
        return o
    if len(data)!=BOOK_SIZE or hashlib.md5(data).hexdigest()!=BOOK_MD5:
        o["status"]="ZENODO_ORIGINAL_XLSX_MD5_OR_SIZE_STOP"
        return o
    o["original_file_sha256"]=hashlib.sha256(data).hexdigest()
    o["original_file_size"]=len(data)
    try:
        o["XLSX_WORKBOOK_XML_METADATA_ONLY"]=workbook_xml_metadata(data)
        o["status"]="ZENODO_XLSX_WORKBOOK_SHEET_TITLES_READY_NO_BIOLOGY"
    except (zipfile.BadZipFile,ET.ParseError,ValueError) as e:
        o["status"]="ZENODO_XLSX_WORKBOOK_SCHEMA_STOP"
        o["error_type"]=type(e).__name__
    return o

def synthetic():
    wb=io.BytesIO()
    with zipfile.ZipFile(wb,"w") as z:
        z.writestr("[Content_Types].xml","<Types/>")
        z.writestr("xl/workbook.xml",
          '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="Original_Method_Source" sheetId="1"/></sheets></workbook>')
    d=workbook_xml_metadata(wb.getvalue())
    assert d["sheet_titles_from_workbook_xml_only"]==["Original_Method_Source"]
    assert not d["read_worksheet_xml_cell_values"]
    print("SWEDEN2026_ORIGINAL_FILE_SOURCEONLY_SYNTHETIC_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",default="sweden2026_original_method_gate/receipt.json")
    a=ap.parse_args()
    synthetic()
    if a.test:return
    x={"schema":"structural.sweden2026_two_publisher_original_method_sourceonly.v1",
       "new_original_biological_effects":0,
       "original_taxon_abundance_or_stump_cells_read":0,
       "prior_2025_Dryad_401_unretried":True,
       "Frostgard_2026_Dryad":source_dryad(),
       "Ramberg_2026_Zenodo":source_zenodo(),
       "eBird_used":False,"TinyFish_used":False}
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("FROSTGARD_README_GATE",x["Frostgard_2026_Dryad"]["status"])
    print("RAMBERG_XLSX_DIRECTORY_GATE",x["Ramberg_2026_Zenodo"]["status"])
    print("BIOLOGICAL_OR_WORKSHEET_CELL_VALUES_READ",x["original_taxon_abundance_or_stump_cells_read"])
if __name__=="__main__":main()
