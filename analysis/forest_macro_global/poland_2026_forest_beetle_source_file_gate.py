#!/usr/bin/env python3
"""2026 independent Poland forest beetle + stand original FILE SOURCE gate.

Downloads only two tiny published xlsx and one original README with exact
MD5s, checks zip workbook structure and sheet names (NO worksheet cells),
and produces anonymous metadata only. No biological original values read.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

MANIFEST={
    "beetle":{
        "record":21486790,
        "filename":"abundance_data_dominant.xlsx",
        "md5":"ecc1836c111bf08cc1eba3f23aaaf6e4",
        "size":17503,
    },
    "readme":{
        "record":21486790,
        "filename":"README.txt",
        "md5":"2d34fa07c7137e15fc99bd826843d495",
        "size":1656,
    },
    "forest_stands":{
        "record":21535672,
        "filename":"Forest_stand_characteristics.xlsx",
        "md5":"283db0672933621c7e4d0e0b8ac03160",
        "size":15002,
    },
}
UA={"User-Agent":"Structural-official-Zenodo-original-study-file-integrity/1.0"}

class SourceStop(RuntimeError):pass


def xlsx_package_metadata(binary:bytes):
    if not binary.startswith(b"PK"):
        raise SourceStop("SOURCE_STOP_PUBLISHED_XLSX_NOT_ZIP_OPENXML")
    with zipfile.ZipFile(io.BytesIO(binary),"r") as archive:
        names=archive.namelist()
        if "xl/workbook.xml" not in names or "[Content_Types].xml" not in names:
            raise SourceStop("SOURCE_STOP_ORIGINAL_EXCEL_PACKAGE_MAIN_XML_MISSING")
        xml=archive.read("xl/workbook.xml")
        root=ET.fromstring(xml)
        children=root.findall(".//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet")
        sheets=[node.attrib.get("name","") for node in children]
        if not sheets or any(not name for name in sheets):
            raise SourceStop("SOURCE_STOP_ORIGINAL_EXCEL_SHEET_DIRECTORY_MISSING")
        # No `xl/worksheets/sheet*.xml`, sharedStrings, embedded tables, source
        # site IDs, beetle names or any numerical forest data is inspected.
        return {"original_source_sheets_metadata_only":sheets,
                "sheet_count":len(sheets),
                "workbook_openxml_package_valid":True,
                "worksheet_cells_original_values_UNREAD":True,
                "original_total_package_entries":len(names)}


def download_one(info:dict):
    rec=int(info["record"])
    fname=info["filename"]
    safe=fname  # all three prespecified archive filenames are ASCII
    url=f"https://zenodo.org/records/{rec}/files/{safe}?download=1"
    req=urllib.request.Request(url,headers=UA)
    try:
        with urllib.request.urlopen(req,timeout=35) as conn:
            data=conn.read(250000)
            if conn.status!=200:
                return {"status":"SOURCE_STOP_ORIGINAL_ZENODO_NON200","http_status":conn.status}
    except urllib.error.HTTPError as exc:
        return {"status":"SOURCE_ACCESS_HTTP_STOP","http_status":exc.code}
    except Exception as exc:
        return {"status":"SOURCE_ACCESS_TRANSPORT_STOP","exception_class":type(exc).__name__}
    if len(data)!=int(info["size"]):
        return {"status":"SOURCE_STOP_ORIGINAL_FILE_SIZE_MISMATCH",
                "bytes_returned":len(data),"bytes_expected":info["size"]}
    md5=hashlib.md5(data).hexdigest()
    if md5!=info["md5"]:
        return {"status":"SOURCE_STOP_ORIGINAL_FILE_MD5_DRIFT"}
    result={"status":"PUBLISHED_ORIGINAL_FILE_DOWNLOADED_AND_MD5_VERIFIED",
            "bytes":len(data),"published_original_md5":md5,
            "no_original_source_row_or_abundance_values_reexported":True}
    if fname.endswith(".xlsx"):
        result.update(xlsx_package_metadata(data))
    else:
        # Public author README only: count method/field vocabulary mentions,
        # do not export source file text or inferred biological study results.
        s=data.decode("utf-8-sig","replace").lower()
        result.update({
           "readme_text_was_publisher_original":True,
           "readme_number_of_lines":len(s.splitlines()),
           "method_words_site_plot_trap_or_sample_occurrences":sum(
               len(re.findall(term,s)) for term in (r"site",r"plot",r"trap",r"sample")),
           "README_content_not_redistributed":True,
        })
    return result


def known_truth():
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,"w") as z:
        z.writestr("[Content_Types].xml","<Types/>")
        z.writestr("xl/workbook.xml",
          '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheets><sheet name="SOURCE_META" sheetId="1"/></sheets></workbook>')
    x=xlsx_package_metadata(stream.getvalue())
    assert x["original_source_sheets_metadata_only"]==["SOURCE_META"]
    assert x["worksheet_cells_original_values_UNREAD"]
    print("SYNTHETIC_ZENODO_CITABLE_ORIGINAL_XLSX_PACKAGE_METADATA_ONLY_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    known_truth()
    if args.test:return
    if not args.out:ap.error("--out required")
    result={
      "schema":"structural.Poland2026_saproxylic_rove_beetles_and_forest_inventory_sourceonly.v1",
      "source_author_2026_article":"10.1111/afe.70091",
      "original_beetle_Zenodo":"10.5281/zenodo.21486790",
      "original_forest_Zenodo":"10.5281/zenodo.21535672",
      "original_public_file_receipts":{},
      "original_beetle_species_abundances_UNREAD":True,
      "original_forest_tree_or_stand_environmental_values_UNREAD":True,
      "no_original_site_join_or_ecological_effect_done":True,
      "one_source_forest_not_independent_country_network_replication":True,
      "Finnish142site_PREDICTS_NEON_BALA_GEB_and_threecountry_endpoints_unchanged":True,
      "eBird_used":False,
    }
    for key,info in MANIFEST.items():
        result["original_public_file_receipts"][key]=download_one(info)
    result["status"]=(
        "SOURCE_ONLY_THREE_PINNED_PUBLISHER_FILES_READY_FOR_AUTHOR_GRAIN_CROSSWALK"
        if all(v["status"]=="PUBLISHED_ORIGINAL_FILE_DOWNLOADED_AND_MD5_VERIFIED"
               for v in result["original_public_file_receipts"].values())
        else "SOURCE_STOP_ONE_OR_MORE_ORIGINAL_PUBLISHED_FILES_UNAVAILABLE"
    )
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Poland2026_original_beetle_forest_source_file_metadata_only.json").write_text(
        json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":main()
