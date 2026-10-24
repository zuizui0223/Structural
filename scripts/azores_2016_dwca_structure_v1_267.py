#!/usr/bin/env python3
"""University of Azores 2016 GBIF IPT Darwin Core Archive SOURCE SCHEMA only.

The biological taxon/distribution files inside the ZIP must NEVER be opened
by this preflight. Only the ZIP directory and 'meta.xml' are parsed.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

SCHEMA="structural.azores2016_dwca_schema_audit.v1_267"
DWCA_URL="https://ipt.gbif.pt/ipt/archive.do?r=uac_checklist_acores&v=1.2"
MAX_BYTES=25_000_000
MAX_UNCOMPRESSED=150_000_000


def xml_local(tag):
    return str(tag).rsplit("}",1)[-1]


def direct_children(parent,tag):
    return [x for x in parent if xml_local(x.tag)==tag]


def first_child(parent,tag):
    children=direct_children(parent,tag)
    return children[0] if children else None


def archive_table(section, allnames):
    files=first_child(section,"files")
    locations=[] if files is None else [
        (x.text or "").strip() for x in direct_children(files,"location")
    ]
    if len(locations)!=1 or locations[0] not in allnames:
        raise ValueError("Original meta.xml references a missing or ambiguous table path")
    path=locations[0]
    fields=[]
    for item in list(section):
        kind=xml_local(item.tag)
        if kind=="field":
            fields.append({"index":item.attrib.get("index"),
                           "term":item.attrib.get("term"),
                           "default":item.attrib.get("default")})
    return {
        "rowtype":section.attrib.get("rowType",""),
        "record_path":path,
        "encoding":section.attrib.get("encoding",""),
        "fields_terminated_by":section.attrib.get("fieldsTerminatedBy",""),
        "lines_terminated_by":section.attrib.get("linesTerminatedBy",""),
        "ignore_header_lines":section.attrib.get("ignoreHeaderLines",""),
        "fields":fields,
        "table_zip_member_bytes":allnames[path]
    }


def summarize_archive(raw,expected_gbif_uuid):
    if len(raw)>MAX_BYTES or not raw.startswith(b"PK\x03\x04"):
        raise ValueError("Source archive exceeds frozen byte cap or is not a DwC-A ZIP")
    try:
        z=zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as e:
        raise ValueError("Source ZIP truncated/corrupt") from e
    with z:
        by_name={info.filename:info.file_size for info in z.infolist()}
        if "meta.xml" not in by_name:
            raise ValueError("Original Darwin Core Archive lacks required meta.xml")
        if sum(by_name.values())>MAX_UNCOMPRESSED:
            raise ValueError("Original source is over compressed expansion limit")
        if len(by_name)!=len(z.infolist()):
            raise ValueError("Duplicated archive member names")
        if any("../" in x or x.startswith("/") for x in by_name):
            raise ValueError("Untrusted path in source archive")
        if by_name["meta.xml"]>1_000_000:
            raise ValueError("Original meta.xml larger than frozen metadata limit")
        try:
            xml=ET.fromstring(z.read("meta.xml"))
        except (ET.ParseError,zipfile.BadZipFile) as e:
            raise ValueError("Malformed original DwC-A meta.xml") from e
        if xml_local(xml.tag)!="archive":
            raise ValueError("Source metadata root is not Darwin Core Archive")
        cores=direct_children(xml,"core")
        if len(cores)!=1:
            raise ValueError("IPT source must declare exactly one Darwin Core table")
        core=archive_table(cores[0],by_name)
        extensions=[archive_table(x,by_name) for x in direct_children(xml,"extension")]
        table_paths=[core["record_path"]]+[x["record_path"] for x in extensions]
        if len(set(table_paths))!=len(table_paths):
            raise ValueError("Source biological table referenced twice")
        island_hints=("island","locality","location","highergeography")
        extensions_matching=[
            x["record_path"] for x in extensions
            if ("distribution" in x["rowtype"].lower() or
                any(any(w in str(v.get("term") or "").lower() for w in island_hints)
                    for v in x["fields"]))
        ]
        return {
            "expected_source_gbif_dataset_uuid":expected_gbif_uuid,
            "archive_member_names_and_sizes":[
                {"file":path,"uncompressed_bytes":by_name[path]}
                for path in sorted(by_name)
            ],
            "core":core,
            "extensions":extensions,
            "potential_island_distribution_extension":bool(extensions_matching),
            "possible_distribution_extension_paths":extensions_matching,
            "any_island_core_field":any(
                any(w in str(f.get("term") or "").lower() for w in island_hints)
                for f in core["fields"]),
            "source_taxon_distribution_rows_decoded":0,
            "source_biological_record_bytes_read":0,
            "ecological_status":"PRE_RESPONSE_SCHEMA_ONLY_NOT_AN_ISLAND_INCIDENT_MATRIX",
        }


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contract",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    contract=json.loads(args.contract.read_text(encoding="utf8"))
    if contract.get("schema")!="structural.azores_2016_island_checklist_source_preflight.v1_267":
        raise ValueError("Expected frozen original 2016 provider/source contract missing")
    src=contract["source"]
    if src["exact_original_dwca_url"]!=DWCA_URL:
        raise ValueError("2016 exact original University of Azores source changed")
    output={
        "schema":SCHEMA,
        "status":"SOURCE_TRANSPORT_STOP_BEFORE_RESPONSE_VALUES",
        "original_source_url":DWCA_URL,
        "published_version":src["version"],
        "pub_date":src["publication_date"],
        "expected_gbif_uuid":src["gbif_dataset_uuid"],
        "source_extirpation_response_rows_read":0,
        "GEB_scientific_HOLD":True,
        "eBird_used":False,
    }
    try:
        request=urllib.request.Request(DWCA_URL,headers={
            "User-Agent":"Structural-Azores-2016-Source-Schema-Audit/1.0",
            "Accept":"application/zip,application/octet-stream"})
        with urllib.request.urlopen(request,timeout=55) as response:
            raw=response.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:
            raise ValueError("Original archive exceeded declared maximum")
        output["archive_sha256"]=hashlib.sha256(raw).hexdigest()
        output["archive_bytes"]=len(raw)
        output["archive"]=summarize_archive(raw,src["gbif_dataset_uuid"])
        output["status"]="ORIGINAL_IPT_DWCA_SCHEMAS_READ"
    except Exception as exc:
        output["stop_error_type"]=type(exc).__name__
        output["stop_reason"]=str(exc)[:350]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(output,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    print(json.dumps({
        "status":output["status"],
        "archive_bytes":output.get("archive_bytes"),
        "source_schema_extension_count":len(output.get("archive",{}).get("extensions",[])),
        "reason":output.get("stop_reason"),
        "source_biological_records_opened":0},sort_keys=True))
    if output["status"]!="ORIGINAL_IPT_DWCA_SCHEMAS_READ":
        raise SystemExit(2)


if __name__=="__main__":
    main()
