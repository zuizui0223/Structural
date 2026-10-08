import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("v225",ROOT/"scripts/diagnose_zhoushan_official_docx_v1_225.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_fixed_two_url_source_and_no_biology():
    x=json.loads((ROOT/"development/zhoushan_official_transport_diagnosis_v1_225.json").read_text())
    assert x["first_v224_status"]=="STOP_SUPPLEMENT_TRANSPORT_OR_ZIP_SCHEMA"
    assert len(x["frozen_official_urls"])==2
    assert x["stop_if_both_official_paths_non_ZIP"] is True
    assert all(m.safe(z) for z in m.URLS)
    assert not m.safe("https://someotherdomain.com/experiment.docx")
def test_html_guard_and_zip_magic():
    assert m.kind(b"<!doctype html><html>no data</html>")=="html_or_xml"
    assert m.kind(b"PK\x03\x04junk")=="zip"
    assert m.kind(b"%PDF-1.5 data")=="pdf"
