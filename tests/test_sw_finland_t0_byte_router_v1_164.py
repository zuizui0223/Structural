from pathlib import Path
import csv,hashlib,importlib.util,json

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/route_sw_finland_t0_columns_v1_164.py"
FIREWALL=ROOT/"development/sw_finland_plant_colonization_column_firewall_v1_162.json"

def load():
    spec=importlib.util.spec_from_file_location("swf_router164",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_byte_router_never_persists_protected_outcome(tmp_path):
    m=load();fw=json.loads(FIREWALL.read_text())
    cols=[]
    for x in ["outcome"]+fw["required_routing_and_t0_columns"]+fw["safe_recipient_state_columns"]+fw["safe_species_or_t0_columns"]:
        if x not in cols: cols.append(x)
    raw=tmp_path/"mixed.csv"
    with raw.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        row={c:"1" for c in cols}
        row["outcome"]="SECRET,FUTURE"
        row["spp.name"]="sp";row["holmkod"]="A"
        w.writerow(row)
    sha=hashlib.sha256(raw.read_bytes()).hexdigest()
    hr={"schema":"structural.sw_finland_plant_colonization_header_audit.v1_163",
        "status":"HEADER_ONLY_AUDIT_COMPLETE_FUTURE_OUTCOME_ROWS_UNREAD",
        "outcome_values_read":0,"file_sha256":sha,"header":cols}
    safe=tmp_path/"safe.csv"
    r=m.route(raw,hr,fw,safe)
    payload=safe.read_bytes()
    assert b"SECRET" not in payload
    assert b"outcome" not in payload.splitlines()[0]
    assert r["protected_field_values_decoded"]==0
    assert r["protected_field_bytes_persisted"]==0
    assert r["outcome_values_read"]==0

def test_router_handles_quoted_newline_in_protected_field(tmp_path):
    m=load();fw=json.loads(FIREWALL.read_text())
    cols=[]
    for x in ["outcome"]+fw["required_routing_and_t0_columns"]+fw["safe_recipient_state_columns"]+fw["safe_species_or_t0_columns"]:
        if x not in cols: cols.append(x)
    raw=tmp_path/"mixed.csv"
    with raw.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        row={c:"1" for c in cols};row["outcome"]="SECRET\nFUTURE";row["spp.name"]="sp";row["holmkod"]="A";w.writerow(row)
    hr={"schema":"structural.sw_finland_plant_colonization_header_audit.v1_163",
        "status":"HEADER_ONLY_AUDIT_COMPLETE_FUTURE_OUTCOME_ROWS_UNREAD","outcome_values_read":0,
        "file_sha256":hashlib.sha256(raw.read_bytes()).hexdigest(),"header":cols}
    safe=tmp_path/"safe.csv";r=m.route(raw,hr,fw,safe)
    assert r["data_row_count"]==1
    assert b"SECRET" not in safe.read_bytes()
