from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_v159_is_response_independent():
    x=json.loads((ROOT/"development/ebird_prebiology_handoff_contract_v1_159.json").read_text())
    assert x["status"]=="FULL_RESPONSE_INDEPENDENT_PREBIOLOGY_HANDOFF_FROZEN"
    assert x["response_access_authorized"] is False
    assert x["counts_as_empirical_source_loss_evidence"] is False
    assert "species names" in x["forbidden_outputs"]
    assert "source-loss events" in x["forbidden_outputs"]

def test_v159_runs_acquisition_then_design():
    s=(ROOT/"scripts/run_ebird_prebiology_handoff_v1_159.py").read_text()
    assert "run_ebird_sed_handoff_v1_157.py" in s
    assert "build_ebird_three_wave_design_v1_158.py" in s
    assert s.index("ACQ") < s.index("DESIGN")
    assert "species_response_opened" in s
    assert "response_access_authorized" in s

def test_priority_reduces_blocker_to_external_file():
    x=json.loads((ROOT/"development/structural_active_priority_v1_159.json").read_text())
    assert x["status"]=="ebird_external_file_only_blocker_full_prebiology_chain_ready"
    assert x["live_candidate"]["status"]=="HOLD_OFFICIAL_SAMPLING_EVENT_DATA_REQUIRED"
    assert x["live_candidate"]["response_access_authorized"] is False
