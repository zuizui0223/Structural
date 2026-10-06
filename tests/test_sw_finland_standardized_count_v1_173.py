from pathlib import Path
import importlib.util,json,math

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/recover_sw_finland_standardized_counts_v1_173.py"
CONTRACT=ROOT/"development/sw_finland_standardized_historical_count_contract_v1_173.json"

def load():
    spec=importlib.util.spec_from_file_location("swf173",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_affine_standardized_log_recovery():
    m=load()
    counts=[0,1,2,7,15,30,66,140,322,415,460]
    mu=1.4;sd=0.7
    z=[(math.log10(n+1)-mu)/sd for n in counts]
    a,b=m.ols_xy(z,[math.log10(n+1) for n in counts])
    assert abs(a-mu)<1e-12
    assert abs(b-sd)<1e-12
    got=[round(10**(a+b*x)-1) for x in z]
    assert got==counts

def test_contract_has_wide_frozen_t0_anchor_range():
    c=json.loads(CONTRACT.read_text())
    vals=list(c["anchors"]["values"].values())
    assert len(vals)>=20
    assert min(vals)==0
    assert max(vals)>=460
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["supplement_future_summary_values_used"]==0
    assert c["response_boundary"]["eBird_enabled"] is False

def test_calibration_thresholds_are_predeclared():
    c=json.loads(CONTRACT.read_text())
    q=c["calibration"]
    assert q["minimum_anchor_matches"]==20
    assert q["maximum_all_species_count_rounding_error"]==0.05
    assert q["maximum_anchor_count_rounding_error"]==0.01
    assert c["support_audit"]["minimum_exact_species"]==30
