import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def test_cameratrap_screen_counts_and_boundaries():
 x=json.loads((R/"development/camtrapasia_original_heldout_centroid_distance_freeze_v1_240.json").read_text())
 assert x["status"]=="PASS_GEOGRAPHY_ONLY_STUDY_CENTER_DISTANCE_SCREEN"
 assert x["execution"]["tests_passed"]==2
 assert sum(x["count_study_centres_by_nearest_heldout_island_centroid_distance_km"].values())==239
 assert x["within_25km"]["study_centers"]==15
 assert x["within_25km"]["unique_heldout_spatial_blocks"]==7
 assert x["candidate_species_name_count"]==38
 assert x["external_original_529_prediction_score_authorized"] is False
 assert x["original_mammal_prediction_values_opened"]==0
 assert x["eBird"] is False
