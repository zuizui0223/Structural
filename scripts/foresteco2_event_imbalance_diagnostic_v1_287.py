#!/usr/bin/env python3
"""Response-opaque ForestEco2 source Event imbalance audit after v1.286 STOP.

Reads ORIGINAL Event survey design only; publishes aggregated nine-cell counts
and never reads Occurrence body, S1 labels, or protected outcomes.
"""
import argparse
from collections import Counter
import hashlib,json,urllib.request
from pathlib import Path

from foresteco2_event_only_qualification_v1_286 import (
    SOURCE,SOURCE_SHA,_read_author_event_only,_norm
)

def diagnostic(events,v286):
    islands={_norm(v):i for i,vv in v286["frozen_group_definitions"]["islands"].items() for v in vv}
    habitats={_norm(v):k for k,vv in v286["frozen_group_definitions"]["habitat"].items() for v in vv}
    if len(events)!=90:
        raise ValueError("Original event set is not exactly frozen 90")
    n=Counter();raw=Counter();years=Counter();sites=set()
    for e in events:
        isl=islands.get(_norm(e.get("island")))
        hab=habitats.get(_norm(e.get("habitat")))
        if isl is None or hab is None:
            raise ValueError("Source site habitat or island does not match original frozen categories")
        n[(isl,hab)]+=1
        raw[(isl,str(e.get("habitat","")).strip())]+=1
        years[str(e.get("eventDate",""))[:4]]+=1
        key=(isl,str(e.get("locationID","")).strip())
        if not key[1] or key in sites: raise ValueError("Not 90 independent author locations")
        sites.add(key)
    grid={isl:{h:n[(isl,h)] for h in ("NF","EW","PF")} for isl in ("Pico","Terceira","São Miguel")}
    grid_exact=all(v==10 for r in grid.values() for v in r.values())
    assert sum(sum(row.values()) for row in grid.values())==90
    return {
        "schema":"structural.foresteco2_event_imbalance_diagnostic_result.v1_287",
        "status":"V1_286_REMAINS_TERMINAL_RESPONSE_UNOPENED",
        "original_Event_rows_examined":90,
        "independent_author_locations":len(sites),
        "island_forest_type_counts":grid,
        "island_totals":{isl:sum(row.values()) for isl,row in grid.items()},
        "exact_predeclared_10_per_type_gate_met":grid_exact,
        "published_claimed_equal_10_per_type":True,
        "habitat_code_vocabulary_counts_by_island":{
            isl:{label:count for (i,label),count in sorted(raw.items()) if i==isl}
            for isl in ("Pico","Terceira","São Miguel")},
        "original_year_counts":dict(sorted(years.items())),
        "strict_v1_286_fail_must_not_be_overridden":True,
        "Occurrence_data_rows_opened":0,
        "S1_loss_taxa_values_opened":0,
        "focal_prediction_scores":0,
        "protected_mammal_BioTIME_RLS_rows_opened":0,
        "confirmatory_admissions":0,
        "GEB_scientific_HOLD":True,
        "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--earlier-protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.protocol.read_text(encoding="utf-8"))
    q=json.loads(args.earlier_protocol.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.foresteco2_post_event_failure_diagnostic.v1_287"
        or c["status"]!="RESPONSE_SEALED_EVENT_ONLY_DIAGNOSTIC_AFTER_V1_286_TERMINAL"
        or c["archive_sha256"]!=SOURCE_SHA
        or q["schema"]!="structural.foresteco2_event_only_qualification.v1_286"):
        raise ValueError("Unfrozen post-gate Event diagnostic")
    result={"schema":"structural.foresteco2_event_imbalance_diagnostic_result.v1_287",
            "status":"STOP_MISSING_OR_MALFORMED_SOURCE","Occurrence_data_rows_opened":0,
            "focal_prediction_scores":0,"GEB_scientific_HOLD":True,"confirmatory_admissions":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-ForestEco2-after-STOP-Event-only-v1.287"})
        with urllib.request.urlopen(req,timeout=60) as f: archive=f.read(5_000_001)
        if len(archive)>5_000_000 or hashlib.sha256(archive).hexdigest()!=SOURCE_SHA:
            raise ValueError("Source hash is no longer frozen original")
        result=diagnostic(_read_author_event_only(archive),q)
    except Exception as e:
        result["stop_type"]=type(e).__name__;result["stop_reason"]=str(e)[:350]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],
        "grid":result.get("island_forest_type_counts"),
        "raw_habitats":result.get("habitat_code_vocabulary_counts_by_island"),
        "Occurrence_data_rows_opened":0,
        "stop_reason":result.get("stop_reason")},sort_keys=True))
    if result["status"]!="V1_286_REMAINS_TERMINAL_RESPONSE_UNOPENED":raise SystemExit(2)

if __name__=="__main__":main()
