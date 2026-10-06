from pathlib import Path
import csv,importlib.util,json

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/route_sw_finland_t0_columns_v1_169.py"
CONTRACT=ROOT/"development/sw_finland_t0_byte_router_contract_v1_169.json"
REQUEST=ROOT/"development/sw_finland_t0_support_audit_request_v1_169.json"

def load_module():
    spec=importlib.util.spec_from_file_location("swf169",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_contract_binds_semicolon_and_protected_outcome():
    x=json.loads(CONTRACT.read_text())
    assert x["exact_input"]["delimiter"]==";"
    assert x["parser"]["source_delimiter_byte"]==59
    assert x["protected_future_endpoint"]["column"]=="outcome"
    assert x["protected_future_endpoint"]["values_may_be_decoded"] is False
    assert x["protected_future_endpoint"]["raw_field_bytes_may_be_persisted"] is False

def test_request_never_requests_future_outcome():
    x=json.loads(REQUEST.read_text())
    assert x["future_outcome_values_opened_before_request"]==0
    assert x["future_outcome_access_requested"] is False
    assert x["effect_estimate_requested"] is False
    assert x["eBird_used"] is False

def test_raw_semicolon_parser_handles_quotes_and_newlines(tmp_path):
    m=load_module()
    p=tmp_path/"x.csv"
    p.write_bytes(b'outcome;"spp.name";holmkod;note\n1;"A; b";I1;"line1\nline2"\n0;"C ""quoted""";I2;x\n')
    rows=list(m.raw_records(p,59))
    assert len(rows)==3
    assert [m.decode_field(x) for x in rows[0]]==["outcome","spp.name","holmkod","note"]
    assert m.decode_field(rows[1][1])=="A; b"
    assert m.decode_field(rows[1][3])=="line1\nline2"
    assert m.decode_field(rows[2][1])=='C "quoted"'

def test_script_never_decodes_protected_index_zero():
    s=SCRIPT.read_text()
    assert 'Never call decode_field on fields[0] (outcome).' in s
    assert '"protected_field_values_decoded":0' in s
    assert '"protected_field_bytes_persisted":0' in s
