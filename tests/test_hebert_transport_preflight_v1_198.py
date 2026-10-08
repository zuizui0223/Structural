from pathlib import Path
import importlib.util
import json
ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("h198",ROOT/"scripts/preflight_dryad_checklist_transport_v1_198.py")
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)

def test_anchor_selection_exact_file_name_only():
    html='<html><a href="/downloads/Adr.csv">Adr.csv</a><a href="/downloads/Other.csv">Other.csv</a><a href="https://evil.example/Alx.csv">Alx.csv</a></html>'
    r=m.named_links(html,"https://datadryad.org/dataset/doi:10.5061/dryad.rfj6q579r",{"Adr.csv","Alx.csv"})
    assert r=={"Adr.csv":["https://datadryad.org/downloads/Adr.csv"]}

def test_redirect_scope_blocks_untrusted_and_plain_http():
    assert m.permitted("https://datadryad.org/downloads/file_stream/773000")
    assert m.permitted("https://s3.amazonaws.com/bucket/file.csv")
    assert not m.permitted("http://datadryad.org/downloads/file_stream/773000")
    assert not m.permitted("https://datadryad.org.evil.example/file.csv")
    assert not m.permitted("https://evil.example/file.csv")

def test_fake_head_preflight_does_not_look_at_binaries():
    c=json.loads((ROOT/"development/hebert_transport_preflight_contract_v1_198.json").read_text())
    parent=json.loads((ROOT/"development/global_mammals_independent_checklist_preintake_v1_188.json").read_text())
    html="<html>10.5061/dryad.rfj6q579r</html>"
    r=m.preflight(c,parent,html,"https://datadryad.org/dataset/doi:10.5061/dryad.rfj6q579r",
       head_func=lambda u: {"state":"HEAD_OK_FILE_IDENTITY_UNVERIFIED","http_status":200})
    assert r["status"]=="HEAD_CANDIDATE_ALL_9"
    assert r["frozen_csv_count"]==9
    assert r["CSV_body_bytes_read"]==0
    assert r["island_species_binary_values_decoded"]==0
    assert r["external_ecological_score_produced"] is False
    assert r["downstream_header_projection_authorized"] is False

def test_missing_heads_is_transport_only():
    c=json.loads((ROOT/"development/hebert_transport_preflight_contract_v1_198.json").read_text())
    parent=json.loads((ROOT/"development/global_mammals_independent_checklist_preintake_v1_188.json").read_text())
    r=m.preflight(c,parent,"<html/>","https://datadryad.org/dataset/doi:10.5061/dryad.rfj6q579r",
       head_func=lambda u: {"state":"HEAD_FAILED","http_status":404})
    assert r["status"]=="NO_HEAD_CANDIDATE"
    assert r["external_ecological_score_produced"] is False
