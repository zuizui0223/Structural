#!/usr/bin/env python3
"""v1.286 ForestEco2: Event-file-only original field-plot structure qualification.

No original Occurrence data, species names, status, plot responses, S1 workbook,
or model predictions are read here. Event habitat/island/site IDs are used
only to freeze 90 independently keyed survey plots before potential scoring.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,urllib.request,xml.etree.ElementTree as ET,zipfile
from collections import Counter
from pathlib import Path
from foresteco2_opaque_original_schema_v1_285 import (
    SOURCE, UUID, check_foresteco_schema
)

SOURCE_SHA="11d87393d716672f9765ed479341f39605c732def3333caaae16095b5008636a"

def _local(t): return t.rsplit("}",1)[-1]
def _term(uri): return uri.rstrip("/").split("/")[-1].split("#")[-1]
def _norm(s): return " ".join(str(s or "").strip().casefold().replace("_"," ").replace("-"," ").split())

def _read_author_event_only(archive):
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        core=next(x for x in root if _local(x.tag)=="core")
        fmap={}
        id_index=None
        name=None
        for item in core.iter():
            tag=_local(item.tag)
            if tag=="field" and "term" in item.attrib and "index" in item.attrib:
                fmap[_term(item.attrib["term"])]=int(item.attrib["index"])
            elif tag=="id" and "index" in item.attrib:
                id_index=int(item.attrib["index"])
            elif tag=="location" and item.text:
                name=item.text.strip()
        if not name or id_index is None:
            raise ValueError("Missing original author Event member or primary ID")
        need={"eventID","locationID","island","habitat","eventDate"}
        if not need.issubset(fmap):
            raise ValueError("Required original Event role field missing")
        delimiter_raw=core.attrib.get("fieldsTerminatedBy",r"\t")
        delimiter=delimiter_raw.replace(r"\t","\t")
        if len(delimiter)!=1:
            raise ValueError("Unsupported original Event delimiter")
        ignored=int(core.attrib.get("ignoreHeaderLines","0"))
        if ignored<0 or ignored>2:
            raise ValueError("Unexpected Event header count")
        with z.open(name) as raw:
            with io.TextIOWrapper(raw,encoding="utf-8-sig",newline="") as stream:
                rdr=csv.reader(stream,delimiter=delimiter)
                for _ in range(ignored):next(rdr,None)
                out=[]
                for row in rdr:
                    if not row or not any(row):continue
                    if any(i>=len(row) for i in (id_index,*[fmap[f] for f in need])):
                        raise ValueError("Short original source Event row")
                    record={k:row[v] for k,v in fmap.items() if v<len(row)}
                    record["source_coreid"]=row[id_index]
                    out.append(record)
                return out

def audit_event_grid(events, protocol):
    expected=protocol["required_rows"]
    if len(events)!=expected:
        raise ValueError(f"Original Event frame {len(events)} differs from prospectively fixed {expected}; published methods conflict is not resolved by retuning")
    island_vocab={_norm(v):name for name,vals in protocol["frozen_group_definitions"]["islands"].items() for v in vals}
    habitat_vocab={_norm(v):name for name,vals in protocol["frozen_group_definitions"]["habitat"].items() for v in vals}
    grid=Counter();years=Counter();units=Counter();seen_ids=set();seen_sites=set()
    for row in events:
        eid=str(row.get("eventID","")).strip()
        core=str(row.get("source_coreid","")).strip()
        loc=str(row.get("locationID","")).strip()
        island=island_vocab.get(_norm(row.get("island")))
        habitat=habitat_vocab.get(_norm(row.get("habitat")))
        if not eid or not core or not loc or island is None or habitat is None:
            raise ValueError("Missing original ID or unknown pre-frozen island/habitat label")
        if eid in seen_ids or core in seen_ids:
            # Event ID may equal core ID: require uniqueness between rows, not across roles.
            if eid in seen_ids and core!=eid:
                raise ValueError("Duplicate Event identity")
        if ("EVENT",eid) in seen_ids or ("CORE",core) in seen_ids:
            raise ValueError("Duplicate original Event/core IDs")
        seen_ids.add(("EVENT",eid));seen_ids.add(("CORE",core))
        if (island,loc) in seen_sites:
            raise ValueError("Duplicate original author locationID within island")
        seen_sites.add((island,loc))
        date=str(row.get("eventDate","")).strip()
        if date[:4] not in ("2017","2018"):
            raise ValueError("Event outside frozen 2017-2018 source year domain")
        years[date[:4]]+=1
        grid[(island,habitat)]+=1
        area=str(row.get("sampleSizeValue","")).strip()
        if area:
            try:v=float(area)
            except ValueError:
                raise ValueError("Non numeric original Event sample size")
            if not math.isfinite(v) or abs(v-100.0)>1e-7:
                raise ValueError("Original plot size not the frozen 100 square meters")
            units["numeric_sample_area_100m2"]+=1
        else:units["source_area_unspecified"]+=1
    for island in ("Pico","São Miguel","Terceira"):
        if sum(grid[(island,h)] for h in ("NF","EW","PF"))!=30:
            raise ValueError("Island does not have 30 original plots")
        for h in ("NF","EW","PF"):
            if grid[(island,h)]!=10:
                raise ValueError("Incomplete source 10-per-island-and-forest 3x3 grid")
    if len(seen_sites)!=90:raise ValueError("Original 90 independent author plots not established")
    return {
        "schema":"structural.foresteco2_event_only_result.v1_286",
        "status":"EVENT_90_BY_9_PHYSICAL_DESIGN_QUALIFIED_OCCURRENCE_UNOPENED",
        "original_author_events":len(events),
        "distinct_original_site_ids":len(seen_sites),
        "island_by_forest_type_counts":{isl:{h:grid[(isl,h)] for h in ("NF","EW","PF")}
                                        for isl in ("Pico","São Miguel","Terceira")},
        "source_years":dict(sorted(years.items())),
        "source_plot_area_status":dict(sorted(units.items())),
        "Event_data_rows_opened":len(events),
        "Occurrence_data_rows_opened":0,
        "S1_workbook_rows_opened":0,
        "biological_predictions_scored":0,
        "new_confirmatory_systems":0,
        "GEB_scientific_HOLD":True,
        "eBird_used":False,
        "raw_plot_IDs_or_species_exported":False
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    c=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.foresteco2_event_only_qualification.v1_286"
        or c["expected_zip_sha256"]!=SOURCE_SHA
        or c["source_archive_url"]!=SOURCE
        or c["status"]!="FROZEN_AFTER_XML_SCHEMA_BEFORE_ANY_EVENT_VALUE"):
        raise ValueError("v1.286 Event-only source/freeze mismatch")
    result={
       "schema":"structural.foresteco2_event_only_result.v1_286",
       "status":"SOURCE_OR_EVENT_STRUCTURE_STOP",
       "Event_data_rows_opened":0,"Occurrence_data_rows_opened":0,
       "S1_workbook_rows_opened":0,"GEB_scientific_HOLD":True,
       "eBird_used":False,"new_confirmatory_systems":0,
    }
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-ForestEco2-EventOnly-v1.286/1.0"})
        with urllib.request.urlopen(req,timeout=60) as handle:
            raw=handle.read(5_000_001)
        if len(raw)>5_000_000 or hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
            raise ValueError("Frozen original source zip hash/size mismatch")
        metadata=check_foresteco_schema(raw)
        if metadata["status"]!="SCHEMA_QUALIFIED_BIOLOGICAL_RESPONSE_STILL_SEALED":
            raise ValueError("v1.285 metadata preflight did not qualify")
        events=_read_author_event_only(raw)
        result["Event_data_rows_opened"]=len(events)
        result=audit_event_grid(events,c)
        result["verified_original_zip_sha256"]=SOURCE_SHA
    except Exception as err:
        result["stop_type"]=type(err).__name__
        result["stop_reason"]=str(err)[:350]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],
        "original_events":result.get("original_author_events"),
        "grid":result.get("island_by_forest_type_counts"),
        "Occurrence_rows_opened":0,
        "stop_reason":result.get("stop_reason")},sort_keys=True))
    if result["status"]!="EVENT_90_BY_9_PHYSICAL_DESIGN_QUALIFIED_OCCURRENCE_UNOPENED":
        raise SystemExit(2)

if __name__=="__main__":main()
