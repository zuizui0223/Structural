#!/usr/bin/env python3
"""v1.325 SLAM exact independent v1.7 source ZIP metadata only.

Never read original 893 Event rows or 14,922 taxon Occurrence rows. This
preflights whether SAME-protocol native/mixed/exotic forest habitat type and
species biogeographic origins can be interpreted from the original source
schema, instead of guessing mechanisms from published aggregate patterns.
"""
from __future__ import annotations
import argparse,hashlib,io,json,urllib.request,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path,PurePosixPath

SOURCE="https://ipt.gbif.pt/ipt/archive.do?r=arthropods_slam_azores&v=1.7"
UUID="079c8358-0b4f-479b-97dd-1f2f775256f9"
MAX_BYTES=1_600_000
MAX_METADATA=160_000

def local(s):return s.rsplit("}",1)[-1]
def term(s):return s.rstrip("/").split("/")[-1].split("#")[-1]

def parse_opaque(source):
    if not 0<len(source)<=MAX_BYTES:
        raise ValueError("Exact original SLAM v1.7 ZIP exceeds frozen 1.6 MB cap")
    with zipfile.ZipFile(io.BytesIO(source)) as z:
        files=z.infolist()
        names=[v.filename for v in files]
        if not 0<len(files)<=80 or names.count("meta.xml")!=1:
            raise ValueError("Exactly one original source meta.xml in bounded ZIP required")
        if any(PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
               or name.startswith("\\") for name in names):
            raise ValueError("Unsafe original source ZIP path")
        if z.getinfo("meta.xml").file_size>MAX_METADATA:
            raise ValueError("Original metadata exceeds bounded safe source size")
        root=ET.fromstring(z.read("meta.xml"))
        cores=[x for x in root if local(x.tag)=="core"]
        ext=[x for x in root if local(x.tag)=="extension" and
             x.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(cores)!=1 or len(ext)!=1:
            raise ValueError("One Event core and one Occurrence extension required")
        def description(node):
            columns={};paths=[];eid=None;oid=None
            for v in node.iter():
                typ=local(v.tag)
                if typ=="field" and v.attrib.get("term") and "index" in v.attrib:
                    columns[term(v.attrib["term"])]=int(v.attrib["index"])
                elif typ=="location" and v.text:paths.append(v.text.strip())
                elif typ=="id" and "index" in v.attrib:eid=int(v.attrib["index"])
                elif typ=="coreid" and "index" in v.attrib:oid=int(v.attrib["index"])
            if len(paths)!=1 or paths[0] not in names:
                raise ValueError("Original DWCA core member path missing")
            return {
              "row_type":node.attrib.get("rowType",""),
              "member_name":paths[0],
              "terms":sorted(columns),
              "index":columns,
              "primary_event_id_index":eid,
              "foreign_event_coreid_index":oid,
              "original_delimiter":node.attrib.get("fieldsTerminatedBy",r"\t"),
              "ignoreHeaderLines":node.attrib.get("ignoreHeaderLines","0")
            }
        event=description(cores[0]);occ=description(ext[0])
        e=set(event["terms"]);o=set(occ["terms"])
        missing_e=sorted({"eventID","eventDate","island","samplingProtocol"}-e)
        missing_o=sorted({"scientificName","taxonRank","order"}-o)
        site_candidates=["locationID","parentEventID","locality","fieldNumber","eventRemarks"]
        habitat_candidates=["habitat","dynamicProperties","eventRemarks","locationRemarks","locality"]
        origin_candidates=["establishmentMeans","degreeOfEstablishment","occurrenceRemarks"]
        site_fields=[x for x in site_candidates if x in e]
        habitat_fields=[x for x in habitat_candidates if x in e]
        origin_fields=[x for x in origin_candidates if x in o]
        prerequisite=(
          not missing_e and not missing_o
          and event["row_type"].rstrip("/").endswith("/Event")
          and occ["row_type"].rstrip("/").endswith("/Occurrence")
          and event["primary_event_id_index"] is not None
          and occ["foreign_event_coreid_index"] is not None
          and len(site_fields)>0 and len(habitat_fields)>0
          and len(origin_fields)>0
        )
        return {
          "schema":"structural.slam_42forest_original_meta_only_result.v1_325",
          "status":("SLAM_HABITAT_AND_ORIGIN_METADATA_PRESENT_EVENT_VALUES_SEALED"
                    if prerequisite else
                    "TERMINAL_MISSING_ORIGINAL_EXPLICIT_HABITAT_OR_ORIGIN_SCHEMA"),
          "source_original_archive_SHA256":hashlib.sha256(source).hexdigest(),
          "source_original_archive_size_bytes":len(source),
          "source_identifier_GBIF_UUID":UUID,
          "event_metadata_schema":event,
          "occurrence_metadata_schema":occ,
          "source_original_Event_rows_published_claim":893,
          "source_original_Occurrence_rows_published_claim":14922,
          "source_original_trap_locations_published_claim":42,
          "missing_required_Event_terms":missing_e,
          "missing_required_Occurrence_terms":missing_o,
          "candidate_site_identity_Event_terms":site_fields,
          "candidate_forest_habitat_Event_terms":habitat_fields,
          "candidate_biogeographic_origin_Occurrence_terms":origin_fields,
          "ZIP_directory":[{"path":v.filename,"original_uncompressed_bytes":v.file_size,
                             "CRC32":f"{v.CRC:08x}"} for v in files],
          "actual_original_forest_type_balance_NOT_YET_ESTIMATED":True,
          "original_Event_rows_opened":0,
          "original_Occurrence_rows_opened":0,
          "raw_original_plot_species_or_habitat_values_opened":0,
          "original_BALA_PRIBES_taxon_outcomes_reopened":0,
          "GEB_scientific_HOLD":True,
          "new_confirmatory_systems":0,
          "eBird_used":False
        }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.slam_habitat_original_source_protocol.v1_325"
        or c.get("status")!="PREORIGINAL_EVENT_AND_OCCURRENCE_META_ONLY_SCHEMA_FREEZE"
        or c["source"]["source_archive_exact"]!=SOURCE
        or c["source"]["GBIF_uuid"]!=UUID):
        raise ValueError("Original SLAM source-habitat question not pre-frozen")
    result={
       "schema":"structural.slam_42forest_original_meta_only_result.v1_325",
       "status":"ORIGINAL_SOURCE_TRANSPORT_OR_META_TECHNICAL_STOP",
       "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
       "original_BALA_PRIBES_taxon_outcomes_reopened":0,
       "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-SLAM-42-forest-habitat-schema-only-v1.325"})
        with urllib.request.urlopen(req,timeout=60) as response:
            data=response.read(MAX_BYTES+1)
        result=parse_opaque(data)
    except Exception as exc:
        result["stop_type"]=type(exc).__name__
        result["stop_reason"]=str(exc)[:290]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({key:result.get(key) for key in (
       "status","source_original_archive_SHA256",
       "source_original_archive_size_bytes",
       "candidate_site_identity_Event_terms","candidate_forest_habitat_Event_terms",
       "candidate_biogeographic_origin_Occurrence_terms",
       "missing_required_Event_terms","missing_required_Occurrence_terms",
       "original_Event_rows_opened","original_Occurrence_rows_opened","stop_reason")
    },sort_keys=True))
    if result["status"]=="ORIGINAL_SOURCE_TRANSPORT_OR_META_TECHNICAL_STOP":raise SystemExit(2)
if __name__=="__main__":main()
