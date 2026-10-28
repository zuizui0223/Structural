#!/usr/bin/env python3
"""v1.291 2026 Azores trail-plant fixed original v1.4 source, ZIP/meta.xml only.

No Event data lines, no species names, no nativeness labels, no non-site
biological contents. This is metadata-only preflight, NOT evidence of ecology.
"""
from __future__ import annotations
import argparse,hashlib,io,json,urllib.request,zipfile,xml.etree.ElementTree as ET
from pathlib import Path,PurePosixPath

SOURCE="https://ipt.gbif.pt/ipt/archive.do?r=plants_trails_azores&v=1.4"
UUID="7c190e4a-6987-4042-97aa-534590b45ce5"
MAX_BYTES=1_000_000
MAX_META_BYTES=256_000

def _local(t):return t.rsplit("}",1)[-1]
def _term(t):return t.rstrip("/").split("/")[-1].split("#")[-1]

def parse_opaque_archive(archive:bytes):
    if len(archive)>MAX_BYTES: raise ValueError("Frozen 1 MB original archive cap exceeded")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        entries=z.infolist()
        if not entries or len(entries)>100:raise ValueError("Unexpected original source ZIP entry count")
        names=[x.filename for x in entries]
        for n in names:
            p=PurePosixPath(n)
            if p.is_absolute() or ".." in p.parts or n.startswith("\\"):
                raise ValueError("Unsafe archive member filename")
        if len([n for n in names if n=="meta.xml"])!=1:raise ValueError("Exactly one original root meta.xml required")
        if z.getinfo("meta.xml").file_size>MAX_META_BYTES:raise ValueError("metadata XML too large")
        root=ET.fromstring(z.read("meta.xml"))
        core=[node for node in root if _local(node.tag)=="core"]
        ext=[node for node in root if _local(node.tag)=="extension"
             and node.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(core)!=1 or len(ext)!=1:raise ValueError("Unexpected one Event and one Occurrence schema")
        def audit(node):
            name=node.attrib.get("rowType","")
            terms={}
            locations=[]
            idindex=None; coreidindex=None
            for k in node.iter():
                typ=_local(k.tag)
                if typ=="location" and k.text:locations.append(k.text.strip())
                elif typ=="field" and "index" in k.attrib and "term" in k.attrib:
                    terms[_term(k.attrib["term"])]=int(k.attrib["index"])
                elif typ=="id" and "index" in k.attrib:
                    idindex=int(k.attrib["index"])
                elif typ=="coreid" and "index" in k.attrib:
                    coreidindex=int(k.attrib["index"])
            if len(locations)!=1 or locations[0] not in names:raise ValueError("Unresolved core/extension data member")
            return {"rowtype":name,"files":locations,
                    "field_terms":sorted(terms),"field_indices":terms,
                    "id_index_declared":idindex is not None,
                    "coreid_index_declared":coreidindex is not None,
                    "ignoreHeaderLines":node.attrib.get("ignoreHeaderLines","0"),
                    "fieldsTerminatedBy":node.attrib.get("fieldsTerminatedBy","")}
        event=audit(core[0]);occurrence=audit(ext[0])
        if not event["rowtype"].rstrip("/").endswith("/Event"):
            raise ValueError("Original source core is not Event")
        evt=set(event["field_terms"]);occ=set(occurrence["field_terms"])
        missing_plant=sorted({"scientificName","establishmentMeans"}-occ)
        missing_event=sorted({"eventID"}-evt)
        roles_qualified=(event["id_index_declared"] and occurrence["coreid_index_declared"] 
                          and not missing_event and not missing_plant and ("island" in evt or "locality" in evt)
                          and ("eventDate" in evt or "year" in evt))
        return {
           "schema":"structural.azores_trail_plants_opaque_schema_result.v1_291",
           "status":"SCHEMA_POSSIBLE_EVENT_UNOPENED" if roles_qualified else "SCHEMA_HOLD_REQUIRED_TERMS_OR_LINK_MISSING",
           "gbif_uuid":UUID,"original_v1_4_archive_sha256":hashlib.sha256(archive).hexdigest(),
           "archive_length_bytes":len(archive),
           "archive_directory":[{"path":e.filename,"uncompressed_bytes":e.file_size,
                                 "crc32_hex":f"{e.CRC:08x}"} for e in entries],
           "Event_meta":event,"Occurrence_meta":occurrence,
           "missing_required_Event_terms":missing_event,
           "missing_required_Occurrence_terms":missing_plant,
           "source_version_discrepancy_260_vs_210_events_unresolved":True,
           "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
           "source_site_ids_and_taxon_names_read":0,
           "confirmatory_systems_admitted":0,"GEB_scientific_HOLD":True,"eBird_used":False,
           "not_plant_response_or_ecological_conclusion":True
        }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    contract=json.loads(args.contract.read_text(encoding="utf-8"))
    if contract.get("schema")!="structural.azores_trail_plants_source_opaque_design.v1_291" or (
      contract["source"]["exact_original_archive"]!=SOURCE or contract["source"]["gbif_uuid"]!=UUID
      or contract["status"]!="FROZEN_SOURCE_ONLY_BEFORE_ORIGINAL_2026_TRAIL_ARCHIVE_OPEN"):
        raise ValueError("Protocol not frozen before source access")
    result={"schema":"structural.azores_trail_plants_opaque_schema_result.v1_291",
            "status":"SOURCE_TRANSPORT_OR_SCHEMA_STOP", "original_Event_rows_opened":0,
            "original_Occurrence_rows_opened":0,"source_site_ids_and_taxon_names_read":0,
            "GEB_scientific_HOLD":True,"confirmatory_systems_admitted":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-Azores-Trail-Source-Metadata-Only-v1.291"})
        with urllib.request.urlopen(req,timeout=60) as remote:
            data=remote.read(MAX_BYTES+1)
        result=parse_opaque_archive(data)
    except Exception as err:
        result["stop_type"]=type(err).__name__
        result["stop_reason"]=str(err)[:320]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"source_sha256":result.get("original_v1_4_archive_sha256"),
      "event_fields":result.get("Event_meta",{}).get("field_terms"),
      "occurrence_fields":result.get("Occurrence_meta",{}).get("field_terms"),
      "missing_occ":result.get("missing_required_Occurrence_terms"),
      "site_or_plant_rows_read":0,"stop_reason":result.get("stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_TRANSPORT_OR_SCHEMA_STOP":raise SystemExit(2)

if __name__=="__main__":main()
