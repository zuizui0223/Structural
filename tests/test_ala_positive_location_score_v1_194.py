from pathlib import Path
import importlib.util,json
import pytest
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/score_global_mammals_ala_positive_locations_v1_194.py"
CONTRACT=ROOT/"development/global_mammals_ala_positive_location_protocol_v1_194.json"

def load():
    pytest.importorskip("numpy")
    spec=importlib.util.spec_from_file_location("ala194",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_uniform_probability_multiplication_has_no_relative_location_gain():
    m=load();np=m.np
    a=np.full(167,.03);b=np.full(167,.06);null=np.tile(a,(20,1))
    x=m.normalized_score(a,b,null,[2,5,8])
    assert abs(x[0])<1e-12
    assert abs(x[1])<1e-12

def test_positive_location_concentration_can_improve_relative_log_score():
    m=load();np=m.np
    a=np.full(167,.05);b=a.copy();b[0]=.5;null=np.tile(a,(20,1))
    x=m.normalized_score(a,b,null,[0])
    assert x[0]<0 and x[1]<0

def test_date_year_domain_and_FID():
    m=load()
    assert m.datayear("2005-04-01")==2005
    assert m.datayear("2026-10-02")==2026
    assert m.datayear("1999-03-01") is None
    assert m.datayear("not a date") is None
    assert m.datayear("2027-01-01") is None
    assert m.parse_fid("54049.000")==54049
    assert m.parse_fid("54049.1") is None

def test_preoutcome_scope_and_no_absence_interpretation():
    c=json.loads(CONTRACT.read_text())
    assert c["eligibility_precommitted"]["no_external_zero_labels"] is True
    assert c["input_authority"]["taxon_eligibility_sha256_bound_in_separate_one_shot_request"] is True
    assert c["response_boundary"]["score_request_currently_authorized"] is False
    assert c["uncertainty"]["joint_support"].startswith("P1 < 0")
