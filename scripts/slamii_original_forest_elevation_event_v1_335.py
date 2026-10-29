#!/usr/bin/env python3
"""SLAM II v1.335 original Event-only elevational habitat sorting (4 islands).

Read 45 Event records from EXACT official original v1.8 SHA ZIP, NEVER
Occurrence taxonomic values. Site-altitude observations determine if any
later species origin analysis is estimable with strict 2-island overlap.
Not direct forest effect, population loss or ecological rescue.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,re,statistics,unicodedata,urllib.request,zipfile
import xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path

from slamii_original_meta_only_v1_334 import SOURCE,local,term,MAX_BYTES
SHA="a0af4661f202d221ea8706dcf8a936d093dec335ce30306f3f0a2e0f474eb734"
ISLANDS=("COR","FLO","SMR","TER")

def normalize(s):
    val=unicodedata.normalize("NFKD",str(s or ""))
    return " ".join(re.sub(r"[^a-z0-9]+"," ", "".join(x for x in val if not unicodedata.combining(x)).casefold()).split())

def classify_habitat(value,protocol):
    text=normalize(value)
    c=protocol["original_habitat_rule"]
    for klass,field in (("native","native_prefixes"),("mixed","mixed_prefixes"),("exotic","exotic_prefixes")):
        if any(text==normalize(v) or text.startswith(normalize(v)+" ") for v in c[field]):
            return klass
    return None

def island_code(value,protocol):
    text=normalize(value)
    matches=[key for key,variants in protocol["island_map"].items()
             if any(text==normalize(n) for n in variants)]
    return matches[0] if len(matches)==1 else None

def source_events(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        node=[x for x in root if local(x.tag)=="core"]
        if len(node)!=1:raise ValueError("Original source Event core missing")
        meta=node[0];fields={};sources=[];coreidx=None
        for v in meta.iter():
            tag=local(v.tag)
            if tag=="field" and "index" in v.attrib and "term" in v.attrib:
                fields[term(v.attrib["term"])]=int(v.attrib["index"])
            elif tag=="id" and "index" in v.attrib:coreidx=int(v.attrib["index"])
            elif tag=="location" and v.text:sources.append(v.text.strip())
        mandatory={"eventID","island","habitat","locationID","minimumElevationInMeters",
                   "samplingProtocol","eventDate","decimalLatitude","decimalLongitude"}
        if coreidx is None or len(sources)!=1 or not mandatory.issubset(fields):
            raise ValueError("Original forest site/habitat/elevation source fields absent")
        delimiter=meta.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        header=int(meta.attrib.get("ignoreHeaderLines","0"))
        if len(delimiter)!=1 or header not in (0,1):raise ValueError("Unrecognized original 45 Event source TSV")
        events=[]
        with z.open(sources[0]) as original_events_only:
            with io.TextIOWrapper(original_events_only,encoding="utf-8-sig",newline="") as f:
                reader=csv.reader(f,delimiter=delimiter)
                for _ in range(header):next(reader,None)
                for row in reader:
                    if not row or not any(row):continue
                    if max(coreidx,*(fields[k] for k in mandatory))>=len(row):
                        raise ValueError("Original 45 Event source row truncated")
                    value={name:row[idx] for name,idx in fields.items() if idx<len(row)}
                    value["__original_coreid"]=row[coreidx]
                    events.append(value)
        return events

def evaluate(events,protocol):
    if len(events)!=45:raise ValueError("Official 2023 45 author source plots changed")
    universe=protocol["expected_source_counts"]
    seen_ids=set();sites=set();counts=Counter();habitat_counts=Counter()
    by_island=defaultdict(lambda:defaultdict(list))
    source_methods=Counter();time_counts=Counter()
    problems=Counter()
    for event in events:
        core=str(event.get("__original_coreid","")).strip()
        if not core or core in seen_ids:
            raise ValueError("Original author Event core ID duplicated/absent")
        seen_ids.add(core)
        island=island_code(event.get("island"),protocol)
        if island is None:
            problems["unrecognized_island"]+=1
            continue
        loc=normalize(event.get("locationID"))
        if not loc:
            problems["empty_original_site_key"]+=1
            continue
        key=(island,loc)
        if key in sites:
            problems["repeated_source_physical_plot_key"]+=1
            continue
        sites.add(key)
        category=classify_habitat(event.get("habitat"),protocol)
        if category is None:
            problems["unknown_original_forest_type"]+=1
            continue
        try:
            elevation=float(event["minimumElevationInMeters"])
            lat=float(event.get("decimalLatitude"))
            lon=float(event.get("decimalLongitude"))
        except (ValueError,TypeError):
            elevation=lat=lon=math.nan
        if not all(map(math.isfinite,(elevation,lat,lon))):
            problems["invalid_original_elevation_or_coordinates"]+=1
            continue
        yr=str(event.get("eventDate","")).strip()[:4]
        if yr not in ("2019","2020") or (event.get("year") and str(event.get("year")).strip()!=yr):
            problems["outside_source_calendar_or_source_year_mismatch"]+=1
            continue
        if not (normalize(event.get("samplingProtocol")).find("slam")>=0):
            problems["not_original_SLAM_interception_method"]+=1
            continue
        sampleunit=normalize(event.get("sampleSizeUnit"))
        samplevalue=str(event.get("sampleSizeValue","")).strip()
        source_methods[normalize(event.get("samplingProtocol"))]+=1
        time_counts[yr]+=1
        counts[island]+=1
        habitat_counts[category]+=1
        by_island[island][category].append(elevation)
    if (counts!=Counter(universe["source_island_site_n"]) or
        habitat_counts!=Counter(universe["habitat_source_total"]) or
        len(sites)!=45 or problems):
        status="STOP_ORIGINAL_SOURCE_SITE_HABITAT_ELEVATION_UNVERIFIED"
    else:status="ORIGINAL_FOREST_ELEVATION_SORTING_SOURCE_RECONCILED"
    comparisons={};eligible_islands=[]
    for island in ISLANDS:
        data=by_island[island]
        natives=data["native"]
        modified=data["mixed"]+data["exotic"]
        subset={
            "original_independent_physical_sites":counts[island],
            "original_native_site_n":len(natives),
            "original_mixed_site_n":len(data["mixed"]),
            "original_exotic_site_n":len(data["exotic"]),
            "original_native_elevation_range_m":[min(natives),max(natives)] if natives else None,
            "original_altered_elevation_range_m":[min(modified),max(modified)] if modified else None,
            "native_minus_altered_median_plot_elevation_m":statistics.median(natives)-statistics.median(modified)
                 if natives and modified else None,
            "common_elevation_interval_m":None,
            "n_original_native_plots_in_common_elevation_range":0,
            "n_original_altered_plots_in_common_elevation_range":0,
            "native_altered_common_support_2_each":False
        }
        if natives and modified:
            lo=max(min(natives),min(modified))
            hi=min(max(natives),max(modified))
            if lo<=hi:
                a=sum(lo<=v<=hi for v in natives)
                b=sum(lo<=v<=hi for v in modified)
                subset.update({
                    "common_elevation_interval_m":[lo,hi],
                    "n_original_native_plots_in_common_elevation_range":a,
                    "n_original_altered_plots_in_common_elevation_range":b,
                    "native_altered_common_support_2_each":a>=2 and b>=2
                })
                if a>=2 and b>=2:eligible_islands.append(island)
        comparisons[island]=subset
    if status=="ORIGINAL_FOREST_ELEVATION_SORTING_SOURCE_RECONCILED":
        status=("ORIGINAL_FOREST_ELEVATION_2ISLAND_COMMON_SUPPORT_TAXA_SEALED"
                if len(eligible_islands)>=2 else
                "TERMINAL_NATIVE_VS_ALTERED_ELEVATION_COMMON_SUPPORT_LT_TWO_ISLANDS")
    return {
        "schema":"structural.slamII_45forest_original_environment_result.v1_335",
        "status":status,
        "original_source_sha256":SHA,
        "original_Event_values_read":len(events),
        "original_Occurrence_values_read":0,
        "original_author_physical_site_n":len(sites),
        "original_4island_physical_sites":dict(sorted(counts.items())),
        "original_habitat_site_totals":dict(sorted(habitat_counts.items())),
        "original_samplingProtocol_original_event_counts":dict(sorted(source_methods.items())),
        "source_first_year_Event_counts":dict(sorted(time_counts.items())),
        "original_per_island_habitat_elevation":comparisons,
        "islands_with_two_native_and_two_altered_inside_common_elevation_support":eligible_islands,
        "island_support_requirement":2,
        "source_plot_elevation_habitat_cannot_separate_without_common_support":len(eligible_islands)<2,
        "original_source_site_metadata_invalid_counts":dict(sorted(problems.items())),
        "source_original_plot_IDs_species_and_coordinates_not_exported":True,
        "old_taxonomic_scorers_reopened":0,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
        "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    cfg=json.loads(a.contract.read_text())
    if (cfg.get("schema")!="structural.slamII_45forest_original_event_elevation_gate.v1_335"
        or cfg.get("status")!="PRE_FROZEN_BEFORE_45_ORIGINAL_EVENT_VALUES"
        or cfg["source"]["v18_url"]!=SOURCE
        or cfg["source"]["v18_sha256"]!=SHA):
        raise ValueError("Original 45 site habitat-elevation interpretation not pre-registered")
    result={"schema":"structural.slamII_45forest_original_environment_result.v1_335",
            "status":"ORIGINAL_SOURCE_OR_EVENT_TECHNICAL_STOP",
            "original_Event_values_read":0,"original_Occurrence_values_read":0,
            "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-v1.335-SLAMII-45-FOREST-EVENT-ONLY"})
        with urllib.request.urlopen(req,timeout=65) as f:blob=f.read(MAX_BYTES+1)
        if len(blob)>MAX_BYTES or hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("Original v1.8 forest source zip SHA changed")
        result=evaluate(source_events(blob),cfg)
    except Exception as err:
        result["stop_type"]=type(err).__name__;result["stop_reason"]=str(err)[:320]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print(json.dumps({k:result.get(k) for k in (
        "status","original_author_physical_site_n","original_habitat_site_totals",
        "islands_with_two_native_and_two_altered_inside_common_elevation_support",
        "original_per_island_habitat_elevation","original_source_site_metadata_invalid_counts",
        "original_Occurrence_values_read","stop_reason"
    )},sort_keys=True))
    if result["status"]=="ORIGINAL_SOURCE_OR_EVENT_TECHNICAL_STOP":raise SystemExit(2)
if __name__=="__main__":main()
