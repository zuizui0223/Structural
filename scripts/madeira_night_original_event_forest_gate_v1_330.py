#!/usr/bin/env python3
"""Madeira v1.330, fixed original Event-only native-versus-modified forest gate.

Read only original Madeira v1.1 Event source member after SHA verification.
Never open Occurrence or any taxonomic source-body member. Counts actual
author physical locationID keys (47 vs 48 publication discrepancy), method,
habitat and matched year-quarter efforts without species-dependent choices.
"""
from __future__ import annotations

import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import io
import json
import math
import re
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

SOURCE="https://ipt.gbif.pt/ipt/archive.do?r=arthropod_madeira_life_naturaatnight&v=1.1"
SOURCE_SHA="54c2e4dc10989a15a0d78a988b496d2e5ae917a4315bc032b28292c083aa10ba"
MAX_BYTES=400000
SOURCE_EVENTS=134

def local(t):
    return t.rsplit("}",1)[-1]

def term(t):
    return t.rstrip("/").split("/")[-1].split("#")[-1]

def standard(s):
    t=unicodedata.normalize("NFKD",str(s or ""))
    t="".join(c for c in t if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+"," ",t.casefold()).split())

def site_id(text):
    s=standard(text).upper()
    return "".join(c for c in s if "A"<=c<="Z" or "0"<=c<="9")

def classify_habitat(value,contract):
    s=standard(value)
    if not s:return "unknown"
    o=contract["habitat_ontology_locked_before_first_original_Event"]
    def has_any(values):
        return any(standard(t) in s for t in values)
    if has_any(o["excluded_nonforest_keywords_any"]):
        return "nonforest"
    if has_any(o["altered_mixed_keywords_any"]):
        return "mixed"
    if has_any(o["altered_exotic_keywords_any"]):
        return "exotic"
    if has_any(o["native_keywords_any"]):
        return "native"
    return "unknown"

def classify_method(value,contract):
    s=standard(value)
    m=contract["capture_method_rule"]
    light=any(standard(t) in s for t in m["light_source_token_any"])
    bait=any(standard(t) in s for t in m["bait_source_token_any"])
    if light and bait:return "ambiguous"
    if light:return "LIGHT"
    if bait:return "BAIT"
    return "unknown"

def year_quarter(value):
    s=str(value or "").strip()
    match=re.match(r"^(\d{4})-(\d{2})-(\d{2})(?:$|[T /])",s)
    if not match:
        raise ValueError("Original Madeira Event date not YYYY-MM-DD; source calendar cannot be inferred")
    y,m,d=map(int,match.groups())
    if y not in (2022,2023) or not 1<=m<=12 or not 1<=d<=31:
        raise ValueError("Original Madeira date outside predeclared 2022/2023 source")
    return (y,(m-1)//3+1)

def read_original_event_core_only(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as source:
        meta=ET.fromstring(source.read("meta.xml"))
        cores=[v for v in meta if local(v.tag)=="core"]
        if len(cores)!=1:
            raise ValueError("Original Madeira archive no unique Event core")
        core=cores[0]
        names={}
        path=[]
        primary_idx=None
        for x in core.iter():
            t=local(x.tag)
            if t=="field" and x.attrib.get("term") and "index" in x.attrib:
                names[term(x.attrib["term"])]=int(x.attrib["index"])
            elif t=="location" and x.text:
                path.append(x.text.strip())
            elif t=="id" and "index" in x.attrib:
                primary_idx=int(x.attrib["index"])
        required={"eventID","eventDate","locationID","habitat","samplingProtocol",
                  "decimalLatitude","decimalLongitude"}
        if len(path)!=1 or primary_idx is None or not required.issubset(names):
            raise ValueError("Original Event physical site, habitat or coordinates missing")
        delimiter=core.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        header=int(core.attrib.get("ignoreHeaderLines","0"))
        if len(delimiter)!=1 or header not in (0,1):
            raise ValueError("Unrecognized original Madeira Event file encoding")
        rows=[]
        with source.open(path[0]) as source_event_only:
            with io.TextIOWrapper(source_event_only,encoding="utf-8-sig",newline="") as f:
                reader=csv.reader(f,delimiter=delimiter)
                for _ in range(header):next(reader,None)
                for values in reader:
                    if not values or not any(values):continue
                    if max(primary_idx,*(names[k] for k in required))>=len(values):
                        raise ValueError("Original Event source field offsets out of bounds")
                    entry={key:values[index] for key,index in names.items() if index<len(values)}
                    entry["__original_coreid"]=values[primary_idx]
                    rows.append(entry)
        return rows

def audit(events,contract):
    if len(events)!=SOURCE_EVENTS:
        raise ValueError("Madeira v1.1 original source is not 134 Event rows")
    observed_ids=set()
    sites=defaultdict(list)
    counts=Counter()
    for e in events:
        key=str(e.get("__original_coreid","")).strip()
        if not key or key in observed_ids:
            raise ValueError("Duplicate or missing original Event core ID")
        observed_ids.add(key)
        loc=site_id(e.get("locationID"))
        if not loc:
            counts["missing_author_locationID"]+=1
            continue
        date=year_quarter(e.get("eventDate"))
        if str(e.get("year","")).strip() and str(e["year"]).strip()!=str(date[0]):
            counts["eventDate_explicit_year_mismatch"]+=1
        try:
            latitude=float(e.get("decimalLatitude"))
            longitude=float(e.get("decimalLongitude"))
        except (ValueError,TypeError):
            counts["non_numeric_source_coordinates"]+=1
            latitude=longitude=math.nan
        if not (math.isfinite(latitude) and math.isfinite(longitude)):
            counts["not_finite_source_coordinates"]+=1
        sites[loc].append({
            "core":key,
            "year":date[0],"quarter":date[1],
            "habitat":classify_habitat(e.get("habitat"),contract),
            "method":classify_method(e.get("samplingProtocol"),contract),
            "lat":latitude,"lon":longitude,
        })
    expected_sites=contract["physical_site_rule"]["original_sites_min_max"]
    habitat_source=defaultdict(Counter)
    method_source=Counter()
    conflicts=0
    coordinate_conflicts=0
    site_habitat={}
    by_method_habitat=defaultdict(Counter)
    method_ambiguous=0
    method_unknown=0
    for loc,rows in sites.items():
        categories={r["habitat"] for r in rows if r["habitat"]!="unknown"}
        if "nonforest" in categories and len(categories)>1:
            conflicts+=1
        if len(categories)>1:
            conflicts+=1
        category=next(iter(categories)) if len(categories)==1 else "unknown"
        site_habitat[loc]=category
        habitat_source[category]["physical_sites"]+=1
        first=rows[0]
        for row in rows:
            method_source[row["method"]]+=1
            by_method_habitat[(row["method"],category)]["Event_rows"]+=1
            if row["method"]=="unknown":method_unknown+=1
            elif row["method"]=="ambiguous":method_ambiguous+=1
            if (not math.isfinite(row["lat"]) or not math.isfinite(row["lon"])
                or max(abs(row["lat"]-first["lat"]),abs(row["lon"]-first["lon"]))>0.0003):
                coordinate_conflicts+=1
    # Eligible original LIGHT source Event, one original Event per
    # exact author locationID × source-year × quarter.
    eligible=defaultdict(lambda:defaultdict(dict))
    for loc,rows in sites.items():
        cat=site_habitat[loc]
        if cat not in ("native","mixed","exotic"):
            continue
        group="native" if cat=="native" else "altered"
        for r in rows:
            if r["method"]!="LIGHT":
                continue
            k=(r["year"],r["quarter"])
            old=eligible[k][group].get(loc)
            if old is None or r["core"]<old:
                eligible[k][group][loc]=r["core"]
    windows=[]
    source_selected=[]
    physically_selected=set()
    for year,quarter in sorted(eligible):
        a=eligible[(year,quarter)]
        natives=a.get("native",{})
        altered=a.get("altered",{})
        windows.append({
            "source_year":year,"source_quarter":quarter,
            "source_native_independent_plot_n":len(natives),
            "source_mixed_or_exotic_independent_plot_n":len(altered),
            "status":"QUALIFIED" if len(natives)>=2 and len(altered)>=2 else "NOT_QUALIFIED"
        })
        if len(natives)>=2 and len(altered)>=2:
            for loc,core in list(natives.items())+list(altered.items()):
                source_selected.append(core)
                physically_selected.add(loc)
    qualified=[x for x in windows if x["status"]=="QUALIFIED"]
    target=contract["predeclared_eligibility"]
    schema_good=(
        len(sites) in expected_sites
        and not counts and not conflicts and not coordinate_conflicts
        and method_ambiguous==0
        and method_unknown/len(events)<=.10
        and len(qualified)>=target["required_different_original_year_quarter_strata"]
        and len(physically_selected)>=target["required_distinct_source_forest_sites_across_qualified_strata_min"]
    )
    return {
        "schema":"structural.madeira_night_original_event_only_result.v1_330",
        "status":"MADEIRA_UV_NATIVE_VS_ALTERED_FOREST_EVENT_FRAME_QUALIFIED_TAXA_SEALED"
            if schema_good else "TERMINAL_MADEIRA_NO_EXACT_SAME_SEASON_UV_FOREST_PLOT_FRAME",
        "original_source_archive_SHA256":SOURCE_SHA,
        "original_Events_opened":len(events),
        "original_Occurrences_opened":0,
        "actual_unique_physical_source_locationIDs":len(sites),
        "original_47_vs_48_physical_site_claim_resolved":len(sites) in expected_sites,
        "original_source_habitat_physical_plot_counts":{
            category:habitat_source[category]["physical_sites"]
            for category in ("native","mixed","exotic","nonforest","unknown")},
        "source_method_Event_counts":dict(sorted(method_source.items())),
        "source_method_and_habitat_Event_counts":{
            f"{method}|{hab}":n["Event_rows"]
            for (method,hab),n in sorted(by_method_habitat.items())},
        "source_year_quarter_method_LIGHT_plot_support":windows,
        "original_eligible_year_quarter_strata_n":len(qualified),
        "original_selected_unique_forest_plot_n":len(physically_selected),
        "original_selected_LIGHT_Event_rows":len(source_selected),
        "original_selected_LIGHT_Event_coreids_SHA256":hashlib.sha256(
            "\n".join(sorted(source_selected)).encode("utf-8")).hexdigest(),
        "original_selected_physical_site_keys_SHA256":hashlib.sha256(
            "\n".join(sorted(physically_selected)).encode("utf-8")).hexdigest(),
        "source_original_habitat_per_site_contradictions":conflicts,
        "source_original_coordinate_mismatch_over_0_0003deg":coordinate_conflicts,
        "source_original_unclassifiable_method_Event_rows":method_unknown,
        "source_original_ambiguous_method_Event_rows":method_ambiguous,
        "source_original_bad_metadata_counts":dict(sorted(counts.items())),
        "no_source_site_names_coordinates_species_status_exported":True,
        "original_Azores_species_sources_reopened":0,
        "scientific_endpoint_if_source_frame_fails":"TERMINAL_NO_RESPONSE",
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    c=json.loads(a.contract.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.madeira_night_source_forest_event_gate.v1_330"
        or c.get("status")!="ORIGINAL_EVENT_ONLY_DESIGN_FROZEN_AFTER_V329_META_BEFORE_FIRST_EVENT_VALUE"
        or c["source"]["original_v1_1"]!=SOURCE
        or c["source"]["original_v1_1_SHA256"]!=SOURCE_SHA):
        raise ValueError("Pre-exposure original Madeira site-level Event study not frozen")
    result={
        "schema":"structural.madeira_night_original_event_only_result.v1_330",
        "status":"ORIGINAL_EVENT_READER_OR_TRANSPORT_TECHNICAL_STOP",
        "original_Events_opened":0,"original_Occurrences_opened":0,
        "original_Azores_species_sources_reopened":0,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-Madeira-v1.1-EventOnly-Strict-v1.330"})
        with urllib.request.urlopen(req,timeout=65) as f:blob=f.read(MAX_BYTES+1)
        if len(blob)>MAX_BYTES or hashlib.sha256(blob).hexdigest()!=SOURCE_SHA:
            raise ValueError("Original Madeira v1.1 source ZIP SHA/size changed")
        result=audit(read_original_event_core_only(blob),c)
    except Exception as ex:
        result["stop_type"]=type(ex).__name__
        result["stop_reason"]=str(ex)[:280]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "original_source_Event_rows":result.get("original_Events_opened"),
        "actual_original_sites":result.get("actual_unique_physical_source_locationIDs"),
        "habitat_site_counts":result.get("original_source_habitat_physical_plot_counts"),
        "source_methods":result.get("source_method_Event_counts"),
        "eligible_year_quarters":result.get("original_eligible_year_quarter_strata_n"),
        "selected_UV_Event_rows":result.get("original_selected_LIGHT_Event_rows"),
        "stop_reason":result.get("stop_reason")
    },sort_keys=True))
    if result["status"]=="ORIGINAL_EVENT_READER_OR_TRANSPORT_TECHNICAL_STOP":
        raise SystemExit(2)

if __name__=="__main__":
    main()
