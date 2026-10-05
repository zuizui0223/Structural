from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_window_selection_rule_is_outcome_free_and_deterministic():
    x=json.loads((ROOT/"development/azores_slam_window_selection_contract_v1_147.json").read_text())
    assert x["site_key_selection"]["priority_order"][0]=="locationID"
    assert x["site_key_selection"]["selection"].startswith("choose the first admissible")
    assert x["temporal_window_selection"]["pilot_rule"].startswith("among eligible windows")
    assert x["temporal_window_selection"]["confirmatory_rule"].startswith("among eligible windows")
    assert x["temporal_window_selection"]["no_window_selection_from_occurrence"] is True

def test_windows_must_be_nonoverlapping():
    x=json.loads((ROOT/"development/azores_slam_window_selection_contract_v1_147.json").read_text())
    assert x["temporal_window_selection"]["nonoverlap"]=="pilot.end_year < confirmatory.start_year"
    assert x["temporal_window_selection"]["if_no_nonoverlapping_pair"]=="STOP"

def test_selection_script_uses_event_summaries_only():
    s=(ROOT/"scripts/freeze_azores_slam_windows_v1_147.py").read_text()
    assert "site-key-candidates" in s
    assert "site-year-coverage" in s
    assert "window-candidates" in s
    assert "Occurrence" not in s
    assert "source_loss_effects_computed" in s
