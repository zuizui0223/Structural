from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
GEB=ROOT/"manuscript/submission/GEB_v1_92"

def test_current_geb_research_article_abstract_format():
    s=(GEB/"blinded_main_text.md").read_text()
    abstract=s.split("## Abstract",1)[1].split("**Keywords:**",1)[0]
    assert len(abstract.split()) <= 300
    for heading in ("Aim","Innovation","Main conclusions"):
        assert f"**{heading}:**" in abstract
    for obsolete in ("Location","Time period","Major taxa studied","Methods","Results"):
        assert f"**{obsolete}:**" not in abstract

def test_geb_v192_title_is_cautious_about_posthoc_attenuation():
    s=(GEB/"blinded_main_text.md").read_text()
    title=s.splitlines()[0]
    assert "widespread but asymmetric" in title
    assert "attenuates" not in title.lower()
    assert "weakens" not in title.lower()

def test_geb_v192_blinded_manuscript_has_no_direct_identity_surface():
    s=(GEB/"blinded_main_text.md").read_text()
    assert "zuizui0223" not in s
    assert "github.com" not in s.lower()
    assert "manuscript/" not in s
    assert "Draft status" not in s
    assert "## Positioning" not in s
    assert "Evidence status and claim boundary" not in s

def test_geb_v192_structure_and_word_budget():
    s=(GEB/"blinded_main_text.md").read_text()
    assert len(s.split()) < 5000
    m=re.search(r"\*\*Running title:\*\* (.+)",s)
    assert m and len(m.group(1).strip()) < 40
    for h in ("## 1. Introduction","## 2. Methods","## 3. Results","## 4. Discussion","## 5. Conclusions","## References","## Data and Code Availability Statement"):
        assert h in s
    assert s.index("## References") < s.index("## Data and Code Availability Statement")

def test_policy_snapshot_records_correction():
    s=(GEB/"policy_snapshot_2026_10.md").read_text()
    assert "Aim; Innovation; Main conclusions" in s
    assert "seven-heading structured-abstract format" in s
    assert "affected no scientific analysis" in s

def test_submission_manifest_binds_neutralized_si():
    x=json.loads((GEB/"submission_manifest.json").read_text())
    assert x["scientific_freeze"]=="development/current_status_v1_88.json"
    assert x["anonymous_review_si"]["artifact_id"]==11261832785
    assert x["anonymous_review_si"]["inner_zip_sha256"]=="fa84e30a5f07de424b52269f17d0d5627589edd0a1cab652fa14b79ead14cc3b"
    assert x["anonymous_review_si"]["raw_biological_response_included"] is False
    assert x["anonymous_review_si"]["public_repository_identifiers_included"] is False
    assert x["current_GEB_research_article_abstract"]["required_headings"]==["Aim","Innovation","Main conclusions"]
    assert x["scientific_analysis_changed"] is False
    assert x["new_response_accessed"] is False

def test_checklist_requires_final_author_and_metadata_actions():
    s=(GEB/"submission_checklist.md").read_text()
    assert "Aim; Innovation; Main conclusions" in s
    assert "neutralized SI ZIP" in s
    assert "temporarily make the public development repository private" in s
    assert "Check final DOCX/PDF document properties" in s
