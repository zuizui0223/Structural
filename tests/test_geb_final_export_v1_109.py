from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
REQ=ROOT/"manuscript/submission/GEB_v1_108/submission_export_request_v1_109.json"
WF=ROOT/".github/workflows/geb-submission-export-v1_109.yml"

def test_v109_export_uses_final_v1108_source_only():
    x=json.loads(REQ.read_text())
    assert x["status"]=="REQUEST_FINAL_GEB_SUBMISSION_EXPORT_FROM_V1108"
    assert x["blinded_manuscript"]=="manuscript/submission/GEB_v1_108/blinded_main_text.md"
    assert x["title_page_template"]=="manuscript/submission/GEB_v1_108/title_page_template.md"
    assert x["cover_letter"]=="manuscript/submission/GEB_v1_108/cover_letter.md"
    assert x["new_scientific_analysis_authorized"] is False
    assert x["new_response_access_authorized"] is False

def test_v109_export_preserves_final_figure_order_and_captions():
    s=WF.read_text()
    assert 'cp manuscript/submission/GEB_v1_108/figure_captions.md "$ROOT/figure_captions_combined.md"' in s
    assert 'fig4_sealed_species_validation.png":figs/"Figure_2.png"' in s
    assert 'fig2_external_isolation_attenuation.png":figs/"Figure_3.png"' in s
    assert 'fig3_species_breadth_attenuation.png":figs/"Figure_4.png"' in s

def test_v109_export_keeps_identity_scrub_and_exact_si():
    s=WF.read_text()
    assert "Scrub DOCX identity metadata" in s
    assert "Enforce blinded manuscript metadata and direct identity scan" in s
    assert "dda3357556760079f0e801173e21758b821f0ce98f22717774475c235dcfd08d" in s
    assert "prepare_dryad_token" not in s

def test_v109_source_is_citation_and_wording_final():
    s=(ROOT/"manuscript/submission/GEB_v1_108/blinded_main_text.md").read_text()
    assert "not uniformly informative across the occupancy regimes tested" in s
    assert "(Fahrig 2013)" in s
    assert "(Schrader et al. 2021)" in s
    assert "not geographically independent confirmation (Figure 2)" in s
