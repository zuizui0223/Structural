"""v1.301 proof of finite permutation precision with original aggregate only."""
import copy,json,sys,math
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from biomoni_woody_beetle_mc_precision_v1_301 import audit, wilson
def data():
    return (json.loads((ROOT/"development/biomoni_woody_beetle_v1_300_observed_aggregate_freeze.json").read_text()),
            json.loads((ROOT/"development/biomoni_woody_beetle_mc_precision_protocol_v1_301.json").read_text()))
def test_exact_original_finite_999_rank_and_mse():
    a,b=data();r=audit(a,b)
    assert r["status"]=="SOURCE_FREE_FINITE_PERMUTATION_PRECISION_COMPLETE"
    assert r["null_gain_ge_observed_count"]==39
    assert r["null_label_permutations"]==999
    assert r["original_plus_one_permutation_rank"]==.04
    assert math.isclose(r["original_relative_MSE_gain"],0.04930609189515262)
    assert math.isclose(r["gain_exceeds_frozen_95pct_null_by"],0.00012077856567687322)
    lo,hi=r["conditional_mc_wilson_95_interval_for_raw_null_fraction"]
    assert .0286<lo<.0288 and .0528<hi<.0530
    assert r["conditional_mc_wilson_upper_crosses_0_05"]
    assert r["mc_interval_is_not_ecological_uncertainty"]
    assert r["spatial_fragment_confounding_not_controlled"]
    assert r["no_site_or_taxon_data_reopened"] and r["no_new_permutations_or_models_fit"]
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]
def test_invalid_source_mse_and_fingerprint_fail_closed():
    a,b=data()
    t=copy.deepcopy(a);t["primary_LOPO_gain"]=0.1
    with pytest.raises(ValueError,match="LOPO"):audit(t,b)
    t=copy.deepcopy(a);t["original_inner_json_sha256"]="incorrect"
    with pytest.raises(ValueError,match="identity"):audit(t,b)
    t=copy.deepcopy(a);t["old_full_method_gate_status"]="SUCCESS"
    with pytest.raises(ValueError,match="STOP"):audit(t,b)
def test_wilson_interval_is_numerical_only_and_rational():
    assert wilson(0,999)[0]>=0
    assert wilson(999,999)[1]<=1
