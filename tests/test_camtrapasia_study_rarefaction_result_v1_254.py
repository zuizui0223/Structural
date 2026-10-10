import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"development/camtrapasia_study_rarefaction_result_freeze_v1_254.json"
def test_empirical_rarefaction_exact_expectations_study_count_not_camera_nights():
    x=json.loads(R.read_text())
    a=x["primary_pre2017"];b=x["all_year_secondary"]
    assert a["java_full_studies"]==18 and a["sumatra_full_studies"]==49
    assert a["standardized_studies"]==18
    assert a["java_observed_wild_positive_taxa"]==13
    assert abs(a["sumatra_18_expected_wild_positive_taxa_exact"]-15.345854766815439)<1e-12
    assert a["sumatra_18_study_subsampling_wild_positive_taxa_5_50_95"]==[14,15,17]
    assert b["java_observed_positive_taxa"]==15
    assert x["provenance"]["synthetic_tests_passed"]==2
def test_no_native_island_persistence_or_model_validation_claim():
    x=json.loads(R.read_text())
    assert x["original_heldout_geography"]["shared_original_heldout_block"]=="GB_8c3e9b18de7d"
    assert x["science"]["random_subset_quantiles_not_population_CI"] is True
    assert x["science"]["no_statistical_test_of_island_effect"] is True
    assert x["science"]["original_IUCN_heldout_response_values_read"]==0
    assert x["science"]["original_GEB_predictions_read"]==0
    assert all(z is False for z in x["policy"].values())
