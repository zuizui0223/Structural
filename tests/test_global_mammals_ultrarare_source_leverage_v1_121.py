from pathlib import Path
import importlib.util, json
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'scripts/run_global_mammals_ultrarare_source_leverage_v1_121.py'
spec=importlib.util.spec_from_file_location('source_leverage',SCRIPT)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)

def test_effective_source_count_equal():
    n,m=mod.effective_source_count(np.array([1.0,1.0,1.0,1.0]))
    assert abs(n-4.0)<1e-12
    assert abs(m-0.25)<1e-12

def test_effective_source_count_unequal():
    n,m=mod.effective_source_count(np.array([9.0,1.0]))
    assert abs(n-(1.0/(0.9**2+0.1**2)))<1e-12
    assert abs(m-0.9)<1e-12

def test_contract_keeps_diagnostic_nonconfirmatory():
    c=json.loads((ROOT/'development/global_mammals_ultrarare_source_leverage_contract_v1_121.json').read_text())
    assert c['population']['heldout_occurrence_values_authorized'] is False
    assert c['matched_random_placement_null']['no_support_threshold'] is True
    text=SCRIPT.read_text()
    assert 'heldout_matrix' not in text
    assert 'heldout_occurrence_values_used' in text
