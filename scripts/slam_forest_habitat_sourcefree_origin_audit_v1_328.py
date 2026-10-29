#!/usr/bin/env python3
"""SLAM v1.328 source-FREE three-island original habitat/origin ecology audit.

Consumes ONLY v1.327 original numeric aggregate with source SHA provenance.
No original 14,922 SLAM species, 893 Event, BALA or PRIBES raw responses
are accessed, modified, reclassified or re-fitted.
"""
from __future__ import annotations
import argparse,json,math,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/"development/slam_three_island_habitat_source_result_freeze_v1_327.json"
PROTOCOL=ROOT/"development/slam_origin_specific_habitat_sourcefree_audit_protocol_v1_328.json"
ORIGINAL_RESULT_SHA="cea311a9a3b88715837603e0f794a34b8fb7fd62e8221bbe57eb2e6917874761"
SOURCE_ARCHIVE_SHA="b86f7fad6468d2fb9aa9473849effe41ba2c4405c786357b6f50d66d9ef552a0"
ISLANDS=("FLO","PIC","TER")

def near(a,b,label):
    if not math.isclose(a,b,rel_tol=0,abs_tol=1e-11):
        raise ValueError("Original SLAM v1.327 source-free original arithmetic changed: "+label)

def summarize_guild(group,label):
    per=group["per_island"]
    if set(per)!=set(ISLANDS) or [per[i]["quarters"] for i in ISLANDS]!=[6,30,34]:
        raise ValueError("Original matched source seasons/islands changed")
    for isl in ISLANDS:
        r=per[isl]
        near(r["endemic_native_minus_altered"]+r["native_nonendemic_native_minus_altered"],
             r["indigenous_native_minus_altered"],label+":"+isl+":indigenous")
        near(r["indigenous_native_minus_altered"]-r["introduced_native_minus_altered"],
             r["double_contrast"],label+":"+isl+":double")
        if not 0<=r["season_quarters_positive_double_contrast"]<=r["quarters"]:
            raise ValueError("Source 70 season subsamples cannot exceed original count")
        for typ in ("native","altered"):
            if not 0<=r["introduced_source_spatial_jaccard_"+typ]<=1:
                raise ValueError("Original source Jaccard similarity outside [0,1]")
    overall=group["original_island_equal"]
    metrics={
      "endemic_native_minus_altered":"endemic_native_minus_altered",
      "native_nonendemic_native_minus_altered":"native_nonendemic_native_minus_altered",
      "indigenous_native_minus_altered":"indigenous_native_minus_altered",
      "introduced_native_minus_altered":"introduced_native_minus_altered",
      "double_contrast":"origin_habitat_double_contrast"
    }
    for field,target in metrics.items():
        near(statistics.fmean(per[isl][field] for isl in ISLANDS),
             overall[target],label+":three_island_mean:"+field)
    positive_double=[i for i in ISLANDS if per[i]["double_contrast"]>0]
    endemic_native=[i for i in ISLANDS if per[i]["endemic_native_minus_altered"]>0]
    intro_altered=[i for i in ISLANDS if per[i]["introduced_native_minus_altered"]<0]
    nonendemic_altered=[i for i in ISLANDS if per[i]["native_nonendemic_native_minus_altered"]<0]
    spatial_alt_shared=[i for i in ISLANDS
        if per[i]["introduced_source_spatial_jaccard_altered"]>
           per[i]["introduced_source_spatial_jaccard_native"]]
    pos_quarters=sum(per[i]["season_quarters_positive_double_contrast"] for i in ISLANDS)
    sum_d=sum(per[i]["double_contrast"] for i in ISLANDS)
    return {
      "source_island_equal_mean_original":overall,
      "original_three_source_islands":list(ISLANDS),
      "original_matched_source_year_quarters_by_island":{i:per[i]["quarters"] for i in ISLANDS},
      "original_matched_source_year_quarters_total":70,
      "original_positive_double_contrast_source_quarters_n":pos_quarters,
      "original_positive_double_contrast_source_quarters_denominator":70,
      "islands_positive_origin_habitat_double_contrast":positive_double,
      "islands_endemic_named_taxa_richer_in_native_forest":endemic_native,
      "islands_introduced_named_taxa_richer_in_altered_forest":intro_altered,
      "islands_native_nonendemic_named_taxa_richer_in_altered_forest":nonendemic_altered,
      "islands_with_greater_within_altered_introduced_taxa_Jaccard_sharing":spatial_alt_shared,
      "overall_positive_double_contrast_fraction_attributable_to_largest_island_absolute_sum":
          max(abs(per[i]["double_contrast"]) for i in ISLANDS)/sum(abs(per[i]["double_contrast"]) for i in ISLANDS),
      "no_sitepair_pseudoreplicated_significance":True,
      "per_island_source_absolute_richness_differences":{
        i:{
          "endemic_native_minus_altered":per[i]["endemic_native_minus_altered"],
          "nonendemic_native_minus_altered":per[i]["native_nonendemic_native_minus_altered"],
          "indigenous_native_minus_altered":per[i]["indigenous_native_minus_altered"],
          "introduced_native_minus_altered":per[i]["introduced_native_minus_altered"],
          "double_contrast":per[i]["double_contrast"],
          "introduced_spatial_source_Jaccard_native_forest":per[i]["introduced_source_spatial_jaccard_native"],
          "introduced_spatial_source_Jaccard_altered_forest":per[i]["introduced_source_spatial_jaccard_altered"],
          "matched_original_season_n":per[i]["quarters"]
        } for i in ISLANDS
      }
    }

