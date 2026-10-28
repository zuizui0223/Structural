#!/usr/bin/env python3
"""v1.306 source Event-only spider/tree coordinate and date diagnostic.

The v1.303 ten-site physical/temporal gate is permanently STOPPED. Reuse the
exact published original source hashes and author Event values ONLY. No
species, taxa, arthropod abundance, or original Occurrence member is read.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
from biomoni_terceira_event_colocation_v1_298 import (
    extract_event_core_only,normalized_site,norm,MAX_BYTES
)
SOURCES={
    "woody":("https://ipt.gbif.pt/ipt/archive.do?r=biomoni_trees&v=1.7",
             "4574d02727654ec5a319f6d1218ff9243080b0128c517d01c905065cbefd6f82",30),
    "spider":("https://ipt.gbif.pt/ipt/archive.do?r=spiders_macaronesia_azores&v=1.8",
              "17f65284214ae35a302fee2fa42747e2ecfabb8d04bf9ec8394b6d33c5c4f7b5",423)
}
COORD_TOLERANCE=0.0003

def date_format(date):
    s=str(date or "").strip()
    if not s:return "empty"
    if re.match(r"^\d{4}(?:-|$)",s):return "four_digit_year_prefix"
    if re.match(r"^\d{1,2}[-/]\d{1,2}[-/]\d{4}",s):return "day_month_year"
    return "nonstandard"

def audit(source_events):
    if set(source_events)!=set(SOURCES):
        raise ValueError("Both independent original source Event arrays required")
    groups={}
    date_summary={}
    for kind,events in source_events.items():
        if len(events)!=SOURCES[kind][2]:
            raise ValueError("Source original Event row denominator changed")
        grouped=defaultdict(list)
        per_island=defaultdict(Counter)
        seen=set()
        for e in events:
            core=str(e.get("source_coreid","")).strip()
            if not core or core in seen:
                raise ValueError("Original Event author key missing/duplicated")
            seen.add(core)
            island=norm(e.get("island"))
            fmt=date_format(e.get("eventDate"))
            yr=str(e.get("year","")).strip()
            per_island[island]["date_format_"+fmt]+=1
            per_island[island]["original_year_field_nonblank" if yr else "original_year_field_blank"]+=1
            if yr and yr.isdigit() and len(yr)==4:
                per_island[island]["year_field_numeric"]+=1
            elif yr:
                per_island[island]["year_field_non_numeric"]+=1
            if island!="terceira": continue
            site=normalized_site(e.get("locationID"))
            if not site:
                raise ValueError("Original Terceira plot missing author locationID")
            try:xy=(float(e.get("decimalLatitude")),float(e.get("decimalLongitude")))
            except (ValueError,TypeError):xy=(float("nan"),float("nan"))
            grouped[site].append({"coord":xy,"date_format":fmt})
        groups[kind]=grouped
        date_summary[kind]={i:dict(sorted(v.items())) for i,v in sorted(per_island.items())}

    a,b=groups["woody"],groups["spider"]
    if len(a)!=10 or len(b)!=10 or set(a)!=set(b):
        raise ValueError("Source original Terceira 10×10 site ID crosswalk is no longer exact")
    if any(len(v)!=1 for v in a.values()):
        raise ValueError("Source original tree Event is not one independent forest site")
    anonymous=[]
    mismatch_event_bins=Counter()
    n_large_003=n_large_001=n_large_01=0
    for index,site in enumerate(sorted(a),1):
        orig=a[site][0]["coord"]
        raw=[q["coord"] for q in b[site]]
        if any(not all(map(math.isfinite,point)) for point in [orig]+raw):
            raise ValueError("Invalid Event metadata coordinate, not eligible for diagnostic distance")
        diffs=[max(abs(pt[0]-orig[0]),abs(pt[1]-orig[1])) for pt in raw]
        lat_range=max(x[0] for x in raw)-min(x[0] for x in raw)
        lon_range=max(x[1] for x in raw)-min(x[1] for x in raw)
        n1=sum(x>COORD_TOLERANCE for x in diffs)
        n2=sum(x>0.001 for x in diffs)
        n3=sum(x>0.01 for x in diffs)
        n_large_003+=n1;n_large_001+=n2;n_large_01+=n3
        for delta in diffs:
            if delta<=COORD_TOLERANCE:label="<=0.0003"
            elif delta<=0.001:label="(0.0003,0.001]"
            elif delta<=0.003:label="(0.001,0.003]"
            elif delta<=0.01:label="(0.003,0.01]"
            else:label=">0.01"
            mismatch_event_bins[label]+=1
        anonymous.append({
            "anonymous_site_index":index,
            "spider_original_Event_count":len(raw),
            "tree_spider_original_coordinate_abs_degree_min":round(min(diffs),9),
            "tree_spider_original_coordinate_abs_degree_max":round(max(diffs),9),
            "spider_within_site_max_axis_span_degrees":round(max(lat_range,lon_range),9),
            "events_beyond_frozen_0_0003deg_limit":n1,
            "events_beyond_0_001deg_diagnostic":n2,
            "events_beyond_0_01deg_diagnostic":n3,
            "spider_events_with_non_yearprefix_or_empty_dates":sum(
                q["date_format"]!="four_digit_year_prefix" for q in b[site])
        })
    return {
        "schema":"structural.biomoni_spider_terceira_coord_date_result.v1_306",
        "status":"SOURCE_ONLY_LOCATION_DATE_QUALITY_DIAGNOSTIC_V1_303_REMAINS_TERMINAL",
        "original_tree_Event_rows_examined":len(source_events["woody"]),
        "original_spider_Event_rows_examined":len(source_events["spider"]),
        "original_exact_Terceira_shared_site_IDs":len(a),
        "original_Terceira_spider_Event_count":sum(z["spider_original_Event_count"] for z in anonymous),
        "anonymous_site_coordinate_discrepancies":anonymous,
        "number_Terceira_sites_failing_any_original_Event_coordinate_limit":sum(
            q["events_beyond_frozen_0_0003deg_limit"]>0 for q in anonymous),
        "total_spider_Terceira_Event_coordinate_mismatches_over_0_0003":n_large_003,
        "total_spider_Terceira_Event_coordinate_mismatches_over_0_001":n_large_001,
        "total_spider_Terceira_Event_coordinate_mismatches_over_0_01":n_large_01,
        "source_date_format_aggregate_by_island":date_summary,
        "coordinate_difference_event_histogram":dict(sorted(mismatch_event_bins.items())),
        "old_v1_303_original_time_and_coordinate_gate_status":"TERMINAL",
        "original_woody_Occurrence_rows_reopened":0,
        "original_spider_Occurrence_rows_opened":0,
        "original_beetle_Occurrence_rows_reopened":0,
        "original_site_IDs_geographic_coordinates_and_species_exported":False,
        "new_confirmatory_systems":0,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    cfg=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (cfg.get("schema")!="structural.biomoni_spider_event_coord_date_quality_v1_306"
        or cfg.get("status")!="FROZEN_POST_EVENT_DIAGNOSTIC_NO_SPECIES_OPEN"
        or any(cfg["sources"][name+"_original_sha256"]!=SOURCES[name][1]
               for name in ("spider","woody"))):
        raise ValueError("Original archive source-only quality contract not frozen")
    result={
      "schema":"structural.biomoni_spider_terceira_coord_date_result.v1_306",
      "status":"TERMINAL_SOURCE_OR_EVENT_META_TRANSPORT",
      "old_v1_303_original_time_and_coordinate_gate_status":"TERMINAL",
      "original_woody_Occurrence_rows_reopened":0,
      "original_spider_Occurrence_rows_opened":0,
      "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        original={}
        for name,(url,sha,n) in SOURCES.items():
            req=urllib.request.Request(url,headers={"User-Agent":"Structural-v1.306-Spider-Event-GeoDate-Only"})
            with urllib.request.urlopen(req,timeout=60) as raw:
                bytes_=raw.read(MAX_BYTES+1)
            if len(bytes_)>MAX_BYTES or hashlib.sha256(bytes_).hexdigest()!=sha:
                raise ValueError("Original spider or tree ZIP SHA256 no longer fixed")
            original[name]=extract_event_core_only(bytes_)
        result=audit(original)
    except Exception as error:
        result["stop_type"]=type(error).__name__
        result["stop_reason"]=str(error)[:280]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "matched_terceira_sites":result.get("original_exact_Terceira_shared_site_IDs"),
        "sites_failing_coordinate_tolerance":result.get("number_Terceira_sites_failing_any_original_Event_coordinate_limit"),
        "spider_events_over_coord_threshold":result.get("total_spider_Terceira_Event_coordinate_mismatches_over_0_0003"),
        "spider_events_over_0_01":result.get("total_spider_Terceira_Event_coordinate_mismatches_over_0_01"),
        "spider_date_format_counts":result.get("source_date_format_aggregate_by_island",{}).get("spider",{}).get("terceira"),
        "occurrence_rows_opened":0,
        "stop_reason":result.get("stop_reason")
    },sort_keys=True))
    if result["status"]=="TERMINAL_SOURCE_OR_EVENT_META_TRANSPORT": raise SystemExit(2)
if __name__=="__main__":main()
