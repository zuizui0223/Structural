from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/structural_active_priority_v0_35.json"

def test_confirmatory_queue_is_empty_until_gate_pass():
    x=json.loads(P.read_text())
    assert x["current_confirmatory_eligible_count"]==0
    assert x["current_confirmatory_eligible_systems"]==[]
    assert x["empirical_denominator"]["reopened"] is False

def test_gate_first_sequence_is_mandatory():
    x=json.loads(P.read_text())
    seq=" ".join(x["required_sequence"])
    assert "v0.31" in seq
    assert "v0.32" in seq
    assert "v0.33" in seq
    assert x["priority_rules"]["confirmatory_without_v0_31_v0_32_v0_33"] is False

def test_candidate_hunting_and_ttf_are_not_active_dependencies():
    x=json.loads(P.read_text())
    assert x["priority_rules"]["new_candidate_hunting_as_primary_objective"] is False
    assert x["priority_rules"]["opportunistic_dataset_search"] is False
    assert x["priority_rules"]["ttf_handoff_is_active_dependency"] is False
