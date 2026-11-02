#!/usr/bin/env python3
"""v1.343 source EVENT-only Madeira COBRA physical plot / day-night diagnostic.

Original v1.342 22-site equal-method gate is terminal. This tool checks
source metadata columns fieldNumber/eventID/locationRemarks/eventTime for
published MF/MD/PSD plot codes or explicit diurnality. Original spider
species+status Occurrence body is NEVER decompressed.
"""
from __future__ import annotations
import argparse,hashlib,json,re,urllib.request,unicodedata
from collections import Counter,defaultdict
from pathlib import Path
from madeira_spider_original_equal_sweeping_v1_342 import (
    SOURCE,SHA,original_event_core_only,canon,sweep
)

PATTERN=re.compile(r"(?<![A-Z0-9])(MF|MD|PSD)[ _-]?0?([1-9]|1[0-2])(?![A-Z0-9])")
PLOT_LIMIT={"MF":12,"MD":5,"PSD":5}
FIELD_CANDIDATES=("fieldNumber","eventID","locationID","locationRemarks")

def source_tokens(text):
    return unicodedata.normalize("NFKD",str(text or "")).encode("ascii","ignore").decode().upper()

def codes(text):
    matched=set()
    for m in PATTERN.finditer(source_tokens(text)):
        prefix,n=m.group(1),int(m.group(2))
        if 1<=n<=PLOT_LIMIT[prefix]:matched.add(prefix+str(n))
    return matched

def nonbiological_time_class(row):
    tokens=" ".join(canon(row.get(k)) for k in
                    ("samplingProtocol","samplingEffort","eventTime"))
    day=bool(re.search(r"\b(day|diurnal|daytime|sunrise|dawn)\b",tokens))
    night=bool(re.search(r"\b(night|nocturnal|nighttime|dusk|after dark)\b",tokens))
    return "DAY" if day and not night else "NIGHT" if night and not day else "AMBIGUOUS" if day and night else "UNSPECIFIED"

def safe_vocabulary(value,max_k=24):
    x=Counter(canon(v)[:90] if v else "<EMPTY>" for v in value)
    if len(x)>max_k:
        return {"unique_unbounded_vocab":len(x),
                "sha12_count":{hashlib.sha256(v.encode()).hexdigest()[:12]:n
                               for v,n in sorted(x.items())}}
    return dict(sorted(x.items()))

