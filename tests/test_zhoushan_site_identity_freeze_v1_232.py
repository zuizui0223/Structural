import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/zhoushan_published_site_identity_freeze_v1_232.json"
def test_study_internal_island_ids_not_fabricated_global_island_names():
    x=json.loads(P.read_text())
    c=x["source"]["internal_island_codes"]
    assert c==["s"+str(i).zfill(2) for i in range(1,40)]
    assert x["source"]["first_header_fields"][0]=="Island code"
    assert x["source"]["source_table_contains_explicit_latitude_longitude_columns"] is False
    assert x["external_validation_gate"]["island_identity_original_4126_crosswalk_verified"] is False
    assert x["external_validation_gate"]["admit_species_by_island_occurrence_validation_now"] is False
def test_no_external_observations_or_original_labels_unsealed():
    x=json.loads(P.read_text())
    assert len(x["prior_taxa"]["shared_five_species"])==5
    assert x["boundaries"]["field_species_island_values_opened"]==0
    assert x["boundaries"]["original_IUCN_heldout_labels_reopened"]==0
    assert x["boundaries"]["original_graph_retuned"] is False
    assert x["boundaries"]["GEB_submission_authorized"] is False
