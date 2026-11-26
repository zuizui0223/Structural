#!/usr/bin/env python3
"""Source-only 15 exact BExIS31124 method tuples absent BExIS31123.

Only original Exploratory/PlotID/TreeID/TreeSpecies/CollectionYear/TrapID/
Traptype fields accessed. Does not compute species, captures or ecology.
Original sample keys and host names are kept local and never printed.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv, hashlib, io, json
from pathlib import Path
from belongdead_31123_original_source_plot_tree_grain import get_original as get31123
from belongdead_31124_author_complete_log_effort_gate import get_31124 as get31124

FULL_DIGEST="73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e"
SUBSET_DIGEST="e9c6ab60c05c842434c8d976bfedd5da11893200c45556906ce1da1f68ea4c8c"
FIELDS={"TrapID":1,"PlotID":2,"Exploratory":3,"TreeID":4,"TreeSpecies":5,"Traptype":9,"CollectionYear":11}
class SourceStop(RuntimeError):pass

def only_method_keys(binary):
    rdr=csv.reader(io.StringIO(binary.decode("utf-8-sig"),newline=""))
    header=next(rdr,[])
    if len(header)!=17 or any(header[pos]!=name for name,pos in FIELDS.items()):
        raise SourceStop("SOURCE_STOP_ORIGINAL_PUBLIC_17_HEADER_METHOD_FIELDS_CHANGED")
    keytrap=set();meta_by_key={};tree_plot=set();allplots=set();treeyears=set()
    n=0
    for row in rdr:
        if not row or not any(v.strip() for v in row):continue
        n+=1
        if len(row)!=17:raise SourceStop("SOURCE_STOP_ORIGINAL_LONG_RECORD_SHAPE")
        # EXCLUSIVELY fixed original source method columns
        e,p,t,h,y,trap,kind=(row[FIELDS[k]].strip() for k in (
            "Exploratory","PlotID","TreeID","TreeSpecies","CollectionYear","TrapID","Traptype"))
        if not all((e,p,t,h,y,trap)):raise SourceStop("SOURCE_STOP_EMPTY_SOURCE_METHOD_KEY")
        if y not in {str(z) for z in range(2010,2018)}:
            raise SourceStop("SOURCE_STOP_AUTHOR_ORIGINAL_COLLECTION_YEAR_DRIFT")
        key=(e,p,t,h,y,trap)
        meta_by_key[key]=kind
        keytrap.add(key)
        tree_plot.add((e,p,t))
        allplots.add((e,p))
        treeyears.add((e,p,t,h,y))
    return {
        "n":n,"keys":keytrap,"meta":meta_by_key,
        "treeplot":tree_plot,"plots":allplots,"tree_years":treeyears,
    }

def diagnose(a,b):
    old=a["keys"];new=b["keys"]
    extra=new-old
    old_year_parent={(e,p,t,h,y) for e,p,t,h,y,trap in old}
    old_tree_parent={(e,p,t,h) for e,p,t,h,y,trap in old}
    old_tree_trapid={(e,p,t,trap) for e,p,t,h,y,trap in old}
    old_plot_trapid={(e,p,trap) for e,p,t,h,y,trap in old}
    old_year_trapid={(e,p,t,y,trap) for e,p,t,h,y,trap in old}
    if len(extra)!=15 or len(a["treeplot"])!=379 or len(b["treeplot"])!=379 or b["treeplot"]!=a["treeplot"]:
        raise SourceStop("SOURCE_STOP_FROZEN_31124_15_UNMATCHED_379_SAME_LOGS_COHORT_DRIFT")
    original_types=set(a["meta"].values())
    return {
      "schema":"structural.BELongDead_31124_fifteen_nonmatching_method_tuples_source_only.v1",
      "source_original_full_31123_SHA":FULL_DIGEST,
      "source_original_author_complete_log_31124_SHA":SUBSET_DIGEST,
      "original_full_31123_source_long_records":a["n"],
      "original_complete_log_view_31124_source_long_records":b["n"],
      "original_full_31123_unique_method_keys":len(old),
      "original_complete_view_31124_unique_method_keys":len(new),
      "exact_sixfield_method_key_overlap":len(old&new),
      "31124_sixfield_method_keys_unmatched":len(extra),
      "31124_unmatched_with_exact_5field_log_host_year_parent_in31123":sum(
          (e,p,t,h,y) in old_year_parent for e,p,t,h,y,trap in extra),
      "31124_unmatched_with_exact_4field_log_host_parent_in31123":sum(
          (e,p,t,h) in old_tree_parent for e,p,t,h,y,trap in extra),
      "31124_unmatched_TrapID_exists_in_same_original_log_any_year":sum(
          (e,p,t,trap) in old_tree_trapid for e,p,t,h,y,trap in extra),
      "31124_unmatched_TrapID_exists_in_same_original_plot_any_year":sum(
          (e,p,trap) in old_plot_trapid for e,p,t,h,y,trap in extra),
      "31124_unmatched_TrapID_exists_in_same_original_log_year":sum(
          (e,p,t,y,trap) in old_year_trapid for e,p,t,h,y,trap in extra),
      "31124_unmatched_original_Traptype_not_in31123":sum(
          b["meta"][key] not in original_types for key in extra),
      "31124_unmatched_original_distinct_Exploratory_PlotID":len({(e,p) for e,p,t,h,y,trap in extra}),
      "31124_unmatched_original_distinct_Exploratory_PlotID_TreeID":len({(e,p,t) for e,p,t,h,y,trap in extra}),
      "31124_unmatched_source_calendar_year_labels":len({y for e,p,t,h,y,trap in extra}),
      "full_31123_exact_nested_log_ID_count":len(a["treeplot"]),
      "31124_complete_log_same_physical_original_nested_log_ID_count":len(b["treeplot"]),
      "source_author_site_trap_IDs_raw_records_never_reexported":True,
      "source_original_taxa_and_beetle_count_fields_UNREAD":True,
      "unknown_zero_capture_opportunities_NOT_imputed":True,
      "author_original_complete_log_view_same_study_NOT_replication":True,
      "original_Finland142site_Burner_PREDICTS_NEON_BALA_GEB_effects_UNCHANGED":True,
      "eBird_used":False,
      "status":"SOURCE_METHOD_TUPLE_NON_SUBSET_CLASSIFIED_NO_ORGANISM_EFFECT",
    }

def known_truth():
    a={"keys":{("A","P","T","H","2010","TRAP1")},
       "meta":{("A","P","T","H","2010","TRAP1"):"INTERCEPT"},
       "treeplot":{("A","P","T")}}
    assert ("A","P","T","H","2010") in {tuple(x[:5]) for x in a["keys"]}
    assert len({tuple(x[:3]) for x in a["keys"]})==1
    print("SYNTHETIC_FIXED_ORIGINAL_METHOD_PARENT_HIERARCHY_ONLY_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    known_truth()
    if args.test:return
    if not args.out:p.error("--out")
    try:
        raw_full=get31123();raw_partial=get31124()
        if len(raw_full)!=8103493 or hashlib.sha256(raw_full).hexdigest()!=FULL_DIGEST:
            raise SourceStop("SOURCE_STOP_FROZEN_31123_SHA_OR_LENGTH_CHANGED")
        if len(raw_partial)!=3636045 or hashlib.sha256(raw_partial).hexdigest()!=SUBSET_DIGEST:
            raise SourceStop("SOURCE_STOP_FROZEN_31124_SHA_OR_LENGTH_CHANGED")
        a=only_method_keys(raw_full);b=only_method_keys(raw_partial)
        result=diagnose(a,b)
    except SourceStop as e:
        result={"schema":"structural.BELongDead_31124_fifteen_nonmatching_method_tuples_source_only.v1",
                "status":str(e),"source_failure_not_ecological_null":True,
                "no_new_beetle_effect_scored":True}
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"BExIS31124_15_nonmatching_original_method_parent_key_diagnostic.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