def diagnose(events,contract):
    if len(events)!=562:
        raise ValueError("Original exact Madeira COBRA 562 source Event rows required")
    all_rows=set()
    fields_match=defaultdict(Counter)
    plot_sets=defaultdict(set)
    time_by_protocol=defaultdict(Counter)
    code_conflicts=0
    any_code=0
    method=Counter();hab=Counter();years=Counter();times=Counter()
    source_effort=Counter();units=Counter();sizes=Counter()
    sample_codes={}
    for row in events:
        core=str(row.get("__source_coreid","")).strip()
        if not core or core in all_rows:
            raise ValueError("Original Event coreID duplicated or absent")
        all_rows.add(core)
        per_column={}
        for field in FIELD_CANDIDATES:
            c=codes(row.get(field))
            if c:
                fields_match[field]["source_records_with_unambiguous_published_plot_code"]+=int(len(c)==1)
                fields_match[field]["source_records_with_ambiguous_plot_code"]+=int(len(c)>1)
                per_column[field]=c
                plot_sets[field].update(c)
        joined=set().union(*per_column.values()) if per_column else set()
        if joined:
            any_code+=1
            if len(joined)>1:code_conflicts+=1
            elif len(joined)==1:sample_codes[core]=next(iter(joined))
        met=canon(row.get("samplingProtocol"))
        method[met or "<EMPTY>"]+=1
        h=canon(row.get("habitat"))
        hab[h or "<EMPTY>"]+=1
        date=str(row.get("eventDate","")).strip()
        years[date[:4] if date[:4].isdigit() else "unknown"]+=1
        time=nonbiological_time_class(row)
        times[time]+=1
        time_by_protocol[met or "<EMPTY>"][time]+=1
        units[canon(row.get("sampleSizeUnit")) or "<EMPTY>"]+=1
        sizes[canon(row.get("sampleSizeValue")) or "<EMPTY>"]+=1
        source_effort[canon(row.get("samplingEffort")) or "<EMPTY>"]+=1
    distinct=set(sample_codes.values())
    candidates={
        "published_MF_plot_n":len({x for x in distinct if x.startswith("MF")}),
        "published_MD_plot_n":len({x for x in distinct if x.startswith("MD")}),
        "published_PSD_plot_n":len({x for x in distinct if x.startswith("PSD")})
    }
    # No original biological source allowed under this diagnostic.
    source_22_complete=candidates=={"published_MF_plot_n":12,"published_MD_plot_n":5,"published_PSD_plot_n":5}
    explicit_sweep_daynight=(
        time_by_protocol["sweeping"]["DAY"]>=34 and
        time_by_protocol["sweeping"]["NIGHT"]>=34
    )
    return {
        "schema":"structural.madeira_spider_cobra_event_identity_result.v1_343",
        "status":"SOURCE_EVENT_DESIGN_POTENTIAL_ALTERNATE_CROSSWALK_DIAGNOSTIC_ONLY"
                 if source_22_complete and explicit_sweep_daynight else
                 "TERMINAL_NO_AUTHOR_PLOT_AND_DIURNAL_SWEEP_FIELD_CROSSWALK",
        "original_source_v18_zip_sha256":SHA,
        "original_Event_rows_inspected":len(events),
        "original_Occurrence_rows_inspected":0,
        "previous_v342_strict_source_gate_TERMINAL":True,
        "published_plot_source_code_candidate_counts":candidates,
        "plot_codes_uniquely_assigned_event_n":len(sample_codes),
        "source_event_any_published_plot_code_n":any_code,
        "conflicting_published_plot_code_source_Event_n":code_conflicts,
        "per_source_column_author_plot_code_coverage":{
            k:dict(fields_match[k])|{"distinct_published_plot_codes_n":len(plot_sets[k])}
            for k in FIELD_CANDIDATES
        },
        "source_original_habitat_vocabulary_counts":safe_vocabulary(hab.elements()),
        "source_original_samplingProtocol_vocabulary_counts":dict(sorted(method.items())),
        "source_event_time_classification_counts":dict(sorted(times.items())),
        "source_sweeping_author_time_counts":dict(sorted(time_by_protocol["sweeping"].items())),
        "source_original_survey_year_Event_counts":dict(sorted(years.items())),
        "source_samplingEffort_vocab_counts":safe_vocabulary(source_effort.elements()),
        "source_sampleSizeValue_vocab_counts":safe_vocabulary(sizes.elements()),
        "source_sampleSizeUnit_vocab_counts":safe_vocabulary(units.elements()),
        "source_plot_code_events_hash_sha256":hashlib.sha256(
             "\n".join(k+"|"+v for k,v in sorted(sample_codes.items())).encode()).hexdigest(),
        "original_plot_IDs_dates_geocoordinates_species_status_not_exported":True,
        "no_post_Event_discovery_relabel_as_v342_success":True,
        "original_2016_forest_vs_2017_dry_year_confound_unresolved":True,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    c=json.loads(a.contract.read_text())
    if (c.get("schema")!="structural.madeira_cobra_source_field_identity_diagnostic.v1_343"
        or c.get("status")!="FROZEN_SOURCE_EVENT_ONLY_DIAGNOSIS_AFTER_V342_TERMINAL_BEFORE_ANY_SPECIES_RESPONSE"
        or c["source"]["source_zip_sha256"]!=SHA):
        raise ValueError("Original physical site/diurnality metadata diagnostic not preregistered")
    out={"schema":"structural.madeira_spider_cobra_event_identity_result.v1_343",
         "status":"SOURCE_OR_EVENT_DIAGNOSTIC_TECHNICAL_STOP",
         "original_Occurrence_rows_inspected":0,
         "previous_v342_strict_source_gate_TERMINAL":True,
         "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False}
    try:
        req=urllib.request.Request(SOURCE,headers={"User-Agent":"Structural-MadeiraSpider-EventMetaDiagnostic-v1.343"})
        with urllib.request.urlopen(req,timeout=65) as f:blob=f.read(400001)
        if len(blob)>400000 or hashlib.sha256(blob).hexdigest()!=SHA:
            raise ValueError("Original source ZIP SHA mismatch")
        out=diagnose(original_event_core_only(blob),c)
    except Exception as ex:
        out["stop_type"]=type(ex).__name__;out["stop_reason"]=str(ex)[:280]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print(json.dumps({k:out.get(k) for k in (
      "status","published_plot_source_code_candidate_counts",
      "source_original_habitat_vocabulary_counts",
      "source_original_samplingProtocol_vocabulary_counts",
      "source_sweeping_author_time_counts","source_event_time_classification_counts",
      "source_sampleSizeUnit_vocab_counts",
      "original_Occurrence_rows_inspected","stop_reason"
    )},sort_keys=True))
    if out["status"]=="SOURCE_OR_EVENT_DIAGNOSTIC_TECHNICAL_STOP":raise SystemExit(2)
if __name__=="__main__":main()
