#!/usr/bin/env python3
"""BioMonI Terceira third taxon: exact spider v1.8 ZIP and meta.xml only."""
import argparse,hashlib,io,json,urllib.request,zipfile,xml.etree.ElementTree as ET
from pathlib import Path,PurePosixPath
SOURCE="https://ipt.gbif.pt/ipt/archive.do?r=spiders_macaronesia_azores&v=1.8"
UUID="6aa5ac09-2b55-4078-bd2d-ec94fb91850a"
MAX_SOURCE=500000
def _local(tag):return tag.rsplit("}",1)[-1]
def _term(t):return t.rstrip("/").split("/")[-1].split("#")[-1]
def inventory(blob):
    if not 0<len(blob)<=MAX_SOURCE:raise ValueError("Original spider archive exceeds frozen cap")
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        members=z.infolist()
        names=[x.filename for x in members]
        if len(members)>70 or not names or names.count("meta.xml")!=1:
            raise ValueError("Invalid spider source archive contents")
        for name in names:
            path=PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or name.startswith("\\"):
                raise ValueError("Unsafe spider source ZIP path")
        if z.getinfo("meta.xml").file_size>120000:
            raise ValueError("Oversized original source metadata XML")
        root=ET.fromstring(z.read("meta.xml"))
        core=[e for e in root if _local(e.tag)=="core"]
        extensions=[e for e in root if _local(e.tag)=="extension"
           and e.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(core)!=1 or len(extensions)!=1:
            raise ValueError("Unexpected Event/Occurrence source archive roles")
        def describe(e):
            terms={};loc=[];id_flag=False;coreid_flag=False
            for v in e.iter():
                tag=_local(v.tag)
                if tag=="location" and v.text:loc.append(v.text.strip())
                if tag=="field" and v.attrib.get("term") and v.attrib.get("index") is not None:
                    terms[_term(v.attrib["term"])]=int(v.attrib["index"])
                if tag=="id" and "index" in v.attrib:id_flag=True
                if tag=="coreid" and "index" in v.attrib:coreid_flag=True
            if len(loc)!=1 or loc[0] not in names:
                raise ValueError("Original source Event/Occurrence member not located")
            return {"rowType":e.attrib.get("rowType",""),
                    "terms":sorted(terms),
                    "data_member_name":loc[0],
                    "source_id_index_declared":id_flag,
                    "source_coreid_index_declared":coreid_flag,
                    "source_encoding":e.attrib.get("encoding","")}
        ce,oe=describe(core[0]),describe(extensions[0])
        need_e={"locationID","island","decimalLatitude","decimalLongitude","eventDate","samplingProtocol"}
        need_o={"scientificName","taxonRank"}
        missing_e=sorted(need_e-set(ce["terms"]))
        missing_o=sorted(need_o-set(oe["terms"]))
        valid=(ce["rowType"].endswith("/Event") and ce["source_id_index_declared"]
               and oe["source_coreid_index_declared"] and not missing_e and not missing_o)
        return {"schema":"structural.biomoni_spider_source_meta_result.v1_302",
            "status":"SPIDER_ORIGINAL_SCHEMA_ELIGIBLE_EVENT_AND_OCCURRENCE_STILL_SEALED" if valid
            else "SPIDER_SOURCE_SCHEMA_TERMINAL",
            "dataset_uuid":UUID,
            "source_zip_sha256":hashlib.sha256(blob).hexdigest(),
            "source_zip_bytes":len(blob),
            "original_Event_meta_only":ce,"original_Occurrence_meta_only":oe,
            "missing_required_Event":missing_e,"missing_required_Occurrence":missing_o,
            "zip_entries":[{"name":e.filename,"uncompressed_bytes":e.file_size,"crc":f"{e.CRC:08x}"} for e in members],
            "published_v1_8_Event_rows_unverified":423,
            "published_v1_8_Occurrence_rows_unverified":1639,
            "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
            "bio_values_or_site_names_read":0,
            "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    protocol=json.loads(args.protocol.read_text())
    if (protocol.get("schema")!="structural.biomoni_spider_third_taxon_source_opaque.v1_302"
        or protocol.get("status")!="PRE_ORIGINAL_SPIDER_BIOLOGICAL_RESPONSE_SOURCE_FREEZE"
        or protocol["published_source"]["archive"]!=SOURCE or protocol["published_source"]["source_uuid"]!=UUID):
        raise ValueError("Spider source original identity/protocol not frozen")
    result={"schema":"structural.biomoni_spider_source_meta_result.v1_302",
            "status":"SPIDER_SOURCE_TRANSPORT_STOP",
            "original_Event_rows_opened":0,"original_Occurrence_rows_opened":0,
            "bio_values_or_site_names_read":0,"GEB_scientific_HOLD":True,
            "new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-BioMonI-Spider-MetaOnly-v1.302"})
        with urllib.request.urlopen(req,timeout=60) as stream:
            blob=stream.read(MAX_SOURCE+1)
        result=inventory(blob)
    except Exception as e:
        result["stop_type"]=type(e).__name__;result["stop_reason"]=str(e)[:260]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    print(json.dumps({k:result.get(k) for k in ("status","source_zip_sha256","source_zip_bytes","missing_required_Event","missing_required_Occurrence","stop_reason")},sort_keys=True))
    if result["status"]=="SPIDER_SOURCE_TRANSPORT_STOP":raise SystemExit(2)
if __name__=="__main__":main()
