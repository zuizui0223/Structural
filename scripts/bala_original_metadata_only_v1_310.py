#!/usr/bin/env python3
"""Independent seven-island BALA 1.0 source META.XML ONLY.

The original Event and Occurrence source members are NEVER read here.
Records in the *published paper* (10,379 events / 63,904 occurrences) are
catalogue claims; they are not observed site/response denominators. This
preflight freezes the actual published source ZIP SHA, DWCA schema and class
roles before a separately frozen Event-only transect temporal gate.
"""
import argparse,hashlib,io,json,urllib.request,xml.etree.ElementTree as ET,zipfile
from pathlib import Path,PurePosixPath

SRC="https://ipt.gbif.pt/ipt/archive.do?r=bala_arthropods&v=1.0"
DATASET="8a4be36d-18cd-484c-b8ce-f67194cf4bac"
MAX_BYTES=7_000_000
MAX_META=320_000

def local(k):return k.rsplit("}",1)[-1]
def field(k):return k.rstrip("/").split("/")[-1].split("#")[-1]

def parse_source(blob):
    if not 0<len(blob)<=MAX_BYTES:
        raise ValueError("Original 2024 archive outside frozen source size envelope")
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        members=archive.infolist()
        names=[x.filename for x in members]
        if not names or len(names)>85 or names.count("meta.xml")!=1:
            raise ValueError("Original source missing exact single meta.xml")
        if any(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts
               or n.startswith("\\") for n in names):
            raise ValueError("Unsafe original source member")
        if archive.getinfo("meta.xml").file_size>MAX_META:
            raise ValueError("Original source meta.xml too big")
        root=ET.fromstring(archive.read("meta.xml"))
        cores=[x for x in root if local(x.tag)=="core"]
        ext=[x for x in root if local(x.tag)=="extension"
             and x.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(cores)!=1 or len(ext)!=1:
            raise ValueError("Exact Event Core and single Occurrence role required")
        def signature(e):
            data=[];terms={};id_=None;coreid=None
            for v in e.iter():
                n=local(v.tag)
                if n=="location" and v.text:data.append(v.text.strip())
                if n=="id" and "index" in v.attrib:id_=int(v.attrib["index"])
                if n=="coreid" and "index" in v.attrib:coreid=int(v.attrib["index"])
                if n=="field" and v.attrib.get("term") and "index" in v.attrib:
                    terms[field(v.attrib["term"])]=int(v.attrib["index"])
            if len(data)!=1 or data[0] not in names:
                raise ValueError("Event/Occurrence source member not in exact published ZIP")
            return {"row_type":e.attrib.get("rowType",""),
                    "source_member_name":data[0],
                    "declared_index_map":terms,
                    "declared_field_names":sorted(terms),
                    "declared_id_index":id_,"declared_coreid_index":coreid,
                    "original_delimiter":e.attrib.get("fieldsTerminatedBy",r"\t"),
                    "ignoreHeaderLines":e.attrib.get("ignoreHeaderLines","0"),
                    "source_encoding":e.attrib.get("encoding","UTF-8")}
        core=signature(cores[0]);occ=signature(ext[0])
        ec=set(core["declared_field_names"])
        oc=set(occ["declared_field_names"])
        has_source_site=bool(ec & {"locationID","locality","fieldNumber","eventRemarks","parentEventID"})
        has_taxonomic_order="order" in oc
        has_origin=bool(oc & {"establishmentMeans","degreeOfEstablishment","occurrenceRemarks"})
        required_event={"eventID","eventDate","samplingProtocol","island"}
        required_occur={"scientificName"}
        conditions={
           "event_core_role":core["row_type"].endswith("/Event"),
           "core_primary_id":core["declared_id_index"] is not None,
           "occurrence_foreign_id":occ["declared_coreid_index"] is not None,
           "island_date_method":required_event.issubset(ec),
           "author_site_key_candidates":has_source_site,
           "guild_order_field":has_taxonomic_order,
           "scientific_name":required_occur.issubset(oc),
           "taxon_origin_field_candidate":has_origin,
        }
        status=("META_ELIGIBLE_EVENT_VALUES_STILL_CLOSED"
                if all(conditions.values()) else "META_HOLD_MISSING_TEMPORAL_OR_GUILD_ROLE")
        return {"schema":"structural.bala_original_archive_metadata_result.v1_310",
           "status":status,"GBIF_uuid":DATASET,
           "original_source_sha256":hashlib.sha256(blob).hexdigest(),
           "original_source_zip_bytes":len(blob),
           "original_published_Event_rows_claimed":10379,
           "original_published_Occurrence_rows_claimed":63904,
           "event_role":core,"occurrence_role":occ,
           "role_qualifiers":conditions,
           "original_source_archive_directory":[{"path":e.filename,
                "original_member_bytes":e.file_size,
                "CRC32":f"{e.CRC:08x}"} for e in members],
           "source_Event_rows_opened":0,"source_Occurrence_rows_opened":0,
           "taxon_species_or_site_values_opened":0,
           "same_site_three_campaigns_not_yet_verified":True,
           "GEB_scientific_HOLD":True,"confirmatory_systems_admitted":0,"eBird_used":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    c=json.loads(a.protocol.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.bala_longitudinal_core_source_design.v1_310"
        or c.get("status")!="FROZEN_BEFORE_ORIGINAL_BALA_ARCHIVE_EVENT_OR_OCCURRENCE_READ"
        or c["source"]["official_archive"]!=SRC or c["source"]["GBIF_uuid"]!=DATASET):
        raise ValueError("BALA source and prospective community turnover research question not frozen")
    r={"schema":"structural.bala_original_archive_metadata_result.v1_310",
       "status":"SOURCE_OR_METADATA_TRANSPORT_STOP","source_Event_rows_opened":0,
       "source_Occurrence_rows_opened":0,"GEB_scientific_HOLD":True,
       "confirmatory_systems_admitted":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SRC,headers={"User-Agent":"Structural-BALA-v1.310-ZIP-MetaOnly/1.0"})
        with urllib.request.urlopen(req,timeout=65) as stream:
            original=stream.read(MAX_BYTES+1)
        r=parse_source(original)
    except Exception as ex:
        r["stop_type"]=type(ex).__name__;r["stop_reason"]=str(ex)[:300]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
      "status":r["status"],"original_source_sha256":r.get("original_source_sha256"),
      "zip_bytes":r.get("original_source_zip_bytes"),
      "Event_fields":r.get("event_role",{}).get("declared_field_names"),
      "Occurrence_fields":r.get("occurrence_role",{}).get("declared_field_names"),
      "source_Event_rows_opened":0,"source_Occurrence_rows_opened":0,
      "stop_reason":r.get("stop_reason")},sort_keys=True))
    if r["status"]=="SOURCE_OR_METADATA_TRANSPORT_STOP":raise SystemExit(2)
if __name__=="__main__":main()
