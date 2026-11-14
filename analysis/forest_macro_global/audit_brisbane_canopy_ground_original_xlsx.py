#!/usr/bin/env python3
"""Source-original Brisbane canopy/ground beetle OOXML workbook schema audit.

Source Stone, Catterall & Stork, DOI 10.5061/dryad.14hp7,
Zenodo-record mirror 4998317 CC0, original publisher checksum MD5
153743ec4d968f20349e7caddd49dac1. 80 flight-intercept-trap points
and original beetle abundance, forest edge, canopy cover and height.

This only reads Office Open XML ZIP source structure with Python stdlib,
not a spreadsheet editor. No raw beetle species values/site IDs, no taxon
or spatial predictors scored. Ecological ground↔canopy effects not re-fit.
"""
from __future__ import annotations
import argparse,hashlib,json,os,posixpath,re,zipfile,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

SOURCE_MD5="153743ec4d968f20349e7caddd49dac1"
SOURCE_DOI="10.5061/dryad.14hp7"
OOXML="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKGREL="http://schemas.openxmlformats.org/package/2006/relationships"


def colindex(a):
    z=0
    for c in a:
        if not c.isalpha():break
        z=z*26+ord(c.upper())-ord("A")+1
    return z-1

def content_types(z):
    names=z.namelist()
    if "xl/workbook.xml" not in names:
        raise ValueError("OOXML_original_workbook_missing")
    tree=ET.fromstring(z.read("xl/workbook.xml"))
    sheets=[]
    for node in tree.findall(f".//{{{OOXML}}}sheet"):
        sheets.append((node.get("name"),node.get(f"{{{REL}}}id")))
    relationships={}
    rel_path="xl/_rels/workbook.xml.rels"
    if rel_path in names:
        for item in ET.fromstring(z.read(rel_path)):
            if item.tag.rsplit("}",1)[-1]=="Relationship":
                target=item.get("Target","")
                target=target[1:] if target.startswith("/") else posixpath.normpath(posixpath.join("xl",target))
                relationships[item.get("Id")]=target
    result=[]
    for i,(name,rid) in enumerate(sheets):
        path=relationships.get(rid,f"xl/worksheets/sheet{i+1}.xml")
        if path not in names:raise ValueError("OOXML_original_sheet_file_missing:"+str(name))
        result.append((name,path))
    if not result:raise ValueError("empty_OOXML_workbook")
    return result

def shared_text(z):
    name="xl/sharedStrings.xml"
    if name not in z.namelist():return []
    strings=[]
    for si in ET.fromstring(z.read(name)).findall(f"{{{OOXML}}}si"):
        strings.append("".join(t.text or "" for t in si.findall(f".//{{{OOXML}}}t")))
    return strings

def celltext(c,strings):
    t=c.get("t")
    if t=="inlineStr":
        return "".join(v.text or "" for v in c.findall(f".//{{{OOXML}}}t"))
    v=c.find(f"{{{OOXML}}}v")
    if v is None:return ""
    data=(v.text or "").strip()
    if t=="s":
        try:return strings[int(data)]
        except (IndexError,ValueError):
            raise ValueError("OOXML_shared_string_invalid")
    return data

def parse_schema(source_path):
    fp=Path(source_path)
    if not fp.is_file():raise ValueError("source_original_Brisbane_excel_file_not_found")
    payload=fp.read_bytes()
    if hashlib.md5(payload).hexdigest()!=SOURCE_MD5:
        raise ValueError("source_Brisbane_Zenodo_MD5_VERSION_MISMATCH")
    if len(payload)>2_000_000:raise ValueError("source_excel_size_unexpected")
    with zipfile.ZipFile(fp) as z:
        files=content_types(z)
        strings=shared_text(z)
        sheets=[]
        for name,path in files:
            if z.getinfo(path).file_size>10_000_000:
                raise ValueError("source_uncompressed_OOXML_sheet_too_large")
            root=ET.fromstring(z.read(path))
            rows=root.findall(f".//{{{OOXML}}}sheetData/{{{OOXML}}}row")
            max_cols=0
            sample=[]
            numeric_nonempty=0
            for i,row in enumerate(rows):
                colcells=[]
                for c in row.findall(f"{{{OOXML}}}c"):
                    letter=re.match(r"[A-Z]+",c.get("r",""))
                    if letter is None:continue
                    idx=colindex(letter.group())
                    text=celltext(c,strings)
                    if text:
                        colcells.append((idx,text))
                        if c.get("t") in (None,"n"):numeric_nonempty+=1
                if colcells:max_cols=max(max_cols,max(j for j,x in colcells)+1)
                if i<5:sample.append(colcells)
            # Only early HEADER TERMS (not raw species or geographic rows)
            # are used to suggest which sheets contain field metadata.
            all_header=[v for ix,v in sample[0]] if sample else []
            identifiers=[
                v for v in all_header
                if re.search(r"(?i)\b(site|strat|layer|height|edge|canopy|cover|trap|habitat|tree|species|abund|rich|date|sample|distance|treatment|forest)\b",v)
            ]
            sheets.append({
                "source_sheet_name":name,
                "OOXML_data_row_count":len(rows),
                "OOXML_max_used_columns":max_cols,
                "source_header_cell_count":len(all_header),
                "source_first_row_field_headers_only_when_15_or_fewer":all_header if len(all_header)<=15 else None,
                "source_study_design_relevant_header_tokens_only":identifiers[:22],
                "first_5_row_nonempty_cell_counts":[len(q) for q in sample],
                "source_numeric_cell_count_in_sheet":numeric_nonempty
            })
    return {
      "schema":"structural.brisbane_forest_beetle_original_xlsx_sheet_grain_audit.v1",
      "source_original_md5_verified":SOURCE_MD5,
      "source_DOI":SOURCE_DOI,
      "source_record":"https://zenodo.org/records/4998317",
      "source_article_DOI":"10.1371/journal.pone.0193369",
      "source_paper_reports_flight_intercept_trap_locations":80,
      "source_paper_reports_species_under_2_trap_locations_excluded":True,
      "source_sheets":sheets,
      "original_independent_forest_study_region_count":1,
      "forest_plot_trap_height_and_raw_species_classification_verified":False,
      "source_incidence_abundance_or_env_join_NOT_SCORED":True,
      "original_species_site_observation_values_NOT_EXPORTED":True,
      "source_same_trap_type_canopy_and_ground_reported_in_publication":True,
      "new_canopy_beetle_effect_scored":False,
    }

def run(source,out):
    r=parse_schema(source)
    target=Path(out);target.mkdir(parents=True,exist_ok=True)
    (target/"brisbane_stone_beetle_original_workbook_schema.json").write_text(
        json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))
    return r

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--source",required=True);p.add_argument("--out",required=True)
    args=p.parse_args();run(args.source,args.out)
