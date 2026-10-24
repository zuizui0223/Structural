#!/usr/bin/env python3
"""v1.299: ORIGINAL Event-only equal-mode-effort Terceira beetle subset.

This is a NEW exploratory metric eligibility after historical v1.298
full-method scientific STOP. Never alters v1.298 or opens woody/beetle
Occurrence bodies. Site and method allocations use Event source only.
"""
from __future__ import annotations
import argparse,hashlib,json,urllib.request
from collections import Counter
from pathlib import Path

from biomoni_terceira_event_colocation_v1_298 import (
    SOURCE,MAX_BYTES,extract_event_core_only,summarize_site_samples,qualify
)

def evaluate(trees,beetles,protocol,original_crosswalk):
    if len(trees)!=30 or len(beetles)!=308:
        raise ValueError("Unexpected originally frozen source Event denominators")
    sites_tree=summarize_site_samples(trees,"woody")
    sites_beetle=summarize_site_samples(beetles,"beetle")
    if set(sites_tree)!=set(sites_beetle) or len(sites_tree)!=10:
        raise ValueError("Original ten author source locationIDs not bijective")
    previous=qualify(trees,beetles,original_crosswalk)
    if previous["status"]!="TERMINAL_COORDINATES_DATES_OR_METHOD_EFFORT_NOT_COMPARABLE":
        raise ValueError("v1.298 scientific full-mode STOP must be preserved")
    if not previous["paired_coordinate_difference_below_0_0003_deg"] or not previous["date_pair_gap_qualifies"]:
        raise ValueError("Source-only site or date mismatch cannot be rescued")
    current_modes=set.intersection(*(set(rec["method"] for rec in sites_beetle[k])
                          for k in sorted(sites_beetle)))
    minima=Counter()
    for method in sorted(current_modes):
        minima[method]=min(sum(rec["method"]==method for rec in sites_beetle[k])
                           for k in sorted(sites_beetle))
    mode_multiset=sorted(minima.values())
    frozen=protocol["method_subsample"]
    if (len(current_modes)!=frozen["prospective_shared_mode_count_exact"]
        or mode_multiset!=sorted(frozen["per_mode_minimum_event_records_at_site"])
        or sum(mode_multiset)!=frozen["standardized_events_per_site"]):
        return {
          "schema":"structural.biomoni_common_method_event_only_result.v1_299",
          "status":"TERMINAL_NO_FROZEN_SHARED_METHODS",
          "ten_exact_plot_keys":True,
          "source_reported_shared_mode_count":len(current_modes),
          "source_shared_mode_min_multiplicities":mode_multiset,
          "original_woody_Occurrence_rows_opened":0,
          "original_beetle_Occurrence_rows_opened":0,
          "old_v1_298_full_method_gate_remains_terminal":True,
          "GEB_scientific_HOLD":True,"confirmatory_systems_admitted":0,"eBird_used":False
        }
    selected=[]
    per_plot_counts=[]
    eachmethod=[]
    for name in sorted(sites_beetle):
        counts=Counter(rec["method"] for rec in sites_beetle[name])
        keep=[]
        for mode in sorted(current_modes):
            original=[x["core"] for x in sites_beetle[name] if x["method"]==mode]
            original.sort()
            k=minima[mode]
            if len(original)<k:raise ValueError("Original method minimum not realized")
            keep.extend(original[:k])
        if len(keep)!=frozen["standardized_events_per_site"]:
            raise ValueError("Cannot construct exactly six source-only samples per plot")
        selected.extend(keep)
        per_plot_counts.append(len(keep))
        eachmethod.append(Counter(x["method"] for x in sites_beetle[name]))
    if len(selected)!=frozen["total_terceira_standardized_beetle_events"]:
        raise ValueError("Standardized original Event source total changed")
    if len(set(selected))!=len(selected):
        raise ValueError("Original source selected Event duplicates")
    checksum=hashlib.sha256("\n".join(sorted(selected)).encode()).hexdigest()
    pair_receipt=hashlib.sha256(
        "\n".join(str(k)+"|"+sites_tree[k][0]["core"]+"|"+
                  ",".join(sorted(x for x in selected if any(v["core"]==x for v in sites_beetle[k])))
                  for k in sorted(sites_tree)).encode()).hexdigest()
    return {
        "schema":"structural.biomoni_common_method_event_only_result.v1_299",
        "status":"EXPLORATORY_TEN_PLOTS_SIX_COMMON_METHOD_BEETLE_EVENTS_EACH_RESPONSE_SEALED",
        "original_tree_Event_rows_examined":len(trees),
        "original_beetle_Event_rows_examined":len(beetles),
        "ten_exact_woody_beetle_plot_keys":True,
        "max_matched_location_abs_degree_difference":previous["max_coordinate_absolute_degree_difference"],
        "full_original_beetle_events_per_Terceira_plot_range":[
             previous["minimum_beetle_sample_events_per_plot"],
             previous["maximum_beetle_sample_events_per_plot"]],
        "shared_protocol_modes_count":len(current_modes),
        "shared_modes_minimum_sampling_events_sorted":mode_multiset,
        "selected_beetle_Event_rows_each_woody_plot":min(per_plot_counts),
        "selected_beetle_Event_rows_total":len(selected),
        "selected_original_Event_coreids_sha256":checksum,
        "selected_cross_taxon_site_tree_beetle_method_fingerprint":pair_receipt,
        "full_original_tree_beetle_Event_crosswalk_SHA256":previous["matched_original_coreids_sha256"],
        "common_method_symbols_anonymized":[
             {"method":f"M{i}","min_event_count":minima[mode],
              "original_max_event_count":max(x[mode] for x in eachmethod)}
             for i,mode in enumerate(sorted(current_modes),1)],
        "source_selected_beetle_EventIDs_or_tree_plot_location_names_exported":False,
        "selection_done_before_any_beetle_or_woody_species_value_access":True,
        "old_v1_298_full_method_gate_remains_terminal":True,
        "this_is_new_exploratory_standardized_subset_not_original_full_mode_claim":True,
        "not_an_independent_geographic_replication":True,
        "original_woody_Occurrence_rows_opened":0,
        "original_beetle_Occurrence_rows_opened":0,
        "GEB_scientific_HOLD":True,"confirmatory_systems_admitted":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--contract",type=Path,required=True)
    p.add_argument("--original-crosswalk-contract",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    c=json.loads(args.contract.read_text(encoding="utf-8"))
    old=json.loads(args.original_crosswalk_contract.read_text(encoding="utf-8"))
    if c.get("schema")!="structural.biomoni_shared_protocol_standardized_event_v1_299" or (
        c["status"]!="EXPLICITLY_EXPLORATORY_POST_EVENT_EXPOSED_FREEZE_BEFORE_ANY_BEETLE_OR_WOODY_OCCURRENCE"
        or c["fixed_archive_sha256"]!={name:s[1] for name,s in SOURCE.items()}
        or old.get("schema")!="structural.biomoni_colocated_terceira_event_crosswalk.v1_298"):
        raise ValueError("Unfrozen exploratory method-defined response-sealed study")
    result={"schema":"structural.biomoni_common_method_event_only_result.v1_299",
           "status":"SOURCE_OR_IDENTITY_STOP_NO_SPECIES_DATA",
           "original_woody_Occurrence_rows_opened":0,"original_beetle_Occurrence_rows_opened":0,
           "old_v1_298_full_method_gate_remains_terminal":True,
           "GEB_scientific_HOLD":True,"confirmatory_systems_admitted":0,"eBird_used":False}
    try:
        source={}
        for kind,(url,sha) in SOURCE.items():
            req=urllib.request.Request(url,headers={
                "User-Agent":"Structural-Terceira-Paired-UniformMode-SourceOnly-v1.299"})
            with urllib.request.urlopen(req,timeout=55) as remote:
                raw=remote.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES or hashlib.sha256(raw).hexdigest()!=sha:
                raise ValueError("Original source hash changed")
            source[kind]=extract_event_core_only(raw)
        result=evaluate(source["woody"],source["beetle"],c,old)
    except Exception as err:
        result["stop_type"]=type(err).__name__;result["stop_reason"]=str(err)[:280]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:result.get(k) for k in ("status","ten_exact_woody_beetle_plot_keys",
      "shared_protocol_modes_count","shared_modes_minimum_sampling_events_sorted",
      "selected_beetle_Event_rows_each_woody_plot","selected_beetle_Event_rows_total",
      "original_woody_Occurrence_rows_opened","original_beetle_Occurrence_rows_opened",
      "stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_OR_IDENTITY_STOP_NO_SPECIES_DATA":raise SystemExit(2)

if __name__=="__main__":main()
