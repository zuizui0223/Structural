from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
REQ=ROOT/"manuscript/submission/GEB_v1_106/submission_export_request_v1_107.json"
WF=ROOT/".github/workflows/geb-submission-export-v1_107.yml"

def test_final_export_uses_v1106_wording_final():
    x=json.loads(REQ.read_text())
    assert x["status"]=="REQUEST_FINAL_EDITABLE_GEB_SUBMISSION_EXPORT_FROM_V1106"
    assert x["blinded_manuscript"]=="manuscript/submission/GEB_v1_106/blinded_main_text.md"
    assert x["title_page_template"]=="manuscript/submission/GEB_v1_106/title_page_template.md"
    assert x["cover_letter"]=="manuscript/submission/GEB_v1_106/cover_letter.md"
    assert x["new_scientific_analysis_authorized"] is False
    assert x["new_response_access_authorized"] is False

def test_final_export_preserves_final_figure_mapping():
    x=json.loads(REQ.read_text())
    assert x["figure_mapping"]["Figure_2"]=="fig4_sealed_species_validation"
    assert x["figure_mapping"]["Figure_3"]=="fig2_external_isolation_attenuation"
    assert x["figure_mapping"]["Figure_4"]=="fig3_species_breadth_attenuation"
    s=WF.read_text()
    assert 'fig4_sealed_species_validation.png":figs/"Figure_2.png"' in s
    assert 'fig2_external_isolation_attenuation.png":figs/"Figure_3.png"' in s
    assert 'fig3_species_breadth_attenuation.png":figs/"Figure_4.png"' in s

def test_final_export_uses_final_caption_file_once():
    s=WF.read_text()
    assert 'cp manuscript/submission/GEB_v1_106/figure_captions.md "$ROOT/figure_captions_combined.md"' in s
    assert "cat manuscript/submission/macro_v1_89/figure_captions.md" not in s

def test_final_export_scrubs_identity_and_binds_exact_si():
    s=WF.read_text()
    assert "Scrub DOCX identity metadata" in s
    assert "Enforce blinded manuscript metadata and direct identity scan" in s
    assert "dda3357556760079f0e801173e21758b821f0ce98f22717774475c235dcfd08d" in s
    assert "prepare_dryad_token" not in s

def test_final_source_has_conservative_abstract_wording():
    s=(ROOT/"manuscript/submission/GEB_v1_106/blinded_main_text.md").read_text()
    abstract=s.split("## Abstract",1)[1].split("**Keywords:**",1)[0]
    assert "not uniformly informative across the occupancy regimes tested" in abstract
    assert "not a general mammalian isolation axis" not in abstract
