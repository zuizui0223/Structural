#!/usr/bin/env python3
"""v1.221 published-methods-only intake check, no outcome reading or model fitting.

This is a scientific source-dependence ledger, NOT an empirical v0.11 pass.
"""
import argparse
import json
from pathlib import Path

def summarize(doc):
    if doc["schema"]!="structural.temporal_rescue_design_intake.v1_221":
        raise ValueError("Wrong contract")
    expected={"hopson_fox_2019","green_anderson_2022"}
    by_id={x["id"]:x for x in doc["sources"]}
    if set(by_id)!=expected or len(doc["sources"])!=2:
        raise ValueError("A source has been changed or opportunistically added")
    h,g=by_id["hopson_fox_2019"],by_id["green_anderson_2022"]
    if (h["independent_metapopulation_replicates"]!=14 or
        sum(h["treatment_replicates"].values())!=14 or
        h["number_patches_per_metapopulation"]!=15 or
        h["independent_heldout_graph_types_at_most"]!=2 or
        h["long_distance_daywise_route_realization_shared_across_replicates"] is not True):
        raise ValueError("Hopson design drift or patch pseudoreplication")
    if (g["independent_experiments_reported"]!=22 or
        g["unique_network_structures_reported"]!=16 or
        g["intended_metacommunity_replicates_per_experiment"]!=4 or
        g["maximum_potential_independent_metacommunity_units_before_source_id_validation"]!=88 or
        g["unambiguous_independent_network_topology_units_at_most"]!=16 or
        g["pooled_earlier_holyoak_studies"] is not True):
        raise ValueError("Green network-reuse or provenance accounting drift")
    if any(not s["article_context_already_exposed"] for s in [h]):
        raise ValueError("Already published outcomes are not fresh")
    if (doc["gate_contract"]["empirical_admitted"] or doc["gate_contract"]["pilot_opened"]
        or doc["gate_contract"]["confirmatory_opened"] or
        doc["guards"]["original_mammal_heldout_reopened"]):
        raise ValueError("Source-only review may not authorize biological effects")
    for s in (h,g):
        if s["raw_source_rows_opened"] or not s["preliminary_design_decision"].startswith("HOLD_NONFRESH"):
            raise ValueError("Response source improperly promoted")
    return {
      "schema":"structural.temporal_rescue_design_readiness_receipt.v1_221",
      "status":"PASS_DESIGN_ACCOUNTING_ONLY_ZERO_NEW_EMPIRICAL_ADMISSIONS",
      "hopson":{"independent_metapopulations":14,"patch_rows_not_independent":210,
        "unique_daywise_long_route_realizations_per_event_across_replicates":1,
        "candidate_decision":h["preliminary_design_decision"]},
      "green":{"experiments":22,"potential_metapopulation_replicates_before_identity_verification":88,
        "unique_network_structures_at_most":16,"pooled_published_source_studies":True,
        "candidate_decision":g["preliminary_design_decision"]},
      "prospectively_eligible_systems_added":0,
      "source_outcome_cells_read":0,"model_fits":0,
      "future_response_access_authorized":False,
      "GEB_scientific_HOLD":True
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    receipt=summarize(json.loads(a.manifest.read_text(encoding="utf-8")))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,sort_keys=True))
if __name__=="__main__":main()
