import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_posthoc_observed_camera_set_overlap_does_not_promote_GEB():
    x=json.loads((ROOT/"development/camtrapasia_field_photo_positive_overlap_freeze_v1_251.json").read_text())
    assert x["Java_Sumatra_positive_wild_taxon_intersection_count"]==10
    assert x["Java_Sumatra_positive_wild_taxon_union_count"]==22
    assert abs(x["Jaccard_observed_positive_wild_name_sets"]-10/22)<1e-12
    assert len(x["cross_island_positive_taxa_with_2plus_surveys_each"])==7
    assert x["original_heldout_spatial_block_Java_equals_Sumatra"] is True
    assert x["limitations"]["same_spatial_block_cannot_validate_crossblock_original_GEB_spatial_gain"] is True
    assert x["limitations"]["original_GEB_prediction_scores_unread"] is True
    assert x["GEB_scientific_hold"] is True
