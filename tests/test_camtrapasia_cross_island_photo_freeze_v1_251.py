import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def test_positive_replicability_without_global_model_overclaim():
    a=json.loads((R/"development/camtrapasia_four_island_field_positive_freeze_v1_250.json").read_text())
    b=json.loads((R/"development/camtrapasia_cross_island_photo_replicability_freeze_v1_251.json").read_text())
    assert a["status"]=="EXECUTED_POSTPUBLICATION_EXPLORATORY_CAMERA_POSITIVE_ONLY"
    assert len(a["four_candidate_areas"])==4
    assert sum(x["studies"] for x in a["four_candidate_areas"])==78
    assert a["source_mammal_photo_row_metadata"]["field_positive_rows_in_38_name_taxa"]==440
    assert b["comparison"]["positive_in_both_any_domestic_label"]==11
    assert b["comparison"]["positive_in_both_non_domestic_source_label"]==10
    assert b["comparison"]["repeated_non_domestic_two_plus_survey_IDs_each_island"]==7
    assert len(b["replicated_each_island_two_plus_survey_IDs_and_all_non_domestic_records"])==7
    assert "Canis lupus" not in b["strict_wild_cross_island_taxa"]
    assert b["ecological_claim_ceiling"]["two_islands_one_original_geo_block_not_between_block_replication"] is True
    assert b["ecological_claim_ceiling"]["no_external_GEB_graph_validation"] is True
    assert all(x is False for x in b["safeguards"].values())
