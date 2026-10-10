#!/usr/bin/env python3
"""Derive independent-photo-positive cross-island replication from frozen v1.250 aggregate ONLY."""
import argparse,json
from pathlib import Path
EXPECT={"Bawean":("65489",2,0),"Buton":("65360",2,0),
        "Java":("65554",25,16),"Sumatra":("70378",49,18)}
def evaluate(source):
    if source.get("schema")!="structural.camtrapasia_four_candidate_island_camera_positive_result.v1_250" or source.get("status")!="PASS_EXPLORATORY_FIELD_POSITIVE_ONLY_NO_MODEL_SCORE":
        raise ValueError("Input not executed v1.250 aggregate")
    if source.get("original_IUCN_heldout_response_values_read")!=0 or source.get("original_model_prediction_scores_read")!=0:
        raise ValueError("Consumed outcome reopened")
    if source.get("eligible_source_camera_survey_centers")!=78 or source.get("original_independent_heldout_geographic_blocks")!=3:
        raise ValueError("Frozen source denominator drift")
    rows=source["per_island_camera_field_positive_summary"]
    island={v["geography_candidate_island"]:v for v in rows}
    if len(rows)!=4 or set(island)!=set(EXPECT):raise ValueError("Four islands not identical")
    for name,(iid,studies,taxa) in EXPECT.items():
        v=island[name]
        if (v["original_heldout_ID"],v["source_camera_survey_studies"],
            v["original_529_shared_taxa_with_positive_field_photo_records"])!=(iid,studies,taxa):
            raise ValueError("Source isotope/island study identity drift")
    a={v["species"]:v for v in island["Java"]["focal_taxon_positive_evidence"]}
    b={v["species"]:v for v in island["Sumatra"]["focal_taxon_positive_evidence"]}
    shared=sorted(set(a)&set(b))
    wild=[s for s in shared if a[s]["confident_non_domestic_records"]>0 and b[s]["confident_non_domestic_records"]>0]
    repeated=[s for s in wild if all(z["survey_count"]>=2 and
        z["confident_non_domestic_records"]==z["records"] and
        z["unknown_domestic_records"]==0 for z in (a[s],b[s]))]
    if (len(shared),len(wild),len(repeated))!=(11,10,7):raise ValueError("Observed v1.250 aggregate inconsistent")
    if "Canis.lupus" not in shared or "Canis.lupus" in wild:raise ValueError("Domestic dogs reclassified as wild")
    return {"schema":"structural.camtrapasia_replicated_java_sumatra_wild_field_positive_result.v1_251",
       "status":"PASS_POSTOUTCOME_DESCRIPTIVE_TWO_ISLAND_POSITIVES_ONLY",
       "original_frozen_pilot_taxa_with_source_name_overlap":38,
       "positive_detected_taxa_Java":len(a),"positive_detected_taxa_Sumatra":len(b),
       "shared_photographic_positive_taxa_any_domestic_code":len(shared),
       "shared_taxa_with_confirmed_non_domestic_positive_both":len(wild),
       "wild_positive_taxa_replicated_two_plus_study_IDs_each_island":len(repeated),
       "shared_wild_species":[t.replace("."," ") for t in wild],
       "shared_replicated_wild_species":[t.replace("."," ") for t in repeated],
       "shared_taxa_study_counts":[{"species":s,"Java_studies":a[s]["survey_count"],
           "Sumatra_studies":b[s]["survey_count"],
           "all_Java_records_non_domestic":a[s]["confident_non_domestic_records"]==a[s]["records"],
           "all_Sumatra_records_non_domestic":b[s]["confident_non_domestic_records"]==b[s]["records"]}
           for s in shared],
       "original_geographic_heldout_blocks_for_Java_and_Sumatra":1,
       "Bawean_and_Buton_zero_matching_photo_rows_does_not_establish_absence":True,
       "pilot_1to4_map_positive_islands_do_not_define_global_species_rarity":True,
       "new_camera_capture_file_accessed":False,
       "original_mammal_heldout_responses_reopened":False,
       "original_model_predictions_scored":False,
       "original_GEB_validation_claimed":False}
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("prior_result",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();x=evaluate(json.loads(a.prior_result.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
    print(json.dumps(x,sort_keys=True))
