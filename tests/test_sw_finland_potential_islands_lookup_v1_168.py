from pathlib import Path
import csv,importlib.util,json
ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/validate_sw_finland_potential_islands_lookup_v1_168.py"
CONTRACT=ROOT/"development/sw_finland_potential_islands_lookup_contract_v1_168.json"

def load():
    spec=importlib.util.spec_from_file_location("swf168",SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_lookup_derives_source_count_without_future_columns(tmp_path):
    m=load();c=json.loads(CONTRACT.read_text());c=dict(c);c["validation"]=dict(c["validation"]);c["validation"]["expected_unique_species"]=2
    p=tmp_path/"safe.csv"
    p.write_text("species,Potential_islands\nAcer platanoides,464\nAllium schoenoprasum,56\n",encoding="utf-8")
    rows,r=m.validate(p,c)
    got={x["species"]:x["historical_source_count"] for x in rows}
    assert got=={"Acer platanoides":7,"Allium schoenoprasum":415}
    assert r["future_summary_values_persisted"]==0

def test_future_summary_column_is_rejected(tmp_path):
    m=load();c=json.loads(CONTRACT.read_text());c=dict(c);c["validation"]=dict(c["validation"]);c["validation"]["expected_unique_species"]=1
    p=tmp_path/"unsafe.csv"
    p.write_text("species,Potential_islands,Num_colonized\nA,470,3\n",encoding="utf-8")
    try:m.validate(p,c)
    except m.Stop:pass
    else:raise AssertionError("future summary columns must be rejected")
