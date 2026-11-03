"""v1.347 double-anonymous JBI artifacts: text and source-free S1 only."""
import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_jbi_anonymous_review_bundle_v1_347 import anonymize,build,MANUSCRIPT,S1

def read():
    return MANUSCRIPT.read_text(encoding="utf-8"),S1.read_text(encoding="utf-8")

def test_authored_reviewer_text_is_anonymous_300_word_structured_and_JBI_ordered():
    main,s1=read()
    clean,clean_s1,words=anonymize(main,s1)
    assert 250<=words<=300
    for title in ("Aim","Location","Taxon","Methods","Results","Main conclusions"):
        assert "**"+title+":**" in clean
    assert clean.index("## References (")<clean.index("## Data availability and reproducibility")<clean.index("## Figure legends")
    assert "## Declarations requiring author review" not in clean
    assert "### Internal non-submission notes" not in clean
    assert "github.com/zuizui0223" not in clean
    assert "github.com/zuizui0223" not in clean_s1
    assert "**Evidence and exact reproducibility:**" not in clean_s1
    assert "0.187500" in clean_s1 and "0.015625" in clean_s1
    assert "−0.4399" in clean_s1
    assert "4.5 | Conclusions" in clean
    assert "Table S1" in clean

def test_evidence_locked_figure_bundle_and_documents_generate_only_original_aggregate(tmp_path):
    main,s1=read()
    orig={
      "schema":"structural.bala_jbi_sourcefree_figure_bundle.v1_345",
      "status":"ORIGINAL_BALA_NUMERICAL_FIGURES_GENERATED_WITHOUT_BIOLOGICAL_SOURCE",
      "original_archive_SHA256":"4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2",
      "physical_islands":7,"physical_sites":29,
      "original_Event_or_Occurrence_rows_opened":0,
      "new_confirmatory_systems":0,"GEB_scientific_HOLD":True,
      "figures":["figure1_temporal_excess","figure2_spatial_beta_by_island","figure3_alpha_spatial_decoupling"]
    }
    (tmp_path/"figure_bundle_manifest.json").write_text(json.dumps(orig))
    d=build(main,s1,tmp_path)
    assert d["status"]=="JBI_REVIEWER_SAFE_MARKDOWN_S1_THREE_FIGURES_SOURCEFREE"
    assert d["reviewer_facing_original_biological_rows_reopened"]==0
    assert d["author_identifying_git_links_in_reviewer_text"]==0
    assert d["not_submitted"]
    assert d["GEB_scientific_HOLD"] and d["new_confirmatory_systems"]==0 and not d["eBird_used"]
    assert len(d["blinded_main_manuscript_sha256"])==64
    assert len(d["blinded_uncertainty_S1_sha256"])==64
    assert (tmp_path/"JBI_anonymized_main_text_v1_347.md").exists()
    assert (tmp_path/"JBI_anonymized_Supplementary_Table_S1_v1_347.md").exists()
    assert json.loads((tmp_path/"JBI_blinded_package_manifest_v1_347.json").read_text())==d
    assert "source_original_BALA" in json.dumps(d)

def test_missing_internal_notes_or_bad_uncertainty_must_stop_not_ship():
    main,s1=read()
    with pytest.raises(ValueError,match="not the reviewed"):
        anonymize(main.split("### Internal non-submission notes")[0],s1)
    with pytest.raises(ValueError,match="S1 missing"):
        anonymize(main,s1.replace("−0.4399","−0.5000"))
    with pytest.raises(ValueError,match="provenance exposure"):
        anonymize(main.replace("Decadal arthropod turnover", "Decadal arthropod turnover"),s1.replace(
          "# Supplementary Table S1", "# Supplementary Table S1\nhttp://github.com/zuizui0223"))
        
def test_source_manifest_rejects_original_biological_replay(tmp_path):
    main,s1=read()
    base={
      "schema":"structural.bala_jbi_sourcefree_figure_bundle.v1_345",
      "status":"ORIGINAL_BALA_NUMERICAL_FIGURES_GENERATED_WITHOUT_BIOLOGICAL_SOURCE",
      "original_archive_SHA256":"4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2",
      "physical_islands":7,"physical_sites":29,
      "original_Event_or_Occurrence_rows_opened":63904,
      "new_confirmatory_systems":0,"GEB_scientific_HOLD":True,
      "figures":["a","b","c"]
    }
    (tmp_path/"figure_bundle_manifest.json").write_text(json.dumps(base))
    with pytest.raises(ValueError,match="evidence-locked"):
        build(main,s1,tmp_path)
