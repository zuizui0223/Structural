#!/usr/bin/env python3
"""Exact original Pico PRIBES Event-date-only diagnosis, NO occurrence values.

This diagnosis does not authorize posthoc temporal status substitutions.
"""
from __future__ import annotations
import argparse
from collections import Counter,defaultdict
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.request
import zipfile
import csv

from azores_2016_dwca_structure_v1_267 import summarize_archive

SRC_URL="https://ipt.gbif.pt/ipt/archive.do?r=pico_vascular_plants&v=1.7"
SRC_SHA="82406dbcb48e188cca6bca116437b951a80f613faadf44a173ddd5d9b92e4a02"
SRC_BYTES=568461


def _day(s):
    try:
        return date.fromisoformat(s)
    except (TypeError,ValueError):
        return None


def date_kind(value):
    s=str(value or "").strip()
    if not s:return "missing"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}",s):
        return "full_day" if _day(s) else "other"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}[Tt ][0-9:.Zz+\-]+",s):
        return "day_and_time" if _day(s[:10]) else "other"
    if re.fullmatch(r"\d{1,2}/\d{1,2}/\d{4}",s):
        return "slash_numeric_day"
    if "/" in s:return "interval"
    if re.fullmatch(r"\d{4}-\d{2}",s):return "month_only"
    if re.fullmatch(r"\d{4}",s):return "year_only"
    return "other"


def _components(row):
    y,m,d=(str(row.get(k) or "").strip() for k in ("year","month","day"))
    if not (y.isdigit() and m.isdigit() and d.isdigit()):
        return None
    try:
        return date(int(y),int(m),int(d))
    except ValueError:
        return None


def slash_date_matches_author_components(original,fields):
    """Compare apparent M/D/Y and D/M/Y against original author's independent date components."""
    component=_components(fields)
    if component is None:
        return "NO_VALID_COMPONENTS"
    m=re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})",str(original or "").strip())
    if not m:return "NOT_SLASH_NUMERIC_DAY"
    a,b,y=map(int,m.groups())
    def trydate(mon,day):
        try:
            return date(y,mon,day)
        except ValueError:
            return None
    us=trydate(a,b)==component
    eu=trydate(b,a)==component
    if us and eu:return "BOTH_SAME_DAY"
    if us:return "MDY"
    if eu:return "DMY"
    return "CONFLICT"


def event_date_diagnostic(event_rows):
    reasons=Counter()
    examples=defaultdict(list)
    yrs=Counter()
    valid_parts=0
    conflict=0
    reliable=0
    slash_validation=Counter()
    unique_dates=set()
    n=0
    for r in event_rows:
        n+=1
        date_value=str(r.get("eventDate") or "").strip()
        kind=date_kind(date_value)
        reasons[kind]+=1
        if date_value and len(examples[kind])<3:
            if date_value not in examples[kind]:
                # Public date alone (not site, eventID or taxon), capped.
                examples[kind].append(date_value[:65])
        p=_components(r)
        if p:
            valid_parts+=1
            yrs[str(p.year)]+=1
        iso_value=(date_value[:10] if kind in {"full_day","day_and_time"} else None)
        dt=_day(iso_value) if iso_value else None
        if kind=="slash_numeric_day":
            comparison=slash_date_matches_author_components(date_value,r)
            slash_validation[comparison]+=1
            if comparison=="CONFLICT":
                conflict+=1
            if comparison in ("MDY","DMY","BOTH_SAME_DAY") and p:
                reliable+=1
                unique_dates.add(p.isoformat())
        if dt and p and p!=dt:
            conflict+=1
        if dt and (not p or dt==p):
            reliable+=1
            unique_dates.add(dt.isoformat())
    return {
        "event_rows":n,
        "event_date_classes":dict(sorted(reasons.items())),
        "author_date_examples_bounded":{k:v for k,v in sorted(examples.items())},
        "full_date_eventDate_rows":reasons["full_day"]+reasons["day_and_time"],
        "component_complete_and_valid_dates":valid_parts,
        "component_years":dict(sorted(yrs.items())),
        "source_field_date_component_conflicts":conflict,
        "slash_MDY_source_component_match":slash_validation["MDY"],
        "slash_DMY_source_component_match":slash_validation["DMY"],
        "slash_both_same_day":slash_validation["BOTH_SAME_DAY"],
        "slash_component_conflicts":slash_validation["CONFLICT"],
        "slash_missing_or_invalid_components":slash_validation["NO_VALID_COMPONENTS"],
        "reliable_full_day_rows":reliable,
        "distinct_exact_days":len(unique_dates),
        "source_taxon_occurrence_rows_decoded":0,
    }


