#!/usr/bin/env python3
"""v1.292: fixed-sha Azores trail Event-only physical hierarchy audit.

Never opens the Occurrence extension, species identity or nativeness.
Reports only aggregate 2-island/4-trail/area matched-line eligibility, not
fake independent 260 line-level replicates.
"""
import argparse,csv,hashlib,io,json,re,urllib.request,xml.etree.ElementTree as ET,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from azores_trail_plants_opaque_source_v1_291 import SOURCE,UUID,parse_opaque_archive

SHA="c6c6ad82e268759aade344528c3649459ed323053969c1ef8053f3f518298da7"

def local(tag):return tag.rsplit("}",1)[-1]
def term(tag):return tag.rstrip("/").split("/")[-1].split("#")[-1]
def norm(x):return " ".join(str(x or "").casefold().strip().split())

def parse_source_events(archive):
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        root=ET.fromstring(z.read("meta.xml"))
        core=next(e for e in root if local(e.tag)=="core")
        cols={};idx=None;path=None
        for e in core.iter():
            if local(e.tag)=="field" and "term" in e.attrib and "index" in e.attrib:
                cols[term(e.attrib["term"])]=int(e.attrib["index"])
            elif local(e.tag)=="id":idx=int(e.attrib["index"])
            elif local(e.tag)=="location" and e.text:path=e.text.strip()
        if idx is None or not path or not {"eventID","eventDate","island"}.issubset(cols):
            raise ValueError("Original Event source lacks frozen key/year/island columns")
        delim=core.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        if len(delim)!=1:raise ValueError("Unexpected Event delimiter")
        ignored=int(core.attrib.get("ignoreHeaderLines","0"))
        if ignored<0 or ignored>2:raise ValueError("Unexpected Event header skip")
        out=[]
        with z.open(path) as src:
            with io.TextIOWrapper(src,encoding="utf-8-sig",newline="") as f:
                reader=csv.reader(f,delimiter=delim)
                for _ in range(ignored):next(reader,None)
                for line in reader:
                    if not line or not any(line):continue
                    if idx>=len(line) or any(cols[x]>=len(line) for x in ("eventID","eventDate","island")):
                        raise ValueError("Malformed original Event line")
                    item={k:line[v] for k,v in cols.items() if v<len(line)}
                    item["original_coreid"]=line[idx]
                    out.append(item)
        return out

def parse_event_label(value):
    parts=str(value or "").strip().split(".")
    if len(parts)<5:raise ValueError("Unrecognized author Event ID number of dot components")
    year=parts[0]
    area,plot,line=parts[-3:]
    trail=".".join(parts[1:-3]).casefold().strip()
    if not trail or year not in ("2017","2018","2019") or area.casefold() not in ("0","50","250","max","control_50"):
        raise ValueError("Unexpected source year, trail, or area")
    if plot not in ("1","2","3") or line not in ("25","50","100","150"):
        raise ValueError("Unexpected author plot or line code")
    if plot in ("2","3") and line=="25":
        raise ValueError("25-cm line allowed only on edge plot 1")
    return year,trail,area.casefold(),plot,line

