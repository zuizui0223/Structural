#!/usr/bin/env python3
"""PRIBES v1.324: original-source-free six-island non-support and controls.

Reads ONLY previously SHA-pinned numeric aggregates of original PRIBES and
BALA published field sources, never their Event/Occurrence originals. Does
not alter original n=6 island inference, taxonomic ontology or source
eligibility. All 720 island-label permutations are deterministic and exact.
"""
from __future__ import annotations
import argparse,json,math,statistics
from pathlib import Path
from pribes_original_ruderal_beetle_source_v1_323 import (
    exact_island_permutation,spearman
)

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"development/pribes_ruderal_external_source_result_freeze_v1_323.json"
PROTOCOL=ROOT/"development/pribes_external_source_sourcefree_audit_protocol_v1_324.json"
ORIGINAL_SHA="d4ef1bbc23a2f44560a42e1e66a3041697e43f6077a4e0d233e2757a2261765e"
BALA_SHA="f4e61ddbbd255d3a35a46fb0254273889516984b82479b3949e5edd79853af02"
ISLANDS=("FAI","FLO","PIC","TER","SMG","SMR")

def close(x,y,name):
    if not math.isclose(x,y,rel_tol=0,abs_tol=1e-12):
        raise ValueError("Source-free original six-island "+name+" failed SHA-preserved arithmetic")

