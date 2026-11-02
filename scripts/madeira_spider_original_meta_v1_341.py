#!/usr/bin/env python3
"""v1.341 Madeira COBRA spider forest/dry natural habitat SOURCE META ONLY.

Only original ZIP directory and meta.xml are opened. Plot, sampling and
original taxonomic data bodies remain sealed. The 2020 original paper is
prior art for the endemic fauna, while the new question is *equal-effort*
forest-only versus natural-habitat monitoring portfolio complementarity.
"""
from __future__ import annotations
import argparse,hashlib,io,json,urllib.request,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path,PurePosixPath

SOURCE="https://ipt.gbif.pt/ipt/archive.do?r=spiders_madeira&v=1.8"
UUID="2a15f6bf-c850-4a52-84cf-d127224be076"
MAX_BYTES=400000
MAX_META=130000

def local(tag):return tag.rsplit("}",1)[-1]
def term(uri):return uri.rstrip("/").split("/")[-1].split("#")[-1]

def metadata_only(blob):
    if not 0<len(blob)<=MAX_BYTES:
        raise ValueError("Original fixed spider v1.8 archive exceeds safe 400kB size")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        items=z.infolist()
        names=[x.filename for x in items]
        if not 0<len(items)<=90 or names.count("meta.xml")!=1:
            raise ValueError("Original source meta.xml missing/duplicated")
        if z.getinfo("meta.xml").file_size>MAX_META:
            raise ValueError("Original author meta.xml oversize")
        if any(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts
               or n.startswith("\\") for n in names):
            raise ValueError("Unsafe source ZIP member")
        root=ET.fromstring(z.read("meta.xml"))
        core=[x for x in root if local(x.tag)=="core"]
        occ=[x for x in root if local(x.tag)=="extension"
             and x.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(core)!=1 or len(occ)!=1:
            raise ValueError("Exactly one original Event core + Occurrence extension required")
        def describe(el):
            labels={};paths=[];idx=None;fid=None
            for x in el.iter():
                key=local(x.tag)
                if key=="field" and "term" in x.attrib and "index" in x.attrib:
                    name=term(x.attrib["term"])
                    if name in labels:raise ValueError("Duplicate original Darwin Core field")
                    labels[name]=int(x.attrib["index"])
                elif key=="location" and x.text:paths.append(x.text.strip())
                elif key=="id" and "index" in x.attrib:idx=int(x.attrib["index"])
                elif key=="coreid" and "index" in x.attrib:fid=int(x.attrib["index"])
            if len(paths)!=1 or paths[0] not in names:
                raise ValueError("Original source member absent")
            return {"row_type":el.attrib.get("rowType",""),
                 "data_member":paths[0],"field_indices":labels,
                 "original_field_names":sorted(labels),
                 "primary_key_index":idx,"foreign_key_index":fid,
                 "delimiter":el.attrib.get("fieldsTerminatedBy",r"\t"),
                 "skip_header":el.attrib.get("ignoreHeaderLines","0")}
        e=describe(core[0]);o=describe(occ[0])
        event=set(e["original_field_names"]);taxa=set(o["original_field_names"])
        groups={
            "author_island_field":[x for x in ("island","stateProvince") if x in event],
            "author_plot_field":[x for x in ("locationID","locality","fieldNumber","parentEventID") if x in event],
            "author_habitat_field":[x for x in ("habitat","eventRemarks","locality") if x in event],
            "author_method_field":[x for x in ("samplingProtocol","samplingEffort","eventRemarks") if x in event],
            "author_taxon_origin_field":[x for x in ("establishmentMeans","degreeOfEstablishment","occurrenceRemarks") if x in taxa]
        }
        qual=(e["row_type"].endswith("/Event") and o["row_type"].endswith("/Occurrence")
              and e["primary_key_index"] is not None
              and o["foreign_key_index"] is not None
              and {"eventDate"}.issubset(event)
              and {"scientificName","taxonRank"}.issubset(taxa)
              and all(groups[k] for k in ("author_island_field","author_plot_field",
                      "author_habitat_field","author_method_field","author_taxon_origin_field")))
        return {
          "schema":"structural.madeira_spider_natural_habitat_source_meta_result.v1_341",
          "status":"MADEIRA_SPIDER_NATURAL_HABITAT_ORIGIN_META_ELIGIBLE_RESPONSES_CLOSED"
            if qual else "TERMINAL_MADEIRA_SPIDER_SOURCE_PLOT_OR_ORIGIN_META_MISSING",
          "original_source_zip_sha256":hashlib.sha256(blob).hexdigest(),
          "original_source_zip_bytes":len(blob),
          "GBIF_dataset_UUID":UUID,"source_version":"1.8",
          "source_original_Event_rows_published":562,
          "source_original_Occurrence_rows_published":3281,
          "original_22_plots_published_not_yet_verified":True,
          "Event_source_meta":e,"Occurrence_source_meta":o,
          "source_candidate_fields":groups,
          "original_ZIP_directory":[{"member":x.filename,"bytes":x.file_size,"CRC32":f"{x.CRC:08x}"}
                                    for x in items],
          "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
          "original_Azores_Madeira_Night_Galapagos_species_sources_reopened":0,
          "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
        }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    contract=json.loads(a.protocol.read_text())
    if (contract.get("schema")!="structural.madeira_spider_natural_habitat_complementarity.v1_341"
        or contract.get("status")!="FROZEN_BEFORE_ORIGINAL_MADEIRA_SPIDER_V18_EVENT_OR_OCCURRENCE_BODY_READ"
        or contract["source"]["original_url"]!=SOURCE or contract["source"]["GBIF_UUID"]!=UUID):
        raise ValueError("Pre-original native habitat conservation complementarity not frozen")
    result={
      "schema":"structural.madeira_spider_natural_habitat_source_meta_result.v1_341",
      "status":"SOURCE_OR_META_TRANSPORT_STOP","original_Event_rows_opened":0,
      "original_Occurrence_rows_opened":0,"GEB_scientific_HOLD":True,
      "new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        request=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-Madeira-Cobra-v1.341-MetaONLY"})
        with urllib.request.urlopen(request,timeout=65) as f:blob=f.read(MAX_BYTES+1)
        result=metadata_only(blob)
    except Exception as ex:
        result["stop_type"]=type(ex).__name__;result["stop_reason"]=str(ex)[:250]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print(json.dumps({k:result.get(k) for k in (
       "status","original_source_zip_sha256","source_candidate_fields",
       "original_Event_rows_opened","original_Occurrence_rows_opened","stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_OR_META_TRANSPORT_STOP":raise SystemExit(2)
if __name__=="__main__":main()
