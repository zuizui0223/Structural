from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
PKG=ROOT/"manuscript/submission/macro_v1_89"

def test_highlights_are_submission_length_and_claim_limited():
    lines=[x.strip() for x in (PKG/"highlights.txt").read_text().splitlines() if x.strip()]
    assert 3 <= len(lines) <= 5
    assert all(len(x) <= 85 for x in lines)
    joined=" ".join(lines).lower()
    assert "confirmation" not in joined
    assert "causal" not in joined
    assert "presence detection" not in joined

def test_figure_captions_preserve_evidence_boundaries():
    s=(PKG/"figure_captions.md").read_text()
    assert "Figure 1" in s and "Figure 2" in s and "Figure 3" in s
    assert "Supplementary Figure S1" in s and "Supplementary Figure S2" in s
    assert "nonconfirmatory exploratory" in s
    assert "descriptive cross-taxon context" in s
    assert "post-hoc nonrescuing diagnostics" in s
    assert "partial rho = +0.286" in s

def test_data_code_availability_uses_exact_public_sources():
    s=(PKG/"data_code_availability.md").read_text()
    assert "10.5061/dryad.hmgqnk9j2" in s
    assert "10.21942/uva.22788464.v5" in s
    assert "GIFT" in s and "version 3.2" in s
    assert "zuizui0223/Structural" in s
    assert "[TO BE MINTED BEFORE SUBMISSION]" in s
    assert "should not be rerun for manuscript formatting" in s

def test_evidence_status_does_not_promote_exploratory_results():
    s=(PKG/"evidence_status.md").read_text()
    assert "**nonconfirmatory exploratory**" in s
    assert "primary was **not supported**" in s
    assert "no ecological primary score" in s
    assert "fresh global confirmation" in s
    assert "two-taxon confirmation" in s

def test_declarations_require_author_confirmation():
    s=(PKG/"declarations_template.md").read_text()
    assert "[TO CONFIRM" in s
    assert "[AUTHOR CONFIRMATION REQUIRED" in s
    assert "adapt to the selected journal's current policy" in s
    assert "permanent code archive DOI remains to be minted" in s

def test_manifest_is_tied_to_v188_frozen_science():
    x=json.loads((PKG/"submission_manifest.json").read_text())
    assert x["status"]=="JOURNAL_NEUTRAL_SUBMISSION_PACKAGE_PREPARED_FROM_V188_FROZEN_SCIENCE"
    assert x["scientific_freeze"]=="development/current_status_v1_88.json"
    assert x["manuscript"]=="manuscript/macro_dual_isolation_mammal_v1_88.md"
    assert x["figure_artifacts"]["main_and_S1"]["artifact_id"]==11139705415
    assert x["figure_artifacts"]["S2"]["artifact_id"]==11259686592
    assert x["new_response_accessed"] is False
    assert x["new_scientific_analysis_performed"] is False
