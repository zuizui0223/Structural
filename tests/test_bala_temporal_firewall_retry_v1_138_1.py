from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_retry_changes_only_runner_operationally():
    x=json.loads((ROOT/"development/bala_confirmatory_temporal_firewall_retry_request_v1_138_1.json").read_text())
    assert x["status"]=="REQUEST_OPERATIONAL_RETRY_SAME_V138_SCIENTIFIC_CONTRACT"
    assert x["original_run"]["workflow_run_id"]==37264285424
    assert x["original_run"]["ecological_semantics_opened"] is False
    assert x["scientific_contract_changed"] is False
    assert x["input_artifacts_changed"] is False
    assert x["authorized_semantics_changed"] is False
    assert x["one_retry_only"] is True

def test_retry_uses_same_splitter_and_ubuntu_2204():
    s=(ROOT/".github/workflows/bala-confirmatory-temporal-firewall-v1_138_1.yml").read_text()
    assert "runs-on: ubuntu-22.04" in s
    assert "split_bala_confirmatory_temporal_v1_138.py" in s
    assert "c11c446a5e3dfeda9839f583a51617f6c909f46fe7088a304f7e6b63eb5eca6e" in s
    assert "a7fcd14b11ff95abf93a007319830377dfed54e35e5937cac7ae9e5f00957e27" in s
    assert "source_leverage_values_computed" in s
    assert "confirmatory_t2_outcomes_opened" in s
