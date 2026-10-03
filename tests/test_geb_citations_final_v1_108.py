from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
GEB=ROOT/"manuscript/submission/GEB_v1_108"

def test_every_reference_is_cited_in_main_text():
    s=(GEB/"blinded_main_text.md").read_text()
    body,rest=s.split("## References",1)
    refs=rest.split("## Data and Code Availability Statement",1)[0]
    entries=[x for x in refs.splitlines() if x.startswith("- ")]
    parsed=[]
    for e in entries:
        m=re.match(r"-\s+([^,]+),.*?\((\d{4})\)",e)
        assert m,e
        parsed.append((m.group(1),m.group(2)))
    assert len(parsed)==13
    for first,year in parsed:
        assert year in body
        assert (
            f"{first} " in body or
            f"{first} &" in body or
            f"{first} et al." in body
        ),(first,year)

def test_fahrig_and_schrader_are_used_for_context_not_claim_support():
    s=(GEB/"blinded_main_text.md").read_text()
    assert "potential immigrants (Fahrig 2013)" in s
    assert "single scalar isolation axis (Schrader et al. 2021)" in s

def test_final_scientific_values_and_evidence_boundaries_unchanged():
    s=(GEB/"blinded_main_text.md").read_text()
    assert "−0.001814" in s
    assert "−0.000442" in s
    assert "11 of 20 null graphs" in s
    assert "prospective species-layer non-replication" in s
    assert "not geographically independent confirmation" in s

def test_manifest_marks_citation_finalization_only():
    x=json.loads((GEB/"submission_manifest.json").read_text())
    assert x["status"]=="GEB_SUBMISSION_PACKAGE_CITATIONS_FINALIZED"
    assert x["reference_count"]==13
    assert x["reference_list_only_entries"]==0
    assert x["new_scientific_analysis_authorized"] is False
    assert x["same_data_rescue_authorized"] is False
