#!/usr/bin/env python3
"""Source-locked Event-only BALA 1.0 seven-island longitudinal physical-site audit.

Inspect exactly 10,379 author Event source records and their survey metadata,
but NEVER open Occurrence/species/origin/abundance data. Do not treat nested
pitfall/beating Events as independent transect or island replicates.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,statistics,urllib.request,xml.etree.ElementTree as ET,zipfile
from collections import Counter,defaultdict
from pathlib import Path

SRC="https://ipt.gbif.pt/ipt/archive.do?r=bala_arthropods&v=1.0"
SHA="4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2"
MAX_BYTES=7_000_000

def _local(t):return t.rsplit("}",1)[-1]
def _term(t):return t.rstrip("/").split("/")[-1].split("#")[-1]
def _trim(t):return " ".join(str(t or "").strip().split())
def _norm(t):return _trim(t).casefold()

def original_event_rows(archive):
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        xml=ET.fromstring(z.read("meta.xml"))
        core=[n for n in xml if _local(n.tag)=="core"]
        if len(core)!=1:raise ValueError("Exactly one original Event core role needed")
        node=core[0]
        terms={};member=None;primary=None
        for x in node.iter():
            k=_local(x.tag)
            if k=="location" and x.text:member=x.text.strip()
            if k=="id" and "index" in x.attrib:primary=int(x.attrib["index"])
            if k=="field" and "term" in x.attrib and "index" in x.attrib:
                terms[_term(x.attrib["term"])]=int(x.attrib["index"])
        required={"eventID","year","eventDate","island","locationID","fieldNumber","samplingProtocol"}
        if member is None or primary is None or not required.issubset(terms):
            raise ValueError("Published BALA Event role no longer contains frozen site/year/method identifiers")
        delimiter=node.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        if len(delimiter)!=1:
            raise ValueError("Unexpected original BALA Event delimiter")
        skip=int(node.attrib.get("ignoreHeaderLines","0"))
        if not 0<=skip<=2:raise ValueError("Unexpected original BALA Event header skip")
        events=[]
        with z.open(member) as stream:
            with io.TextIOWrapper(stream,encoding="utf-8-sig",newline="") as textfile:
                reader=csv.reader(textfile,delimiter=delimiter)
                for _ in range(skip):next(reader,None)
                for fields in reader:
                    if not fields or not any(fields):continue
                    if max(primary,*(terms[k] for k in required))>=len(fields):
                        raise ValueError("Malformed Event row width in published original")
                    item={k:fields[i] for k,i in terms.items() if i<len(fields)}
                    item["__original_coreid"]=fields[primary]
                    events.append(item)
        return events

def assign_phase(year):
    if 1997<=year<=2004:return "B1"
    if 2010<=year<=2012:return "B2"
    if 2019<=year<=2022:return "B3"
    return None

def summarize(events,contract,expected_n=None):
    if expected_n is None:
        expected_n=contract["original_source"]["published_Event_rows"]
    if len(events)!=expected_n:
        raise ValueError("Original Event source count differs from frozen publication")
    island_allowed=set(contract["field_role"]["island_exact_expected"])
    ids=set();authors=set()
    island_counts=Counter();year_counts=Counter();phase_counts=Counter()
    method_counts=Counter();source_year_mismatch=0;non_numeric_year=0
    empty_site=0;unparsed_source_dates=0
    events_by_site_phase=Counter()
    events_by_site_phase_method=Counter()
    sites_by_phase=defaultdict(set)
    source_island_by_site={}
    original_n=0
    for v in events:
        core=_trim(v.get("__original_coreid"))
        author=_trim(v.get("eventID"))
        if not core or not author or core in ids or author in authors:
            raise ValueError("Original source Event primary ID or author eventID empty/duplicate")
        ids.add(core);authors.add(author)
        island=_norm(v.get("island"))
        yearstr=_trim(v.get("year"))
        source_date=_trim(v.get("eventDate"))
        if not yearstr.isdigit() or len(yearstr)!=4:
            non_numeric_year+=1;continue
        yr=int(yearstr)
        if source_date[:4].isdigit() and len(source_date)>=4:
            if int(source_date[:4])!=yr:source_year_mismatch+=1
        else:unparsed_source_dates+=1
        island_counts[island or "(missing)"]+=1
        year_counts[yr]+=1
        method=_trim(v.get("samplingProtocol"))
        method_counts[method or "(missing)"]+=1
        phase=assign_phase(yr)
        if not phase:
            phase_counts["OUTSIDE_FROZEN_PHASES"]+=1;continue
        phase_counts[phase]+=1
        if island not in island_allowed:
            phase_counts["OTHER_ISLAND_OR_SOURCE"]+=1;continue
        site=_trim(v.get("locationID"))
        if not site:
            empty_site+=1;continue
        key=(island,site)
        if key in source_island_by_site and source_island_by_site[key]!=island:
            raise ValueError("Source locationID changed island unexpectedly")
        source_island_by_site[key]=island
        sites_by_phase[phase].add(key)
        events_by_site_phase[key+(phase,)]+=1
        events_by_site_phase_method[key+(phase,method)]+=1
        original_n+=1
    phases=("B1","B2","B3")
    shared_all=set.intersection(*(sites_by_phase[p] for p in phases))
    shared_b13=sites_by_phase["B1"]&sites_by_phase["B3"]
    shared_b12=sites_by_phase["B1"]&sites_by_phase["B2"]
    shared_b23=sites_by_phase["B2"]&sites_by_phase["B3"]
    island_summary={}
    for i in sorted(island_allowed):
        island_sites={p:{s for s in sites_by_phase[p] if s[0]==i} for p in phases}
        island_summary[i]={
            "B1_1997_2004_site_count":len(island_sites["B1"]),
            "B2_2010_2012_site_count":len(island_sites["B2"]),
            "B3_2019_2022_site_count":len(island_sites["B3"]),
            "paired_B1_B3_source_site_count":len(shared_b13&{s for s in shared_b13 if s[0]==i}),
            "complete_all_three_source_site_count":len(shared_all&{s for s in shared_all if s[0]==i})
        }
    matched_by_mode=defaultdict(set)
    for (island,site,phase,method),n in events_by_site_phase_method.items():
        if (island,site) in shared_all:
            matched_by_mode[(phase,method)].add((island,site))
    method_short=[]
    for m,n in method_counts.most_common():
        source_label=m if len(m)<=100 else "(overlong-source-method)"
        method_short.append({
          "source_samplingProtocol_label":source_label,
          "source_Event_count":n,
          "complete_three_phase_site_count_by_phase":{
             ph:len(matched_by_mode[(ph,m)]) for ph in phases
          }})
    coverage=len(ids)/len(events)
    n_islands=sum(island_summary[i]["paired_B1_B3_source_site_count"]>0 for i in island_summary)
    gate=contract["eligibility_gates"]
    qualified=(
       coverage>=gate["minimum_original_Event_source_join_coverage"]
       and len(shared_b13)>=gate["minimum_complete_B1_B3_same_source_transects_across_islands"]
       and len(shared_all)>=gate["minimum_complete_B1_B2_B3_same_source_transects"]
       and n_islands>=gate["minimum_distinct_islands_with_B1_B3_repeats"]
    )
    hash_=hashlib.sha256("\n".join(sorted(i+"|"+s for i,s in shared_all)).encode()).hexdigest()
    return {
      "schema":"structural.bala_repeated_transect_original_event_result.v1_311",
      "status":"EVENT_SAME_TRANSECT_THREE_PHASE_DESIGN_QUALIFIED_OCCURRENCE_SEALED" if qualified
          else "EVENT_REPEATED_SITE_SUPPORT_INSUFFICIENT_TERMINAL_NO_BIOLOGICAL_SCORE",
      "original_published_source_Event_rows":len(events),
      "complete_author_Event_primary_ids":len(ids),
      "site_key_role":"exact string island+locationID, no geographic matching",
      "source_event_year_mismatch":source_year_mismatch,
      "source_event_year_non_numeric":non_numeric_year,
      "source_date_without_four_digit_year_prefix":unparsed_source_dates,
      "original_event_rows_with_blank_eligible_locationID":empty_site,
      "raw_source_Event_counts_by_island":dict(sorted(island_counts.items())),
      "raw_source_Event_counts_by_year":{str(k):v for k,v in sorted(year_counts.items())},
      "original_Event_counts_by_phase":dict(sorted(phase_counts.items())),
      "author_source_site_counts_by_phase":{p:len(sites_by_phase[p]) for p in phases},
      "same_physical_transect_paired_site_count_B1_B2":len(shared_b12),
      "same_physical_transect_paired_site_count_B2_B3":len(shared_b23),
      "same_physical_transect_paired_site_count_B1_B3":len(shared_b13),
      "same_physical_transect_all_three_phase_site_count":len(shared_all),
      "island_count_with_B1_B3_repeated_transects":n_islands,
      "island_repeated_site_table":island_summary,
      "three_phase_site_author_ID_set_sha256":hash_,
      "original_source_sampling_protocol_counts":method_short,
      "complete_three_phase_sampling_events_min_max":{
        ph: [min([n for (i,s,p),n in events_by_site_phase.items() if p==ph and (i,s) in shared_all],default=0),
             max([n for (i,s,p),n in events_by_site_phase.items() if p==ph and (i,s) in shared_all],default=0)]
        for ph in phases
      },
      "core_id_to_Occurrence_join_not_yet_checked":True,
      "no_biological_species_or_origin_values_read":True,
      "original_Occurrence_rows_opened":0,
      "all_site_labels_and_coordinates_redacted":True,
      "prior_2026_abundance_richness_paper_is_background_not_new_discovery":True,
      "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--protocol",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    cfg=json.loads(args.protocol.read_text(encoding="utf-8"))
    if (cfg.get("schema")!="structural.bala_original_event_repeated_site_gate.v1_311"
        or cfg.get("status")!="FROZEN_BEFORE_FIRST_ORIGINAL_BALA_EVENT_VALUES"
        or cfg["original_source"]["source_sha256"]!=SHA
        or cfg["original_source"]["archive"]!=SRC):
        raise ValueError("Source identity or fixed Event-only gate not frozen")
    result={"schema":"structural.bala_repeated_transect_original_event_result.v1_311",
            "status":"SOURCE_OR_EVENT_READER_TECHNICAL_STOP",
            "original_Occurrence_rows_opened":0,"GEB_scientific_HOLD":True,
            "new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SRC,headers={"User-Agent":"Structural-BALA-v1.311-EventOnly-RepeatSource/1.0"})
        with urllib.request.urlopen(req,timeout=65) as r:body=r.read(MAX_BYTES+1)
        if len(body)>MAX_BYTES or hashlib.sha256(body).hexdigest()!=SHA:
            raise ValueError("Exact 2024 BALA original source ZIP fingerprint changed")
        original=original_event_rows(body)
        result=summarize(original,cfg)
        result["original_ZIP_SHA256"]=SHA
    except Exception as e:
        result["stop_type"]=type(e).__name__
        result["stop_reason"]=str(e)[:260]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({
      "status":result["status"],
      "original_Event_rows":result.get("original_published_source_Event_rows"),
      "B1_B3_matched_transects":result.get("same_physical_transect_paired_site_count_B1_B3"),
      "all_three_matched_transects":result.get("same_physical_transect_all_three_phase_site_count"),
      "islands_with_B1_B3_repeat":result.get("island_count_with_B1_B3_repeated_transects"),
      "source_methods":result.get("original_source_sampling_protocol_counts"),
      "original_Occurrence_rows_opened":0,
      "stop_reason":result.get("stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_OR_EVENT_READER_TECHNICAL_STOP":raise SystemExit(2)
if __name__=="__main__":main()
