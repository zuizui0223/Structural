from pathlib import Path
import csv,importlib.util,json,math

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/calibrate_sw_finland_source_counts_v1_170_2.py"
CONTRACT=ROOT/"development/sw_finland_anchor_source_count_inversion_contract_v1_170_2.json"

def load():
    spec=importlib.util.spec_from_file_location("swf1702",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_affine_calibration_recovers_integer_lattice():
    m=load()
    counts=[0,7,42,109,415,460]
    intercept=1.2;slope=.7
    pts=[((math.log10(n+1)-intercept)/slope,math.log10(n+1)) for n in counts]
    a,b=m.ols_affine(pts)
    assert abs(a-intercept)<1e-12
    assert abs(b-slope)<1e-12
    for n in [0,1,7,42,109,415,460,471]:
        z=(math.log10(n+1)-a)/b
        got,_,_,ratio=m.nearest_count(a+b*z,471)
        assert got==n and ratio==0

def test_contract_uses_only_frozen_t0_anchors_and_no_future_summary():
    c=json.loads(CONTRACT.read_text())
    assert c["anchor_source"]["required_anchor_species"]==6
    assert c["anchor_source"]["future_summary_columns_used"] is False
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["published_future_summary_values_used"]==0
    assert c["response_boundary"]["eBird_enabled"] is False
    assert c["calibration"]["maximum_ambiguity_ratio"]==0.25
