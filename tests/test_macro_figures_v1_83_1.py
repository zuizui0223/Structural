from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_rerender_request_changes_layout_only():
    x=json.loads((ROOT/"development/macro_figure_rerender_request_v1_83_1.json").read_text())
    assert x["diagnostics_artifact_id"]==11130602935
    assert x["species_breadth_artifact_id"]==11131608867
    assert x["scientific_data_or_claim_changed"] is False
    assert x["new_response_access_authorized"] is False

def test_polished_script_removes_crowded_bottom_annotations():
    s=(ROOT/"scripts/build_macro_figures_v1_83.py").read_text()
    assert "Positive association = less-negative" not in s
    assert "Connected points are the four pre-defined" not in s
    assert "ax.barh" in s
    assert 'label="Rank-group means"' in s
    assert 'render_revision":"v1.83.1_layout_only"' in s

def test_rerender_workflow_is_response_free():
    s=(ROOT/".github/workflows/macro-figures-v1_83_1.yml").read_text()
    assert "11130602935" in s
    assert "11131608867" in s
    assert "DRYAD_TOKEN" not in s
    assert "GIFT_checklists" not in s
