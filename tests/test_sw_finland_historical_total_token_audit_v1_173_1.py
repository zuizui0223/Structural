from pathlib import Path
import importlib.util,json

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/audit_sw_finland_historical_total_tokens_v1_173_1.py"
CONTRACT=ROOT/"development/sw_finland_historical_total_token_audit_contract_v1_173_1.json"

def load():
    spec=importlib.util.spec_from_file_location("swf1731",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_numeric_helper_rejects_na_blank_and_nonfinite():
    m=load()
    assert m.numeric("1.23")==1.23
    assert m.numeric("NA") is None
    assert m.numeric("") is None
    assert m.numeric("nan") is None
    assert m.numeric("inf") is None

def test_contract_is_t0_only():
    c=json.loads(CONTRACT.read_text())
    assert c["response_boundary"]["future_outcome_values_opened"]==0
    assert c["response_boundary"]["protected_outcome_values_decoded"]==0
    assert c["response_boundary"]["eBird_enabled"] is False
    assert "changing v1.173 calibration thresholds" in c["scope"]["forbidden"]
