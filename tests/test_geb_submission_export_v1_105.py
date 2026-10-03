from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
REQ=ROOT/"manuscript/submission/GEB_v1_104/submission_export_request_v1_105.json"
WF=ROOT/".github/workflows/geb-submission-export-v1_105.yml"

def test_export_uses_final_v1104_package():
    x=json.loads(REQ.read_text())
    assert x["status"]=="REQUEST_EDITABLE_GEB_SUBMISSION_EXPORT_FROM_V1104_FIGURE_ORDER_FINAL"
    assert x["blinded_manuscript"]=="manuscript/submission/GEB_v1_104/blinded_main_text.md"
    assert x["figure_mapping"]["Figure_2"]=="fig4_sealed_species_validation"
    assert x["figure_mapping"]["Figure_3"]=="fig2_external_isolation_attenuation"
    assert x["figure_mapping"]["Figure_4"]=="fig3_species_breadth_attenuation"
    assert x["new_scientific_analysis_authorized"] is False
    assert x["new_response_access_authorized"] is False

def test_export_maps_frozen_images_to_narrative_numbers():
    s=WF.read_text()
    assert 'fig4_sealed_species_validation.png":figs/"Figure_2.png"' in s
    assert 'fig2_external_isolation_attenuation.png":figs/"Figure_3.png"' in s
    assert 'fig3_species_breadth_attenuation.png":figs/"Figure_4.png"' in s
    assert 'sha(figs/"Figure_2.png")=="83a2489578771c283febad371457f7eee99715fde92627e105b7a99cfb6d5abe"' in s

def test_export_uses_only_final_caption_file():
    s=WF.read_text()
    assert 'cp manuscript/submission/GEB_v1_104/figure_captions.md "$ROOT/figure_captions_combined.md"' in s
    assert 'cat manuscript/submission/macro_v1_89/figure_captions.md' not in s

def test_export_still_scrubs_metadata_and_binds_si():
    s=WF.read_text()
    assert "Scrub DOCX identity metadata" in s
    assert "Enforce blinded manuscript metadata and direct identity scan" in s
    assert "dda3357556760079f0e801173e21758b821f0ce98f22717774475c235dcfd08d" in s
    assert "prepare_dryad_token" not in s
