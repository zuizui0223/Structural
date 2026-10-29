#!/usr/bin/env python3
"""Independent Galapagos ant source ZIP metadata ONLY, original field values sealed.

Original GBIF/Pensoft 2026 archive may encode 2023/2024 ant samples as
Darwin Core Event core + Occurrence extension. Read original ZIP directory
and meta.xml ONLY, never Event sites, dates, habitat or taxon identities.
"""
from __future__ import annotations
import argparse,hashlib,io,json,urllib.request,zipfile,xml.etree.ElementTree as ET
from pathlib import Path,PurePosixPath

SOURCE="https://ipt.pensoft.net/archive.do?r=antga"
UUID="eb7e79d2-434b-42b2-a891-99686fe676ec"
MAX_BYTES=2_500_000
MAX_META=300_000
def local(x):return x.rsplit("}",1)[-1]
def term(x):return x.rstrip("/").split("/")[-1].split("#")[-1]

def inventory(blob,contract):
    if not 0<len(blob)<=MAX_BYTES:raise ValueError("Source ZIP exceeds fixed 2.5MB cap")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        items=z.infolist()
        names=[e.filename for e in items]
        if len(items)>100 or names.count("meta.xml")!=1:
            raise ValueError("Darwin Core source missing sole meta.xml")
        if any(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts or n.startswith("\\") for n in names):
            raise ValueError("Source ZIP traversal path")
        if z.getinfo("meta.xml").file_size>MAX_META:
            raise ValueError("Source meta.xml exceeds frozen cap")
        root=ET.fromstring(z.read("meta.xml"))
        cores=[x for x in root if local(x.tag)=="core"]
        extensions=[x for x in root if local(x.tag)=="extension"
                    and x.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        def desc(x):
            columns={};primary=None;foreign=None;paths=[]
            for v in x.iter():
                k=local(v.tag)
                if k=="location" and v.text:paths.append(v.text.strip())
                elif k=="field" and "term" in v.attrib and "index" in v.attrib:
                    f=term(v.attrib["term"])
                    if f in columns:raise ValueError("Ambiguous source field term")
                    columns[f]=int(v.attrib["index"])
                elif k=="id" and "index" in v.attrib:primary=int(v.attrib["index"])
                elif k=="coreid" and "index" in v.attrib:foreign=int(v.attrib["index"])
            if len(paths)!=1 or paths[0] not in names:
                raise ValueError("Original source Event/Occurrence member missing")
            return {"row_type":x.attrib.get("rowType",""),
                    "original_member":paths[0],
                    "field_names":sorted(columns),
                    "field_indices":columns,
                    "primary_Event_id_index":primary,
                    "foreign_Event_id_index":foreign,
                    "original_delimiter":x.attrib.get("fieldsTerminatedBy",r"\t"),
                    "header_rows_to_ignore":x.attrib.get("ignoreHeaderLines","0")}
        if len(cores)!=1 or len(extensions)!=1:
            return {
                "schema":"structural.galapagos_ant_original_source_schema_result.v1_338",
                "status":"TERMINAL_NOT_SINGLE_EVENT_CORE_AND_OCCURRENCE_EXTENSION",
                "original_zip_sha256":hashlib.sha256(blob).hexdigest(),
                "original_zip_bytes":len(blob),
                "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
                "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
        e=desc(cores[0]);o=desc(extensions[0])
        event=set(e["field_names"]);occ=set(o["field_names"])
        src=contract["source_only_v338"]
        candidates={
          "site":[f for f in src["Event_plot_identifiers"] if f in event],
          "habitat":[f for f in src["Event_habitat_candidates"] if f in event],
          "elevation":[f for f in src["Event_elevation_candidates"] if f in event],
          "origin":[f for f in src["Occurrence_origin_candidates"] if f in occ]
        }
        check={
          "Event_role":e["row_type"].rstrip("/").endswith("/Event"),
          "Occurrence_role":o["row_type"].rstrip("/").endswith("/Occurrence"),
          "Event_coreid":e["primary_Event_id_index"] is not None,
          "Occurrence_coreid":o["foreign_Event_id_index"] is not None,
          "Event_method_and_date":set(src["Event_required"]).issubset(event),
          "Occurrence_scientific_name_and_rank":set(src["Occurrence_required"]).issubset(occ),
          "source_site_id":bool(candidates["site"]),
          "source_habitat":bool(candidates["habitat"]),
          "source_elevation":bool(candidates["elevation"]),
          "source_taxonomic_origin":bool(candidates["origin"])
        }
        return {
            "schema":"structural.galapagos_ant_original_source_schema_result.v1_338",
            "status":"GALAPAGOS_ANT_SITE_HABITAT_ELEVATION_AND_ORIGIN_SCHEMA_PRESENT_RESPONSES_SEALED" if all(check.values()) else
                   "TERMINAL_SOURCE_MISSING_ANT_HABITAT_ORIGIN_FIELD",
            "original_zip_sha256":hashlib.sha256(blob).hexdigest(),
            "original_zip_bytes":len(blob),
            "source_dataset_uuid":UUID,
            "source_published_2026_version":"2026-09-29 Pensoft antga",
            "original_Event_source_metadata":e,
            "original_Occurrence_source_metadata":o,
            "original_schema_candidates":candidates,
            "source_qualification":check,
            "source_directory":[{"path":z.filename,"uncompressed_bytes":z.file_size,"CRC32":f"{z.CRC:08x}"} for z in items],
            "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
            "source_plot_coordinates_status_taxa_values_unopened":True,
            "older_Azores_biological_sources_reopened":0,
            "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
        }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    c=json.loads(a.contract.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.galapagos_ant_native_modified_habitat_source.v1_338"
        or c.get("status")!="SOURCE_ARCHIVE_META_ONLY_BEFORE_FIRST_EVENT_OCCURRENCE_VALUE"
        or c["source"]["official_source_archive"]!=SOURCE
        or c["source"]["GBIF_dataset_uuid"]!=UUID):
        raise ValueError("Galapagos original source hypothesis/version not frozen")
    result={"schema":"structural.galapagos_ant_original_source_schema_result.v1_338",
        "status":"ORIGINAL_SOURCE_TRANSPORT_OR_META_TECHNICAL_STOP",
        "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-Galapagos-ant-EventMetaOnly-v1.338"})
        with urllib.request.urlopen(req,timeout=75) as response:
            data=response.read(MAX_BYTES+1)
        result=inventory(data,c)
    except Exception as err:
        result["stop_type"]=type(err).__name__;result["stop_reason"]=str(err)[:280]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:result.get(k) for k in (
        "status","original_zip_sha256","original_zip_bytes","original_schema_candidates",
        "original_Event_rows_opened","original_Occurrence_rows_opened","stop_reason"
    )},sort_keys=True))
    if result["status"]=="ORIGINAL_SOURCE_TRANSPORT_OR_META_TECHNICAL_STOP":raise SystemExit(2)
if __name__=="__main__":main()
