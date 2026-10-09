import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
F=ROOT/"development/zhoushan_taxon_overlap_terminal_v1_230.json"
def test_original_global_mammal_validation_stops_before_field_outcomes():
    a=json.loads(F.read_text())
    t=a["taxon_crosscheck"]
    assert t["exact_name_overlaps"]==0
    assert t["field_species_island_incidence_opened"]==0
    assert t["original_heldout_0_1_reopened"]==0
    assert a["scientific_decision"]["this_survey_directly_validates_frozen_529_species"] is False
    assert a["scientific_decision"]["is_negative_test_of_original_predictive_skill"] is False
    assert a["scientific_decision"]["additional_Zhoushan_field_0_1_access_for_this_original_529_claim"] is False
    assert a["scientific_decision"]["GEB_scientific_HOLD"] is True
def test_underlying_docx_stable_outside_zip_container():
    a=json.loads(F.read_text())
    z=a["official_zip"]
    assert z["v227_outer_SHA256"]!=z["v229_outer_SHA256"]
    assert z["outer_archive_byte_length_both"]==841453
    assert z["verified_inner_docx_sha256"]=="ec1d1d0a5dbe3f0cee955dfe4018e678a48a796d5135b2311888d47aad9ecd64"
    assert a["table_structure"]["Word_tables"]==9
    assert a["table_structure"]["rectangular_39_40_by_18_plus_candidate_count"]==0
    assert all(x is False for x in a["policy"].values())
