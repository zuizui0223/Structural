#!/usr/bin/env python3
"""Original JNCC comparative seabird census XLSX source-only structural audit.

No colonial/species numerical abundance or site occupancy response rows are
decoded or reported. Public workbook is archived verbatim for later authorized
design audits, not a fresh confirmatory ecological outcome.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import posixpath
import re
import urllib.request
import zipfile
from xml.etree import ElementTree as ET

SCHEMA="structural.jncc_comparative_seabird_xlsx_source.v1_264"
JNCC_URL=("https://data.jncc.gov.uk/data/63f0ea40-485d-46dd-b967-150df90a7b2b/"
          "comparative-seabirds-count-dataset-revised-20240708.xlsx")
MAX_SOURCE_BYTES=8_000_000
M="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
R="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
P="http://schemas.openxmlformats.org/package/2006/relationships"

def _sheet_rels(blob:zipfile.ZipFile):
    name="xl/_rels/workbook.xml.rels"
    if name not in blob.namelist():
        raise ValueError("XLSX original workbook relationships absent")
    root=ET.fromstring(blob.read(name))
    mapping={}
    for rel in root.findall(f"{{{P}}}Relationship"):
        key=rel.get("Id")
        target=(rel.get("Target") or "").strip()
        if not key or not target: continue
        if target.startswith("/"):
            path=target.lstrip("/")
        elif target.startswith("xl/"):
            path=target
        else:
            path=posixpath.normpath(posixpath.join("xl",target))
        if not path.startswith("xl/worksheets/") or ".." in path.split("/"):
            continue
        mapping[key]=path
    return mapping

def _shared_strings(z:zipfile.ZipFile):
    if "xl/sharedStrings.xml" not in z.namelist(): return []
    with z.open("xl/sharedStrings.xml") as inp:
        root=ET.parse(inp).getroot()
    values=[]
    for si in root.findall(f"{{{M}}}si"):
        values.append("".join(t.text or "" for t in si.iter(f"{{{M}}}t")))
    return values

def _preview_one_sheet(z:zipfile.ZipFile,path,shared):
    if path not in z.namelist():
        raise ValueError("Original workbook missing source-referenced worksheet")
    result={"approx_dimension_ref":None,"header_only_text_preview":[]}
    with z.open(path) as file:
        for ev,node in ET.iterparse(file,events=("start","end")):
            if ev=="start" and node.tag==f"{{{M}}}dimension":
                result["approx_dimension_ref"]=node.attrib.get("ref")
            if ev!="end" or node.tag!=f"{{{M}}}row":
                continue
            rid=node.attrib.get("r")
            try:row_index=int(rid)
            except (TypeError,ValueError):row_index=999
            if row_index>4:break
            for c in node.findall(f"{{{M}}}c"):
                ty=c.attrib.get("t")
                value=None
                if ty=="s":
                    elem=c.find(f"{{{M}}}v")
                    if elem is not None and elem.text and elem.text.isdigit():
                        ix=int(elem.text)
                        if 0<=ix<len(shared): value=shared[ix]
                elif ty=="inlineStr":
                    value="".join(t.text or "" for t in c.iter(f"{{{M}}}t"))
                elif ty=="str":
                    elem=c.find(f"{{{M}}}v")
                    if elem is not None:value=elem.text
                if value is None:continue
                val=" ".join(str(value).strip().split())
                if not val or re.fullmatch(r"[-+]?[\d.,Ee]+",val):continue
                if len(result["header_only_text_preview"])<75:
                    result["header_only_text_preview"].append(val[:100])
            node.clear()
    return result

def scan_workbook(raw:bytes)->dict:
    try:
        archive=zipfile.ZipFile(io.BytesIO(raw))
    except (zipfile.BadZipFile,ValueError) as exc:
        raise ValueError("Invalid XLSX original binary source") from exc
    with archive as z:
        members=set(z.namelist())
        if "xl/workbook.xml" not in members or "xl/_rels/workbook.xml.rels" not in members:
            raise ValueError("XLSX missing workbook manifest or relationships")
        try:
            book=ET.fromstring(z.read("xl/workbook.xml"))
            names=book.find(f"{{{M}}}sheets")
            if names is None:raise ValueError("No worksheet list")
            rels=_sheet_rels(z)
            shared=_shared_strings(z)
            sheets=[]
            for item in names.findall(f"{{{M}}}sheet"):
                rid=item.attrib.get(f"{{{R}}}id")
                target=rels.get(rid)
                if target is None:
                    raise ValueError("XLSX sheet has missing canonical worksheet relationship")
                meta=_preview_one_sheet(z,target,shared)
                sheets.append({
                    "name":item.attrib.get("name","")[:120],
                    "hidden":item.attrib.get("state") in ("hidden","veryHidden"),
                    "approx_dimension_ref":meta["approx_dimension_ref"],
                    "header_only_text_preview":meta["header_only_text_preview"]
                })
        except ET.ParseError as exc:
            raise ValueError("Invalid XLSX source XML") from exc
        if not sheets:raise ValueError("XLSX contains no physical worksheets")
        return {
            "sheet_count":len(sheets),
            "sheets":sheets,
            "contains_macro_code":any(s.endswith("vbaProject.bin") for s in members),
            "contains_external_workbook_links":any(s.startswith("xl/externalLinks/") for s in members),
            "workbook_shared_string_count":len(shared),
            "biological_census_count_rows_read":0,
            "biological_census_count_values_emitted":0,
            "evidence_class":"SOURCE_XLSX_WORKSHEET_SCHEMA_AND_FIRST_FOUR_TEXT_HEADER_ROWS_ONLY"
        }

def download_original(source,expected_url):
    if source!=JNCC_URL or expected_url!=JNCC_URL:
        raise ValueError("Publisher source URL deviates from pre-frozen official July 2024 resource")
    request=urllib.request.Request(source,headers={
        "User-Agent":"Mozilla/5.0 (compatible; Structural ecological-source-integrity/1.0)",
        "Accept":"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/octet-stream,*/*"
    })
    sha=hashlib.sha256();size=0
    chunks=[]
    with urllib.request.urlopen(request,timeout=90) as response:
        while True:
            block=response.read(65536)
            if not block:break
            size+=len(block)
            if size>MAX_SOURCE_BYTES:raise ValueError("JNCC workbook exceeds original 8MB provenance cap")
            sha.update(block);chunks.append(block)
    raw=b"".join(chunks)
    if not zipfile.is_zipfile(io.BytesIO(raw)):
        raise ValueError("Original JNCC URL did not return an XLSX file")
    return raw,sha.hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",required=True,type=Path)
    p.add_argument("--source-out",required=True,type=Path)
    p.add_argument("--receipt-out",required=True,type=Path)
    a=p.parse_args()
    contract=json.loads(a.protocol.read_text(encoding="utf-8"))
    if (contract.get("schema")!="structural.jncc_seabirds_count_comparative_source_preflight.v1_264"
        or contract.get("status")!="SOURCE_ONLY_FROZEN_BEFORE_BIOLOGICAL_SITE_X_SPECIES_COUNT_ROWS"
        or contract["official_source"]["exact_original_file_url"]!=JNCC_URL):
        raise ValueError("Original JNCC response-independent source protocol changed")
    try:
        raw,digest=download_original(JNCC_URL,contract["official_source"]["exact_original_file_url"])
        inspected=scan_workbook(raw)
        a.source_out.parent.mkdir(parents=True,exist_ok=True)
        a.source_out.write_bytes(raw)
        result={
            "schema":SCHEMA,
            "status":"SOURCE_DOWNLOADED_XLSX_SHEETS_STRUCTURE_ONLY",
            "official_source_url":JNCC_URL,
            "original_version":"corrected_July_2024",
            "official_source_sha256":digest,
            "original_source_bytes":len(raw),
            "licence":"Open Government Licence 3.0",
            "original_mammal_holdout_unopened":True,
            "new_colony_census_effects_estimated":0,
            "eBird_used":False,
            "GEB_scientific_HOLD":True,
            **inspected
        }
    except Exception as exc:
        result={
            "schema":SCHEMA,
            "status":"SOURCE_STOP_NO_BIOLOGICAL_RESPONSE",
            "error_type":type(exc).__name__,
            "error":str(exc)[:300],
            "biological_census_count_rows_read":0,
            "GEB_scientific_HOLD":True
        }
    a.receipt_out.parent.mkdir(parents=True,exist_ok=True)
    a.receipt_out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({k:result.get(k) for k in
            ("status","sheet_count","original_source_bytes","error")},sort_keys=True))
    if result["status"]!="SOURCE_DOWNLOADED_XLSX_SHEETS_STRUCTURE_ONLY":
        raise SystemExit(2)

if __name__=="__main__":main()