def original_pico_events(raw):
    meta=summarize_archive(raw,"f40f80dc-1815-4e73-9097-9d7893d87f6f")
    core=meta["core"]
    if not core["rowtype"].endswith("/Event"):
        raise ValueError("Source original Event core removed")
    keys={str(x["term"]).rsplit("/",1)[-1]:int(x["index"]) for x in core["fields"]
          if x["term"] and x["index"] is not None}
    if not {"eventDate","year","month","day"}<=set(keys):
        raise ValueError("Missing source eventDate/year/month/day components")
    event_rows=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        # Important: only source Event core opened, no Occurrence extension.
        with z.open(core["record_path"]) as bytes_stream:
            with io.TextIOWrapper(bytes_stream,encoding="utf-8-sig",newline="") as stream:
                reader=csv.reader(stream,delimiter="\t")
                for _ in range(int(core.get("ignore_header_lines") or 0)):
                    next(reader,None)
                for values in reader:
                    if not values or not any(values):continue
                    if any(v>=len(values) for v in keys.values()):
                        raise ValueError("Truncated source Event row")
                    event_rows.append({k:values[keys[k]] for k in ("eventDate","year","month","day")})
    return event_date_diagnostic(event_rows)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contract",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf8"))
    if (c["schema"]!="structural.pico_PRIBES_original_event_date_diagnostic.v1_272"
        or c["status"]!="DIAGNOSTIC_ONLY_NO_NEW_OCCURRENCE_VALUES"
        or c["source"]["sha256"]!=SRC_SHA
        or c["source"]["url"]!=SRC_URL):
        raise ValueError("Original source date diagnosis contract modified")
    out={
        "schema":"structural.pico_PRIBES_original_event_date_result.v1_272",
        "status":"SOURCE_EVENT_DATE_TRANSPORT_STOP",
        "source":{"sha256":SRC_SHA,"doi":c["source"]["doi"]},
        "source_occurrence_values_read":0,
        "S2_S3_S4_values_accessed":0,
        "GEB_scientific_HOLD":True,"eBird_off":True,
    }
    try:
        req=urllib.request.Request(SRC_URL,headers={
            "User-Agent":"Structural-Pico-PRIBES-Event-Date-Only/1.0",
            "Accept":"application/zip,application/octet-stream"})
        with urllib.request.urlopen(req,timeout=70) as response:
            raw=response.read(SRC_BYTES+1)
        if len(raw)!=SRC_BYTES or hashlib.sha256(raw).hexdigest()!=SRC_SHA:
            raise ValueError("Original Pico author source fingerprint changed")
        out["events"]=original_pico_events(raw)
        if out["events"]["event_rows"]!=2801:
            raise ValueError("Previously observed 2801 source Event rows changed")
        out["status"]="OFFICIAL_PICO_AUTHOR_EVENT_DATE_ONLY"
    except Exception as exc:
        out["stop_reason"]=str(exc)[:350]
        out["stop_type"]=type(exc).__name__
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"status":out["status"],
                      "event_date_classes":out.get("events",{}).get("event_date_classes"),
                      "stop_reason":out.get("stop_reason"),
                      "source_occurrence_values_read":0},sort_keys=True))
    if out["status"]!="OFFICIAL_PICO_AUTHOR_EVENT_DATE_ONLY":
        raise SystemExit(2)


if __name__=="__main__":
    main()