def audit(events,contract):
    seen_e=set();seen_core=set();raw=Counter()
    tree=defaultdict(lambda:defaultdict(set))
    by_island_trails=defaultdict(set)
    for e in events:
        ident=str(e.get("eventID","")).strip()
        core=str(e.get("original_coreid","")).strip()
        if not ident or not core or ident in seen_e or core in seen_core:
            raise ValueError("Nonunique original Event identifier or core ID")
        seen_e.add(ident);seen_core.add(core)
        year,trail,area,plot,line=parse_event_label(ident)
        island=norm(e.get("island"))
        if island in ("são miguel","sao miguel"):isl="São Miguel"
        elif island=="terceira":isl="Terceira"
        else:raise ValueError("Event outside two prospectively frozen islands")
        yr=str(e.get("year","")).strip()
        date=str(e.get("eventDate","")).strip()
        if date[:4]!=year or (yr and yr!=year):
            raise ValueError("Date/year in original source Event differs from eventID")
        if "fieldNumber" in e and str(e["fieldNumber"]).strip() and str(e["fieldNumber"]).strip()!=ident:
            # Metadata does not equate fieldNumber with eventID; keep source value
            # response independent and do not fail unless explicitly required.
            pass
        raw[(isl,year,area,plot,line)]+=1
        tree[(isl,year,trail,area)][plot].add(line)
        by_island_trails[isl].add(trail)
    common=set(contract["qualified_minimum"]["matched_common_lines_for_each_plot"])
    groups_by_island=Counter();eligible_trails=defaultdict(set)
    interior_per_group=Counter()
    for key,plots in tree.items():
        island,year,trail,area=key
        edge=common.issubset(plots.get("1",set()))
        inside=[p for p in ("2","3") if common.issubset(plots.get(p,set()))]
        if edge and inside:
            groups_by_island[island]+=1
            eligible_trails[island].add(trail)
            interior_per_group[len(inside)]+=1
    viable=(len([x for x in eligible_trails if eligible_trails[x]])>=2 and
            sum(len(v) for v in eligible_trails.values())>=contract["qualified_minimum"]["independent_trails_total"] and
            all(len(eligible_trails[i])>=1 and groups_by_island[i]>=1
                for i in ("Terceira","São Miguel")) and
            sum(groups_by_island.values())>=contract["qualified_minimum"]["matched_area_year_trail_groups_total"])
    return {
      "schema":"structural.azores_trail_2017_19_event_only_result.v1_292",
      "status":"MATCHED_TRAIL_LINE_FRAME_POSSIBLE_OCCURRENCE_UNOPENED" if viable
               else "SOURCE_ONLY_TERMINAL_NO_MATCHED_TRAIL_FRAME",
      "original_Event_rows_opened":len(events),"source_distinct_event_ids":len(seen_e),
      "source_distinct_coreids":len(seen_core),
      "number_unique_source_trails_by_island":{k:len(by_island_trails[k]) for k in ("Terceira","São Miguel")},
      "number_complete_edge_and_interior_trails_by_island":{k:len(eligible_trails[k]) for k in ("Terceira","São Miguel")},
      "source_year_counts":dict(sorted(Counter(k[1] for k in raw for _ in range(raw[k])).items())),
      "number_unique_trail_year_area_groups":len(tree),
      "matched_fully_sampled_area_year_groups_by_island":{k:groups_by_island[k] for k in ("Terceira","São Miguel")},
      "matched_interior_plots_per_eligible_group":dict(sorted(interior_per_group.items())),
      "line_event_totals_by_island":{k:sum(v for q,v in raw.items() if q[0]==k) for k in ("Terceira","São Miguel")},
      "excluded_25cm_line_from_future_matched_comparison":True,
      "original_Occurrence_rows_opened":0,"plant_names_or_native_placement_read":0,
      "qualifies_only_future_protocol_freeze_not_plant_access":viable,
      "not_4_independent_island_replicates":True,
      "not_causal_trampling_study":True,
      "confirmatory_systems_admitted":0,"GEB_scientific_HOLD":True,"eBird_used":False
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8"))
    if c.get("schema")!="structural.azores_trail_event_only_hierarchy_gate.v1_292" or (
       c.get("status")!="FROZEN_BEFORE_OPENING_ORIGINAL_V1_4_EVENT_ROWS" or
       c["source"]["expected_zip_sha256"]!=SHA or c["source"]["archive_url"]!=SOURCE):
        raise ValueError("Unknown or unfrozen original Event gate")
    result={"schema":"structural.azores_trail_2017_19_event_only_result.v1_292",
            "status":"SOURCE_OR_EVENT_FORMAT_STOP","original_Event_rows_opened":0,
            "original_Occurrence_rows_opened":0,"plant_names_or_native_placement_read":0,
            "GEB_scientific_HOLD":True,"confirmatory_systems_admitted":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-Azores-Trail-EventOnly-v1.292"})
        with urllib.request.urlopen(req,timeout=60) as remote:archive=remote.read(1_000_001)
        if len(archive)>1_000_000 or hashlib.sha256(archive).hexdigest()!=SHA:
            raise ValueError("Original v1.4 exact ZIP identity changed")
        m=parse_opaque_archive(archive)
        if m["status"]!="SCHEMA_POSSIBLE_EVENT_UNOPENED":
            raise ValueError("v1.291 original source meta not eligible")
        rows=parse_source_events(archive)
        result["original_Event_rows_opened"]=len(rows)
        result=audit(rows,c)
        result["original_archive_sha256"]=SHA
    except Exception as e:
        result["stop_type"]=type(e).__name__;result["stop_reason"]=str(e)[:350]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:result.get(k) for k in ("status","original_Event_rows_opened",
       "number_unique_source_trails_by_island","number_complete_edge_and_interior_trails_by_island",
       "matched_fully_sampled_area_year_groups_by_island","original_Occurrence_rows_opened","stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_OR_EVENT_FORMAT_STOP":raise SystemExit(2)

if __name__=="__main__":main()
