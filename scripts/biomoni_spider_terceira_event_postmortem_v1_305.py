#!/usr/bin/env python3
"""v1.305: Exact-source Event-only spider/tree postmortem; no biological rows.

v1.303 remains permanently terminal. Diagnose original spider Event years,
original site-key overlap, coordinate compatibility and sampling methods
without opening species names, taxonomic status, or any Occurrence member.
"""
from __future__ import annotations
import argparse,hashlib,json,math,re,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
from biomoni_terceira_event_colocation_v1_298 import (
    extract_event_core_only,normalized_site,norm,MAX_BYTES
)
SOURCE={
    "woody":("https://ipt.gbif.pt/ipt/archive.do?r=biomoni_trees&v=1.7",
             "4574d02727654ec5a319f6d1218ff9243080b0128c517d01c905065cbefd6f82",30),
    "spider":("https://ipt.gbif.pt/ipt/archive.do?r=spiders_macaronesia_azores&v=1.8",
              "17f65284214ae35a302fee2fa42747e2ecfabb8d04bf9ec8394b6d33c5c4f7b5",423)
}

def inspect_original_events(sources):
    if set(sources)!=set(SOURCE):
        raise ValueError("Both original source Event arrays required")
    frames={};by_island={}
    for kind,records in sources.items():
        if len(records)!=SOURCE[kind][2]:
            raise ValueError("Published Event denominators no longer fixed")
        seen=set();sites=defaultdict(list);islands=Counter();years=Counter();year_col_mismatch=0
        malformed_dates=0;bad_coord=0; missing_ids=0
        for e in records:
            core=str(e.get("source_coreid","")).strip()
            if not core or core in seen:
                raise ValueError("Missing or duplicate author original source Event key")
            seen.add(core)
            island=norm(e.get("island"))
            islands[island or "unknown"]+=1
            year=str(e.get("eventDate","")).strip()[:4]
            if not re.fullmatch(r"20[0-3][0-9]",year):
                malformed_dates+=1;year="unknown"
            years[(island,year)]+=1
            ycol=str(e.get("year","")).strip()
            if ycol and year!="unknown" and ycol!=year:
                year_col_mismatch+=1
            if island!="terceira": continue
            site=normalized_site(e.get("locationID"))
            if not site:missing_ids+=1;continue
            try:lat=float(e.get("decimalLatitude"));lon=float(e.get("decimalLongitude"))
            except (ValueError,TypeError):bad_coord+=1;lat=lon=float("nan")
            if not all(map(math.isfinite,(lat,lon))):bad_coord+=1 if math.isfinite(lat) or math.isfinite(lon) else 0
            method=norm(e.get("samplingProtocol"))
            sites[site].append({"year":year,"lat":lat,"lon":lon,"method":method,"id":core})
        frames[kind]=sites
        by_island[kind]={
            "original_Event_row_count":len(records),
            "source_island_Event_counts":dict(sorted(islands.items())),
            "source_island_year_Event_counts":{
                island:{y:n for (i,y),n in sorted(years.items()) if i==island}
                for island in sorted(islands)
            },
            "original_year_column_date_disagreement_events":year_col_mismatch,
            "events_with_unparsed_calendar_year":malformed_dates,
            "Terceira_original_unique_normalized_sites":len(sites),
            "Terceira_original_Event_rows":sum(len(x) for x in sites.values()),
            "Terceira_missing_author_locationID_count":missing_ids,
            "Terceira_invalid_coordinate_Event_count":bad_coord,
            "Terceira_unique_site_counts_per_calendar_year":{
                year:len({site for site,rows in sites.items() if any(r["year"]==year for r in rows)})
                for year in sorted({r["year"] for group in sites.values() for r in group})
            },
        }
    woody,spider=frames["woody"],frames["spider"]
    overlap=set(woody)&set(spider)
    mismatch={"Terceira_tree_sites_unmatched":len(set(woody)-set(spider)),
              "Terceira_spider_sites_unmatched":len(set(spider)-set(woody))}
    maxdelta=None;min_gap=None;max_gap=None;mode_min=[];original_effort=[]
    if overlap:
        coords=[];gaps=[];method_arrays=[];efforts=[]
        for site in sorted(overlap):
            w=woody[site];s=spider[site]
            if all(math.isfinite(r["lat"]) and math.isfinite(r["lon"]) for r in w+s):
                coords.append(max(max(abs(a["lat"]-b["lat"]),abs(a["lon"]-b["lon"]))
                                  for a in w for b in s))
            else:coords.append(None)
            if all(r["year"]!="unknown" for r in w+s):
                gaps.append(min(abs(int(a["year"])-int(b["year"]))
                                for a in w for b in s))
            original_effort.append(len(s))
            method_arrays.append(Counter(r["method"] for r in s if r["method"]))
        if coords and all(x is not None for x in coords):maxdelta=max(coords)
        if gaps:
            min_gap,max_gap=min(gaps),max(gaps)
        common=set.intersection(*(set(c) for c in method_arrays)) if method_arrays else set()
        mode_min=sorted(min(c[m] for c in method_arrays) for m in common)
    else:common=set()
    return {
        "schema":"structural.biomoni_spider_terceira_event_diagnostic_result.v1_305",
        "status":"ORIGINAL_EVENT_ONLY_POSTGATE_DIAGNOSTIC_303_REMAINS_TERMINAL",
        "source_meta":by_island,
        "Terceira_exact_original_site_overlap_count":len(overlap),
        "Terceira_site_mismatch_counts":mismatch,
        "Terceira_paired_max_coordinate_abs_difference_degrees":maxdelta,
        "Terceira_minimum_nearest_observation_year_gap":min_gap,
        "Terceira_maximum_nearest_observation_year_gap":max_gap,
        "Terceira_shared_spider_protocol_modes_count":len(common),
        "Terceira_min_multiplicity_of_shared_spider_modes_sorted":mode_min,
        "Terceira_spider_original_Events_per_matched_plot_min_max":[min(original_effort),max(original_effort)] if original_effort else None,
        "Terceira_exact_10_tree_and_spider_plots_supported":len(overlap)==10 and len(woody)==len(spider)==10,
        "original_spider_Occurrence_rows_opened":0,
        "original_woody_Occurrence_rows_reopened":0,
        "old_v1_303_year_gate_status":"TERMINAL",
        "no_taxon_names_original_site_names_or_raw_coordinates_emitted":True,
        "GEB_scientific_HOLD":True,
        "new_confirmatory_systems":0,
        "eBird_used":False
    }

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--protocol",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    contract=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (contract.get("schema")!="structural.biomoni_spider_terceira_event_diagnostic.v1_305"
        or contract.get("status")!="FROZEN_EVENT_ONLY_DIAGNOSIS_AFTER_TERMINAL_303_BEFORE_ORIGINAL_EVENT_REACCESS"
        or any(contract["source"][name+"_sha256"]!=SOURCE[name][1] for name in ("woody","spider"))
        or any(contract["source"][name+"_archive"]!=SOURCE[name][0] for name in ("woody","spider"))):
        raise ValueError("Original spider year diagnostic not frozen")
    result={
      "schema":"structural.biomoni_spider_terceira_event_diagnostic_result.v1_305",
      "status":"SOURCE_OR_ORIGINAL_EVENT_FORMAT_STOP",
      "original_spider_Occurrence_rows_opened":0,"original_woody_Occurrence_rows_reopened":0,
      "old_v1_303_year_gate_status":"TERMINAL",
      "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        sources={}
        for name,(url,sha,total) in SOURCE.items():
            req=urllib.request.Request(url,headers={"User-Agent":"Structural-BioMonI-v1.305-EventOnly-Postmortem"})
            with urllib.request.urlopen(req,timeout=60) as remote:data=remote.read(MAX_BYTES+1)
            if len(data)>MAX_BYTES or hashlib.sha256(data).hexdigest()!=sha:
                raise ValueError("Original spider/tree ZIP identity differs")
            sources[name]=extract_event_core_only(data)
        result=inspect_original_events(sources)
    except Exception as err:
        result["stop_type"]=type(err).__name__
        result["stop_reason"]=str(err)[:240]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "Terceira_exact_original_site_overlap_count":result.get("Terceira_exact_original_site_overlap_count"),
        "Terceira_maximum_nearest_observation_year_gap":result.get("Terceira_maximum_nearest_observation_year_gap"),
        "Terceira_shared_spider_protocol_modes_count":result.get("Terceira_shared_spider_protocol_modes_count"),
        "year_counts":result.get("source_meta",{}).get("spider",{}).get("source_island_year_Event_counts"),
        "original_spider_Occurrence_rows_opened":0,
        "stop_reason":result.get("stop_reason")
    },sort_keys=True))
    if result["status"]=="SOURCE_OR_ORIGINAL_EVENT_FORMAT_STOP":
        raise SystemExit(2)
if __name__=="__main__":main()
