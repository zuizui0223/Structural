import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))

def test_source_loss_transition_v123_is_three_time_and_non_tautological():
    x = load("development/prospective_source_loss_leverage_transition_hypothesis_v1_123.json")
    assert x["status"] == "FUTURE_ONLY_INDEPENDENT_TEMPORAL_RESPONSE_SEALED_HYPOTHESIS"
    assert x["minimum_temporal_design"]["required_response_times"] == 3
    assert x["future_endpoint"]["lost_source_sites_excluded_from_endpoint"] is True
    assert x["source_loss_exposure"]["primary_exposure"] == "E_i"
    assert x["reference_ladder"]["primary_contrast"].startswith("heldout predictive loss of C minus R2")
    assert x["counts_as_current_evidence"] is False

def test_source_loss_transition_v123_excludes_target_self_anchor():
    x = load("development/prospective_source_loss_leverage_transition_hypothesis_v1_123.json")
    s = x["source_loss_exposure"]
    assert s["self_anchor_exclusion"] is True
    assert "excluding target i itself" in s["baseline_sources"]
    assert "K_ii is never used" in s["kernel"]
    assert any("target population itself" in z for z in x["anti_selection"])

def test_source_loss_transition_v123_holds_count_and_distance_reference():
    x = load("development/prospective_source_loss_leverage_transition_hypothesis_v1_123.json")
    r1 = " ".join(x["reference_ladder"]["R1"])
    r2 = " ".join(x["reference_ladder"]["R2"])
    assert "occupied-source count" in r1
    assert "source-loss count" in r1
    assert "ordinary Euclidean distance" in r2
    assert "self-anchor" in r2
    assert "E_i" in " ".join(x["reference_ladder"]["C"])
    assert any("do not redefine L01 using t2" in s for s in x["anti_selection"])

def test_v123_priority_requires_metadata_first_candidate_triage():
    p = load("development/structural_active_priority_v1_123.json")
    assert "metadata-only" in p["next_scientific_event"]
    assert any("three response times" in s for s in p["do_now"])
    assert any("global mammal system" in s for s in p["do_not"])

def test_v123_candidate_template_keeps_response_closed():
    t = load("development/source_loss_temporal_candidate_intake_template_v1_123.json")
    assert t["response_values_opened"] is False
    assert "candidate-specific t2 contraction direction" in t["forbidden_pre_admission_information"]
