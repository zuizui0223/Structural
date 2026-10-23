#!/usr/bin/env python3
"""Source-only authentic MOVECLIM 2013 four-island 58-plot sampling archive.

Never decode or enumerate any Event or Occurrence *record* before biological
design; only meta.xml, EML file descriptors, and archive member sizes.
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
from azores_2016_dwca_structure_v1_267 import summarize_archive

SCHEMA="structural.moveclim2013_source_schema.v1_277"
SOURCE_URL="https://ipt.gbif.pt/ipt/archive.do?r=plants_plots_moveclim&v=1.6"
MAX_BYTES=15_000_000

def inspect_moveclim(raw):
    a=summarize_archive(raw,"f92047fa-f2cb-445d-9a93-546d637b2820")
    core=a["core"]
    extensions=a["extensions"]
    if not core["rowtype"].endswith("/Event"):
        raise ValueError("Expected 2013 field sampling Event core")
    occurrence=[x for x in extensions if x["rowtype"].endswith("/Occurrence")]
    if len(occurrence)!=1:
        raise ValueError("Expected exactly one Occurrence extension")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        root=ET.fromstring(z.read("meta.xml"))
    core_nodes=[x for x in root if x.tag.endswith("}core") or x.tag=="core"]
    ext_nodes=[x for x in root if x.tag.endswith("}extension") or x.tag=="extension"]
    if len(core_nodes)!=1 or len(ext_nodes)!=1:
        raise ValueError("Unexpected original author Event/Occurrence file schema")
    ids=[x.attrib.get("index") for x in core_nodes[0] if x.tag.endswith("}id") or x.tag=="id"]
    coreids=[x.attrib.get("index") for x in ext_nodes[0] if x.tag.endswith("}coreid") or x.tag=="coreid"]
    if ids!=["0"] or coreids!=["0"]:
        raise ValueError("Original author Event ID and Occurrence coreid join mismatch")
    return {**a,
        "has_author_event_occurrence_coreid_keys":True,
        "source_event_or_occurrence_records_scored":0,
        "biological_elevation_and_plant_cover_values_opened":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    cfg=json.loads(args.contract.read_text(encoding="utf-8"))
    if cfg.get("schema")!="structural.moveclim2013_azores_original_source_preflight.v1_277":
        raise ValueError("Frozen 2013 independent vegetation source protocol mismatch")
    if cfg.get("status")!="PUBLISHED_SOURCE_SCHEMA_ONLY_BEFORE_MOVECLIM_SPECIES_OBSERVATIONS":
        raise ValueError("Original archive endpoint/source access not in schema-only stage")
    src=cfg["source"]
    if src["original_url"]!=SOURCE_URL or src["version"]!="1.6":
        raise ValueError("Prospective publisher version or URL changed")
    out={
        "schema":SCHEMA,
        "source_publisher":src["provider"],
        "source_url":SOURCE_URL,
        "source_declared_event_core_rows":src["declared_event_core_rows"],
        "source_declared_occurrence_extension_rows":src["declared_occurrence_extension_rows"],
        "source_declared_independent_plots":src["declared_independent_plots"],
        "status":"SOURCE_STOP_NO_ECOLOGICAL_OBSERVATIONS",
        "source_biological_record_bytes_read":0,
        "source_event_or_occurrence_records_scored":0,
        "original_CSIC_loss_cases_S2_S3_S4_unopened":True,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }
    try:
        req=urllib.request.Request(SOURCE_URL,headers={
            "User-Agent":"Structural-Azores-MOVECLIM-2013-field-schema-audit/1.0",
            "Accept":"application/zip,application/octet-stream,*/*"})
        with urllib.request.urlopen(req,timeout=60) as r:
            raw=r.read(MAX_BYTES+1)
        if len(raw)>MAX_BYTES:
            raise ValueError("Original 2013 source greater than frozen download cap")
        out["source_sha256"]=hashlib.sha256(raw).hexdigest()
        out["source_download_bytes"]=len(raw)
        out["schema"]=inspect_moveclim(raw)
        out["status"]="AUTHOR_2013_PLOT_SOURCE_SCHEMAS_VERIFIED"
    except Exception as e:
        out["stop_type"]=type(e).__name__
        out["stop_reason"]=str(e)[:420]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":out["status"],"download_bytes":out.get("source_download_bytes"),
        "archive_sha256":out.get("source_sha256"),
        "core":out.get("schema",{}).get("core",{}).get("rowtype"),
        "extension_count":len(out.get("schema",{}).get("extensions",[])),
        "stop_reason":out.get("stop_reason")},sort_keys=True))
    if out["status"]!="AUTHOR_2013_PLOT_SOURCE_SCHEMAS_VERIFIED":
        raise SystemExit(2)

if __name__=="__main__":
    main()
