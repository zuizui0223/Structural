from pathlib import Path
import importlib.util,json

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/audit_sw_finland_colonization_header_v1_163.py"
CONTRACT=ROOT/"development/sw_finland_plant_colonization_column_firewall_v1_162.json"

def load_module():
    spec=importlib.util.spec_from_file_location("swf163",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_header_audit_opens_no_rows(tmp_path):
    m=load_module()
    c=json.loads(CONTRACT.read_text())
    cols=[]
    for x in c["protected_future_endpoint_columns"]+c["required_routing_and_t0_columns"]+c["safe_recipient_state_columns"]+c["safe_species_or_t0_columns"]:
        if x not in cols: cols.append(x)
    p=tmp_path/"colonization_select.csv"
    # A deliberately explosive future row: the auditor must never parse it.
    p.write_text(",".join(cols)+"\n"+"THIS,ROW,MUST,NOT,BE,PARSED\n",encoding="utf-8")
    r=m.audit(p,c)
    assert r["status"]=="HEADER_ONLY_AUDIT_COMPLETE_FUTURE_OUTCOME_ROWS_UNREAD"
    assert r["data_rows_semantically_opened"]==0
    assert r["outcome_values_read"]==0
    assert r["t0_projection_authorized"] is True

def test_missing_outcome_stops(tmp_path):
    m=load_module();c=json.loads(CONTRACT.read_text())
    cols=[x for x in c["required_routing_and_t0_columns"]]
    p=tmp_path/"bad.csv";p.write_text(",".join(cols)+"\n",encoding="utf-8")
    try:
        m.audit(p,c)
    except m.Stop:
        pass
    else:
        raise AssertionError("missing future endpoint header must stop")

def test_contract_is_nonfresh_and_temporal():
    p=ROOT/"development/sw_finland_plant_colonization_preintake_v1_162.json"
    x=json.loads(p.read_text())
    assert x["evidence_class"]["independent_geography"] is True
    assert x["evidence_class"]["temporal_endpoint"] is True
    assert x["evidence_class"]["pristine_fresh_confirmation"] is False
    assert x["response_boundary"]["row_level_future_outcome_opened"]==0