def audit(d,protocol):
    if (
       protocol.get("schema")!="structural.slam_three_island_sourcefree_habitat_ecology_audit.v1_328"
       or protocol.get("status")!="FROZEN_AFTER_SINGLE_ORIGINAL_SOURCE_EXECUTION_NO_NEW_BIOLOGICAL_READ"
       or protocol["source_original_result_JSON_SHA256"]!=ORIGINAL_RESULT_SHA
       or protocol["original_one_shot_run"]!=40829500865
       or protocol["source"]!="development/slam_three_island_habitat_source_result_freeze_v1_327.json"
       or d.get("schema")!="structural.slam_three_island_habitat_original_aggregate.v1_327"
       or d.get("status")!="SOURCE_OBSERVED_THREE_ISLAND_NATIVE_ALTERED_HABITAT_ORIGIN_CONTRAST_COMPLETE"
       or d["original_source"]["response_original_inner_JSON_SHA256"]!=ORIGINAL_RESULT_SHA
       or d["original_source"]["response_original_one_shot_run"]!=40829500865
       or d["original_source"]["source_v17_zip_SHA256"]!=SOURCE_ARCHIVE_SHA
       or d["original_source"]["original_Event_rows"]!=893
       or d["original_source"]["original_Occurrence_rows"]!=14922
       or d["original_source"]["original_fixed_selected_Event_rows"]!=664
       or d["original_source"]["original_source_sites_in_matched_strata"]!=33
       or d["original_source"]["original_islands_in_matched_habitat"]!=list(ISLANDS)
       or d["original_source"]["original_matched_yearquarter_n_by_island"]!={"FLO":6,"PIC":30,"TER":34}
    ):
        raise ValueError("Original response source identity, 42 site and 664 source Event gate differs")
    flags=d["scientific_status"]
    if not all(flags[x] for x in (
      "biological_response_not_rerun","old_BALA_PRIBES_original_scorers_sealed",
      "SLAM_original_one_shot_scorer_sealed","GEB_scientific_HOLD"
    )) or flags.get("new_confirmatory_systems")!=0 or flags.get("eBird"):
        raise ValueError("Previous source one-shot seal or scientific HOLD changed")
    prior=d["original_source"]["source_taxonomic_status_coverage"]
    if (prior["selected_occurrence_rows"]!=11163
        or prior["species_subspecies_named_records"]!=10554
        or prior["species_rank_origin_unclassified_n"]!=508
        or prior["selected_Source_Event_with_at_least_one_occurrence_fraction"]!=1
        or sum(prior[k] for k in (
          "recognized_endemic_occurrence_records",
          "recognized_native_occurrence_records",
          "recognized_introduced_occurrence_records",
          "species_rank_origin_unclassified_n"))!=10554
        or prior["species_subspecies_named_records"]+prior["higher_rank_or_unnamed_records"]!=11163):
        raise ValueError("Original taxonomic source response count/coverage changed")
    near(prior["species_rank_origin_unclassified_fraction"],508/10554,"origin uncertain")
    allg=summarize_guild(d["main_all_arthropods"],"all arthropods")
    beetlegroup=d["secondary_Coleoptera"]
    if beetlegroup["status"]!="OBSERVED_ORIGIN_SPECIFIC_HABITAT_RICHNESS_CONTRAST":
        raise ValueError("Original source Coleoptera secondary status no longer eligible")
    beeg=summarize_guild(beetlegroup,"Coleoptera")
    near(beetlegroup["source_event_fraction_with_any_named_coleoptera"],559/664,"Coleoptera source Event detectability")
    if (allg["islands_endemic_named_taxa_richer_in_native_forest"]!=list(ISLANDS)
        or allg["islands_introduced_named_taxa_richer_in_altered_forest"]!=list(ISLANDS)
        or allg["islands_native_nonendemic_named_taxa_richer_in_altered_forest"]!=["PIC","TER"]
        or allg["islands_with_greater_within_altered_introduced_taxa_Jaccard_sharing"]!=["TER"]
        or beeg["islands_endemic_named_taxa_richer_in_native_forest"]!=["PIC","TER"]
        or beeg["islands_with_greater_within_altered_introduced_taxa_Jaccard_sharing"]!=["TER"]):
        raise ValueError("Pre-frozen original ecological sign contrasts or spatial similarity changed")
    return {
      "schema":"structural.slam_original_habitat_origin_sourcefree_result.v1_328",
      "status":"SLAM_THREE_ISLAND_FOREST_HABITAT_ORIGIN_SOURCEFREE_AUDITED",
      "original_response_run_id":40829500865,
      "original_response_inner_JSON_SHA256":ORIGINAL_RESULT_SHA,
      "source_island_contexts":["FLO","PIC","TER"],
      "actual_original_physical_forest_plots_compared":33,
      "actual_original_source_site_yearquarter_Event_rows":664,
      "main_arthropods":allg,
      "secondary_coleoptera":beeg,
      "original_species_rank_status_unclassified_fraction":prior["species_rank_origin_unclassified_fraction"],
      "endemic_vs_nonendemic_native_respond_differently":True,
      "increased_introduced_richness_in_altered_does_not_imply_uniform_within_habitat_spatial_homogenization":True,
      "three_island_equal_double_contrast_largely_contributed_by_Flores":True,
      "original_source_quarters_repeated_not_70_independent_landscapes":True,
      "original_SLAM_v327_Event_Occurrence_rows_reopened":0,
      "original_BALA_PRIBES_species_rows_reopened":0,
      "SLAM_original_scorer_SEALED":True,
      "not_forest_type_randomized_or_causally_identified":True,
      "no_actual_immigration_or_true_extinction_measured":True,
      "not_independent_multi_archipelago_confirmation":True,
      "GEB_scientific_HOLD":True,
      "new_confirmatory_systems":0,
      "eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,default=ORIGINAL)
    p.add_argument("--contract",type=Path,default=PROTOCOL)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    r=audit(json.loads(a.input.read_text(encoding="utf-8")),
            json.loads(a.contract.read_text(encoding="utf-8")))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(r,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print(json.dumps({
       "status":r["status"],
       "all_endemic_islands_native_affinity":r["main_arthropods"]["islands_endemic_named_taxa_richer_in_native_forest"],
       "all_introduced_islands_altered_affinity":r["main_arthropods"]["islands_introduced_named_taxa_richer_in_altered_forest"],
       "nonendemic_native_altered_affinity_islands":r["main_arthropods"]["islands_native_nonendemic_named_taxa_richer_in_altered_forest"],
       "beetle_double_contrast":r["secondary_coleoptera"]["source_island_equal_mean_original"]["origin_habitat_double_contrast"],
       "source_island_similarity_intro_altered_higher":r["main_arthropods"]["islands_with_greater_within_altered_introduced_taxa_Jaccard_sharing"],
       "original_biological_rows_reopened":0
    },sort_keys=True))
if __name__=="__main__":main()
