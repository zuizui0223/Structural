from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/run_global_mammals_ultrarare_source_leverage_v1_121.py"

def test_contract_keeps_diagnostic_nonconfirmatory():
    c=json.loads((ROOT/"development/global_mammals_ultrarare_source_leverage_contract_v1_121.json").read_text())
    assert c["population"]["heldout_occurrence_values_authorized"] is False
    assert c["matched_random_placement_null"]["no_support_threshold"] is True

def test_runner_keeps_response_boundary_and_exact_numerics():
    text=SCRIPT.read_text()
    assert "heldout_matrix" not in text
    assert "heldout_occurrence_values_used" in text
    assert 'np.__version__!="2.3.3"' in text
    assert "effective_source_count" in text
    assert "actual_minus_null_mean_effective_count" in text

def test_specialized_workflow_installs_numpy():
    text=(ROOT/".github/workflows/global-mammals-ultrarare-source-leverage-v1_121.yml").read_text()
    assert "numpy==2.3.3" in text
    assert "heldout_occurrence_values_used" in text
