from pathlib import Path
import csv,importlib.util,json,math

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/invert_sw_finland_historical_source_counts_v1_170_1.py"
CONTRACT=ROOT/"development/sw_finland_anchor_inversion_contract_v1_170_1.json"

def load():
    spec=importlib.util.spec_from_file_location("swf1701",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_affine_log_inverse_recovers_integer_counts():
    m=load()
    mean=1.2;sd=0.7
    for n in (0,1,7,42,109,415,460,471):
        z=(math.log10(n+1)-mean)/sd
        raw,got,res=m.invert(z,mean,sd)
        assert got==n
        assert res<1e-9

def test_contract_uses_disjoint_calibration_and_validation_anchors():
    c=json.loads(CONTRACT.read_text())
    assert set(c["calibration_anchors"]).isdisjoint(c["validation_anchors"])
    assert len(c["calibration_anchors"])==2
    assert len(c["validation_anchors"])==4
    assert c["inversion_gate"]["expected_species"]==587
    assert c["source_identity_gate"]["minimum_positive_source_exact_species"]==30

def test_anchor_fields_are_t0_only():
    c=json.loads(CONTRACT.read_text())
    assert c["anchor_provenance"]["permitted_field"]=="Potential_islands only"
    assert c["anchor_provenance"]["future_summary_fields_used"]==[]
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["future_summary_values_used"]==0
    assert c["response_boundary"]["eBird_enabled"] is False

def test_calibration_math_from_two_anchors():
    m=load()
    c=json.loads(CONTRACT.read_text())
    z0=-1.5;z1=2.0
    zs={"Anchusa arvensis":z0,"Agrostis stolonifera":z1}
    mean,sd,items=m.calibrate(zs,c)
    assert sd>0
    for sp,z,n,L in items:
        assert abs((mean+sd*z)-math.log10(n+1))<1e-12