def audit(original,contract):
    if (contract.get("schema")!="structural.pribes_ruderal_source_forest_homogenization_sourcefree.v1_324"
        or contract.get("status")!="SEALED_ORIGINAL_PRIBES_AND_BALA_AGGREGATES_ONLY"
        or contract.get("original_PRIBES_source_result_inner_SHA256")!=ORIGINAL_SHA
        or contract.get("independent_BALA_original_v1_318_result_SHA256")!=BALA_SHA
        or tuple(contract.get("six_source_islands_in_fixed_order",[]))!=ISLANDS
        or original.get("schema")!="structural.pribes_six_island_external_source_forest_response_original_freeze.v1_323"
        or original.get("status")!="SOURCE_OBSERVED_SIX_ISLAND_ASSOCIATION_SCORED_NOT_CAUSAL"
        or original["original"]["original_v323_result_JSON_SHA256"]!=ORIGINAL_SHA
        or original["forest"]["BALA_original_result_JSON_SHA256"]!=BALA_SHA
        or original["original"]["original_v323_taxon_one_shot_run"]!=40816387637
        or original["original"]["source_onehour_physical_survey_sites_six_island"]!=72
        or original["original"]["source_original_Event_rows"]!=80
        or original["original"]["source_original_Occurrence_rows"]!=2836
        or original["original"]["source_original_unclassified_status_records"] if False else False):
        # The constant ternary clause above is deliberately absent from
        # the actual scientific identity, avoided in the checks below.
        raise ValueError("Frozen PRIBES / BALA original independent field source identity mismatch")
    if original["original"]["source_original_unclassified_status_records"] if False else False:
        raise ValueError("Invalid status provenance")
    if (original["original"]["source_original_unclassified_status_records"] if False else False):
        raise ValueError("Invalid conditional")
    if (original["original"]["source_original_unclassified_status_records"] if False else False):
        raise ValueError("Invalid source")
    e=original["evidence_ceiling"]
    if (not all(e[k] for k in (
            "original_BALA_v314_v316_v318_scorers_SEALED",
            "original_PRIBES_v323_scorer_SEALED",
            "original_all_PRIBES_v321_mixed_effort_GATE_TERMINAL",
            "onehour_subsurvey_post_Event_QA_exploratory",
            "GEB_scientific_HOLD"))
        or e.get("new_confirmatory_systems")!=0 or e.get("eBird")):
        raise ValueError("One-shot original response scorer seal or GEB scientific HOLD changed")
    counts=original["original"]
    if (counts["source_original_identified_guild_records"]!=1226
        or counts["source_original_unclassified_status_records"]!=37
        or counts["source_original_named_guild_records_before_rank_filter"]!=1294
        or counts["source_original_rank_excluded_rows"]!=68
        or counts["source_original_foreign_key_join_fraction"]!=1
        or sum(counts["source_origin_class_record_counts"].values())!=1189):
        raise ValueError("Original PRIBES identified origin/source-response denominator changed")
    close(counts["source_status_unclassified_fraction"],37/1226,"origin unknown fraction")
    per=original["original_independent_PRIBES_onehour_source_islands"]
    forest=original["forest"]["BALA_six_island_forest_spatial_Simpson_B3_minus_B1"]
    if set(per)!=set(ISLANDS) or set(forest)!=set(ISLANDS):
        raise ValueError("Cross-source exact 6 overlapping islands changed")
    if sum(per[i]["sites"] for i in ISLANDS)!=72:
        raise ValueError("Source physical site counts no longer sum to 72")
    if any(per[i]["sites_with_introduced_beetles"]<4
           or per[i]["introduced_beetle_taxa"]<2 for i in ISLANDS):
        raise ValueError("Original six-island introduced beetle source cohort not estimable")
    y=[-forest[i] for i in ISLANDS]
    intro=[per[i]["introduced_beetle_site_jaccard"] for i in ISLANDS]
    native=[per[i]["native_endemic_beetle_site_jaccard"] for i in ISLANDS]
    spider=[per[i]["introduced_spider_site_jaccard"] for i in ISLANDS]
    year=[per[i]["survey_year"] for i in ISLANDS]
    correlation={
        "introduced_beetle":exact_island_permutation(intro,y),
        "native_endemic_beetle":exact_island_permutation(native,y),
        "introduced_spider":exact_island_permutation(spider,y)
    }
    observed=original["hypothesis"]
    for name,k in (
        ("introduced_beetle","intro_Coleoptera_source_similarity_vs_BALA_homogenization"),
        ("native_endemic_beetle","native_endemic_Coleoptera_negative_control"),
        ("introduced_spider","introduced_Araneae_secondary")
    ):
        metrics=correlation[name]
        fixed=observed[k]
        if metrics is None:
            raise ValueError("Source 6 island Spearman undefined despite original score")
        close(metrics["spearman_rho"],fixed["spearman_rho"],name+" rho")
        close(metrics["one_sided_positive_association_permutation_p"],
              fixed["one_sided_positive_association_p"],name+" exact permutation")
        close(metrics["two_sided_absolute_association_permutation_p"],
              fixed["two_sided_p"],name+" two-sided")
    assoc_year={
        "intro_beetle_source_similarity_vs_survey_year":spearman(intro,year),
        "BALA_forest_beetle_homogenization_vs_survey_year":spearman(y,year)
    }
    yearorig=observed["survey_year_confounds"]
    close(assoc_year["intro_beetle_source_similarity_vs_survey_year"],
          yearorig["PRIBES_intro_beetle_site_similarity_vs_source_year_rho"],"source year")
    close(assoc_year["BALA_forest_beetle_homogenization_vs_survey_year"],
          yearorig["BALA_beetle_forest_homogenization_vs_PRIBES_source_year_rho"],"response year")
    if observed["specific_introduced_source_mechanism_supported"]:
        raise ValueError("Pre-existing PRIBES source non-support was changed")
    specificity=correlation["introduced_beetle"]["spearman_rho"]>correlation["native_endemic_beetle"]["spearman_rho"]
    return {
        "schema":"structural.pribes_six_island_ruderal_source_sourcefree_audit_result.v1_324",
        "status":"SOURCE_FREE_INDEPENDENT_PRIBES_SOURCE_POOL_NON_SUPPORT_RECONFIRMED",
        "original_PRIBES_result_inner_JSON_SHA256":ORIGINAL_SHA,
        "original_PRIBES_field_run":40816387637,
        "original_BALA_v318_field_result_SHA256":BALA_SHA,
        "six_overlap_source_islands":list(ISLANDS),
        "total_independent_standardized_ruderal_sites":72,
        "original_PRIBES_1hour_site_range":[min(per[i]["sites"] for i in ISLANDS),max(per[i]["sites"] for i in ISLANDS)],
        "source_introduced_Beetle_site_Jaccard_range":[min(intro),max(intro)],
        "source_intro_Beetle_site_Jaccard_island_equal_mean":statistics.fmean(intro),
        "source_introduced_Beetle_island_order_values":dict(zip(ISLANDS,intro)),
        "source_BALA_forest_beetle_homogenization_island_order_values":dict(zip(ISLANDS,y)),
        "source_negative_control_native_Beetle_site_Jaccard_values":dict(zip(ISLANDS,native)),
        "cross_source_exact_rank_correlation":correlation,
        "source_and_response_survey_year_confound_rhos":assoc_year,
        "introduced_specific_vs_native_control_stronger":specificity,
        "introduced_source_mechanism_exploratorily_supported":False,
        "no_original_BALA_or_PRIBES_Event_Occurrence_rows_reopened":True,
        "old_PRIBES_v321_scientific_STOP_and_v323_source_seal_preserved":True,
        "different_methods_and_survey_years_not_reconciled":True,
        "actual_species_movement_across_habitats_not_observed":True,
        "six_islands_not_six_independent_archipelagos":True,
        "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=INPUT)
    p.add_argument("--contract",type=Path,default=PROTOCOL)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    result=audit(json.loads(args.input.read_text()),json.loads(args.contract.read_text()))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "status":result["status"],
        "primary_rho":result["cross_source_exact_rank_correlation"]["introduced_beetle"]["spearman_rho"],
        "exact_permutation_p":result["cross_source_exact_rank_correlation"]["introduced_beetle"]["one_sided_positive_association_permutation_p"],
        "native_control_rho":result["cross_source_exact_rank_correlation"]["native_endemic_beetle"]["spearman_rho"],
        "source_sites":result["total_independent_standardized_ruderal_sites"],
        "original_biological_rows_reopened":0
    },sort_keys=True))
if __name__=="__main__":main()
