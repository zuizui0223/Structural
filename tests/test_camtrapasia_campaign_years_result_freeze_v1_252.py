import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/camtrapasia_campaign_years_result_freeze_v1_252.json"
def test_postoutcome_source_campaign_temporal_boundary():
    x=json.loads(P.read_text())
    assert x["sampling"]["total_study_centers"]==74
    assert x["sampling"]["study_windows_valid"]==74
    assert x["temporal_observations"]["with_at_least_two_strictly_nonoverlapping_positive_study_intervals_on_each_island"]==6
    assert x["temporal_observations"]["Sumatra_seven_taxa_positive_study_campaign_post2017_count"]==0
    assert x["temporal_observations"]["taxa_with_positive_nonoverlap_campaigns_before_and_after2017_on_both_islands"]==0
    assert x["conclusion_boundary"]["published_during_or_after2024_does_not_mean_data_collected_after2017"] is True
    assert x["conclusion_boundary"]["original_IUCN_heldout_species_values_opened"]==0
    assert x["conclusion_boundary"]["global_GEB_predictive_skill_unmeasured"] is True
    assert all(y is False for y in x["safeguards"].values())
