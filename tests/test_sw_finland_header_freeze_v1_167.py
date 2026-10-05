from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/freeze_sw_finland_header_audit_v1_167.py"
CONTRACT=ROOT/"development/sw_finland_header_freeze_contract_v1_167.json"

def load_module():
    spec=importlib.util.spec_from_file_location("swf167",SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_clean_receipts_authorize_only_t0_dispatch():
    m=load_module();c=json.loads(CONTRACT.read_text())
    d={"schema":"structural.sw_finland_download_identity.v1_166","status":"EXACT_ZENODO_FILE_MD5_VERIFIED",
       "md5":"ff648878946ba430fb86c4ab2aa02baa","data_rows_semantically_opened":0,"outcome_values_read":0,"size_bytes":123}
    h={"schema":"structural.sw_finland_plant_colonization_header_audit.v1_163",
       "status":"HEADER_ONLY_AUDIT_COMPLETE_FUTURE_OUTCOME_ROWS_UNREAD","data_rows_semantically_opened":0,
       "outcome_values_read":0,"t0_projection_authorized":True,"unknown_headers":[],"file_size_bytes":123,
       "file_sha256":"a"*64,"header_sha256":"b"*64,"file_name":"colonization_select.csv"}
    r=m.verify(d,h,c)
    assert r["t0_projection_may_be_dispatched"] is True
    assert r["future_outcome_opened"] is False
    assert r["outcome_values_read"]==0

def test_unknown_header_cannot_freeze():
    m=load_module();c=json.loads(CONTRACT.read_text())
    d={"schema":"structural.sw_finland_download_identity.v1_166","status":"EXACT_ZENODO_FILE_MD5_VERIFIED",
       "md5":"ff648878946ba430fb86c4ab2aa02baa","data_rows_semantically_opened":0,"outcome_values_read":0,"size_bytes":123}
    h={"schema":"structural.sw_finland_plant_colonization_header_audit.v1_163",
       "status":"HEADER_ONLY_AUDIT_COMPLETE_FUTURE_OUTCOME_ROWS_UNREAD","data_rows_semantically_opened":0,
       "outcome_values_read":0,"t0_projection_authorized":True,"unknown_headers":["surprise"],"file_size_bytes":123,
       "file_sha256":"a"*64,"header_sha256":"b"*64,"file_name":"colonization_select.csv"}
    try:m.verify(d,h,c)
    except m.Stop:pass
    else:raise AssertionError("unknown columns must stop canonical freeze")
