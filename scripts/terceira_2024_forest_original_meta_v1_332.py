#!/usr/bin/env python3
"""2024 Terceira stratified 10 native/10 exotic forest source META-ONLY v1.332.

Read exact original ZIP directory + meta.xml, no Event, Occurrence, plant,
arthropod identity or habitat values. A balanced original field design in
a published 2025 source is NOT itself a new ecological finding; biological
source must remain opaque until method/vertical-stratum sample gate passes.
"""
from __future__ import annotations
import argparse,hashlib,io,json,urllib.request,zipfile,xml.etree.ElementTree as ET
from pathlib import Path,PurePosixPath

ORIGINAL="https://ipt.gbif.pt/ipt/archive.do?r=azores_forest_arthropods&v=1.6"
UUID="d3580ac2-a504-44e0-8e59-de89c430924c"
MAX_BYTES=400000
MAX_META_BYTES=150000

def local(x):return x.rsplit("}",1)[-1]
def term(x):return x.rstrip("/").split("/")[-1].split("#")[-1]

def opaque_inventory(blob):
    if not 0<len(blob)<=MAX_BYTES:
        raise ValueError("Official Terceira original archive exceeds frozen source ZIP cap")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        info=z.infolist()
        names=[e.filename for e in info]
        if len(info)>80 or names.count("meta.xml")!=1:
            raise ValueError("Original 2024 source has noncanonical ZIP metadata")
        if any(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts
               or n.startswith("\\") for n in names):
            raise ValueError("Unsafe original 2024 source ZIP member path")
        if z.getinfo("meta.xml").file_size>MAX_META_BYTES:
            raise ValueError("2024 source XML exceeds frozen cap")
        root=ET.fromstring(z.read("meta.xml"))
        core=[x for x in root if local(x.tag)=="core"]
        extension=[x for x in root if local(x.tag)=="extension"
                    and x.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(core)!=1 or len(extension)!=1:
            raise ValueError("Original 2024 Event core/Occurrence extension is not one-to-one")
        def role(e):
            path=[];columns={};id_index=None;foreign_index=None
            for node in e.iter():
                t=local(node.tag)
                if t=="field" and node.attrib.get("term") and "index" in node.attrib:
                    field=term(node.attrib["term"])
                    if field in columns:
                        raise ValueError("Duplicate Darwin Core source field name")
                    columns[field]=int(node.attrib["index"])
                elif t=="location" and node.text:
                    path.append(node.text.strip())
                elif t=="id" and "index" in node.attrib:id_index=int(node.attrib["index"])
                elif t=="coreid" and "index" in node.attrib:foreign_index=int(node.attrib["index"])
            if len(path)!=1 or path[0] not in names:
                raise ValueError("Original 2024 source data member missing from ZIP")
            return {
                "rowType":e.attrib.get("rowType",""),
                "source_member_filename":path[0],
                "source_declared_term_indices":columns,
                "source_declared_terms_sorted":sorted(columns),
                "source_Event_primary_id_index":id_index,
                "source_Occurrence_foreign_id_index":foreign_index,
                "source_delimiter":e.attrib.get("fieldsTerminatedBy",r"\t"),
                "source_header_rows_to_skip":e.attrib.get("ignoreHeaderLines","0"),
            }
        e=role(core[0]);o=role(extension[0])
        ec=set(e["source_declared_terms_sorted"])
        oc=set(o["source_declared_terms_sorted"])
        req_event={"eventID","eventDate","samplingProtocol"}
        req_occ={"scientificName","taxonRank","order"}
        sites=["locationID","locality","parentEventID","fieldNumber"]
        habitats=["habitat","eventRemarks","locationRemarks","locality"]
        strata=["minimumDepthInMeters","maximumDepthInMeters","verbatimDepth",
                "samplingEffort","eventRemarks","dynamicProperties",
                "locationRemarks","fieldNumber"]
        statuses=["establishmentMeans","degreeOfEstablishment","occurrenceRemarks"]
        keys={
            "Event_core":e["rowType"].endswith("/Event"),
            "Occurrence_extension":o["rowType"].endswith("/Occurrence"),
            "original_Event_coreid":e["source_Event_primary_id_index"] is not None,
            "original_Occurrence_coreid":o["source_Occurrence_foreign_id_index"] is not None,
            "original_Event_method_date":req_event.issubset(ec),
            "original_plot_identifier":any(x in ec for x in sites),
            "original_explicit_forest_habitat":any(x in ec for x in habitats),
            "original_vertical_or_effort_meta":any(x in ec for x in strata),
            "original_taxon_name_rank_order":req_occ.issubset(oc),
            "original_biogeographic_origin":any(x in oc for x in statuses),
        }
        return {
            "schema":"structural.terceira_2024_source_opaque_result.v1_332",
            "status":("TERCEIRA_2024_NATIVE_EXOTIC_SOURCE_META_ELIGIBLE_ALL_VALUES_CLOSED"
                      if all(keys.values()) else
                      "TERMINAL_2024_ORIGINAL_VERTICAL_HABITAT_OR_ORIGIN_SCHEMA"),
            "original_DwCA_archive_SHA256":hashlib.sha256(blob).hexdigest(),
            "original_DwCA_archive_bytes":len(blob),
            "original_dataset_UUID":UUID,
            "original_version":"1.6",
            "original_published_Event_n":326,
            "original_published_Occurrence_n":2399,
            "original_published_independent_plot_n":20,
            "original_published_native_plot_n":10,
            "original_published_exotic_plot_n":10,
            "Event_source_meta":e,
            "Occurrence_source_meta":o,
            "required_meta_gate_checks":keys,
            "author_site_meta_field_candidates":[x for x in sites if x in ec],
            "author_forest_habitat_meta_field_candidates":[x for x in habitats if x in ec],
            "author_vertical_stratum_meta_field_candidates":[x for x in strata if x in ec],
            "author_origin_meta_field_candidates":[x for x in statuses if x in oc],
            "original_ZIP_directory":[{"member":v.filename,"uncompressed_bytes":v.file_size,
                                       "CRC32":f"{v.CRC:08x}"} for v in info],
            "original_Event_rows_opened":0,
            "original_Occurrence_rows_opened":0,
            "original_species_and_forest_habitat_values_opened":0,
            "older_source_biological_rows_reopened":0,
            "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
        }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    contract=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (contract.get("schema")!="structural.terceira2024_stratified_forest_source.v1_332"
        or contract.get("status")!="PRE_ORIGINAL_2024_HABITAT_EVENT_AND_SPECIES_SOURCE_META_FREEZE"
        or contract["original_2024_source"]["official_archive"]!=ORIGINAL
        or contract["original_2024_source"]["source_GBIF_UUID"]!=UUID):
        raise ValueError("Unfrozen 2024 original forest stratification source and endpoint")
    result={
        "schema":"structural.terceira_2024_source_opaque_result.v1_332",
        "status":"TERCEIRA_2024_SOURCE_TRANSPORT_OR_META_TECHNICAL_STOP",
        "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
        "older_source_biological_rows_reopened":0,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        req=urllib.request.Request(ORIGINAL,headers={
            "User-Agent":"Structural-Terceira2024-NativeExotic-Forest-MetaONLY-v1.332"})
        with urllib.request.urlopen(req,timeout=65) as f:raw=f.read(MAX_BYTES+1)
        result=opaque_inventory(raw)
    except Exception as exc:
        result["stop_type"]=type(exc).__name__
        result["stop_reason"]=str(exc)[:300]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "original_source_SHA256":result.get("original_DwCA_archive_SHA256"),
        "original_source_bytes":result.get("original_DwCA_archive_bytes"),
        "source_site_fields":result.get("author_site_meta_field_candidates"),
        "source_habitat_fields":result.get("author_forest_habitat_meta_field_candidates"),
        "source_vertical_fields":result.get("author_vertical_stratum_meta_field_candidates"),
        "source_origin_fields":result.get("author_origin_meta_field_candidates"),
        "original_species_rows_opened":0,
        "stop_reason":result.get("stop_reason")
    },sort_keys=True))
    if result["status"]=="TERCEIRA_2024_SOURCE_TRANSPORT_OR_META_TECHNICAL_STOP":
        raise SystemExit(2)
if __name__=="__main__":main()
