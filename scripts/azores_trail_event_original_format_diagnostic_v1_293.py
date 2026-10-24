#!/usr/bin/env python3
"""v1.293 safe Event-only grammar diagnosis after v1.292 terminal STOP.

No occurrence body opened; no plot/trail/Event IDs or taxon names exported.
"""
import argparse,hashlib,json,urllib.request
from collections import Counter
from pathlib import Path
from azores_trail_plants_event_hierarchy_v1_292 import SHA,SOURCE,parse_source_events

def audit_syntax(events):
    years=Counter(); lengths=Counter(); suffix=Counter(); weird=Counter();single=Counter()
    domain={ "area":set(("0","50","250","max","control_50")),
             "plot":set(("1","2","3")),
             "line":set(("25","50","100","150"))}
    n=0
    for row in events:
        p=str(row.get("eventID","")).strip().split(".")
        lengths[len(p)]+=1
        if len(p)<5: weird["too_few_dot_tokens"]+=1;continue
        prefix=p[0]
        area,plot,line=[x.strip().casefold() for x in p[-3:]]
        years[prefix if prefix in ("2017","2018","2019") else "unrecognized_year"]+=1
        yearcol=str(row.get("year","")).strip()
        datecol=str(row.get("eventDate","")).strip()[:4]
        if yearcol and yearcol!=prefix:weird["year_column_mismatch"]+=1
        if datecol!=prefix:weird["eventDate_year_mismatch"]+=1
        for key,val in (("area",area),("plot",plot),("line",line)):
            if val not in domain[key]:
                weird["unrecognized_"+key]+=1
                # Abstract the unrecognized token only, not the original
                # physical trail/site name (do not disclose Event IDs).
                display=(val if len(val)<=25 and val.replace("_","").replace("-","").isalnum()
                         else "[other-format]")
                single[(key,display)]+=1
        if area in domain["area"] and plot in domain["plot"] and line in domain["line"]:
            suffix[(area,plot,line)]+=1
        n+=1
    return {
      "schema":"structural.azores_trail_event_format_diagnostic_result.v1_293",
      "status":"RESPONSE_UNOPENED_EVENT_FORMAT_DIAGNOSED_OLD_V1_292_TERMINAL",
      "original_Event_rows_examined":len(events),
      "original_Event_ID_token_count_distribution":dict(sorted(lengths.items())),
      "Event_first_year_token_counts":dict(sorted(years.items())),
      "source_year_or_code_mismatch_counts":dict(sorted(weird.items())),
      "unrecognized_published_area_plot_line_code_vocabulary_counts":[
          {"code_kind":a,"value":b,"count":c}
          for (a,b),c in sorted(single.items())],
      "accepted_published_suffix_pattern_counts":[
          {"area":a,"plot":b,"line":c,"count":n} for (a,b,c),n in sorted(suffix.items())],
      "source_Event_or_site_full_identifier_exported":False,
      "original_Occurrence_data_rows_opened":0,
      "species_or_nativeness_values_opened":0,
      "old_v1_292_remains_terminal":True,
      "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    contract=json.loads(args.contract.read_text(encoding="utf-8"))
    if contract.get("schema")!="structural.azores_trail_event_original_format_diagnostic.v1_293" or (
       contract.get("status")!="RESPONSE_SEALED_SOURCE_EVENT_METADATA_AFTER_V1_292_TERMINAL" or
       contract["source"]["sha256"]!=SHA or contract["source"]["archive"]!=SOURCE):
        raise ValueError("Unfrozen v1.293 diagnostic")
    result={"schema":"structural.azores_trail_event_format_diagnostic_result.v1_293",
            "status":"SOURCE_ONLY_TERMINAL_TRANSPORT","original_Occurrence_data_rows_opened":0,
            "species_or_nativeness_values_opened":0,"old_v1_292_remains_terminal":True,
            "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-Azores-Trail-Event-Diagnostic-v1.293"})
        with urllib.request.urlopen(req,timeout=60) as r:archive=r.read(1_000_001)
        if len(archive)>1_000_000 or hashlib.sha256(archive).hexdigest()!=SHA:
            raise ValueError("Original ZIP identity changed")
        result=audit_syntax(parse_source_events(archive))
        result["archive_sha256"]=SHA
    except Exception as e:
        result["stop_type"]=type(e).__name__;result["stop_reason"]=str(e)[:250]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],
       "original_Event_rows_examined":result.get("original_Event_rows_examined"),
       "Event_first_year_token_counts":result.get("Event_first_year_token_counts"),
       "source_year_or_code_mismatch_counts":result.get("source_year_or_code_mismatch_counts"),
       "unrecognized_codes":result.get("unrecognized_published_area_plot_line_code_vocabulary_counts"),
       "original_Occurrence_rows_opened":0,
       "stop_reason":result.get("stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_ONLY_TERMINAL_TRANSPORT":raise SystemExit(2)
if __name__=="__main__":main()
