from pathlib import Path
import ast,json,re
ROOT=Path(__file__).resolve().parents[1]
GEB=ROOT/"manuscript/submission/GEB_v1_90"

def test_v191_blinded_data_statement_uses_direct_supporting_information():
    s=(GEB/"blinded_main_text.md").read_text()
    block=s.split("## Data and Code Availability Statement",1)[1]
    assert "Supporting Information" in block
    assert "ANONYMIZED STABLE REVIEW LINK" not in block
    assert "github.com" not in block.lower()
    assert "public development-repository URL is intentionally omitted" in block

def test_v191_review_bundle_request_is_frozen_only():
    x=json.loads((GEB/"anonymous_bundle_request_v1_91.json").read_text())
    assert x["scientific_freeze"]=="development/current_status_v1_88.json"
    assert x["raw_response_access_authorized"] is False
    assert x["new_scientific_analysis_authorized"] is False
    assert x["one_shot"] is True

def test_v191_bundle_builder_neutralizes_public_identifiers():
    s=(ROOT/"scripts/build_geb_anonymous_review_bundle_v1_91.py").read_text()
    assert 's = s.replace("structural.", "review.")' in s
    assert 's = s.replace("global_mammals_", "island_mammal_")' in s
    assert 's = VERSION_TOKEN_RE.sub("review", s)' in s
    assert 'COMMIT_RE.sub("<commit-redacted>", s)' in s
    assert 'ast.unparse(tree)' in s
    assert 'if isinstance(node.value, bytes) and node.value == ORIGINAL_MAGIC' in s
    assert '"raw_biological_response_included": False' in s
    assert '"public_repository_identifiers_included": False' in s

def test_v191_builder_maps_public_script_names_to_generic_review_names():
    s=(ROOT/"scripts/build_geb_anonymous_review_bundle_v1_91.py").read_text()
    for name in (
        "analysis/01_fit_predict.py",
        "analysis/02_score_heldout.py",
        "analysis/03_geographic_diagnostics.py",
        "analysis/04_species_breadth.py",
        "analysis/05_prediction_behavior.py",
        "analysis/06_isolation_empty_support.py",
        "analysis/07_main_figures.py",
        "analysis/08_prediction_behavior_figure.py",
    ):
        assert name in s

def test_v191_workflow_never_fetches_raw_response():
    s=(ROOT/".github/workflows/geb-neutralized-review-bundle-v1_91.yml").read_text()
    assert "prepare_dryad_token" not in s
    assert "Appendix_1_presence_absence.csv" not in s
    assert "run_global_mammals_exploratory_pilot_v1_70.py" not in s
    assert "raw_response_access_authorized" in s
    assert "build_geb_anonymous_review_bundle_v1_91.py" in s
    assert "READY_FOR_DIRECT_GEB_SUPPORTING_INFORMATION_UPLOAD" in s

def test_v191_workflow_binds_all_reproduction_inputs_by_sha():
    s=(ROOT/".github/workflows/geb-neutralized-review-bundle-v1_91.yml").read_text()
    required=[
      "c15cb86ba0b0bd88e8d22fd566c495adcec113a3c9f7dd65f4b7c3415796335e",
      "77be952a6c45707e5e71cd0f192551f6365d6fde1ac1ba5aaaef2755c03366e2",
      "5a04e8b64682979ee708f281418c017ff34c930bc8e51d7eff3d3437929b74b0",
      "92e0ec3e5335233f6430b18a972235481845848796d0d7e1cd12cc6fb10d090f",
      "b60fbfd643b8a517d3a632a50db6b2b9916f9f3f34bae123ba7b7e89665b39e8",
      "f48ab1f09c825f99bced712a64e7c5f1ff927d024fdbe1aaf80db588b0372ef8",
      "25db7bf42396c66452c7611503522e68b6b4262bc83770c737be43076677a252",
    ]
    for digest in required:
        assert digest in s

def test_v191_checklist_flags_public_repo_anonymity_boundary():
    s=(GEB/"submission_checklist.md").read_text()
    assert "temporarily make the public development repository private during peer review" in s
    assert "requires repository-administration access" in s
    assert "Upload Supporting Information ZIP separately" in s

def test_neutralizer_source_parses():
    ast.parse((ROOT/"scripts/build_geb_anonymous_review_bundle_v1_91.py").read_text())
