from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_figure_request_is_frozen_output_only():
    x=json.loads((ROOT/"development/macro_figure_request_v1_83.json").read_text())
    assert x["diagnostics_artifact_id"]==11130602935
    assert x["species_breadth_artifact_id"]==11131608867
    assert x["new_response_access_authorized"] is False
    assert x["one_shot"] is True

def test_figure_script_has_four_separate_plots_and_no_response_access():
    s=(ROOT/"scripts/build_macro_figures_v1_83.py").read_text()
    assert "fig1_bioregion_effects" in s
    assert "fig2_external_isolation_attenuation" in s
    assert "fig3_species_breadth_attenuation" in s
    assert "figS1_gift_endpoint_attrition" in s
    assert "plt.subplots" in s
    assert "Appendix_1" not in s
    assert "GIFT_checklists" not in s
    assert "DRYAD" not in s

def test_figure_workflow_downloads_only_frozen_artifacts():
    s=(ROOT/".github/workflows/macro-figures-v1_83.yml").read_text()
    assert "11130602935" in s
    assert "11131608867" in s
    assert "prepare_dryad_token" not in s
    assert "GIFT_checklists" not in s
    assert "new_response_access_authorized" in s

def test_figure_plan_keeps_gift_as_supplementary_boundary():
    s=(ROOT/"docs/MACRO_FIGURE_PLAN_V1_83.md").read_text()
    assert "Supplementary Figure S1" in s
    assert "descriptive cross-taxon concordance only" in s
    assert "post-hoc, nonrescuing" in s
