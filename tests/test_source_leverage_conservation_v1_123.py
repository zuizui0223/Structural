from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parents[1]
GEB=ROOT/"manuscript/submission/GEB_v1_124"

def test_source_leverage_is_discussion_only_and_posthoc():
    s=(GEB/"blinded_main_text.md").read_text()
    discussion=s.split("## 4. Discussion",1)[1].split("## 5. Conclusions",1)[0]
    assert "median **66.1%**" in discussion
    assert "median effective source number of **2.57**" in discussion
    assert "higher by **0.282** on average" in discussion
    assert "post-hoc" not in s.split("## Abstract",1)[1].split("**Keywords:**",1)[0].lower()

def test_conservation_wording_is_leverage_not_intervention_claim():
    s=(GEB/"blinded_main_text.md").read_text()
    assert "population counts should not automatically be treated as equal units of source access" in s
    assert "Occupied pilot islands are source endpoints" in s
    assert "intermediate islands on a shortest path need not be occupied" in s
    assert "does **not** identify occupied-population stepping-stone chains" in s
    assert "loss of a high-leverage source predict a larger subsequent contraction" in s

def test_main_evidence_numbers_and_title_unchanged():
    s=(GEB/"blinded_main_text.md").read_text()
    assert s.startswith("# When do source islands matter? Species occupancy changes the role of connectivity across islands")
    for value in (
        "−0.5963","−0.7439 to −0.4645",
        "−0.000442","−0.001098 to +0.000204",
        "+1.56 × 10⁻⁶","11/20",
        "+0.000225","0/20"
    ):
        assert value in s

def test_manifest_does_not_promote_leverage_diagnostic():
    x=json.loads((GEB/"submission_manifest.json").read_text())
    d=x["conservation_leverage_diagnostic"]
    assert d["evidence_class"]=="posthoc response-free pilot-plus-geometry diagnostic"
    assert d["evidence_hierarchy_changed"] is False
    assert d["species_with_2_4_sources"]==212
    assert d["mean_actual_minus_null_effective_count"]==0.28242921346906974
    assert x["future_hypothesis"]=="development/prospective_source_loss_leverage_hypothesis_v1_123.json"
    assert x["new_same_dataset_mechanism_search_authorized"] is False

def test_future_source_loss_hypothesis_is_independent_only():
    x=json.loads((ROOT/"development/prospective_source_loss_leverage_hypothesis_v1_123.json").read_text())
    assert x["status"]=="FUTURE_ONLY_INDEPENDENT_TEMPORAL_OR_RESPONSE_SEALED_HYPOTHESIS"
    assert x["counts_as_current_evidence"] is False
    assert "same-dataset mammal threshold mining is closed" in x["guardrails"]

def test_manuscript_remains_within_geb_word_budget():
    s=(GEB/"blinded_main_text.md").read_text()
    assert len(s.split()) < 5000
