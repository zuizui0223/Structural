#!/usr/bin/env python3
"""2026 Poland original bee... no, BEETLE/forest stand source-only Excel grain audit.

Parses publisher original workbook package structure, sheet dimensions,
and generic site/plot/time/wood field headers only. Does NOT score original
beetle species/abundance, tree resources, or taxon–environment associations.
Never prints site IDs, species names, row data, or source sample values.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
import math
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

MANIFEST={
 "beetle":("21486790","abundance_data_dominant.xlsx","ecc1836c111bf08cc1eba3f23aaaf6e4",17503),
 "forest":("21535672","Forest_stand_characteristics.xlsx","283db0672933621c7e4d0e0b8ac03160",15002),
 "readme":("21486790","README.txt","2d34fa07c7137e15fc99bd826843d495",1656),
}
MAIN="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
OFFICEREL="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKGREL="http://schemas.openxmlformats.org/package/2006/relationships"
DATE_WORDS={"date","year","month","season","period","samplingyear"}
PLOT_WORDS={"site","siteid","plot","plotid","stand","standid","location","locationid","forest","forestid","locality","localityid"}
METHOD_WORDS={"method","trap","trapid","trapnumber","sample","sampleid","effort","duration","area","treatment","replicate","sampling"}
HOST_WORDS={"treespecies","tree","hosttree","treefamily","woodspecies","deadwood","dbh","diameter","volume","basalarea","canopy","decay","deadwoodvolume","microhabitat","habitat"}
COMMON_FIELDS=PLOT_WORDS|DATE_WORDS|METHOD_WORDS|HOST_WORDS|{"id","code","no","number","species","speciesid","taxon","taxonid","latitude","longitude","x","y","northing","easting"}
EXPECTED_SHEETS={
    "beetle":["21_species_abundance","276 species"],
    "forest":["Stand characteristics"],
}
START_ROWS=3

class ScientificStop(Exception):pass


def normalize_label(x:str):
    return re.sub(r"[^a-z0-9]","",str(x).lower().strip())


def safe_candidate_label(text:str):
    label=str(text).strip()
    normalized=normalize_label(label)
    # Exact known data-frame field names and generic, non-biological labels
    # only; never output species names from first-row table labels.
    if len(label)>45 or normalized not in COMMON_FIELDS:
        return None
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 _./()-]{0,44}",label):
        return None
    if normalized in PLOT_WORDS:return ("site_plot_grain",label)
    if normalized in DATE_WORDS:return ("time",label)
    if normalized in METHOD_WORDS:return ("method_effort",label)
    if normalized in HOST_WORDS:return ("tree_resource",label)
    return ("other_generic",label)


def fetch_original(rec,filename,digest,nbytes):
    url=f"https://zenodo.org/records/{rec}/files/{filename}?download=1"
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url,headers={"User-Agent":"Structural-original-Zenodo-source-QA/1.0"}),
            timeout=38
        ) as r:
            data=r.read(250000)
            status=r.status
    except urllib.error.HTTPError as e:
        raise ScientificStop(f"SOURCE_ACCESS_STOP_HTTP_{e.code}") from e
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        raise ScientificStop("SOURCE_ACCESS_STOP_TRANSPORT_"+type(e).__name__) from e
    if status!=200 or len(data)!=nbytes:
        raise ScientificStop("SOURCE_STOP_PUBLISHER_SOURCE_SIZE_OR_STATUS_CHANGED")
    if hashlib.md5(data).hexdigest()!=digest:
        raise ScientificStop("SOURCE_STOP_PUBLISHER_MD5_DRIFT")
    return data


def workbook_sheet_paths(z:zipfile.ZipFile):
    if "xl/workbook.xml" not in z.namelist() or "xl/_rels/workbook.xml.rels" not in z.namelist():
        raise ScientificStop("SOURCE_STOP_OFFICIAL_XLSX_WORKBOOK_RELATIONSHIPS")
    wb=ET.fromstring(z.read("xl/workbook.xml"))
    rel=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    targets={}
    for r in rel.findall(f"{{{PKGREL}}}Relationship"):
        rid=r.attrib.get("Id");target=r.attrib.get("Target","")
        if not rid or "://" in target or ".." in target:
            continue
        t=target.lstrip("/")
        path=t if t.startswith("xl/") else "xl/"+t
        if path in z.namelist():
            targets[rid]=path
    rows=[]
    for node in wb.findall(f".//{{{MAIN}}}sheet"):
        rid=node.attrib.get(f"{{{OFFICEREL}}}id")
        name=node.attrib.get("name","")
        if rid not in targets:
            raise ScientificStop("SOURCE_STOP_AUTHOR_SHEET_RELATION_UNRESOLVED")
        rows.append((name,targets[rid]))
    if not rows:raise ScientificStop("SOURCE_STOP_AUTHOR_WORKBOOK_WITHOUT_SHEETS")
    return rows


def shared_strings(z:zipfile.ZipFile):
    # Workbook source strings remain runner-private and NEVER re-exported.
    p="xl/sharedStrings.xml"
    if p not in z.namelist():
        return []
    root=ET.fromstring(z.read(p))
    values=[]
    for node in root.findall(f"{{{MAIN}}}si"):
        values.append("".join(t.text or "" for t in node.findall(f".//{{{MAIN}}}t")))
    return values


def cell_value_first_header_only(cell,table:list[str]):
    # Only first START_ROWS of each source worksheet inspected for generic
    # column-field words; no actual biological data row values read.
    t=cell.attrib.get("t","")
    if t=="s":
        v=cell.find(f"{{{MAIN}}}v")
        if v is not None and v.text and v.text.isdigit():
            idx=int(v.text)
            if 0<=idx<len(table):
                return table[idx]
    if t=="inlineStr":
        return "".join(x.text or "" for x in cell.findall(f".//{{{MAIN}}}t"))
    if t=="str":
        v=cell.find(f"{{{MAIN}}}v")
        return v.text or "" if v is not None else ""
    # no numeric source values copied
    return ""


def original_sheet_metadata(z:zipfile.ZipFile,path:str,strings:list[str]):
    root=ET.fromstring(z.read(path))
    ref=(root.find(f"{{{MAIN}}}dimension") or ET.Element("empty")).attrib.get("ref","")
    sheet=root.find(f"{{{MAIN}}}sheetData")
    if sheet is None:raise ScientificStop("SOURCE_STOP_WORKSHEET_WITHOUT_SHEETDATA")
    row_n=0
    col_max=0
    header_matches=[]
    worksheet_rows=[]
    for row in sheet.findall(f"{{{MAIN}}}row"):
        row_n+=1
        cells=row.findall(f"{{{MAIN}}}c")
        if cells:
            col_max=max(col_max,len(cells))
        if row_n<=START_ROWS:
            found=[]
            for c in cells:
                raw=cell_value_first_header_only(c,strings)
                hit=safe_candidate_label(raw)
                if hit:
                    field_category, field_name=hit
                    found.append({"generic_field_category":field_category,
                                  "safe_generic_field_name":field_name,
                                  "source_header_column":re.sub(r"[0-9]","",c.attrib.get("r",""))[:3]})
            worksheet_rows.append({
               "top_header_row_position":row_n,
               "generic_source_method_field_matches":found,
               "generic_field_match_count":len(found),
               "nonempty_original_cells_in_row":len(cells),
            })
            header_matches.extend(found)
    return {
        "source_original_excel_dimension_ref":ref[:25],
        "source_original_worksheet_rows_including_headers":row_n,
        "source_original_max_nonempty_cells_per_row":col_max,
        "first_three_header_rows_GENERIC_FIELD_DIAGNOSTICS":worksheet_rows,
        "generic_site_plot_header_present":any(x["generic_field_category"]=="site_plot_grain" for x in header_matches),
        "original_source_taxa_and_abundance_row_values_UNREAD":True,
        "original_source_species_labels_not_printed":True,
        "source_original_stand_numeric_resource_values_UNREAD":True,
    }


def original_workbook(binary:bytes,name:str):
    if not binary.startswith(b"PK"):
        raise ScientificStop("SOURCE_STOP_ORIGINAL_EXCEL_PACKAGE_BYTES")
    with zipfile.ZipFile(io.BytesIO(binary),"r") as z:
        if any(i.file_size>20_000_000 for i in z.infolist()):
            raise ScientificStop("SOURCE_STOP_OVERSIZE_EXCEL_XML")
        pairs=workbook_sheet_paths(z)
        actual=[v[0] for v in pairs]
        if actual!=EXPECTED_SHEETS[name]:
            raise ScientificStop("SOURCE_STOP_ORIGINAL_WORKBOOK_SHEET_SET_DRIFT")
        table=shared_strings(z)
        return {
          "original_worksheet_count":len(pairs),
          "source_original_sheets":[
            {"source_sheet_name":sheet,
             **original_sheet_metadata(z,location,table)}
            for sheet,location in pairs
          ],
          "source_published_xlsx_md5_verified":True,
          "source_site_IDs_not_reexported":True,
        }


def known_truth():
    assert safe_candidate_label("siteID")==("site_plot_grain","siteID")
    assert safe_candidate_label("Tree species")==("tree_resource","Tree species")
    assert safe_candidate_label("Betula pendula") is None
    assert safe_candidate_label("Acylophorus wagenschieberi") is None
    assert safe_candidate_label("number") is not None
    assert safe_candidate_label("111.22") is None
    assert safe_candidate_label("sample year") is not None if normalize_label("sample year") in COMMON_FIELDS else True
    # one sheet with literal header field and numerical taxa data excluded
    ss='<sst xmlns="'+MAIN+'"><si><t>Site</t></si><si><t>Abies alba</t></si></sst>'
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,"w") as w:
        w.writestr("xl/workbook.xml",
          '<workbook xmlns="'+MAIN+'" xmlns:r="'+OFFICEREL+'"><sheets><sheet name="21_species_abundance" sheetId="1" r:id="rId1"/></sheets></workbook>')
        w.writestr("xl/_rels/workbook.xml.rels",
          '<Relationships xmlns="'+PKGREL+'"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        w.writestr("xl/sharedStrings.xml",ss)
        w.writestr("xl/worksheets/sheet1.xml",
          '<worksheet xmlns="'+MAIN+'"><dimension ref="A1:B2"/><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="s"><v>1</v></c></row><row r="2"><c r="A2"><v>100</v></c><c r="B2"><v>42</v></c></row></sheetData></worksheet>')
    with zipfile.ZipFile(io.BytesIO(buf.getvalue()),"r") as z:
        p=workbook_sheet_paths(z)
        assert p==[("21_species_abundance","xl/worksheets/sheet1.xml")]
        a=original_sheet_metadata(z,p[0][1],shared_strings(z))
        assert a["source_original_worksheet_rows_including_headers"]==2
        hits=a["first_three_header_rows_GENERIC_FIELD_DIAGNOSTICS"][0]["generic_source_method_field_matches"]
        assert len(hits)==1 and hits[0]["safe_generic_field_name"]=="Site"
    print("SYNTHETIC_SOURCE_EXCEL_XML_HEADER_ONLY_TAXON_REDACTION_PASS")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",type=Path)
    a=ap.parse_args()
    known_truth()
    if a.test:return
    if not a.out:ap.error("--out needed")
    result={
      "schema":"structural.Poland2026_original_beetle_forest_worksheet_source_grain_gate.v1",
      "original_2026_Poland_Zenodo_beetles":"10.5281/zenodo.21486790",
      "original_2026_Poland_Zenodo_forest_stands":"10.5281/zenodo.21535672",
      "original_source_file_manifests_md5_verified":False,
      "original_beetle_taxa_abundances_UNSCORED":True,
      "original_forest_measurement_values_UNSCORED":True,
      "no_original_beetle_forest_site_rows_JOINED":True,
      "same_one_lowland_forest_original_study_NOT_independent_countries":True,
      "original_Finland_DEADWOOD_PREDICTS_NEON_BALA_GEB_results_unchanged":True,
      "eBird_used":False,
    }
    try:
        data={}
        for key,(rec,filename,digest,size) in MANIFEST.items():
            data[key]=fetch_original(rec,filename,digest,size)
        result["original_source_file_manifests_md5_verified"]=True
        result["original_sheet_grain"]= {
          k:original_workbook(data[k],k) for k in ("beetle","forest")
        }
        readme=data["readme"].decode("utf-8-sig","replace")
        result["readme_source_only_metadata"]={
            "original_author_README_lines":len(readme.splitlines()),
            "original_author_readme_MD5_verified":True,
            "raw_author_site_IDs_and_readme_source_text_NOT_REEXPORTED":True,
        }
        result["status"]="SOURCE_GRANULARITY_NOT_YET_ESTABLISHED_NO_BIOLOGICAL_SCORE"
    except ScientificStop as exc:
        result["status"]=str(exc)
        result["scientific_SOURCE_STOP_not_ecological_null"]=True
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Poland2026_original_author_excel_sheet_grain_sourceonly.json").write_text(
      json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(result,indent=2,ensure_ascii=False))


if __name__=="__main__":main()
