"""v1.296 source-free arithmetic on four locked original trail aggregate rows."""
import copy
import json
import math
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from azores_trail_weighting_sensitivity_v1_296 import calculate


def source():
    d=json.loads((ROOT/"development/azores_trail_native_alien_field_aggregate_freeze_v1_295.json").read_text(encoding="utf-8"))
    p=json.loads((ROOT/"development/azores_trail_weighting_sensitivity_protocol_v1_296.json").read_text(encoding="utf-8"))
    return d,p


def test_original_four_trails_and_three_weighting_estimates_reconcile_exactly():
    data,protocol=source()
    r=calculate(data,protocol)
    v=r["three_weighting_estimates"]
    assert r["status"]=="SOURCE_FREE_EXACT_AGGREGATION_SENSITIVITY_COMPLETE"
    assert math.isclose(v["original_equal_independent_trails"],-0.034415487924049845,abs_tol=1e-12)
    assert math.isclose(v["descriptive_equal_two_islands"],-0.1250427704287148,abs_tol=1e-12)
    assert math.isclose(v["nonindependent_repeated_area_group_weight"],0.09785153573826866,abs_tol=1e-12)
    assert r["three_weighting_directions"]=={
        "original_equal_independent_trails":"negative",
        "descriptive_equal_two_islands":"negative",
        "nonindependent_repeated_area_group_weight":"positive",
    }
    assert r["repeated_groups_reverses_original_equal_trail_sign"] is True
    assert r["equal_islands_reverses_original_equal_trail_sign"] is False
    assert r["original_primary_reproduced"]==r["original_fixed_primary_unmodified"]
    assert r["source_repeated_area_groups"]==17
    assert r["independent_trails"]==4 and r["independent_islands"]==2
    assert r["per_island"]["Terceira"]["independent_trails"]==3
    assert r["per_island"]["São Miguel"]["independent_trails"]==1
    assert r["per_island"]["Terceira"]["repeated_matched_area_year_groups"]==14
    assert r["per_island"]["São Miguel"]["repeated_matched_area_year_groups"]==3


def test_relative_native_enrichment_is_not_always_absolute_native_gain():
    data,protocol=source()
    r=calculate(data,protocol)
    t={(x["island"],x["anonymized_trail"]):x for x in r["per_trail"]}
    # Terceira T1: native species richness increases, yet the native/alien
    # composition worsens because introduced taxa increase even more.
    assert t[("Terceira","T1")]["logratio_direction"]=="negative"
    assert t[("Terceira","T1")]["native_richness_direction"]=="positive"
    assert t[("Terceira","T1")]["alien_richness_direction"]=="positive"
    assert t[("Terceira","T1")]["relative_native_decline_but_absolute_native_gain"]
    # Terceira T3: native richness falls but alien richness also falls;
    # therefore native/alien composition improves.
    assert t[("Terceira","T3")]["logratio_direction"]=="positive"
    assert t[("Terceira","T3")]["native_richness_direction"]=="negative"
    assert t[("Terceira","T3")]["alien_richness_direction"]=="negative"
    assert t[("Terceira","T3")]["relative_native_gain_but_absolute_native_decline"]
    assert r["positive_relative_ratio_but_declining_absolute_native_trails"]==1
    assert r["negative_relative_ratio_but_increasing_absolute_native_trails"]==1
    assert r["whole_trail_effect_min_max"]==[
        -0.30629733543804477,0.29349175199865246]
    assert r["per_island"]["Terceira"]["positive_trails"]==2


def test_source_and_safeguard_flags_never_promote_scientific_claims():
    data,protocol=source()
    r=calculate(data,protocol)
    assert r["group_weighted_contrast_is_nonindependent_sensitivity_NOT_primary"]
    assert r["summary_is_not_cross_island_statistical_generalization"]
    assert r["no_p_values_or_confidence_intervals"]
    assert r["no_original_2017_2019_Event_or_Occurrence_rows_reopened"]
    assert r["no_old_Pico_GEB_mammal_BioTIME_RLS_S2_S3_S4_responses_reopened"]
    assert r["not_causal_trail_intervention_or_movement_rescue"]
    assert r["old_v1_292_failure_terminal_unchanged"]
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_admissions"]==0 and not r["eBird_used"]
    assert "scientificName" not in json.dumps(r)
    assert "original_coreid" not in json.dumps(r)


def test_nonreproducible_original_primary_or_pseudoreplicate_count_is_stop():
    data,protocol=source()
    modified=copy.deepcopy(data)
    modified["per_trail"][1]["matched_area_year_groups"]=8
    with pytest.raises(ValueError, match="17 matched area-year"):
        calculate(modified,protocol)
    modified=copy.deepcopy(data)
    modified["per_trail"][0]["logratio_interior_minus_edge"]+=0.1
    with pytest.raises(ValueError, match="original equal-trail primary"):
        calculate(modified,protocol)
    modified=copy.deepcopy(data)
    modified["original_extracted_result_JSON_sha256"]="tampered"
    with pytest.raises(ValueError, match="identity/scientific boundary"):
        calculate(modified,protocol)
    modified=copy.deepcopy(data)
    modified["per_trail"][0]["anonymized_trail"]="T2"
    with pytest.raises(ValueError, match="duplicate original trail"):
        calculate(modified,protocol)


def test_source_aggregate_permutation_must_not_impact_source_free_arithmetic():
    data,protocol=source()
    baseline=calculate(data,protocol)
    new=copy.deepcopy(data)
    new["per_trail"].reverse()
    result=calculate(new,protocol)
    assert result["three_weighting_estimates"]==baseline["three_weighting_estimates"]
