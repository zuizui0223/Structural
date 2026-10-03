from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
REQ=ROOT/"manuscript/submission/GEB_v1_102/submission_export_request_v1_103.json"
WF=ROOT/".github/workflows/geb-submission-export-v1_103.yml"

def test_v103_export_uses_narrative_final_source():
    x=json.loads(REQ.read_text())
    assert x["schema"]=="structural.geb_submission_export_request.v1_103"
    assert x["status"]=="REQUEST_EDITABLE_GEB_SUBMISSION_EXPORT_FROM_V1102_NARRATIVE_FINAL"
    assert x["blinded_manuscript"]=="manuscript/submission/GEB_v1_102/blinded_main_text.md"
    assert x["title_page_template"]=="manuscript/submission/GEB_v1_102/title_page_template.md"
    assert x["cover_letter"]=="manuscript/submission/GEB_v1_102/cover_letter.md"
    assert x["new_scientific_analysis_authorized"] is False
    assert x["new_response_access_authorized"] is False

def test_v103_workflow_converts_v102_files_not_v197():
    s=WF.read_text()
    assert "GEB_v1_102/blinded_main_text.md" in s
    assert "GEB_v1_102/title_page_template.md" in s
    assert "GEB_v1_102/cover_letter.md" in s
    assert "GEB_v1_102/figure4_caption.md" in s
    assert "GEB_v1_102/submission_manifest.json" in s
    assert "GEB_v1_97/blinded_main_text.md" not in s
    assert "GEB_submission_package_v1_103.zip" in s
    assert "GEB_anonymous_review_SI.zip" in s

def test_v103_still_scrubs_blinded_docx_metadata():
    s=WF.read_text()
    assert "Scrub DOCX identity metadata" in s
    assert "dc:creator" in s
    assert "cp:lastModifiedBy" in s
    assert "Enforce blinded manuscript metadata and direct identity scan" in s
