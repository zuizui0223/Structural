import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/camtrapasia_study_year_eligibility_freeze_v1_253.json"
def test_source_year_availability_nonneutral_sampling_design():
    x=json.loads(P.read_text())
    assert x["source_camera_studies"]==78
    assert x["original_heldout_spatial_blocks"]==3
    assert x["totals"]["pre2017_studies"]==71
    assert x["totals"]["spans2017_studies"]==4
    assert x["totals"]["after2017_studies"]==3
    assert x["totals"]["islands_with_after2017"]==1
    assert x["totals"]["original_heldout_blocks_with_after2017"]==1
    assert sum(a["total"] for a in x["by_island"])==78
def test_sampling_era_not_biological_absence_or_source_temporal_gain():
    x=json.loads(P.read_text())
    assert x["interpretation"]["no_post2017_Sumatra_field_detection_is_due_to_lack_of_camera_survey_opportunity"] is True
    assert x["interpretation"]["no_camera_detection_or_species_value_read_in_v253"] is True
    assert x["interpretation"]["no_prospective_two_island_post2017_external_predictive_skill_test"] is True
    assert x["interpretation"]["original_529_IUCN_heldout_labels_read"]==0
    assert all(y is False for y in x["safeguards"].values())
