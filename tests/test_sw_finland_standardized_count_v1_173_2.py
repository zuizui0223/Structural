from pathlib import Path
import importlib.util,json,math

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/recover_sw_finland_standardized_counts_v1_173_2.py"
CONTRACT=ROOT/"development/sw_finland_standardized_historical_count_contract_v1_173_2.json"

def load():
    spec=importlib.util.spec_from_file_location("swf1732",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_nonnumeric_rule_is_logical_zero_only():
    c=json.loads(CONTRACT.read_text())
    r=c["nonnumeric_rule"]
    assert r["if_archived_absent_count_equals_471"].startswith("historical_source_count is logically 0")
    assert r["if_archived_absent_count_less_than_471"].startswith("terminal STOP")
    assert r["nonnumeric_species_may_enter_OLS_calibration"] is False

def test_ols_identity_still_matches_v173_math():
    m=load();counts=[1,2,7,30,140,322,460];mu=1.2;sd=.65
    z=[(math.log10(n+1)-mu)/sd for n in counts]
    a,b=m.ols_xy(z,[math.log10(n+1) for n in counts])
    assert abs(a-mu)<1e-12 and abs(b-sd)<1e-12

def test_thresholds_are_not_loosened():
    c=json.loads(CONTRACT.read_text())
    u=c["unchanged_from_v1_173"]
    assert u["minimum_numeric_anchor_matches"]==20
    assert u["maximum_anchor_count_rounding_error"]==0.01
    assert u["maximum_all_numeric_species_count_rounding_error"]==0.05
    assert u["minimum_exact_source_species"]==30
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["eBird_enabled"] is False
