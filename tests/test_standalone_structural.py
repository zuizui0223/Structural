from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AIS_FP = "5c9b1594b29d362e5983484614a49d530797d06e826c0b96a3e8442a6b6b493a"
TZ_FP = "6b555c28d61d3f39b9e672f5a97250de6870301871cf3e60378e97863cd109e4"


def load_module(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_standalone_boundary_and_migration_are_frozen():
    boundary = json.loads((ROOT / "manuscript/STRUCTURAL_ISLAND_PAPER_BOUNDARY_V1.json").read_text())
    migration = json.loads((ROOT / "STANDALONE_MIGRATION.json").read_text())
    assert boundary["empirical_systems"]["aislands_strong_reference"]["result_fingerprint"] == AIS_FP
    assert boundary["empirical_systems"]["tanzania"]["result_fingerprint"] == TZ_FP
    assert boundary["non_overlap_with_eog_wf_paper"]["structural_paper_empirical_denominator_is_separate"] is True
    assert boundary["non_overlap_with_eog_wf_paper"]["structural_paper_does_not_use_eog_wf_three_endpoint_denominator"] is True
    assert migration["scientific_result_changed"] is False
    assert migration["empirical_denominator_changed"] is False
    assert migration["eog_wf_assets_included"] is False


def test_method_mainline_separates_original_isolation_from_fragmentation():
    text = (ROOT / "docs/STRUCTURAL_EGWE_METHOD_MAINLINE.md").read_text()
    assert "pre-existing / original isolation" in text
    assert "habitat fragmentation" in text
    assert "These histories are not ecologically equivalent" in text
    assert "candidate-state adequacy" in text
    assert "residual origin / history test" in text


def test_reference_conditioned_figures_rebuild_exactly():
    fig1 = load_module("figures/build_figure_1_reference_conditioned.py", "fig1")
    fig2 = load_module("figures/build_figure_2_aislands_reference_conditioned.py", "fig2")
    for assets in (fig1.build_assets(), fig2.build_assets()):
        for relative, content in assets.items():
            path = ROOT / relative
            assert path.is_file(), relative
            assert path.read_text(encoding="utf-8") == content, relative


def test_standalone_submission_package_builds_without_eog_wf(tmp_path: Path):
    builder = load_module("manuscript/build_structural_submission_package_v2.py", "pkg")
    receipt = builder.build(tmp_path / "structural_submission")
    assert receipt["schema"] == "eog.structural_submission_package.v3"
    assert receipt["eog_wf_empirical_denominator_included"] is False
    assert receipt["aislands_strong_reference_result_fingerprint"] == AIS_FP
    assert receipt["tanzania_result_fingerprint"] == TZ_FP
    assert receipt["canonical_submission_figures"]["figure_1"].endswith("figure_1_reference_conditioned.svg")
    assert receipt["canonical_submission_figures"]["figure_2"].endswith("figure_2_aislands_reference_conditioned.svg")
