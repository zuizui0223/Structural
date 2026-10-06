from pathlib import Path
import importlib.util,json,math

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/recover_sw_finland_numeric_counts_v1_173_3.py"
CONTRACT=ROOT/"development/sw_finland_standardized_historical_count_contract_v1_173_3.json"

def load():
    spec=importlib.util.spec_from_file_location("swf1733",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_thresholds_remain_at_v173_levels():
    c=json.loads(CONTRACT.read_text())
    assert c["anchors"]["minimum_numeric_anchor_matches"]==20
    assert c["calibration"]["maximum_anchor_count_rounding_error"]==0.01
    assert c["calibration"]["maximum_all_numeric_species_count_rounding_error"]==0.05
    assert c["calibration"]["minimum_exact_source_species"]==30
    assert c["calibration"]["thresholds_loosened_from_v1_173"] is False

def test_numeric_pool_and_nonnumeric_exclusion_are_frozen():
    c=json.loads(CONTRACT.read_text())
    assert c["eligibility"]["expected_numeric_species"]==312
    assert c["eligibility"]["excluded_species_expected"]==275
    assert c["eligibility"]["nonnumeric_species_may_reenter"] is False

def test_three_added_anchors_raise_expected_numeric_anchor_count_above_gate():
    c=json.loads(CONTRACT.read_text())
    assert c["anchors"]["base_numeric_anchor_count_expected"]==18
    assert len(c["anchors"]["additional_t0_anchors"])==3
    assert c["anchors"]["expected_numeric_anchor_matches"]==21

def test_ols_recovery_math_is_unchanged():
    m=load();counts=[7,13,23,26,30,42,66,83,109,140,322,354,415,460];mu=1.1;sd=.72
    z=[(math.log10(n+1)-mu)/sd for n in counts]
    a,b=m.ols_xy(z,[math.log10(n+1) for n in counts])
    assert abs(a-mu)<1e-12 and abs(b-sd)<1e-12

def test_future_response_remains_sealed():
    c=json.loads(CONTRACT.read_text())
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["protected_outcome_values_decoded"]==0
    assert c["response_boundary"]["supplement_future_summary_values_used"]==0
    assert c["response_boundary"]["eBird_enabled"] is False
