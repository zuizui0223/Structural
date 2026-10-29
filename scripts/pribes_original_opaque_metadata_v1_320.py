#!/usr/bin/env python3
"""PRIBES independent anthropogenic island-site source: ZIP/meta.xml ONLY.

No Darwin Core Event values, Occurrence/species/origin rows, or individual
island site identities are opened. Source-v1.3 original SHA and field roles
are frozen before any outcome. 80 Event != necessarily 80 physical sites.
"""
from __future__ import annotations
import argparse,hashlib,io,json,urllib.request,zipfile,xml.etree.ElementTree as ET
from pathlib import Path,PurePosixPath

SOURCE="https://ipt.gbif.pt/ipt/archive.do?r=pribes_arthropods&v=1.3"
UUID="0e2398ac-2430-42dd-918a-6a2eb8533ffa"
MAX_SOURCE=2_000_000
MAX_META=200_000

def local(x):return x.rsplit("}",1)[-1]
def term(x):return x.rstrip("/").split("/")[-1].split("#")[-1]

def parse_opaque(blob):
    if not 0<len(blob)<=MAX_SOURCE:
        raise ValueError("Official original PRIBES archive over 2 MB source cap")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        items=z.infolist()
        names=[v.filename for v in items]
        if len(items)>80 or names.count("meta.xml")!=1:
            raise ValueError("Unexpected original Darwin Core archive members")
        if any(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts
               or n.startswith("\\") for n in names):
            raise ValueError("Unsafe source ZIP path")
        if z.getinfo("meta.xml").file_size>MAX_META:
            raise ValueError("Source meta.xml exceeds frozen size")
        root=ET.fromstring(z.read("meta.xml"))
        cores=[x for x in root if local(x.tag)=="core"]
        exts=[x for x in root if local(x.tag)=="extension"
              and x.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(cores)!=1 or len(exts)!=1:
            raise ValueError("Original source lacks exactly one Event core and one Occurrence extension")
        def describe(node):
            path=[];terms={};idx=None;foreign=None
            for v in node.iter():
                k=local(v.tag)
                if k=="location" and v.text:path.append(v.text.strip())
                elif k=="field" and "index" in v.attrib and "term" in v.attrib:
                    terms[term(v.attrib["term"])]=int(v.attrib["index"])
                elif k=="id" and "index" in v.attrib:idx=int(v.attrib["index"])
                elif k=="coreid" and "index" in v.attrib:foreign=int(v.attrib["index"])
            if len(path)!=1 or path[0] not in names:
                raise ValueError("No actual Event or Occurrence original member")
            return {"rowType":node.attrib.get("rowType"),
                "original_data_member":path[0],
                "terms":sorted(terms),
                "field_indices":terms,
                "event_primary_id_index":idx,
                "occurrence_foreign_coreid_index":foreign,
                "delimiter":node.attrib.get("fieldsTerminatedBy",r"\t"),
                "header_skip":node.attrib.get("ignoreHeaderLines","0")}
        e=describe(cores[0]);o=describe(exts[0])
        et=set(e["terms"]);ot=set(o["terms"])
        required_e={"eventID","eventDate","island"}
        required_o={"scientificName","taxonRank","order","establishmentMeans"}
        missing_e=sorted(required_e-et)
        missing_o=sorted(required_o-ot)
        has_location=bool(et&{"locationID","locality","fieldNumber","parentEventID"})
        has_method=bool(et&{"samplingProtocol","samplingEffort","eventRemarks"})
        qualified=(e["rowType"].endswith("/Event") and
                   o["rowType"].endswith("/Occurrence") and
                   e["event_primary_id_index"] is not None and
                   o["occurrence_foreign_coreid_index"] is not None and
                   not missing_e and not missing_o and has_location and has_method)
        return {
          "schema":"structural.pribes_original_opaque_schema_result.v1_320",
          "status":"PRIBES_SOURCE_SCHEMA_ELIGIBLE_EVENT_AND_TAXON_VALUES_SEALED" if qualified
            else "PRIBES_SOURCE_SCHEMA_HOLD_BEFORE_SOURCE_SITE_VALUES",
          "original_pribes_v1_3_zip_sha256":hashlib.sha256(blob).hexdigest(),
          "original_pribes_v1_3_zip_bytes":len(blob),
          "source_Event_metadata_only":e,
          "source_Occurrence_metadata_only":o,
          "missing_required_Event_terms":missing_e,
          "missing_required_Occurrence_terms":missing_o,
          "author_site_identifier_column_exists":has_location,
          "source_method_metadata_column_exists":has_method,
          "source_80_Event_vs_79_physical_sites_discrepancy_unresolved":True,
          "ZIP_original_member_directory":[{"path":x.filename,"bytes_uncompressed":x.file_size,
              "CRC32":f"{x.CRC:08x}"} for x in items],
          "original_Event_rows_opened":0,
          "original_Occurrence_rows_opened":0,
          "source_sites_species_and_origin_labels_read":0,
          "no_BALA_original_biological_source_access":True,
          "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
        }
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    protocol=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (protocol.get("schema")!="structural.pribes_ruderal_external_source.v1_320"
        or protocol.get("status")!="FROZEN_BEFORE_OPENING_PRIBES_ORIGINAL_EVENT_OR_OCCURRENCE"
        or protocol["publication"]["official_source_archive"]!=SOURCE
        or protocol["publication"]["GBIF_uuid"]!=UUID):
        raise ValueError("Source original v1.3 and hypothesis not frozen")
    result={"schema":"structural.pribes_original_opaque_schema_result.v1_320",
        "status":"PRIBES_SOURCE_TRANSPORT_OR_SCHEMA_TECHNICAL_STOP",
        "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
        "no_BALA_original_biological_source_access":True,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-PRIBES-v1.320-meta-only"})
        with urllib.request.urlopen(req,timeout=60) as stream:blob=stream.read(MAX_SOURCE+1)
        result=parse_opaque(blob)
    except Exception as error:
        result["stop_type"]=type(error).__name__;result["stop_reason"]=str(error)[:290]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:result.get(k) for k in ("status","original_pribes_v1_3_zip_sha256",
         "original_pribes_v1_3_zip_bytes","missing_required_Event_terms",
         "missing_required_Occurrence_terms","stop_reason")},sort_keys=True))
    if result["status"]=="PRIBES_SOURCE_TRANSPORT_OR_SCHEMA_TECHNICAL_STOP":
        raise SystemExit(2)
if __name__=="__main__":main()
