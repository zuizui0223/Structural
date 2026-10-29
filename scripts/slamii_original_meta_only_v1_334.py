#!/usr/bin/env python3
"""SLAM II original 45-plot multi-island forest elevation ZIP metadata ONLY.

Unpack ONLY meta.xml and ZIP member directory; original source Event and
Occurrence bodies are sealed. Tested roles: author site, habitat, elevation,
island, method, dates, origin and species rank. Official source v1.8 fixed.
"""
from __future__ import annotations
import argparse,hashlib,io,json,urllib.request,zipfile,xml.etree.ElementTree as ET
from pathlib import Path,PurePosixPath

SOURCE="https://ipt.gbif.pt/ipt/archive.do?r=pribes_exotic_arthropods&v=1.8"
UUID="020231d8-39b6-478f-ac24-715bf97c8ef4"
MAX_BYTES=350000
MAX_META=130000

def local(k):return k.rsplit("}",1)[-1]
def term(k):return k.rstrip("/").split("/")[-1].split("#")[-1]

def inspect(blob,protocol):
    if not 0<len(blob)<=MAX_BYTES:
        raise ValueError("Original 45-plot archived source ZIP exceeds frozen 350k cap")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        items=z.infolist();names=[x.filename for x in items]
        if len(items)>85 or names.count("meta.xml")!=1:
            raise ValueError("Archive has nonunique source meta.xml")
        if any(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts
               or n.startswith("\\") for n in names):
            raise ValueError("Unsafe original source filename")
        if z.getinfo("meta.xml").file_size>MAX_META:
            raise ValueError("Source meta.xml outside fixed size")
        root=ET.fromstring(z.read("meta.xml"))
        cores=[x for x in root if local(x.tag)=="core"]
        extension=[x for x in root if local(x.tag)=="extension"
                   and x.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(cores)!=1 or len(extension)!=1:
            raise ValueError("Expected one Event core and Occurrence extension")
        def describe(n):
            files=[];cols={};idx=None;foreign=None
            for x in n.iter():
                kind=local(x.tag)
                if kind=="location" and x.text:files.append(x.text.strip())
                if kind=="field" and "term" in x.attrib and "index" in x.attrib:
                    k=term(x.attrib["term"])
                    if k in cols:raise ValueError("Original source ambiguous duplicate term")
                    cols[k]=int(x.attrib["index"])
                if kind=="id" and "index" in x.attrib:idx=int(x.attrib["index"])
                if kind=="coreid" and "index" in x.attrib:foreign=int(x.attrib["index"])
            if len(files)!=1 or files[0] not in names:
                raise ValueError("Original data member missing")
            return {"row_type":n.attrib.get("rowType",""),
                    "member":files[0],"fields":sorted(cols),"indices":cols,
                    "id_index":idx,"coreid_index":foreign,
                    "delimiter":n.attrib.get("fieldsTerminatedBy",r"\t"),
                    "ignoreHeaderLines":n.attrib.get("ignoreHeaderLines","0")}
        e=describe(cores[0]);o=describe(extension[0]);es=set(e["fields"]);os=set(o["fields"])
        vertical=protocol["pre_frozen_event_habitat_ontology"]["elevation_field_candidates"]
        requirements={
            "Event_core":e["row_type"].endswith("/Event"),
            "Occurrence_ext":o["row_type"].endswith("/Occurrence"),
            "source_Event_core_id":e["id_index"] is not None,
            "source_Occurrence_foreign_key":o["coreid_index"] is not None,
            "source_plot_identity":"locationID" in es,
            "source_island":"island" in es,
            "source_habitat":"habitat" in es,
            "source_elevation_any":any(k in es for k in vertical),
            "source_year_and_sampling":{"eventDate","samplingProtocol"}.issubset(es),
            "source_taxonomic_status":{"scientificName","taxonRank","order","establishmentMeans"}.issubset(os)
        }
        return {
            "schema":"structural.slamII_45site_original_meta_receipt.v1_334",
            "status":"ORIGINAL_45SITE_FOREST_ELEVATION_SOURCE_SCHEMA_READY_EVENT_VALUES_SEALED"
                 if all(requirements.values()) else
                 "TERMINAL_ORIGINAL_FOREST_ELEVATION_OR_TAXON_SOURCE_SCHEMA",
            "original_publication_DOI":"10.15468/ucfehv",
            "source_dataset_UUID":UUID,
            "original_source_archive_SHA256":hashlib.sha256(blob).hexdigest(),
            "original_source_zip_bytes":len(blob),
            "source_Event_fields":e,
            "source_Occurrence_fields":o,
            "original_schema_eligibility":requirements,
            "available_original_elevation_fields":[k for k in vertical if k in es],
            "source_original_45_Event_and_2097_Occurrence_rows_claimed":True,
            "source_zip_member_directory":[{"path":v.filename,"size":v.file_size,"crc":f"{v.CRC:08x}"} for v in items],
            "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
            "previous_source_taxonomy_reopened":0,
            "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    contract=json.loads(a.contract.read_text())
    if (contract.get("schema")!="structural.slamII_original_forest_elevation_meta.v1_334"
        or contract.get("status")!="FROZEN_BEFORE_SOURCE_EVENT_OR_OCCURRENCE_VALUES"
        or contract["source"]["original_DwCA_archive"]!=SOURCE
        or contract["source"]["GBIF_UUID"]!=UUID):
        raise ValueError("SLAM II original source hypothesis not frozen")
    result={"schema":"structural.slamII_45site_original_meta_receipt.v1_334",
            "status":"SOURCE_META_TRANSPORT_OR_READER_STOP",
            "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
            "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-v1.334-SLAMII-Source-META-ONLY"})
        with urllib.request.urlopen(req,timeout=60) as f:data=f.read(MAX_BYTES+1)
        result=inspect(data,contract)
    except Exception as exc:
        result["stop_type"]=type(exc).__name__;result["stop_reason"]=str(exc)[:290]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:result.get(k) for k in ("status","original_source_archive_SHA256",
           "available_original_elevation_fields","original_Event_rows_opened",
           "original_Occurrence_rows_opened","stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_META_TRANSPORT_OR_READER_STOP":raise SystemExit(2)
if __name__=="__main__":main()
