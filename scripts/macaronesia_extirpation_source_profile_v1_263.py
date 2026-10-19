#!/usr/bin/env python3
"""CSIC Macaronesian vascular flora: original publisher workbook schema ONLY.

No species × island extirpation values, traits, current source status or
population outcomes are decoded. Frozen source bytes, worksheet names,
nominal dimensions and first-row header labels are the only workbook output.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import posixpath
import re
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

M="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR="http://schemas.openxmlformats.org/package/2006/relationships"
W="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
SCHEMA="structural.macaronesia_source_header_inventory.v1_263"
MAX_WORKBOOK=5_000_000
MAX_DOCX=1_000_000


def _first_row_cells(xlsx,member):
    """Iterparse only row 1; stop BEFORE reading any taxon/island outcome rows."""
    cells=[];dimension=None
    with xlsx.open(member) as stream:
        try:
            for ev,elm in ET.iterparse(stream,events=("start","end")):
                if ev=="start" and elm.tag==f"{{{M}}}dimension":
                    dimension=elm.attrib.get("ref")
                if ev=="end" and elm.tag==f"{{{M}}}row":
                    row_number=elm.attrib.get("r")
                    if row_number=="1":
                        for c in elm.findall(f"{{{M}}}c"):
                            addr=c.attrib.get("r","")
                            if not re.fullmatch(r"[A-Z]{1,3}1",addr):
                                continue
                            tp=c.attrib.get("t","")
                            if tp=="s":
                                v=c.find(f"{{{M}}}v")
                                if v is not None and v.text and v.text.isdigit():
                                    cells.append(("shared",int(v.text)))
                            elif tp=="inlineStr":
                                inline=c.find(f"{{{M}}}is")
                                if inline is not None:
                                    cells.append(("inline","".join(
                                        x.text or "" for x in inline.iter(f"{{{M}}}t"))))
                            elif tp=="str":
                                v=c.find(f"{{{M}}}v")
                                cells.append(("inline",v.text or "" if v is not None else ""))
                    break  # do not inspect row >=2, including source published response records
                # Do not clear row children before their containing row is processed.
        except ET.ParseError as exc:
            raise ValueError("Malformed official Excel worksheet XML") from exc
    return dimension,cells


def _shared_header_strings(xlsx,indices):
    if not indices:
        return {}
    if "xl/sharedStrings.xml" not in xlsx.namelist():
        raise ValueError("Shared first-row header index without author shared strings")
    requested=set(indices)
    if any(i<0 or i>1_000_000 for i in requested):
        raise ValueError("Implausible shared header cell index")
    result={};count=0
    with xlsx.open("xl/sharedStrings.xml") as stream:
        try:
            for ev,elem in ET.iterparse(stream,events=("end",)):
                if elem.tag==f"{{{M}}}si":
                    if count in requested:
                        result[count]="".join(x.text or "" for x in elem.iter(f"{{{M}}}t"))[:160]
                    count+=1;elem.clear()
                    if len(result)==len(requested):
                        break  # never decode later biological strings
        except ET.ParseError as exc:
            raise ValueError("Malformed author Excel shared-string XML") from exc
    if len(result)!=len(requested):
        raise ValueError("First-row shared header references missing")
    return result


def inventory_workbook(raw:bytes):
    """Inventory workbook names, nominal dimensions and FIRST ROW headers ONLY."""
    if not raw.startswith(b"PK\x03\x04"):
        raise ValueError("Publisher source did not return a valid zipped OOXML workbook")
    if len(raw)>MAX_WORKBOOK:
        raise ValueError("Excel source exceeds prespecified 5 MB transfer limit")
    try:
        z=zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as exc:
        raise ValueError("Unusable truncated/invalid original XLSX ZIP") from exc
    with z:
        names=z.namelist()
        if ("xl/workbook.xml" not in names or
            "xl/_rels/workbook.xml.rels" not in names):
            raise ValueError("Invalid original workbook directory structure")
        if sum(x.file_size for x in z.infolist())>80_000_000:
            raise ValueError("Workbook uncompressed size exceeds original-source guard")
        try:
            root=ET.fromstring(z.read("xl/workbook.xml"))
            rels=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        except ET.ParseError as exc:
            raise ValueError("Malformed workbook or relationship metadata") from exc
        pathmap={}
        for rr in rels.findall(f"{{{PR}}}Relationship"):
            target=rr.attrib.get("Target","")
            if not target or ".." in target.split("/"):
                raise ValueError("Unsafe worksheet relationship path")
            pathmap[rr.attrib.get("Id","")]=(
                target.lstrip("/") if target.startswith("/")
                else posixpath.normpath(posixpath.join("xl",target)))
        workbook_sheets=root.find(f"{{{M}}}sheets")
        if workbook_sheets is None:
            raise ValueError("Original workbook has no sheet listing")
        staging=[]
        for sheet in workbook_sheets.findall(f"{{{M}}}sheet"):
            sheetname=sheet.attrib.get("name","")
            rid=sheet.attrib.get(f"{{{R}}}id")
            target=pathmap.get(rid)
            if not target or target not in names:
                raise ValueError("Workbook missing original target worksheet for "+sheetname)
            if not sheetname or len(sheetname)>120:
                raise ValueError("Invalid source sheet name")
            dimension,cells=_first_row_cells(z,target)
            row_end=None
            if dimension:
                match=re.search(r"\$?[A-Z]{1,3}\$?(\d+)$",dimension)
                row_end=int(match.group(1)) if match else None
            staging.append({"sheet_name":sheetname,"nominal_dimension":dimension,
                            "nominal_max_row":row_end,"first_row_cells":cells})
        if len(staging)<1 or len(staging)>80:
            raise ValueError("No Excel worksheets or implausibly many source sheets")
        indices=[val for sh in staging for tp,val in sh["first_row_cells"] if tp=="shared"]
        strings=_shared_header_strings(z,indices)
        sheets=[]
        for item in staging:
            headers=[(strings[v] if tp=="shared" else str(v)[:160])
                     for tp,v in item.pop("first_row_cells")]
            sheets.append({**item,"first_row_headers":headers[:80],
                           "first_row_is_header_not_author_verified":True})
        return {"sheet_count":len(sheets),"sheets":sheets,
                "species_or_island_extirpation_observation_rows_read":0,
                "species_level_response_predictions_run":0}


def read_docx_methods_flags(raw):
    if not raw.startswith(b"PK\x03\x04") or len(raw)>MAX_DOCX:
        raise ValueError("CSIC README.docx not original OOXML signature/size")
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            if "word/document.xml" not in z.namelist():
                raise ValueError("Original methods README is not a DOCX")
            root=ET.fromstring(z.read("word/document.xml"))
            paragraph_count=len(root.findall(f".//{{{W}}}p"))
            text=" ".join((el.text or "") for el in root.iter(f"{{{W}}}t"))
    except (zipfile.BadZipFile,ET.ParseError) as exc:
        raise ValueError("Invalid original CSIC methods DOCX") from exc
    lower=text.casefold()
    return {
       "README_paragraph_count":paragraph_count,
       "mentions_extinction_or_extirpation":"extinct" in lower or "extirpat" in lower,
       "mentions_azores":"azores" in lower,
       "mentions_canary":"canar" in lower,
       "source_text_emitted":False
    }


def download_original(url,expected_bytes,maxbytes):
    request=urllib.request.Request(url,headers={
        "User-Agent":"Structural-ecological-database-source-validation/1.0",
        "Accept":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream,*/*"})
    with urllib.request.urlopen(request,timeout=75) as src:
        data=src.read(maxbytes+1)
    if len(data)>maxbytes:
        raise ValueError("Original publisher file too large; no downloaded-data substitution")
    if len(data)!=expected_bytes:
        raise ValueError(f"Official source length mismatch {len(data)} expected {expected_bytes}")
    return data


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    cfg=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (cfg.get("schema")!="structural.macaronesia_local_extirpation_source_gate.v1_263"
        or cfg.get("status")!="FROZEN_SOURCE_IDENTITY_AND_HEADER_ONLY_BEFORE_EXTIRPATION_OUTCOMES"):
        raise ValueError("Data source protocol was modified after biological endpoint was named")
    src=cfg["source"]
    report={
        "schema":SCHEMA,"status":"SOURCE_TRANSPORT_STOP_NO_BIOLOGY",
        "source_handle":src["handle"],"original_peer_reviewed_paper":src["original_peer_reviewed_paper"],
        "GEB_scientific_HOLD":True,"eBird_off":True,
        "previous_mammal_holdout_opened":False,"new_confirmatory_systems":0,
        "species_or_extirpation_values_read":0}
    try:
        wb=download_original(src["workbook_url"],int(src["workbook_expected_bytes"]),MAX_WORKBOOK)
        report["workbook_sha256"]=hashlib.sha256(wb).hexdigest()
        report["workbook_bytes"]=len(wb)
        report["workbook"]=inventory_workbook(wb)
        methods=download_original(src["readme_url"],int(src["readme_expected_bytes"]),MAX_DOCX)
        report["readme_sha256"]=hashlib.sha256(methods).hexdigest()
        report["readme_bytes"]=len(methods)
        report["README_method_flags"]=read_docx_methods_flags(methods)
        report["status"]="EXACT_PUBLISHER_FILES_VERIFIED_HEADERS_ONLY"
    except Exception as e:
        report["reason_type"]=type(e).__name__
        report["reason"]=str(e)[:350]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"reason":report.get("reason"),
                     "sheets":report.get("workbook",{}).get("sheet_count"),
                     "biological_rows_decoded":0},sort_keys=True))
    if report["status"]!="EXACT_PUBLISHER_FILES_VERIFIED_HEADERS_ONLY":
        raise SystemExit(2)


if __name__=="__main__":main()
