from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
REQ=ROOT/"manuscript/submission/GEB_v1_108/submission_export_docx_fix_request_v1_110.json"
WF=ROOT/".github/workflows/geb-submission-export-v1_110.yml"

def test_docx_fix_is_packaging_only():
    x=json.loads(REQ.read_text())
    assert x["status"]=="REQUEST_DOCX_VALIDITY_FIX_SAME_V1108_CONTENT"
    assert x["scientific_content_changed"] is False
    assert x["manuscript_content_changed"] is False
    assert x["figure_mapping_changed"] is False
    assert x["artifact_bindings_changed"] is False
    assert x["docx_metadata_anonymization_changed"] is False
    assert x["new_scientific_analysis_authorized"] is False
    assert x["new_response_access_authorized"] is False

def test_docx_fix_retains_valid_empty_custom_properties_part():
    s=WF.read_text()
    assert 'custom=td/"docProps/custom.xml"' in s
    assert "custom.unlink()" not in s
    assert 'xmlns="http://schemas.openxmlformats.org/officeDocument/2006/custom-properties"' in s
    assert "python-docx" in s

def test_all_five_docx_are_opened_before_upload():
    s=WF.read_text()
    assert "Validate every DOCX is a structurally readable package" in s
    assert "assert len(docs)==5" in s
    assert "doc=Document(p)" in s
    assert 'Document(root/"GEB_blinded_main_text.docx")' in s

def test_final_content_and_artifact_bindings_remain_exact():
    s=WF.read_text()
    assert "GEB_v1_108/blinded_main_text.md" in s
    assert 'fig4_sealed_species_validation.png":figs/"Figure_2.png"' in s
    assert "dda3357556760079f0e801173e21758b821f0ce98f22717774475c235dcfd08d" in s
    assert "prepare_dryad_token" not in s
