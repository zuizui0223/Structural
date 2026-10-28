#!/usr/bin/env python3
"""v1.307: NEW eight physically compatible Terceira spider/tree plots, Event only.

Keeps permanently failed 10-plot v1.303/v1.304 endpoints terminal.
Fixes *nothing* about the old design and does not open any biological
Occurrence. All source/target site selection is response-independent.
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

def date_year(value):
    text=str(value or "").strip()
    m=re.match(r"^(\d{4})(?:-|$)",text)
    if m:return int(m.group(1))
    m=re.match(r"^\d{1,2}[-/]\d{1,2}[-/](\d{4})(?:\b|$)",text)
    return int(m.group(1)) if m else None

def event_index(rows,kind):
    sites=defaultdict(list);seen=set();n_terceira=0
    for e in rows:
        core=str(e.get("source_coreid","")).strip()
        if not core or core in seen:raise ValueError("Original author Event coreid missing or duplicated")
        seen.add(core)
        if norm(e.get("island"))!="terceira":continue
        n_terceira+=1
        key=normalized_site(e.get("locationID"))
        if not key:raise ValueError("Original Terceira author site key absent")
        yy=date_year(e.get("eventDate"))
        col=str(e.get("year","")).strip()
        if yy not in (2012,2013) or col!=str(yy):
            raise ValueError("Original Terceira date and explicit year field not 2012/2013 consistent")
        try:lat=float(e.get("decimalLatitude"));lon=float(e.get("decimalLongitude"))
        except (ValueError,TypeError):raise ValueError("Original author geographic coordinates cannot be verified")
        if not all(map(math.isfinite,(lat,lon))):raise ValueError("Original author coordinates not finite")
        method=norm(e.get("samplingProtocol"))
        if not method:raise ValueError("Original sampling method identity missing")
        sites[key].append({"core":core,"lat":lat,"lon":lon,"year":yy,"method":method})
    if len(sites)!=10:
        raise ValueError(f"Original {kind} source did not contain exactly ten Terceira plot IDs")
    return sites,n_terceira

def qualify(tree_rows,spider_rows,contract):
    if len(tree_rows)!=30 or len(spider_rows)!=423:
        raise ValueError("Original source archive Event row totals changed")
    tree,tree_n=event_index(tree_rows,"tree")
    spider,spider_n=event_index(spider_rows,"spider")
    if tree_n!=10 or spider_n!=260:
        raise ValueError("Frozen original Terceira Event population changed")
    if set(tree)!=set(spider) or any(len(x)!=1 for x in tree.values()):
        raise ValueError("Ten nominal author forest plot keys not bijective")
    rules=contract["fixed_response_blind_criteria"]
    cutoff=0.0003
    sites_qualified=[];fails=[];over=0
    all_methods=[Counter(x["method"] for x in spider[k]) for k in sorted(spider)]
    common=set.intersection(*(set(x) for x in all_methods))
    min_modes={m:min(x[m] for x in all_methods) for m in common}
    if len(common)!=rules["original_spider_modes_shared_across_all_ten_nominal_sites"] or sorted(min_modes.values())!=rules["minimum_events_per_common_spider_mode_across_all_ten_sorted"]:
        return {"status":"STOP_SOURCE_METHOD_MULTIPLICITY_NOT_FROZEN","spider_woody_Occurrence_opened":0,
                "old_303_GATE_TERMINAL":True,"GEB_scientific_HOLD":True,
                "new_confirmatory_systems":0,"eBird_used":False}
    maxd=[]
    for k in sorted(tree):
        t=tree[k][0]
        dates=[abs(t["year"]-x["year"]) for x in spider[k]]
        if max(dates)>rules["paired_woody_spider_calendar_year_difference_max"]:
            raise ValueError("Original tree–spider sampling year gap exceeds frozen threshold")
        diffs=[max(abs(t["lat"]-x["lat"]),abs(t["lon"]-x["lon"])) for x in spider[k]]
        maxd.append(max(diffs))
        over+=sum(v>cutoff for v in diffs)
        if max(diffs)<=cutoff:
            sites_qualified.append(k)
        else:fails.append(k)
    if (len(sites_qualified)!=rules["require_eligible_site_count"]
        or len(fails)!=rules["require_excluded_site_count"]
        or over!=rules["original_source_mismatch_events_expected"]):
        return {
           "status":"STOP_SPATIAL_QUALIFIED_EIGHT_PLOT_FRAME_NOT_FROZEN",
           "source_compatible_sites":len(sites_qualified),
           "source_coordinate_mismatch_events":over,
           "original_spider_Occurrence_rows_opened":0,
           "old_303_GATE_TERMINAL":True,"GEB_scientific_HOLD":True,
           "new_confirmatory_systems":0,"eBird_used":False
        }
    selected=[];pairing=[]
    for site in sites_qualified:
        sample=[]
        for mode in sorted(common):
            coreids=sorted(x["core"] for x in spider[site] if x["method"]==mode)
            minimum=min_modes[mode]
            if len(coreids)<minimum:
                raise ValueError("Original common method minimum not reached in selected plot")
            sample.extend(coreids[:minimum])
        if len(sample)!=rules["original_event_count_per_selected_plot"]:
            raise ValueError("Equal-protocol effort count changed")
        selected.extend(sample)
        pairing.append(site+"|"+tree[site][0]["core"]+"|"+",".join(sorted(sample)))
    if len(selected)!=rules["selected_spider_event_total_expected"] or len(set(selected))!=len(selected):
        raise ValueError("Original fixed 8×23 Spider Event subset changed")
    return {
       "schema":"structural.biomoni_spider_eight_plot_source_result.v1_307",
       "status":"NEW_EXPLORATORY_EIGHT_PHYSICAL_PLOTS_EQUAL_SPIDER_METHODS_RESPONSE_SEALED",
       "original_tree_Event_rows":len(tree_rows),
       "original_spider_Event_rows":len(spider_rows),
       "original_tree_Terceira_plots":len(tree),
       "original_spider_Terceira_plots":len(spider),
       "nominal_Terceira_site_IDs_shared":len(tree),
       "spatially_matched_within_0_0003deg_sites":len(sites_qualified),
       "spatially_excluded_site_count":len(fails),
       "source_site_coordinates_outside_frozen_limit_event_count":over,
       "spider_common_original_method_count":len(common),
       "spider_shared_method_min_multiplicities_sorted":sorted(min_modes.values()),
       "selected_original_spider_Events_each_eligible_site":len(selected)//len(sites_qualified),
       "selected_original_spider_Events_total":len(selected),
       "source_original_qualified_tree_coreids_sha256":hashlib.sha256("\n".join(sorted(tree[k][0]["core"] for k in sites_qualified)).encode()).hexdigest(),
       "source_original_qualified_spider_coreids_sha256":hashlib.sha256("\n".join(sorted(selected)).encode()).hexdigest(),
       "source_original_physical_plot_and_subevent_join_sha256":hashlib.sha256("\n".join(sorted(pairing)).encode()).hexdigest(),
       "new_physical_subset_post_Event_QA_not_303_confirmation":True,
       "old_v1_303_and_304_full_ten_plot_gate_TERMINAL":True,
       "original_spider_Occurrence_rows_opened":0,
       "original_woody_Occurrence_rows_reopened":0,
       "original_beetle_Occurrence_rows_reopened":0,
       "exact_original_plot_names_and_coordinates_not_exported":True,
       "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.contract.read_text())
    if (c.get("schema")!="structural.biomoni_terceira_spider_eight_site_metadata_sample.v1_307"
        or c.get("status")!="EXPLORATORY_AFTER_EVENT_DIAGNOSTIC_BEFORE_SPIDER_SPECIES_RESPONSES"
        or any(c["source"][x+"_sha256"]!=SOURCE[x][1] for x in SOURCE)
        or any(c["source"][x+"_zip"]!=SOURCE[x][0] for x in SOURCE)):
        raise ValueError("Unfrozen original source-only eight-site sampling rule")
    res={
      "schema":"structural.biomoni_spider_eight_plot_source_result.v1_307",
      "status":"SOURCE_OR_SOURCE_EVENT_TECHNICAL_STOP",
      "original_spider_Occurrence_rows_opened":0,
      "original_woody_Occurrence_rows_reopened":0,
      "old_v1_303_and_304_full_ten_plot_gate_TERMINAL":True,
      "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        ev={}
        for kind,(url,sha,n) in SOURCE.items():
            req=urllib.request.Request(url,headers={"User-Agent":"Structural-BioMonI-EightPlot-v1.307-EventOnly"})
            with urllib.request.urlopen(req,timeout=60) as z:blob=z.read(MAX_BYTES+1)
            if len(blob)>MAX_BYTES or hashlib.sha256(blob).hexdigest()!=sha:
                raise ValueError("Original archive source identity mismatched")
            ev[kind]=extract_event_core_only(blob)
        res=qualify(ev["woody"],ev["spider"],c)
    except Exception as e:
        res["stop_type"]=type(e).__name__;res["stop_reason"]=str(e)[:260]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(res,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:res.get(k) for k in (
      "status","nominal_Terceira_site_IDs_shared","spatially_matched_within_0_0003deg_sites",
      "spatially_excluded_site_count","selected_original_spider_Events_each_eligible_site",
      "selected_original_spider_Events_total","original_spider_Occurrence_rows_opened",
      "stop_reason")},sort_keys=True))
    if res["status"]=="SOURCE_OR_SOURCE_EVENT_TECHNICAL_STOP":raise SystemExit(2)
if __name__=="__main__":main()
