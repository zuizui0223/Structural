from pathlib import Path
import importlib.util,json

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/resolve_sw_finland_supplement_v1_170_2.py"
CONTRACT=ROOT/"development/sw_finland_supplement_resolver_contract_v1_170_2.json"

def load():
    spec=importlib.util.spec_from_file_location("swf1702",SCRIPT)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_html_resolution_persists_only_matching_file_urls():
    m=load();c=json.loads(CONTRACT.read_text())
    html=b'''<html><a href="/files/ecog-05013.pdf">pdf</a><a href="/bad.pdf">bad</a><a href="ecog05013-sup.zip">z</a></html>'''
    r=m.resolve(html,final_url="https://host/x",content_type="text/html; charset=utf-8",contract=c)
    assert r["candidate_count"]==2
    assert all("ecog" in x.lower() for x in r["candidate_urls"])
    assert r["supplement_table_values_parsed"]==0
    assert r["future_summary_values_persisted"]==0
    assert r["landing_body_persisted"] is False

def test_pdf_landing_is_accepted_as_candidate_without_parsing():
    m=load();c=json.loads(CONTRACT.read_text())
    r=m.resolve(b"%PDF-1.7 fake",final_url="https://host/ecog-05013.pdf",content_type="application/pdf",contract=c)
    assert r["candidate_urls"]==["https://host/ecog-05013.pdf"]
    assert r["supplement_table_values_parsed"]==0

def test_contract_preserves_preaccess_boundary():
    c=json.loads(CONTRACT.read_text())
    assert c["response_boundary"]["supplement_table_values_parsed"]==0
    assert c["response_boundary"]["future_summary_values_parsed"]==0
    assert c["response_boundary"]["row_level_recent_outcome_opened"] is False
    assert c["response_boundary"]["eBird_enabled"] is False
