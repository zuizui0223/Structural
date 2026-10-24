#!/usr/bin/env python3
"""v1.297 two independent BioMonI original ZIP meta.xml inventory ONLY.

Never opens Event values, woody plant shoot occurrences, beetle species or
specimen counts. Site-level crosswalk and any taxonomic ecology are separate
stages, after original beetle SHA-256 and both source identities are frozen.
"""
from __future__ import annotations
import argparse,hashlib,io,json,urllib.request,xml.etree.ElementTree as ET,zipfile
from pathlib import Path,PurePosixPath

SOURCES={
 "woody":{
  "url":"https://ipt.gbif.pt/ipt/archive.do?r=biomoni_trees&v=1.7",
  "uuid":"eab982cf-81df-4d08-b9f4-c2f5c56b8ad3",
  "sha":"4574d02727654ec5a319f6d1218ff9243080b0128c517d01c905065cbefd6f82"
 },
 "beetle":{
  "url":"https://ipt.gbif.pt/ipt/archive.do?r=biomoni_beetles&v=1.3",
  "uuid":"bd42f57d-c7c2-4b59-a12c-550e01b2ebcc",
  "sha":None
 }
}
MAX_ZIP=500_000
MAX_META=120_000

def local(s):return s.rsplit("}",1)[-1]
def term(s):return s.rstrip("/").split("/")[-1].split("#")[-1]

