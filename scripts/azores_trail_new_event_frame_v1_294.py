#!/usr/bin/env python3
"""v1.294 source-Event-only, independent 2017-19 native forest trail frame.

A NEW explicitly retrospective design; old v1.292 remains terminal.
Never reads original Occurrence rows or any native/alien labels.
"""
import argparse,hashlib,json,urllib.request
from collections import Counter,defaultdict
from pathlib import Path
from azores_trail_plants_event_hierarchy_v1_292 import SHA,SOURCE,parse_source_events

def norm(s): return " ".join(str(s or "").casefold().split())

def parse_event(e):
    ident=str(e.get("eventID","")).strip()
    parts=ident.split(".")
    if len(parts)<5: return None,"bad_id_token_length"
    year=parts[0]
    if year not in ("2017","2018","2019"):return None,"unexpected_event_year"
    trail=".".join(parts[1:-3]).casefold()
    if not trail:return None,"empty_trail_name"
    area,plot,line=[k.strip().casefold() for k in parts[-3:]]
    if area=="control50":area="control_50"
    if area not in {"0","50","250","max","control_50"}:
        return None,"unrecognized_sampling_area"
    if plot not in {"1","2","3"}:return None,"unrecognized_physical_plot"
    if line not in {"25","50","100","150"} or (line=="25" and plot!="1"):
        return None,"unrecognized_or_incompatible_line"
    source_year=str(e.get("year","")).strip()
    date=str(e.get("eventDate","")).strip()[:4]
    if (source_year and source_year!=year) or date!=year:
        return None,"year_source_field_disagreement"
    island=norm(e.get("island"))
    if island in {"sao miguel","são miguel"}:island="São Miguel"
    elif island=="terceira":island="Terceira"
    else:return None,"unsupported_island"
    return (island,year,trail,area,plot,line),None

def profile(events,contract):
    if len(events)!=contract["source"]["original_event_rows"]:
        raise ValueError("Original 210 Event identity/denominator not matched")
    seen_core=set();seen_id=set();excluded=Counter();parsed={}
    tree=defaultdict(lambda:defaultdict(set))
    for e in events:
        original_core=str(e.get("original_coreid","")).strip()
        author_id=str(e.get("eventID","")).strip()
        if not original_core or not author_id or original_core in seen_core or author_id in seen_id:
            raise ValueError("Original core ID or author Event ID is duplicate/missing")
        seen_core.add(original_core);seen_id.add(author_id)
        parts,reason=parse_event(e)
        if reason:
            excluded[reason]+=1
            continue
        island,year,trail,area,plot,line=parts
        key=(island,year,trail,area)
        if line in tree[key][plot]:
            raise ValueError("Duplicate original physical trail-plot-line slot")
        tree[key][plot].add(line)
        parsed[original_core]=parts
    unmatched_ratio=sum(excluded.values())/len(events)
    need=set(("50","100","150"))
    matched=defaultdict(set)
    matched_groups=Counter()
    accepted_cores=[]
    matched_interior_plot_count=Counter()
    for key,plots in tree.items():
        isl,year,trail,area=key
        if not need.issubset(plots.get("1",set())):continue
        interiors=[p for p in ("2","3") if need.issubset(plots.get(p,set()))]
        if not interiors:continue
        matched[isl].add(trail)
        matched_groups[isl]+=1
        matched_interior_plot_count[len(interiors)]+=1
        allowed={"1",*interiors}
        accepted_cores.extend([core for core,v in parsed.items() if v[:4]==key and v[4] in allowed and v[5] in need])
    qualifying=(unmatched_ratio<=1-contract["fixed_sampling_eligibility"]["min_source_event_retention_fraction"]
         and all(len(matched[isl])>=contract["fixed_sampling_eligibility"]["minimum_independent_trails_per_island"] for isl in ("Terceira","São Miguel"))
         and sum(matched_groups.values())>=contract["fixed_sampling_eligibility"]["minimum_matched_area_year_groups_total"])
    return {
      "schema":"structural.azores_trail_post_event_frame_result.v1_294",
      "status":"RETROSPECTIVE_MATCHED_FRAME_PASS_ONLY_OCCURRENCE_STILL_SEALED" if qualifying
          else "RETROSPECTIVE_PHYSICAL_FRAME_TERMINAL_NO_BIOLOGY",
      "original_2026_v1_4_Event_rows":len(events),
      "structurally_parsed_event_rows":len(parsed),
      "excluded_Event_rows":sum(excluded.values()),
      "excluded_Event_reasons":dict(sorted(excluded.items())),
      "excluded_fraction":unmatched_ratio,
      "matched_trails_by_island":{"Terceira":len(matched["Terceira"]),"São Miguel":len(matched["São Miguel"])},
      "matched_trail_year_area_groups_by_island":{"Terceira":matched_groups["Terceira"],"São Miguel":matched_groups["São Miguel"]},
      "matched_interior_plot_count_per_group":dict(sorted(matched_interior_plot_count.items())),
      "number_source_Event_rows_qualifying_for_future_score":len(accepted_cores),
      "future_scoring_event_coreids_sha256":hashlib.sha256("\n".join(sorted(accepted_cores)).encode()).hexdigest(),
      "all_25cm_lines_excluded_from_equal_effort_comparison":True,
      "v1_292_original_gate_terminal_immutable":True,
      "new_exploratory_not_pristine_confirmatory":True,
      "original_Occurrence_rows_opened":0,
      "original_species_or_nativeness_values_opened":0,
      "new_confirmatory_systems":0,"GEB_scientific_HOLD":True,"eBird_used":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--protocol",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    c=json.loads(a.protocol.read_text(encoding="utf-8"))
    if (c.get("schema")!="structural.azores_trail_post_event_diagnostic_physical_gate.v1_294" or
        c.get("status")!="NEW_RETROSPECTIVE_EVENT_EXPOSED_RESPONSE_SEALED_PROTOCOL_FROZEN" or
        c["source"]["sha256"]!=SHA or c["source"]["archive_url"]!=SOURCE):
        raise ValueError("v1.294 not frozen")
    result={"schema":"structural.azores_trail_post_event_frame_result.v1_294","status":"SOURCE_OR_FRAME_ERROR_STOP",
         "original_Occurrence_rows_opened":0,"GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-Azores-Trail-Event-Frame-v1.294"})
        with urllib.request.urlopen(req,timeout=60) as r:source=r.read(1_000_001)
        if len(source)>1_000_000 or hashlib.sha256(source).hexdigest()!=SHA:
            raise ValueError("Source zip hash differs from v1.291")
        result=profile(parse_source_events(source),c)
        result["original_source_zip_sha256"]=SHA
    except Exception as e:
        result["stop_type"]=type(e).__name__;result["stop_reason"]=str(e)[:300]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:result.get(k) for k in ("status","original_2026_v1_4_Event_rows",
         "excluded_Event_reasons","matched_trails_by_island","matched_trail_year_area_groups_by_island",
         "number_source_Event_rows_qualifying_for_future_score","original_Occurrence_rows_opened",
         "stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_OR_FRAME_ERROR_STOP":raise SystemExit(2)
if __name__=="__main__":main()
