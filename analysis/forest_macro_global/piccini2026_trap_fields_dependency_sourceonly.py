#!/usr/bin/env python3
"""Original Piccini2026 trap-like source field functional-dependency diagnosis.
Only method fields from publicly pinned original text; no species/trait/count values.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import hashlib
import io
import json
import re
from pathlib import Path
from statistics import median
from piccini2026_gro_original_method_unit_gate import (
    DOI, metadata_source_files, head_shape, get_one_original_publisher_file, MethodStop
)
from piccini2026_gro_original_header_only_gate import normalized

CORE=("site","stand","plot","stratum","period")
TRAP_NAMES={"trap","trapid","trapcode","trapnumber"}
EXPECTED_ROWS=22414
EXPECTED_TRAP_FIELD_CARDINALITIES=[8,320,557]

def quant(x):
    return ({"min":min(x),"median":float(median(x)),"max":max(x)}
            if x else None)

def audit(raw: bytes, expected_counts=None, expected_rows=EXPECTED_ROWS):
    try:
        r=csv.reader(io.StringIO(raw.decode("utf-8-sig"),newline=""),
                     delimiter=";",strict=True)
        hdr=next(r)
    except (StopIteration,UnicodeError,csv.Error) as e:
        raise MethodStop("SOURCE_STOP_AUTHOR_HEADER_UNREADABLE") from e
    hn=[normalized(h) for h in hdr]
    if len(hdr)!=17:
        raise MethodStop("SOURCE_STOP_ORIGINAL_HEADER_WIDTH_DRIFT")
    ids={k:[i for i,h in enumerate(hn) if h==k] for k in CORE}
    if any(len(v)!=1 for v in ids.values()):
        raise MethodStop("SOURCE_STOP_ORIGINAL_CORE_ROLES_NOT_UNIQUE")
    trapcols=[i for i,h in enumerate(hn) if h in TRAP_NAMES]
    if len(trapcols)!=3:
        raise MethodStop("SOURCE_STOP_ORIGINAL_THREE_TRAP_HEADER_DRIFT")
    safe_original_header_spelling=[]
    for i in trapcols:
        val=hdr[i].strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9 _.-]{0,35}",val):
            raise MethodStop("SOURCE_STOP_ORIGINAL_HEADER_NAME_NOT_SAFE")
        safe_original_header_spelling.append(val)
    # All operations below touch core + 3 author-defined trap-like fields only.
    selected={k:v[0] for k,v in ids.items()}
    traps={i:defaultdict(set) for i in trapcols}
    plots=defaultdict(set);stands=defaultdict(set);plotlayers=defaultdict(set)
    unit_label_contexts={i:defaultdict(lambda:{"plots":set(),"layers":set(),
        "plotlayers":set(),"plotlayerperiods":set(),"periods":set()}) for i in trapcols}
    per_plot_layer_period={i:defaultdict(set) for i in trapcols}
    original_rows=0;missing={i:0 for i in trapcols}
    plot_layer_period=set()
    try:
        for row in r:
            original_rows+=1
            if original_rows>100000 or len(row)!=17:
                raise MethodStop("SOURCE_STOP_ORIGINAL_ROW_WIDTH_OR_LIMIT")
            site,stand,plot,layer,period=[row[selected[k]].strip() for k in CORE]
            if not all((site,stand,plot,layer,period)):
                raise MethodStop("SOURCE_STOP_ORIGINAL_CORE_VALUE_MISSING")
            plots[plot].add(site)
            stands[plot].add(stand)
            plotlayers[plot].add(layer)
            plot_layer_period.add((plot,layer,period))
            for i in trapcols:
                x=row[i].strip()
                if not x:
                    missing[i]+=1
                    continue
                ctx=unit_label_contexts[i][x]
                ctx["plots"].add(plot);ctx["layers"].add(layer)
                ctx["plotlayers"].add((plot,layer))
                ctx["plotlayerperiods"].add((plot,layer,period))
                ctx["periods"].add(period)
                per_plot_layer_period[i][(plot,layer,period)].add(x)
    except csv.Error as e:
        raise MethodStop("SOURCE_STOP_CSV_PARSE") from e
    if original_rows!=expected_rows:
        raise MethodStop("SOURCE_STOP_FROZEN_ORIGINAL_SOURCE_ROW_N_CHANGED")
    if len(plots)!=40 or len({next(iter(x)) for x in plots.values() if len(x)==1})!=8 or (
       sum(len(x)!=1 for x in plots.values())!=0) or (
       sum(len(x)!=1 for x in stands.values())!=0) or (
       sum(len(x)==3 for x in plotlayers.values())!=40):
        raise MethodStop("SOURCE_STOP_EIGHT_SITE_40PLOT_THREELAYER_HIERARCHY_DRIFT")
    out=[]
    for i in trapcols:
        groups=unit_label_contexts[i]
        card=len(groups)
        out.append({
          "source_original_column_ordinal_1based":i+1,
          "source_exact_safe_generic_field_name":safe_original_header_spelling[trapcols.index(i)],
          "source_normalized_generic_field_name":hn[i],
          "distinct_source_method_label_count":card,
          "source_nonmissing_records":original_rows-missing[i],
          "source_missing_records":missing[i],
          "labels_spanning_more_than_one_plot":sum(len(v["plots"])>1 for v in groups.values()),
          "labels_spanning_more_than_one_vertical_stratum":
             sum(len(v["layers"])>1 for v in groups.values()),
          "labels_spanning_more_than_one_plot_stratum":
             sum(len(v["plotlayers"])>1 for v in groups.values()),
          "labels_spanning_more_than_one_plot_stratum_period":
             sum(len(v["plotlayerperiods"])>1 for v in groups.values()),
          "number_of_period_tokens_per_label":quant(
              [len(v["periods"]) for v in groups.values()]),
          "recorded_unique_labels_per_plot_stratum_period":quant(
              [len(v) for v in per_plot_layer_period[i].values()]),
          "source_plot_layer_period_contexts_with_any_label":
              len(per_plot_layer_period[i]),
        })
    all_counts=sorted(x["distinct_source_method_label_count"] for x in out)
    return {
       "status": ("AUTHOR_TRAP_ROLE_UNVERIFIED_PENDING_CODEBOOK"
             if expected_counts is None or all_counts==expected_counts
             else "SOURCE_STOP_PUBLISHED_TRAP_CARDINALITIES_DRIFT"),
       "source_rows_checked_method_only":original_rows,
       "source_plot_labels":len(plots),
       "source_parent_site_labels":8,
       "source_plot_stratum_period_tokens":len(plot_layer_period),
       "source_three_trap_columns_in_original_column_order":out,
       "sorted_distinct_trap_field_label_counts":all_counts,
       "zero_capture_or_complete_trap_days_NOT_ESTABLISHED":True,
       "candidate_key_role_NOT_selected_by_cardinality_or_functional_dependencies":True,
       "no_species_guild_count_resource_or_taxon_values_accessed":True,
       "no_raw_site_plot_trap_period_values_exported":True,
    }

def original_source_only():
    ans={"DOI":DOI,"status":"SOURCE_UNREAD",
         "original_2024_canopy_file_unread":True,
         "no_original_species_or_guild_responses_opened":True}
    try:
        files=metadata_source_files()
        heads=[head_shape(z["file_id"]) for z in files]
        picked=[z for z,h in zip(files,heads)
            if h["header_column_count"]==17 and h["header_delimiter_category"]=="semicolon"]
        if len(picked)!=1: raise MethodStop("SOURCE_STOP_ORIGINAL_17FIELD_TEXT_NOT_UNIQUE")
        f=picked[0]
        raw=get_one_original_publisher_file(f["file_id"],f["expected_size"])
        check=f.get("published_checksum")
        if not (isinstance(check,dict) and check.get("type","").lower()=="md5"
            and hashlib.md5(raw).hexdigest()==str(check.get("value","")).lower()):
            raise MethodStop("SOURCE_STOP_ORIGINAL_PUBLISHER_MD5_NOT_MATCHED")
        result=audit(raw,expected_counts=EXPECTED_TRAP_FIELD_CARDINALITIES)
        ans["result"]=result
        ans["status"]=result["status"]
    except MethodStop as e:
        ans["status"]=str(e)
        ans["source_access_or_method_stop_NOT_biological_null"]=True
    return ans

def known_truth():
    header=["Site","Stand","Plot","Stratum","Period","Trap","TrapID","Trap_ID"]+[
        "Species","FeedingGuild","Abundance","EX1","EX2","EX3","EX4","EX5","EX6"]
    assert len(header)==17
    rows=[]
    for site in range(8):
        for stand in range(5):
            plot="P"+str(site)+"_"+str(stand)
            for layer in range(3):
                for period in range(2):
                    for trap in range(3):
                        row=["S"+str(site),"T"+str(stand),plot,str(layer),str(period),
                             "local"+str(trap),plot+"_"+str(layer)+"_"+str(trap),
                             plot+"_"+str(layer)+"_"+str(period)+"_"+str(trap),
                             "PROTECTED_SPECIES","PROTECTED_GUILD","999"]+["0"]*6
                        rows.append(row)
    s="\n".join(";".join(r) for r in [header]+rows)+"\n"
    z=audit(s.encode(),expected_rows=len(rows))
    assert z["status"]=="AUTHOR_TRAP_ROLE_UNVERIFIED_PENDING_CODEBOOK"
    assert z["source_parent_site_labels"]==8
    assert z["source_plot_stratum_period_tokens"]==240
    assert len(z["source_three_trap_columns_in_original_column_order"])==3
    assert z["sorted_distinct_trap_field_label_counts"]==[3,360,720]
    assert z["source_three_trap_columns_in_original_column_order"][0][
       "labels_spanning_more_than_one_plot"]==3
    assert z["source_three_trap_columns_in_original_column_order"][2][
       "labels_spanning_more_than_one_plot"]==0
    assert "PROTECTED_SPECIES" not in json.dumps(z)
    assert "999" not in json.dumps(z)
    print("SYNTHETIC_PICCINI_TRAP_ID_FUNCTIONAL_DEPENDENCY_SOURCE_ONLY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    a=p.parse_args()
    known_truth()
    if a.test:return
    if a.out is None:p.error("--out required")
    o={"schema":"structural.Piccini2026_three_trap_field_dependencies_sourceonly.v1",
       "protocol":"docs/FOREST_BEETLE_PICCINI2026_TRAP_COLUMNS_DEPENDENCY_PRESPEC_20261117.md",
       "original":original_source_only(),
       "no_new_beetle_biological_parameter_or_pvalue":True,
       "prior_Thai_Finland_PREDICTS_NEON_BALA_GEB_UNCHANGED":True,
       "eBird_used":False,"TinyFish_used":False}
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/"Piccini2026_trap_fields_sourceonly.json").write_text(
       json.dumps(o,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(o,indent=2,ensure_ascii=False))
if __name__=="__main__":
    main()
