from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
RETRY=ROOT/"manuscript/submission/GEB_v1_108/submission_export_retry_request_v1_109_1.json"
WF=ROOT/".github/workflows/geb-submission-export-v1_109_1.yml"

def test_retry_changes_runner_only():
    x=json.loads(RETRY.read_text())
    assert x["status"]=="REQUEST_OPERATIONAL_EXPORT_RETRY_SAME_V1108_CONTENT"
    assert x["repair"]=="change runner image only from ubuntu-24.04 to ubuntu-22.04"
    assert x["scientific_content_changed"] is False
    assert x["manuscript_content_changed"] is False
    assert x["figure_mapping_changed"] is False
    assert x["artifact_bindings_changed"] is False
    assert x["docx_scrub_logic_changed"] is False
    assert x["new_scientific_analysis_authorized"] is False
    assert x["new_response_access_authorized"] is False

def test_retry_workflow_uses_alternate_runner_and_parent_request():
    s=WF.read_text()
    assert "runs-on: ubuntu-22.04" in s
    assert "GEB editable submission export operational retry v1.109.1" in s
    assert "submission_export_request_v1_109.json" in s
    assert "submission_export_retry_request_v1_109_1.json" in s
    assert "REQUEST_FINAL_GEB_SUBMISSION_EXPORT_FROM_V1108" in s
    assert "REQUEST_OPERATIONAL_EXPORT_RETRY_SAME_V1108_CONTENT" in s

def test_retry_retains_exact_si_and_docx_scrub():
    s=WF.read_text()
    assert "dda3357556760079f0e801173e21758b821f0ce98f22717774475c235dcfd08d" in s
    assert "Scrub DOCX identity metadata" in s
    assert "Enforce blinded manuscript metadata and direct identity scan" in s
    assert "prepare_dryad_token" not in s
