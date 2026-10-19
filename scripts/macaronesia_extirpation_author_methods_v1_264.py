#!/usr/bin/env python3
"""Source-author CSIC README semantics only: NO source species×island data cells."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile

from macaronesia_extirpation_source_profile_v1_263 import (
    M,R,PR,W,MAX_WORKBOOK,_shared_header_strings,download_original
)


def extract_readme_tab(workbook_bytes):
    if not workbook_bytes.startswith(b"PK\x03\x04") or len(workbook_bytes)>MAX_WORKBOOK:
        raise ValueError("Author workbook source is not original XLSX ZIP")
    try:
        z=zipfile.ZipFile(io.BytesIO(workbook_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError("Invalid source workbook ZIP") from exc
    with z:
        sheetindex=ET.fromstring(z.read("xl/workbook.xml"))
        rels=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        targetmap={}
        for r in rels.findall(f"{{{PR}}}Relationship"):
            target=r.attrib.get("Target","")
            if not target or ".." in target.split("/"):raise ValueError("Unsafe source target")
            targetmap[r.attrib.get("Id","")]=(target.lstrip("/")
                if target.startswith("/") else posixpath.normpath(posixpath.join("xl",target)))
        methods_sheets=[s for s in sheetindex.findall(f".//{{{M}}}sheet")
                        if s.attrib.get("name")=="Read me"]
        if len(methods_sheets)!=1:
            raise ValueError("The original author-defined Read me metadata tab is missing")
        sheet=targetmap.get(methods_sheets[0].attrib.get(f"{{{R}}}id"))
        if not sheet or sheet not in z.namelist():
            raise ValueError("Read me worksheet relationship is missing")
        raw_rows=[]
        with z.open(sheet) as stream:
            for event,elem in ET.iterparse(stream,events=("end",)):
                if elem.tag!=f"{{{M}}}row":continue
                number=int(elem.attrib.get("r","0"))
                if number>60:
                    raise ValueError("Author Read me tab exceeds frozen methods-only row boundary")
                cells=[]
                for cell in elem.findall(f"{{{M}}}c"):
                    kind=cell.attrib.get("t","")
                    if kind=="s":
                        v=cell.find(f"{{{M}}}v")
                        if v is not None and v.text and v.text.isdigit():
                            cells.append(("shared",int(v.text)))
                    elif kind=="inlineStr":
                        zt=cell.find(f"{{{M}}}is")
                        if zt is not None:
                            cells.append(("inline","".join(
                                t.text or "" for t in zt.iter(f"{{{M}}}t"))))
                    elif kind=="str":
                        v=cell.find(f"{{{M}}}v")
                        if v is not None:cells.append(("inline",v.text or ""))
                raw_rows.append((number,cells))
                elem.clear()
        wanted={value for _,cells in raw_rows for kind,value in cells if kind=="shared"}
        strings=_shared_header_strings(z,wanted)
        methods=[]
        for number,cells in raw_rows:
            txt=" ".join(
                strings[val] if kind=="shared" else val for kind,val in cells).strip()
            if txt:methods.append({"row":number,"text":txt[:550]})
        return {"source_tab":"Read me","method_rows":methods,
                "readme_nonempty_rows":len(methods),
                "non_method_worksheet_values_decoded":0,
                "original_species_status_is_not_decoded":True}


def extract_docx_paragraph_methods(readme_bytes):
    if not readme_bytes.startswith(b"PK\x03\x04") or len(readme_bytes)>1_000_000:
        raise ValueError("Original author README.docx signature/size invalid")
    with zipfile.ZipFile(io.BytesIO(readme_bytes)) as z:
        root=ET.fromstring(z.read("word/document.xml"))
    texts=[]
    cues=("table","extinct","extirpat","island","native","introduced",
          "azores","canar","breeding","pollinat","dispers","species",
          "taxon","classification","endem","record","habitat")
    raw_pars=root.findall(f".//{{{W}}}p")
    for i,p in enumerate(raw_pars):
        t=" ".join((x.text or "") for x in p.iter(f"{{{W}}}t")).strip()
        if t and any(cue in t.casefold() for cue in cues):
            texts.append({"paragraph":i+1,"source_excerpt":t[:450]})
    return {"source_original_paragraphs":len(raw_pars),
            "selected_author_methods_paragraphs":texts[:45],
            "not_author_species_record_data":True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract",required=True,type=Path)
    parser.add_argument("--output",required=True,type=Path)
    args=parser.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.macaronesia_source_methods_gate.v1_264"
        or c.get("status")!="AUTHOR_METHOD_NOT_RESPONSE_ANNOTATION_FROZEN_BEFORE_CELL_ACCESS"):
        raise ValueError("Author original methodology source gate not frozen")
    src=c["source"]
    result={"schema":"structural.macaronesia_author_methods_result.v1_264",
            "status":"METHODS_SOURCE_ACCESS_STOP",
            "source_sheet":"Read me",
            "species_extirpation_rows_read":0,
            "GEB_scientific_HOLD":True,
            "eBird_off":True}
    try:
        wb=download_original(src["workbook_exact_url"],332776,5_000_000)
        rd=download_original(src["readme_exact_url"],23793,1_000_000)
        wsha=hashlib.sha256(wb).hexdigest()
        rsha=hashlib.sha256(rd).hexdigest()
        if wsha!=src["workbook_sha256"] or rsha!=src["readme_sha256"]:
            raise ValueError("Official Macaronesia source SHA256 changed from frozen original")
        result["workbook_sha256"]=wsha
        result["readme_sha256"]=rsha
        result["tab_author_methods"]=extract_readme_tab(wb)
        result["docx_author_methods"]=extract_docx_paragraph_methods(rd)
        result["status"]="AUTHOR_METHODOLOGY_ONLY_VERIFIED"
    except Exception as exc:
        result["stop_type"]=type(exc).__name__
        result["stop_detail"]=str(exc)[:400]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"tab_rows":result.get("tab_author_methods",{}).get("readme_nonempty_rows"),"original_response_cells_decoded":0,"error":result.get("stop_detail")},sort_keys=True))
    if result["status"]!="AUTHOR_METHODOLOGY_ONLY_VERIFIED":
        raise SystemExit(2)


if __name__=="__main__":main()
