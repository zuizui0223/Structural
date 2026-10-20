#!/usr/bin/env python3
"""Original 2020+ Azores PRIBES publisher Event/Occurrence schema-only intake.

Reads ZIP member names and the <meta.xml> field definitions only; NEVER opens
event.txt or occurrence.txt biological record payloads in this preflight.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

from azores_2016_dwca_structure_v1_267 import summarize_archive

URLS={
 "Pico PRIBES":"https://ipt.gbif.pt/ipt/archive.do?r=pico_vascular_plants&v=1.7",
 "Graciosa Santa Maria PRIBES":"https://ipt.gbif.pt/ipt/archive.do?r=gra_smr_vascular_plants&v=1.6",
}
MAX_BYTES=10_000_000


def inspect_publisher_archive(raw,source_label):
    if not raw or len(raw)>MAX_BYTES:
        raise ValueError("Original PRIBES source exceeds original predeclared transport cap")
    meta=summarize_archive(raw,"SOURCE_PRECHECK_ONLY")
    core=meta["core"]
    extensions=meta["extensions"]
    event=core["rowtype"].endswith("/Event")
    cand=[e for e in extensions if e["rowtype"].endswith("/Occurrence")]
    def has_field(fields,field):
        return any(str(r["term"] or "").rsplit("/",1)[-1]==field for r in fields)
    occurrence=len(cand)==1
    event_id_index=bool(event and core["record_path"])
    event_field=has_field(core["fields"],"eventDate")
    island_field=has_field(core["fields"],"island")
    name_field=bool(occurrence and has_field(cand[0]["fields"],"scientificName"))
    eligibility=all((event,event_id_index,occurrence,event_field,island_field,name_field))
    return {
        "source_label":source_label,
        "event_core":event,
        "occurrence_extension":occurrence,
        "author_has_island_field":island_field,
        "author_has_eventDate_field":event_field,
        "author_has_scientificName_field":name_field,
        "event_and_occurrence_fields_eligible":eligibility,
        "core_metadata":core,
        "occurrence_metadata":cand[0] if occurrence else None,
        "original_source_archive_members":meta["archive_member_names_and_sizes"],
        "biological_event_occurrence_rows_decoded":0,
    }


def fetch_exact(url):
    request=urllib.request.Request(url,headers={
        "User-Agent":"Structural-PRIBES-Original-DwC-Archive-Header-Only/1.0",
        "Accept":"application/zip,application/octet-stream"})
    with urllib.request.urlopen(request,timeout=60) as f:
        raw=f.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:
        raise ValueError("Original source archive over 10MB cap")
    return raw


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    cfg=json.loads(args.contract.read_text(encoding="utf-8"))
    if (cfg["schema"]!="structural.azores_modern_field_observation_cross_island_S1_protocol.v1_270"
       or cfg["status"]!="PREDECLARED_BEFORE_PICO_AND_GRACIOSA_SANTA_MARIA_BIOLOGICAL_OCCURRENCES"):
        raise ValueError("Original prospective 3-source contract not verified")
    sources=cfg["field_sources"][1:]
    if len(sources)!=2 or {x["label"] for x in sources}!=set(URLS):
        raise ValueError("Frozen original two new PRIBES source identifiers changed")
    result={
        "schema":"structural.azores_pribes_two_original_source_schema_audit.v1_270",
        "status":"SOURCE_STOP_BEFORE_NEW_PRIBES_BIOLOGY",
        "source_original_contract":str(args.contract),
        "biological_event_occurrence_rows_read":0,
        "new_field_taxon_identity_data_read":False,
        "GEB_scientific_HOLD":True,
        "eBird_used":False,
    }
    try:
        items=[]
        for src in sources:
            label=src["label"]
            if src["original_url"]!=URLS[label]:
                raise ValueError("Original GBIF PT release and URL changed")
            raw=fetch_exact(src["original_url"])
            item=inspect_publisher_archive(raw,label)
            item["sha256"]=hashlib.sha256(raw).hexdigest()
            item["bytes"]=len(raw)
            item["published_version"]=src["release_version"]
            item["source_original_url"]=src["original_url"]
            items.append(item)
        result["sources"]=items
        result["status"]=(
            "SOURCE_TWO_NEW_PRIBES_SCHEMA_VERIFIED"
            if all(x["event_and_occurrence_fields_eligible"] for x in items)
            else "SOURCE_SCHEMA_NOT_ELIGIBLE_NO_BIOLOGICAL_READ")
    except Exception as exc:
        result["stop_type"]=type(exc).__name__
        result["stop_reason"]=str(exc)[:350]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({k:result.get(k) for k in ("status","stop_reason")},sort_keys=True))
    if result["status"]!="SOURCE_TWO_NEW_PRIBES_SCHEMA_VERIFIED":
        raise SystemExit(2)


if __name__=="__main__":
    main()
