#!/usr/bin/env python3
"""v1.251 postoutcome Java/Sumatra observational positive-name overlap from pre-scored v1.250 only."""
import argparse,json
from pathlib import Path
def calc(x):
    if x.get("status")!="PASS_EXPLORATORY_FIELD_POSITIVE_ONLY_NO_MODEL_SCORE":
        raise ValueError("Frozen v1.250 positive-only source not PASS")
    a=x.get("per_island_camera_field_positive_summary")
    if not isinstance(a,list) or len(a)!=4:raise ValueError("Incorrect original candidate island set")
    by={z["geography_candidate_island"]:z for z in a}
    if set(by)!={"Bawean","Buton","Java","Sumatra"}:raise ValueError("Different island source panel")
    if [by[n]["source_camera_survey_studies"] for n in ("Bawean","Buton","Java","Sumatra")]!=[2,2,25,49]:
        raise ValueError("Source camera-study denominators drift")
    def wild(name):
        z=by[name]["focal_taxon_positive_evidence"]
        if name in ("Bawean","Buton") and z:raise ValueError("No original frozen field overlap allowed")
        return {t["species"].replace("."," "):t for t in z if t["confident_non_domestic_records"]>0}
    java=wild("Java");sumatra=wild("Sumatra")
    j=set(java);s=set(sumatra)
    common=j&s;union=j|s
    if not union:raise ValueError("No positive observed taxa")
    repeat=sorted(name for name in common if java[name]["survey_count"]>=2 and sumatra[name]["survey_count"]>=2)
    return {
       "schema":"structural.camtrapasia_field_positive_overlap_posthoc_result.v1_251",
       "status":"PASS_POSTHOC_CONFIDENT_WILD_CAMERA_POSITIVE_OVERLAP_NO_GEB_INFERENCE",
       "frozen_camera_study_counts":{"Bawean":2,"Buton":2,"Java":25,"Sumatra":49},
       "confidently_non_domestic_positive_species":{"Java":len(j),"Sumatra":len(s)},
       "wild_camera_positive_taxa_union":len(union),
       "wild_camera_positive_taxa_shared":len(common),
       "Jaccard_OF_OBSERVED_POSITIVE_TAXA_ONLY":len(common)/len(union),
       "camera_positive_names_seen_on_both_large_islands":sorted(common),
       "camera_positive_taxa_with_two_plus_survey_ids_on_each_large_island":repeat,
       "twice_surveyed_wild_positive_taxa_both_islands":len(repeat),
       "Java_and_Sumatra_original_heldout_blocks_are_distinct":False,
       "unrecorded_island_species_are_true_absences":False,
       "independent_field_detection_is_not_dispersal_or_model_skill":True,
       "new_original_mammal_heldout_species_values_read":0,
       "new_camera_capture_source_rows_read":0,
       "external_GEB_global_model_prediction_validation":False
    }
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("frozen_positive_receipt",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();x=calc(json.loads(a.frozen_positive_receipt.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
    print(json.dumps(x,sort_keys=True))
