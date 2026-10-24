#!/usr/bin/env python3
"""Macaronesian vascular-plant source audit: strictly published Table S1 only.

This is a retrospective **observation-denominator** audit, not an original
island extinction mechanism test or historical donor-population reconstruction.
Never touch native-flora S3/S4 response values, S2 extirpation outcome totals,
or original Structural 529-mammal heldout.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import posixpath
import re
import xml.etree.ElementTree as ET
import zipfile

from macaronesia_extirpation_source_profile_v1_263 import (
    M,R,PR,MAX_WORKBOOK,download_original
)

COLUMNS=(
    "Species","Extinction category","Category","Island","Archipelago","Date",
    "Pollination mechanism","Seed dispersal mechanism","Habit","Endemicity"
)
STATUS="PUBLISHED_SOURCE_RETROSPECTIVE_ISLAND_LOSS_AUDIT"
CLASS_LOCAL="extirpation (island level)"
CONFIRMED="well-supported"


def _xml_xlsx_s1(raw:bytes):
    if not raw.startswith(b"PK\x03\x04") or len(raw)>MAX_WORKBOOK:
        raise ValueError("Original publisher workbook ZIP signature/size invalid")
    try:
        z=zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as e:
        raise ValueError("Original XLSX is missing or truncated") from e
    with z:
        members=set(z.namelist())
        if not {"xl/workbook.xml","xl/_rels/workbook.xml.rels"}<=members:
            raise ValueError("Original workbook metadata parts missing")
        root=ET.fromstring(z.read("xl/workbook.xml"))
        rel=ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        indices={}
        for node in rel.findall(f"{{{PR}}}Relationship"):
            target=node.attrib.get("Target","")
            if not target or ".." in target.split("/"):
                raise ValueError("Untrusted OOXML source path")
            indices[node.attrib.get("Id")]=(
                target.lstrip("/") if target.startswith("/")
                else posixpath.normpath(posixpath.join("xl",target)))
        named=[s for s in root.findall(f".//{{{M}}}sheet")
               if s.attrib.get("name")=="Table S1"]
        if len(named)!=1:
            raise ValueError("Exact source Table S1 not found")
        path=indices.get(named[0].attrib.get(f"{{{R}}}id"))
        if not path or path not in members:
            raise ValueError("Table S1 not linked to source worksheet")
        rows=[]
        shared_requested=set()
        with z.open(path) as stream:
            try:
                for event,elem in ET.iterparse(stream,events=("end",)):
                    if elem.tag!=f"{{{M}}}row":continue
                    ix=int(elem.attrib.get("r","0"))
                    if ix>1000 or ix<1:
                        raise ValueError("Original sheet unexpected row index")
                    cells={}
                    for cell in elem.findall(f"{{{M}}}c"):
                        a=cell.attrib.get("r","")
                        ma=re.fullmatch(r"([A-Z]{1,3})\d+",a)
                        if not ma:continue
                        col=ma.group(1)
                        tp=cell.attrib.get("t","")
                        val=None
                        if tp=="inlineStr":
                            inn=cell.find(f"{{{M}}}is")
                            if inn is not None:
                                val="".join(n.text or "" for n in inn.iter(f"{{{M}}}t"))
                        elif tp=="s":
                            node=cell.find(f"{{{M}}}v")
                            if node is not None and node.text and node.text.isdigit():
                                val=("shared",int(node.text))
                                shared_requested.add(int(node.text))
                        else:
                            node=cell.find(f"{{{M}}}v")
                            if node is not None: val=node.text or ""
                        if val is not None:
                            cells[col]=val
                    rows.append((ix,cells))
                    elem.clear()
            except ET.ParseError as exc:
                raise ValueError("Malformed Table S1 source XML") from exc
        if not rows or rows[0][0]!=1:
            raise ValueError("Missing first author-declared S1 column header")
        # Parse original sharedStrings text for *requested Table S1 only* indices.
        strings={}
        if shared_requested:
            if "xl/sharedStrings.xml" not in members:
                raise ValueError("Table S1 shared string references are invalid")
            n=0
            with z.open("xl/sharedStrings.xml") as stream:
                for ev,el in ET.iterparse(stream,events=("end",)):
                    if el.tag!=f"{{{M}}}si":continue
                    if n in shared_requested:
                        strings[n]="".join(t.text or "" for t in el.iter(f"{{{M}}}t"))
                    n+=1;el.clear()
                    if len(strings)==len(shared_requested):break
            if set(strings)!=shared_requested:
                raise ValueError("Missing author-shared-string entries for Table S1")
        def decode(val):
            if isinstance(val,tuple):
                return strings[val[1]].strip()
            return ("" if val is None else str(val)).strip()
        headers={col:decode(val) for col,val in rows[0][1].items()}
        if not set(COLUMNS)<=set(headers.values()):
            raise ValueError("Original S1 header fields inconsistent with pre-response protocol: "+
                             str(sorted(set(COLUMNS)-set(headers.values()))))
        selected={col:name for col,name in headers.items() if name in COLUMNS}
        data=[]
        for ix,cells in rows[1:]:
            values={name:decode(cells.get(col)) for col,name in selected.items()}
            if any(values.values()):
                if not values.get("Species"):
                    raise ValueError(f"Non-empty row {ix} in S1 without source species key")
                data.append(values)
        return data


def parse_sheet_s1(raw:bytes):
    """Read only original Table S1; other biological worksheets are never opened."""
    return _xml_xlsx_s1(raw)


def _year(value):
    # Date in original author data may be a last-collection notation, not a loss date.
    v=(value or "").strip()
    if re.fullmatch(r"(17|18|19|20)\d{2}(?:\.0+)?",v):
        n=int(float(v))
        return n if 1753<=n<=2026 else None
    return None


def summarize_source_events(records,expected_num_records=168):
    if expected_num_records is not None and len(records)!=expected_num_records:
        raise ValueError(f"Original published expected {expected_num_records} species-loss records, "
                         f"observed {len(records)}. Do not recode biology until resolved.")
    if not records:
        raise ValueError("Empty author published S1 response table")
    for row in records:
        if not set(COLUMNS)<=set(row):
            raise ValueError("Source S1 required field absent")
    categories=Counter((r.get("Extinction category") or "").strip() or "[MISSING]"
                       for r in records)
    confidence=Counter((r.get("Category") or "").strip() or "[MISSING]"
                       for r in records)
    raw_strict=[]
    malformed=0
    for row in records:
        status=(row.get("Extinction category") or "").strip().casefold()
        cert=(row.get("Category") or "").strip().casefold()
        if status==CLASS_LOCAL and cert==CONFIRMED:
            if not all((row.get(k) or "").strip() for k in ("Species","Island","Archipelago")):
                malformed+=1;continue
            raw_strict.append(row)
    pair_map={}
    for row in raw_strict:
        key=(row["Species"].casefold().strip(),
             row["Archipelago"].casefold().strip(),row["Island"].casefold().strip())
        pair_map.setdefault(key,row)
    by_arch=defaultdict(set)
    taxon_islands=defaultdict(set)
    taxon_arch=defaultdict(set)
    traits=defaultdict(Counter)
    dates=Counter()
    for key,row in pair_map.items():
        species,arch,island=key
        arch_disp=row["Archipelago"].strip()
        by_arch[arch_disp].add((species,island))
        taxon_islands[species].add((arch,island))
        taxon_arch[species].add(arch)
        for field in ("Pollination mechanism","Seed dispersal mechanism","Habit","Endemicity"):
            traits[field][(row.get(field) or "").strip() or "[MISSING]"]+=1
        y=_year(row.get("Date"))
        dates["parseable_last_observation_year" if y is not None else "unparsed_or_missing_date"]+=1
        if y is not None:
            dates["before_1960" if y<1960 else "1960_or_later"]+=1
    original_taxa={r["Species"].strip().casefold() for r in records if r.get("Species")}
    return {
      "source_species_records":len(records),
      "author_source_taxa_distinct_name_strings":len(original_taxa),
      "source_extinction_categories":dict(sorted(categories.items())),
      "source_confidence_categories":dict(sorted(confidence.items())),
      "strict_well_supported_island_loss_raw_records":len(raw_strict),
      "strict_qualified_records_missing_species_island_or_archipelago":malformed,
      "strict_distinct_taxon_island_loss_pairs":len(pair_map),
      "strict_duplicate_raw_records_same_taxon_island":len(raw_strict)-len(pair_map),
      "strict_taxa_with_any_island_level_local_loss":len(taxon_islands),
      "strict_island_loss_named_island_count":len({(k[1],k[2]) for k in pair_map}),
      "strict_island_loss_archipelagos":{k:len(v) for k,v in sorted(by_arch.items())},
      "taxa_with_strict_losses_on_two_plus_islands":
         sum(len(x)>=2 for x in taxon_islands.values()),
      "taxa_with_strict_losses_in_two_plus_archipelagos":
         sum(len(x)>=2 for x in taxon_arch.values()),
      "strict_status_by_trait_descriptive":{k:dict(v) for k,v in traits.items()},
      "last_observation_date_quality_counts":dict(dates),
      "species_or_island_names_disclosed_in_artifact":False,
      "historically_occupied_but_persisting_island_denominator_available":False,
      "prior_t0_viable_conspecific_donor_island_states_measured":False,
      "directional_interisland_migration_observed":False,
      "native_flora_S3_S4_response_rows_opened":0
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    original=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (original.get("schema")!="structural.macaronesia_published_extirpation_event_pilot.v1_265"
        or original.get("status")!="S1_ONLY_RETROSPECTIVE_EVENT_DESIGN_LOCKED_BEFORE_EXTINCTION_RESPONSE_ACCESS"):
        raise ValueError("S1 biological trial not authorized by original frozen response design")
    source=original["source"]
    if source["sheet"]!="Table S1":
        raise ValueError("Only S1 source endpoint authorised")
    raw=download_original(source["source_workbook_url"],
                          int(source["exact_original_workbook_bytes"]),MAX_WORKBOOK)
    if hashlib.sha256(raw).hexdigest()!=source["sha256"]:
        raise ValueError("Official publisher workbook SHA mismatch: cannot access changed biological values")
    results=summarize_source_events(parse_sheet_s1(raw),expected_num_records=168)
    result={
      "schema":"structural.macaronesia_local_loss_pilot.v1_265",
      "status":STATUS,
      "source_workbook_sha256":source["sha256"],
      "source_doi":source["DOI"],
      "evidence_class":"PUBLISHED_POST_OUTCOME_EXPLORATORY_S1_EVENT_DENOMINATOR_ONLY",
      "original_2025_publication_already_documented_168_event_126_taxa_census":True,
      "S2_S3_S4_biological_values_read":0,
      "original_529_mammal_holdout_rows_accessed":0,
      "new_confirmatory_systems":0,
      "GEB_scientific_HOLD":True,"eBird_off":True,
      **results
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:result.get(k) for k in (
        "status","source_species_records",
        "strict_well_supported_island_loss_raw_records",
        "strict_distinct_taxon_island_loss_pairs",
        "taxa_with_strict_losses_on_two_plus_islands",
        "taxa_with_strict_losses_in_two_plus_archipelagos")},sort_keys=True))


if __name__=="__main__":main()
