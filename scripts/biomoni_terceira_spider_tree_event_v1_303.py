#!/usr/bin/env python3
"""v1.303: ten shared Terceira spider/tree forest plot IDs and Event-only effort.

No source Occurrence bytes, taxon labels, abundance or old beetle outcomes are
opened. Original exact source hashes and author's plot codes cannot be tuned.
"""
import argparse,hashlib,json,urllib.request
from pathlib import Path
from collections import Counter
from biomoni_terceira_event_colocation_v1_298 import (
    extract_event_core_only,summarize_site_samples,MAX_BYTES
)
SPIDER="https://ipt.gbif.pt/ipt/archive.do?r=spiders_macaronesia_azores&v=1.8"
SPIDER_SHA="17f65284214ae35a302fee2fa42747e2ecfabb8d04bf9ec8394b6d33c5c4f7b5"
TREE="https://ipt.gbif.pt/ipt/archive.do?r=biomoni_trees&v=1.7"
TREE_SHA="4574d02727654ec5a319f6d1218ff9243080b0128c517d01c905065cbefd6f82"
def evaluate(t_events,s_events,contract):
    rules=contract["event_only_rules"]
    if len(t_events)!=30 or len(s_events)!=423:
        raise ValueError("Original published Event row counts do not match the fixed source")
    tree=summarize_site_samples(t_events,"woody")
    spider=summarize_site_samples(s_events,"spider")
    if len(tree)!=10 or len(spider)!=10 or set(tree)!=set(spider):
        return {"status":"STOP_ORIGINAL_TEN_PHYSICAL_SITE_BIJECTION_MISSING",
                "tree_site_count":len(tree),"spider_site_count":len(spider),
                "exact_shared_site_count":len(set(tree)&set(spider)),
                "spider_Event_rows_opened":len(s_events),"original_spider_Occurrence_rows_opened":0,
                "original_woody_Occurrence_rows_reopened":0,"GEB_scientific_HOLD":True,
                "new_confirmatory_systems":0,"eBird_used":False}
    if any(len(v)!=1 for v in tree.values()):
        raise ValueError("Original woody plot Event was not one per physical site")
    coord=[];offset=[];modes=[];effort=[]
    for key in sorted(tree):
        w=tree[key][0];s=spider[key]
        coord.append(max(max(abs(x["lat"]-w["lat"]),abs(x["lon"]-w["lon"])) for x in s))
        offset.append(min(abs(x["year"]-w["year"]) for x in s))
        modes.append(Counter(x["method"] for x in s))
        effort.append(len(s))
    common=set.intersection(*(set(m) for m in modes))
    minimum={m:min(c[m] for c in modes) for m in common}
    selected=[]
    for site in sorted(spider):
        for m in sorted(common):
            rows=sorted(x["core"] for x in spider[site] if x["method"]==m)
            selected.extend(rows[:minimum[m]])
    sel_sha=hashlib.sha256("\n".join(sorted(selected)).encode()).hexdigest()
    matching_sha=hashlib.sha256("\n".join(f"{site}|{tree[site][0]['core']}|"+
        ",".join(sorted(x["core"] for x in spider[site]))
        for site in sorted(spider)).encode()).hexdigest()
    criteria=(max(coord)<=rules["max_abs_coordinate_difference_degrees"]
              and max(offset)<=rules["max_paired_year_gap"]
              and min(effort)>=rules["min_spider_Event_rows_per_site"]
              and max(effort)/min(effort)<=rules["max_event_effort_ratio"]
              and len(common)>=rules["min_common_protocol_modes"]
              and len(selected)>=10*rules["min_spider_Event_rows_per_site"])
    return {"schema":"structural.biomoni_spider_tree_event_result.v1_303",
       "status":("TEN_SITE_SPIDER_TREE_EVENT_FRAME_QUALIFIED_RESPONSES_SEALED"
                 if criteria else "TERMINAL_SITE_COORDINATE_OR_SPIDER_METHOD_EFFORT"),
       "original_tree_Event_rows":len(t_events),
       "original_spider_Event_rows":len(s_events),
       "exact_terceira_original_woody_spider_shared_sites":10,
       "max_coordinate_abs_difference_degrees":max(coord),
       "max_year_offset":max(offset),
       "spider_original_Events_per_site_min_max":[min(effort),max(effort)],
       "common_spider_method_count":len(common),
       "common_spider_method_min_counts_anonymized":sorted(minimum.values()),
       "selected_equal_mode_spider_Events_per_site":sum(minimum.values()),
       "selected_equal_mode_spider_Events_total":len(selected),
       "selected_original_spider_Event_coreids_SHA256":sel_sha,
       "complete_woody_spider_original_site_crosswalk_SHA256":matching_sha,
       "sample_methods_selected_before_any_spider_taxon_values":True,
       "original_spider_Occurrence_rows_opened":0,
       "original_woody_Occurrence_rows_reopened":0,
       "original_beetle_Occurrence_rows_reopened":0,
       "original_site_IDs_coordinates_or_method_labels_exported":False,
       "one_island_only":True,
       "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--protocol",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    c=json.loads(args.protocol.read_text())
    if (c.get("schema")!="structural.biomoni_terceira_spider_tree_event_crosswalk.v1_303"
        or c["status"]!="FROZEN_BEFORE_SPIDER_ORIGINAL_EVENT_VALUES"
        or c["source"]["spider_archive"]!=SPIDER or c["source"]["spider_sha256"]!=SPIDER_SHA
        or c["source"]["tree_archive"]!=TREE or c["source"]["tree_sha256"]!=TREE_SHA):
        raise ValueError("Spider/tree physical co-location design not frozen")
    result={"schema":"structural.biomoni_spider_tree_event_result.v1_303",
            "status":"SOURCE_OR_EVENT_TECHNICAL_STOP",
            "original_spider_Occurrence_rows_opened":0,
            "original_woody_Occurrence_rows_reopened":0,
            "original_beetle_Occurrence_rows_reopened":0,
            "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        events=[]
        for source,sha in ((TREE,TREE_SHA),(SPIDER,SPIDER_SHA)):
            req=urllib.request.Request(source,headers={"User-Agent":"Structural-ThirdGuild-Original-EventOnly-v1.303"})
            with urllib.request.urlopen(req,timeout=60) as remote: blob=remote.read(MAX_BYTES+1)
            if len(blob)>MAX_BYTES or hashlib.sha256(blob).hexdigest()!=sha:
                raise ValueError("Original third-guild archive checksum changed")
            events.append(extract_event_core_only(blob))
        result=evaluate(events[0],events[1],c)
    except Exception as e:
        result["stop_type"]=type(e).__name__
        result["stop_reason"]=str(e)[:230]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:result.get(k) for k in ("status","exact_terceira_original_woody_spider_shared_sites",
      "tree_site_count","spider_site_count","spider_original_Events_per_site_min_max",
      "common_spider_method_count","selected_equal_mode_spider_Events_per_site",
      "original_spider_Occurrence_rows_opened","stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_OR_EVENT_TECHNICAL_STOP":raise SystemExit(2)
if __name__=="__main__":main()
