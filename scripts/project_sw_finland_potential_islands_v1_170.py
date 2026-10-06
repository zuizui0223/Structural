#!/usr/bin/env python3
"""Project only species + Potential_islands from pdftotext bbox XHTML.

The parser uses word coordinates to read only the first two species-table
columns. It never parses or stores the published future-summary values in later
columns.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,unicodedata,xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/sw_finland_potential_islands_projection_contract_v1_170.json"

class Stop(RuntimeError): pass

def norm_species(x:str)->str:
    return " ".join(unicodedata.normalize("NFC",str(x)).strip().split())

def sha256_file(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

def load(path:Path)->dict:
    x=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(x,dict):raise Stop("contract must be JSON object")
    return x

def tagname(node):
    return node.tag.rsplit("}",1)[-1]

def words_in_line(line):
    out=[]
    for node in line.iter():
        if tagname(node)!="word":continue
        text="".join(node.itertext()).strip()
        if not text:continue
        try:
            xmin=float(node.attrib["xMin"]);xmax=float(node.attrib["xMax"])
        except (KeyError,ValueError) as exc:
            raise Stop("bbox word missing finite x coordinates") from exc
        if not math.isfinite(xmin) or not math.isfinite(xmax) or xmax<xmin:
            raise Stop("invalid bbox word coordinates")
        out.append((text,xmin,xmax))
    return out

def page_lines(page):
    return [node for node in page.iter() if tagname(node)=="line"]

def extract_bbox(xml_text:str,contract:dict):
    if contract.get("schema")!="structural.sw_finland_potential_islands_projection_contract.v1_170":
        raise Stop("contract schema drift")
    try:root=ET.fromstring(xml_text)
    except ET.ParseError as exc:raise Stop("invalid pdftotext bbox XHTML") from exc
    pages=[n for n in root.iter() if tagname(n)=="page"]
    if not pages:raise Stop("bbox XHTML contains no pages")

    start=None;end=None;potential_x=None;next_x=None
    for pi,page in enumerate(pages):
        for li,line in enumerate(page_lines(page)):
            words=words_in_line(line)
            texts=[w[0] for w in words]
            if start is None and "species" in texts and "Potential_islands" in texts:
                try:
                    pword=next(w for w in words if w[0]=="Potential_islands")
                    nword=next(w for w in words if w[0]=="Num_colonized")
                except StopIteration as exc:
                    raise Stop("species-table header lacks next-column boundary") from exc
                potential_x=pword[1];next_x=nword[1]
                if not potential_x<next_x:raise Stop("invalid supplement column order")
                start=(pi,li)
                continue
            if start is not None and "Island_name" in texts:
                end=(pi,li);break
        if end is not None:break
    if start is None:raise Stop("species-table bbox header not found")
    if end is None:raise Stop("island-table bbox end marker not found")

    # The Potential_islands values are right-aligned within the band bounded by
    # the Potential_islands and Num_colonized header starts. Use a small margin
    # around the left header start but never enter the next column.
    band_left=potential_x-4.0
    band_right=next_x-2.0

    rows=[];seen={}
    for pi,page in enumerate(pages):
        if pi<start[0] or pi>end[0]:continue
        for li,line in enumerate(page_lines(page)):
            if pi==start[0] and li<=start[1]:continue
            if pi==end[0] and li>=end[1]:break
            words=words_in_line(line)
            if not words:continue
            texts=[w[0] for w in words]
            if "Potential_islands" in texts or "species"==texts[0].lower():
                continue

            potential_words=[
                (text,xmin,xmax) for text,xmin,xmax in words
                if xmin>=band_left and xmin<band_right and text.isdigit()
            ]
            if len(potential_words)!=1:
                continue
            ptext,pxmin,_=potential_words[0]
            potential=int(ptext)
            if not 0<=potential<=471:
                raise Stop("Potential_islands outside frozen range")

            species_words=[
                text for text,xmin,xmax in words
                if xmax<band_left+1e-9
            ]
            species=norm_species(" ".join(species_words))
            if not species:
                raise Stop(f"blank species at Potential_islands={potential}")
            # Do not inspect words to the right of the potential column.
            if species in seen:raise Stop(f"duplicate species: {species}")
            seen[species]=potential
            rows.append({
                "species":species,
                "Potential_islands":potential,
                "historical_source_count":471-potential,
            })

    expected=int(contract["validation"]["expected_unique_species"])
    if len(rows)!=expected:
        raise Stop(f"expected {expected} parsed species, found {len(rows)}")
    for species,expected_p in contract["validation"]["sentinels"].items():
        if seen.get(species)!=int(expected_p):raise Stop(f"sentinel mismatch for {species}")
    rows.sort(key=lambda r:r["species"])
    return rows

def write_safe(rows,path:Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(
            f,fieldnames=["species","Potential_islands","historical_source_count"],
            lineterminator="\n"
        )
        w.writeheader();w.writerows(rows)

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("bbox_xhtml",type=Path)
    p.add_argument("--source-pdf",type=Path,required=True)
    p.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    p.add_argument("--safe-output",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    a=p.parse_args()
    try:
        c=load(a.contract)
        rows=extract_bbox(a.bbox_xhtml.read_text(encoding="utf-8",errors="strict"),c)
        write_safe(rows,a.safe_output)
        receipt={
          "schema":"structural.sw_finland_potential_islands_projection_result.v1_170",
          "status":"T0_ONLY_POTENTIAL_ISLANDS_LOOKUP_PROJECTED",
          "candidate_id":c["candidate_id"],
          "source_pdf_sha256":sha256_file(a.source_pdf),
          "safe_lookup_sha256":sha256_file(a.safe_output),
          "species_count":len(rows),
          "minimum_Potential_islands":min(r["Potential_islands"] for r in rows),
          "maximum_Potential_islands":max(r["Potential_islands"] for r in rows),
          "species_with_zero_historical_sources":sum(r["historical_source_count"]==0 for r in rows),
          "future_summary_values_decoded_by_structural_parser":0,
          "future_summary_values_persisted":0,
          "future_summary_values_used_for_eligibility":False,
          "archive_outcome_values_read":0,
          "row_level_recent_outcome_opened":False,
          "counts_as_empirical_evidence":False,
          "next_gate":c["next_gate"],
        };code=0
    except (OSError,UnicodeDecodeError,ValueError,KeyError,json.JSONDecodeError,Stop) as exc:
        a.safe_output.unlink(missing_ok=True)
        receipt={
          "schema":"structural.sw_finland_potential_islands_projection_result.v1_170",
          "status":"STOP_SUPPLEMENT_T0_PROJECTION",
          "reason":str(exc),
          "future_summary_values_decoded_by_structural_parser":0,
          "future_summary_values_persisted":0,
          "future_summary_values_used_for_eligibility":False,
          "archive_outcome_values_read":0,
          "row_level_recent_outcome_opened":False,
          "counts_as_empirical_evidence":False,
        };code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,sort_keys=True))
    return code

if __name__=="__main__":raise SystemExit(main())
