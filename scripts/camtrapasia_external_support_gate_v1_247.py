#!/usr/bin/env python3
"""No raw biological files: original mammal external support decision from frozen geography receipts."""
import argparse,json
from pathlib import Path
def evaluate(taxon,area):
    names=taxon["summary"]["exact_shared_taxa"]
    g=area["results"]
    if names!=38 or g["study_centers_total"]!=15 or g["original_nearest_heldout_ids"]!=10:
        raise ValueError("Prior pre-outcome evidence drift")
    if g["same_polygon_and_area_ratio_le_2"]!=2 or g["offland_nearest_polygon_same_and_area_ratio_le_2"]!=0:
        raise ValueError("Original source island area constraints drift")
    studies=g["remaining_area_consistent_studies"]
    if len(studies)!=2:raise ValueError("Expected exactly two candidate study centers")
    islands={r["nearest_original_heldout_ID"] for r in studies}
    blocks={r["original_heldout_block"] for r in studies}
    if len(islands)!=1 or len(blocks)!=1:raise ValueError("Unexpected spatial independence")
    return {
      "schema":"structural.camtrapasia_mammal_external_support_result.v1_247",
      "status":"STOP_ORIGINAL_GLOBAL_529_EXTERNAL_FIELD_SCORE_NO_INDEPENDENT_ISLAND_REPLICATES",
      "published_species_name_overlaps":names,
      "source_studies_with_centroid_distance_below25km":15,
      "spatially_proximate_original_heldout_island_ids":10,
      "geographic_heuristic_nearest_land_candidates_without_area_gate":11,
      "geographic_area_consistent_same_component_survey_studies":2,
      "distinct_source_original_heldout_island_ids":len(islands),
      "distinct_original_heldout_spatial_blocks":len(blocks),
      "maximum_possible_species_x_distinct_island_cells":names*len(islands),
      "verified_mammal_field_observation_cells":0,
      "independent_global_529_prediction_evaluation_admitted":False,
      "field_camera_capture_rows_read":0,
      "original_IUCN_heldout_presence_absence_values_read":0,
      "original_modelled_mammal_predictions_read":0
    }
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("taxa",type=Path);p.add_argument("geometry",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();obj=evaluate(json.loads(a.taxa.read_text()),json.loads(a.geometry.read_text()))
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    print(json.dumps(obj,sort_keys=True))
