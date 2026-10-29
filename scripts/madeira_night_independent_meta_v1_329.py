#!/usr/bin/env python3
"""v1.329 Madeira LIFE Natura@night v1.1 original DwCA META-ONLY.

No original sampling Event or species/biogeographic origin rows read.
Use exact frozen June 2026 source v1.1 to prevent latest-version drift.
Intended test is independent archipelago native vs mixed/exotic forest
endemism, NOT restating published inventory of endemic moth species.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath

ORIGINAL="https://ipt.gbif.pt/ipt/archive.do?r=arthropod_madeira_life_naturaatnight&v=1.1"
UUID="115de336-e519-4fc8-9a60-28e601ce2876"
MAX_BYTES=400000
MAX_META=120000

def local(t):
    return t.rsplit("}",1)[-1]

def last_term(t):
    return t.rstrip("/").split("/")[-1].split("#")[-1]

def inspect_meta_only(blob):
    if not 0<len(blob)<=MAX_BYTES:
        raise ValueError("Original Madeira source ZIP over 400 kB pre-fixed cap")
    with zipfile.ZipFile(io.BytesIO(blob)) as original:
        items=original.infolist()
        names=[v.filename for v in items]
        if not 0<len(names)<=80 or names.count("meta.xml")!=1:
            raise ValueError("Unexpected original source member count or missing meta.xml")
        if any(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts
               or n.startswith("\\") for n in names):
            raise ValueError("Unexpected path traversal in original source archive")
        if original.getinfo("meta.xml").file_size>MAX_META:
            raise ValueError("Original meta.xml larger than frozen bound")
        root=ET.fromstring(original.read("meta.xml"))
        cores=[v for v in root if local(v.tag)=="core"]
        extensions=[v for v in root if local(v.tag)=="extension"
                    and v.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(cores)!=1 or len(extensions)!=1:
            raise ValueError("Original source must have exactly one Event core and one Occurrence extension")
        def describe(node):
            fields={}
            locations=[]
            id_key=None
            core_id_key=None
            for v in node.iter():
                t=local(v.tag)
                if t=="field" and "index" in v.attrib and "term" in v.attrib:
                    field=last_term(v.attrib["term"])
                    if field in fields:
                        raise ValueError("Ambiguous original source duplicate field term")
                    fields[field]=int(v.attrib["index"])
                elif t=="location" and v.text:
                    locations.append(v.text.strip())
                elif t=="id" and "index" in v.attrib:
                    id_key=int(v.attrib["index"])
                elif t=="coreid" and "index" in v.attrib:
                    core_id_key=int(v.attrib["index"])
            if len(locations)!=1 or locations[0] not in names:
                raise ValueError("Original Event/Occurrence data member absent")
            return {
                "source_member_path":locations[0],
                "rowType":node.attrib.get("rowType",""),
                "source_field_term_indices":fields,
                "source_field_term_names":sorted(fields),
                "primary_Event_coreid_index":id_key,
                "Occurrence_foreign_coreid_index":core_id_key,
                "original_delimiter":node.attrib.get("fieldsTerminatedBy",r"\t"),
                "original_header_rows_to_skip":node.attrib.get("ignoreHeaderLines","0"),
            }
        e=describe(cores[0])
        o=describe(extensions[0])
        event=set(e["source_field_term_names"])
        occ=set(o["source_field_term_names"])
        e_req={"eventID","eventDate","samplingProtocol"}
        o_req={"scientificName","taxonRank","order"}
        site_candidates=["locationID","parentEventID","locality","fieldNumber"]
        habitat_candidates=["habitat","dynamicProperties","eventRemarks","locality"]
        origin_candidates=["establishmentMeans","degreeOfEstablishment","occurrenceRemarks"]
        site=[x for x in site_candidates if x in event]
        habitat=[x for x in habitat_candidates if x in event]
        origin=[x for x in origin_candidates if x in occ]
        checks={
            "Event_core_role":e["rowType"].endswith("/Event"),
            "Occurrence_extension_role":o["rowType"].endswith("/Occurrence"),
            "Event_primary_id_index_present":e["primary_Event_coreid_index"] is not None,
            "Occurrence_foreign_id_index_present":o["Occurrence_foreign_coreid_index"] is not None,
            "Event_date_and_method_fields_present":e_req.issubset(event),
            "source_physical_site_identity_available":bool(site),
            "source_forest_habitat_description_available":bool(habitat),
            "taxon_order_rank_and_scientificName_present":o_req.issubset(occ),
            "source_origin_field_available":bool(origin),
        }
        return {
            "schema":"structural.madeira_night_original_source_meta_receipt.v1_329",
            "status":"ORIGINAL_MADEIRA_FOREST_HABITAT_ORIGIN_SCHEMA_POSSIBLE_VALUES_SEALED"
                if all(checks.values()) else
                "TERMINAL_MADEIRA_HABITAT_OR_ORIGIN_SOURCE_SCHEMA_INSUFFICIENT",
            "original_archival_sha256":hashlib.sha256(blob).hexdigest(),
            "original_archival_bytes":len(blob),
            "original_fixed_dataset_UUID":UUID,
            "source_original_publication_version":"1.1",
            "published_claimed_original_Event_rows":134,
            "published_claimed_original_Occurrence_rows":1939,
            "published_conflicting_physical_site_claims":[47,48],
            "original_Event_source_schema":e,
            "original_Occurrence_source_schema":o,
            "source_schema_qualification":checks,
            "candidate_original_site_fields":site,
            "candidate_original_habitat_fields":habitat,
            "candidate_original_biogeographic_origin_fields":origin,
            "source_original_ZIP_directory":[
                {"path":item.filename,"source_uncompressed_bytes":item.file_size,
                 "CRC32":f"{item.CRC:08x}"} for item in items],
            "original_Event_rows_opened":0,
            "original_Occurrence_rows_opened":0,
            "original_species_and_habitat_values_inspected":0,
            "Azores_original_species_sources_reopened":0,
            "GEB_scientific_HOLD":True,
            "new_confirmatory_systems":0,
            "eBird_used":False,
        }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    contract=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (contract.get("schema")!="structural.madeira_night_independent_source_meta.v1_329"
        or contract.get("status")!="FROZEN_PRE_ORIGINAL_MADEIRA_EVENT_OR_SPECIES_READ"
        or contract["new_source"]["original_v1_1_archive"]!=ORIGINAL
        or contract["new_source"]["dataset_uuid"]!=UUID):
        raise ValueError("Original Madeira ecological hypothesis, data version and source frozen contract mismatch")
    result={
        "schema":"structural.madeira_night_original_source_meta_receipt.v1_329",
        "status":"ORIGINAL_MADEIRA_META_TRANSPORT_OR_SOURCE_TECHNICAL_STOP",
        "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
        "Azores_original_species_sources_reopened":0,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False,
    }
    try:
        req=urllib.request.Request(ORIGINAL,headers={
            "User-Agent":"Structural-Madeira-Original-v1.1-MetaONLY-v1.329"})
        with urllib.request.urlopen(req,timeout=65) as response:
            blob=response.read(MAX_BYTES+1)
        result=inspect_meta_only(blob)
    except Exception as error:
        result["stop_type"]=type(error).__name__
        result["stop_reason"]=str(error)[:300]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:result.get(k) for k in (
        "status","original_archival_sha256","original_archival_bytes",
        "candidate_original_site_fields","candidate_original_habitat_fields",
        "candidate_original_biogeographic_origin_fields",
        "original_Event_rows_opened","original_Occurrence_rows_opened","stop_reason")
    },sort_keys=True))
    if result["status"]=="ORIGINAL_MADEIRA_META_TRANSPORT_OR_SOURCE_TECHNICAL_STOP":
        raise SystemExit(2)

if __name__=="__main__":
    main()
