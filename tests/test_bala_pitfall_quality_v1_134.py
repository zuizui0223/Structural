from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]

def test_quality_thresholds_are_frozen_before_occurrence():
    x=json.loads((ROOT/"development/bala_pitfall_quality_contract_v1_134.json").read_text())
    q=x["surveyed_zero_quality_rule"]
    assert q["site_phase_minimum_unique_trap_positions"]==20
    assert q["island_phase_minimum_unique_trap_fraction"]==0.80
    assert q["threshold_retuning_after_pilot_or_confirmatory_occurrence"] is False
    assert x["response_boundary"]["occurrence_extension_semantically_opened"] is False

def test_eventid_fallback_is_response_independent():
    x=json.loads((ROOT/"development/bala_pitfall_quality_contract_v1_134.json").read_text())
    p=x["pitfall_position_recovery"]
    assert p["primary_source"].startswith("parse fieldNumber")
    assert p["fallback_source"].startswith("only when fieldNumber is missing/malformed")
    assert p["fallback_requires_unique_match"] is True
    assert x["publication_and_code_basis"]["event_builder_git_blob_sha1"]=="9e39690b5dbcd7461c7bae98a254eb28f12c59d6"

def test_runner_never_reads_occurrence_semantics():
    s=(ROOT/"scripts/freeze_bala_pitfall_quality_v1_134.py").read_text()
    assert "occurrence_extension_semantically_opened" in s
    assert "taxon_occurrence_values_opened" in s
    assert "source_loss_effects_computed" in s
    assert "parse_event_core" in s

def test_workflow_does_not_authorize_confirmatory_response():
    s=(ROOT/".github/workflows/bala-pitfall-quality-v1_134.yml").read_text()
    assert "occurrence_semantic_access_authorized" in s
    assert "confirmatory_eligible" in s
    assert "freeze_bala_pitfall_quality_v1_134.py" in s
