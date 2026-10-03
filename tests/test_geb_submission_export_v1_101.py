from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]

def test_export_request_binds_final_v1100_assets():
    x=json.loads((ROOT/"manuscript/submission/GEB_v1_97/submission_export_request_v1_101.json").read_text())
    assert x["scientific_freeze"]=="development/current_status_v1_97.json"
    assert x["artifacts"]["figure_4"]["artifact_id"]==11269267611
    assert x["artifacts"]["anonymous_SI"]["artifact_id"]==11269048949
    assert x["artifacts"]["anonymous_SI"]["inner_zip_sha256"]=="dda3357556760079f0e801173e21758b821f0ce98f22717774475c235dcfd08d"
    assert x["new_scientific_analysis_authorized"] is False
    assert x["new_response_access_authorized"] is False

def test_export_workflow_builds_editable_docx_and_exact_figures():
    s=(ROOT/".github/workflows/geb-submission-export-v1_101.yml").read_text()
    assert "pandoc manuscript/submission/GEB_v1_97/blinded_main_text.md" in s
    assert "GEB_blinded_main_text.docx" in s
    assert "GEB_title_page_TEMPLATE.docx" in s
    assert "GEB_cover_letter_TEMPLATE.docx" in s
    assert "GEB_figure_captions.docx" in s
    assert "Figure_4.png" in s
    assert "GEB_anonymous_review_SI.zip" in s
    assert "dda3357556760079f0e801173e21758b821f0ce98f22717774475c235dcfd08d" in s

def test_export_workflow_scrubs_blinded_docx_identity():
    s=(ROOT/".github/workflows/geb-submission-export-v1_101.yml").read_text()
    assert "Scrub DOCX identity metadata" in s
    assert "dc:creator" in s
    assert "cp:lastModifiedBy" in s
    assert "Direct identity scan" not in s  # wording is lower-case in step name
    assert "Enforce blinded manuscript metadata and direct identity scan" in s

def test_export_never_opens_response():
    s=(ROOT/".github/workflows/geb-submission-export-v1_101.yml").read_text()
    assert "prepare_dryad_token" not in s
    assert "Appendix_1_presence_absence.csv" not in s
    assert "new_response_accessed" in s
