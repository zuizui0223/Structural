from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
GEB=ROOT/"manuscript/submission/GEB_v1_90"

def test_geb_blinded_main_text_matches_current_requirements():
    s=(GEB/"blinded_main_text.md").read_text()
    assert s.startswith("# Island isolation is not one-dimensional:")
    m=re.search(r"\*\*Running title:\*\* (.+)",s)
    assert m and len(m.group(1).strip()) < 40
    for heading in ("Aim","Location","Time period","Major taxa studied","Methods","Results","Main conclusions"):
        assert f"**{heading}:**" in s
    abstract=s.split("## Abstract",1)[1].split("**Keywords:**",1)[0]
    assert len(abstract.split()) <= 300
    assert "## 1. Introduction" in s
    assert "## 2. Methods" in s
    assert "## 3. Results" in s
    assert "## 4. Discussion" in s
    assert "## 5. Conclusions" in s
    assert s.index("## References") < s.index("## Data and Code Availability Statement")
    assert "manuscript/" not in s
    assert "zuizui0223" not in s
    assert "Draft status" not in s
    assert "## Positioning" not in s
    assert "Evidence status and claim boundary" not in s

def test_geb_manuscript_word_budget_is_comfortable():
    s=(GEB/"blinded_main_text.md").read_text()
    assert len(s.split()) < 5000

def test_geb_cover_letter_emphasizes_generality_without_overclaim():
    s=(GEB/"cover_letter.md").read_text()
    assert "5,401 islands, 79 mammal species and 12 bioregions" in s
    assert "nonconfirmatory exploratory" in s
    assert "fresh local boreal test was non-support" in s
    assert "manufacture cross-taxon confirmation" in s

def test_geb_data_code_statement_is_blinded_and_requires_stable_archive():
    s=(GEB/"blinded_main_text.md").read_text()
    block=s.split("## Data and Code Availability Statement",1)[1]
    assert "10.5061/dryad.hmgqnk9j2" in block
    assert "10.21942/uva.22788464.v5" in block
    assert "ANONYMIZED STABLE REVIEW LINK" in block
    assert "github.com" not in block.lower()

def test_title_page_requires_author_confirmation():
    s=(GEB/"title_page_template.md").read_text()
    assert "AUTHOR LIST AND ORDER" in s
    assert "ONE CORRESPONDING AUTHOR ONLY" in s
    assert "AUTHOR CONFIRMATION REQUIRED" in s
    assert "AI-assisted" in s

def test_anonymous_review_bundle_excludes_raw_response_and_public_repo_link():
    x=json.loads((GEB/"anonymized_review_bundle_manifest.json").read_text())
    assert x["new_response_access_authorized"] is False
    assert "raw Dryad biological response bytes" in x["exclude"]
    assert "public repository URL" in x["exclude"]
    w=(ROOT/".github/workflows/geb-anonymous-review-bundle-v1_90.yml").read_text()
    assert "prepare_dryad_token" not in w
    assert "Appendix_1_presence_absence.csv" not in w
    assert "direct identity leakage" in w
    assert "GEB_anonymous_review_bundle_v1_90.zip" in w

def test_geb_checklist_requires_anonymous_stable_link_before_submission():
    s=(GEB/"submission_checklist.md").read_text()
    assert "Insert an anonymized stable peer-review code archive link" in s
    assert "GitHub" in s
    assert "double-anonymous" in s.lower()
