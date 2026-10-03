from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v198_is_layout_only():
    x=json.loads((ROOT/"development/sealed_species_figure_rerender_request_v1_98.json").read_text())
    assert x["source_result_artifact_id"]==11269176943
    assert x["scientific_values_changed"] is False
    assert x["new_response_access_authorized"] is False

def test_panel_c_uses_scaled_axis_and_jitter_only():
    s=(ROOT/"scripts/build_sealed_species_figure_v1_97.py").read_text()
    assert "Block-weighted C−R3 (×10⁻⁴)" in s
    assert "null_y=" in s
    assert "actual*1e4" in s
    assert "P4_topology_specificity" in s
