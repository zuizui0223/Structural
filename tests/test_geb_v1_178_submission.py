from pathlib import Path
import json
import re

ROOT=Path(__file__).resolve().parents[1]
DIR=ROOT/"manuscript/submission/GEB_v1_178"

def words(text):
    return len(re.sub(r"[#*_>`\[\]{}()]"," ",text).split())

def test_geb_v178_research_article_abstract_and_limits():
    text=(DIR/"blinded_main_text.md").read_text()
    abstract=text[text.index("## Abstract"):text.index("## 1. Introduction")]
    for h in ("Aim","Location","Time period","Major taxa studied","Methods","Results","Main conclusions"):
        assert f"**{h}:**" in abstract
    assert words(abstract) <= 300
    main=text[text.index("## 1. Introduction"):text.index("## References")]
    assert words(main) <= 5000
    run=re.search(r"\*\*Running title:\*\* (.+)",text).group(1)
    assert len(run) < 40

def test_geb_v178_claim_boundaries():
    qa=json.loads((DIR/"submission_qa_v1_178.json").read_text())
    c=qa["scientific_claims"]
    assert c["monotonic_rarity_law_claimed"] is False
    assert c["realized_dispersal_claimed"] is False
    assert c["rescue_claimed"] is False
    assert c["management_priority_metric_validated"] is False
    assert c["occupancy_dependent_connectivity_itself_claimed_new"] is False

def test_sw_finland_is_provenance_only_not_a_biological_negative_in_manuscript():
    text=(DIR/"blinded_main_text.md").read_text().lower()
    qa=json.loads((DIR/"submission_qa_v1_178.json").read_text())
    assert "sw finland" not in text
    assert qa["provenance_boundaries"]["sw_finland_in_manuscript"] is False
    assert qa["provenance_boundaries"]["sw_finland_biological_negative_claimed"] is False

def test_references_are_alphabetized_and_no_escaped_newline_artifact():
    text=(DIR/"blinded_main_text.md").read_text()
    refs=text[text.index("## References"):text.index("## Data and Code Availability Statement")]
    rows=[x for x in refs.splitlines() if x.startswith("- ")]
    # Alphabetize by first-author surname; preserve author-order chronology within Hanski references.
    assert rows == sorted(rows, key=lambda row: row.split(",",1)[0].casefold())
    assert "\\n-" not in text
