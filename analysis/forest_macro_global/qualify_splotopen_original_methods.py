#!/usr/bin/env python3
"""Join frozen GIVD original field protocol decisions to actual sPlotOpen source cohort.

This is a NO-BIOLOGY source-method audit. Inputs are the source-only
sPlotOpen v76 aggregation and externally verified GIVD protocol metadata.
Never assume source projects/plot labels are independent natural forests.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

EXPECTED_IDS=("AS-BD-001","AS-CN-003","SA-BR-002","EU-CH-005")
STOP_WORDS={"ADMITTED","SCORED","CONFIRMED","GENERALIZED"}

def run(source_csv,crosswalk_path,out_dir):
    source=list(csv.DictReader(Path(source_csv).open(encoding="utf-8",newline="")))
    byid={r["source_givd_dataset"]:r for r in source}
    if len(byid)!=len(source) or len(source)<80:
        raise ValueError("source_cohort_duplicate_or_incomplete")
    meta=json.loads(Path(crosswalk_path).read_text(encoding="utf-8"))
    if meta.get("schema")!="structural.forest_macro_splotopen_original_method_crosswalk.v1":
        raise ValueError("original_methods_version_mismatch")
    entries=meta.get("source_records",[])
    if {x["source_givd_dataset"] for x in entries}!=set(EXPECTED_IDS):
        raise ValueError("original_source_method_cohort_drift")
    out=[]
    for m in entries:
        sid=m["source_givd_dataset"]
        r=byid.get(sid)
        if not r:raise ValueError("source_original_dataset_not_in_splotopen:"+sid)
        if m["source_outcome_admission"].startswith("PENDING_") is False:
            raise ValueError("not_yet_outcome_eligible_source_marked_admitted")
        height_cover=int(r["contemporaneous_height_and_cover_plots"])
        woody=int(r["declared_woody_height_and_cover_plots"])
        unrecorded=int(r["UNSPECIFIED_survey_scope_height_and_cover_plots"])
        if height_cover<20:raise ValueError("source_candidate_support_below_frozen_20_plot_gate")
        if woody+unrecorded>height_cover:raise ValueError("source_survey_scope_overlap")
        out.append({
            "GIVD_ID":sid,
            "source_database_name":m["source_database_name"],
            "forest_original_open_subset_plot_nodes_NOT_independent_forests":int(r["forest_plots"]),
            "open_subset_height_and_cover_plot_nodes":height_cover,
            "declared_woody_scope_height_and_cover_plot_nodes":woody,
            "scope_not_specified_in_open_subset_height_and_cover_nodes":unrecorded,
            "source_metadata_scope":m["source_scope"],
            "source_original_units":json.dumps(m.get("original_units"),sort_keys=True),
            "source_independence_gate":m["source_independence_gate"],
            "outcome_admission":m["source_outcome_admission"],
            "ecological_endpoint_scored":False,
            "forest_site_network_identity_verified":False,
            "source_original_metadata_url":m["original_metadata_url"],
        })
    dest=Path(out_dir);dest.mkdir(parents=True,exist_ok=True)
    fields=list(out[0])
    with (dest/"four_source_original_field_method_crosswalk.csv").open("w",encoding="utf-8",newline="") as fd:
        w=csv.DictWriter(fd,fieldnames=fields);w.writeheader();w.writerows(out)
    summary={
        "schema":"structural.forest_macro_splotopen_source_field_method_qualification.v1",
        "source_original_givd_identity_verified":len(out),
        "open_subset_matched_height_cover_plot_nodes_not_independent_forests":sum(x["open_subset_height_and_cover_plot_nodes"] for x in out),
        "declared_woody_scope_source_count":sum(x["declared_woody_scope_height_and_cover_plot_nodes"]>=20 for x in out),
        "unclear_open_subset_scope_source_count":sum(x["scope_not_specified_in_open_subset_height_and_cover_nodes"]>=20 for x in out),
        "forest_source_networks_certified_for_island_biogeographic_occurrence_test":0,
        "matched_original_study_method_and_temporal_panels_certified":0,
        "new_species_data_opened":0,
        "new_biodiversity_results_calculated":False,
        "outcome_target_not_known_from_metadata":True,
        "unobserved_forest_patches_assumed_unoccupied":False,
        "eBird_used":False
    }
    (dest/"four_source_original_field_method_manifest.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
    for r in out:
        print("source field protocol:",r["GIVD_ID"],r["open_subset_height_and_cover_plot_nodes"],
              r["source_independence_gate"],r["outcome_admission"])
    return summary


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True)
    p.add_argument("--crosswalk",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.source,a.crosswalk,a.out)