def schema_only(archive,source):
    if len(archive)>MAX_ZIP or not archive:
        raise ValueError("Frozen original source bytes cap or empty file")
    digest=hashlib.sha256(archive).hexdigest()
    if SOURCES[source]["sha"] and digest!=SOURCES[source]["sha"]:
        raise ValueError("Original frozen woody-source SHA mismatch")
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        entries=z.infolist()
        if not entries or len(entries)>65:
            raise ValueError("Suspicious ZIP entry count")
        names=[e.filename for e in entries]
        if any(PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts or n.startswith("\\")
               for n in names):
            raise ValueError("Unsafe original archive path")
        if names.count("meta.xml")!=1 or z.getinfo("meta.xml").file_size>MAX_META:
            raise ValueError("Single small source meta.xml required")
        root=ET.fromstring(z.read("meta.xml"))
        cores=[v for v in root if local(v.tag)=="core"]
        extensions=[v for v in root if local(v.tag)=="extension" and
                    v.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(cores)!=1 or len(extensions)!=1:
            raise ValueError("Unexpected Event/Occurrence original archive roles")
        def parse(node):
            roles={"rowType":node.attrib.get("rowType",""),
                   "encoding":node.attrib.get("encoding",""),
                   "fieldsTerminatedBy":node.attrib.get("fieldsTerminatedBy",""),
                   "ignoreHeaderLines":node.attrib.get("ignoreHeaderLines","0"),
                   "terms":[],"field_indices":{},"primary_id_index":None,
                   "coreid_index":None,"data_member":[]}
            for v in node.iter():
                tag=local(v.tag)
                if tag=="id":roles["primary_id_index"]=v.attrib.get("index")
                elif tag=="coreid":roles["coreid_index"]=v.attrib.get("index")
                elif tag=="location" and v.text:roles["data_member"].append(v.text.strip())
                elif tag=="field" and "term" in v.attrib and "index" in v.attrib:
                    roles["field_indices"][term(v.attrib["term"])]=int(v.attrib["index"])
            roles["terms"]=sorted(roles["field_indices"])
            if len(roles["data_member"])!=1 or roles["data_member"][0] not in names:
                raise ValueError("Original data member location missing")
            return roles
        event=parse(cores[0]);occ=parse(extensions[0])
        if not event["rowType"].rstrip("/").endswith("/Event"):
            raise ValueError("Original core is not Event")
        required_event={"locationID","island"}
        required_occ={"scientificName","establishmentMeans"}
        missing_e=sorted(required_event-set(event["terms"]))
        missing_o=sorted(required_occ-set(occ["terms"]))
        complete=(event["primary_id_index"] is not None and occ["coreid_index"] is not None
                  and not missing_e and not missing_o)
        return {
          "source_id":source,
          "original_zip_sha256":digest,
          "original_zip_bytes":len(archive),
          "original_Event_meta_only":event,
          "original_Occurrence_meta_only":occ,
          "missing_Event_terms":missing_e,
          "missing_Occurrence_terms":missing_o,
          "response_opaque_join_schema_qualified":complete,
          "zip_member_directory":[{"member":e.filename,"uncompressed_bytes":e.file_size,
                                   "CRC32":f"{e.CRC:08x}"} for e in entries],
          "meta_xml_uncompressed_bytes":z.getinfo("meta.xml").file_size,
          "Event_rows_opened":0,"Occurrence_rows_opened":0,
          "site_labels_opened":0,"taxa_and_abundances_opened":0,
        }

def inventory(sources):
    if set(sources)!=set(SOURCES):
        raise ValueError("Both originally distinct taxa source blobs required")
    two={i:schema_only(sources[i],i) for i in ("woody","beetle")}
    eligible=all(v["response_opaque_join_schema_qualified"] for v in two.values())
    return {
      "schema":"structural.biomoni_colocated_opaque_metadata_result.v1_297",
      "status":"TWO_SOURCE_META_QUALIFIED_SITE_VALUES_UNOPENED" if eligible
         else "TERMINAL_MISSING_SAME_SITE_SOURCE_SCHEMA_BEFORE_RESPONSES",
      "sources":two,
      "potential_exact_shared_Terceira_plot_count_from_papers_only":10,
      "actual_original_site_match_scored":False,
      "eligible_to_freeze_event_only_exact_crosswalk":eligible,
      "biological_cross_taxon_concordance_scored":False,
      "original_biological_Event_rows_opened":0,
      "original_plant_Occurrence_rows_opened":0,
      "original_beetle_Occurrence_rows_opened":0,
      "original_source_identity_names_exported":False,
      "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.biomoni_colocated_cross_taxon_source_gate.v1_297"
        or c["status"]!="PRE_BIOLOGICAL_RESPONSE_TWO_SOURCE_FREEZE"
        or any(c["sources"][i]["original_archive"]!=SOURCES[i]["url"] for i in SOURCES)):
        raise ValueError("Cross-taxon sources not frozen")
    result={"schema":"structural.biomoni_colocated_opaque_metadata_result.v1_297",
            "status":"TERMINAL_SOURCE_TRANSPORT_OR_SCHEMA",
            "original_biological_Event_rows_opened":0,
            "original_plant_Occurrence_rows_opened":0,
            "original_beetle_Occurrence_rows_opened":0,
            "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        original={}
        for taxon,pinned in SOURCES.items():
            req=urllib.request.Request(pinned["url"],headers={
                  "User-Agent":"Structural-BioMonI-Paired-Taxa-Meta-Only-v1.297/1.0"})
            with urllib.request.urlopen(req,timeout=55) as response:
                original[taxon]=response.read(MAX_ZIP+1)
        result=inventory(original)
    except Exception as e:
        result["stop_type"]=type(e).__name__;result["stop_reason"]=str(e)[:300]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
      "status":result["status"],
      "beetle_sha256":result.get("sources",{}).get("beetle",{}).get("original_zip_sha256"),
      "woody_sha256":result.get("sources",{}).get("woody",{}).get("original_zip_sha256"),
      "beetle_event_fields":result.get("sources",{}).get("beetle",{}).get("original_Event_meta_only",{}).get("terms"),
      "woody_event_fields":result.get("sources",{}).get("woody",{}).get("original_Event_meta_only",{}).get("terms"),
      "site_rows_opened":0,"plant_beetle_species_rows_opened":0,
      "stop_reason":result.get("stop_reason")},sort_keys=True))
    if result["status"]=="TERMINAL_SOURCE_TRANSPORT_OR_SCHEMA":raise SystemExit(2)

if __name__=="__main__":main()
