import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RESULT=ROOT/"development/wolfe_robustness_evidence_freeze_v1_212.json"

def test_exact_posthoc_bounds_and_separation_from_inference():
    r=json.loads(RESULT.read_text())
    q=r["outcome"]["estimate_point_and_missingness_bounds"]
    assert q["overall"]["lower"] > 0
    assert q["four_patches"]["upper"] < 0
    assert q["six_patches"]["lower"] > 0
    assert q["six_minus_four"]["lower"] > 0
    assert abs(q["six_minus_four"]["lower"]-
        (q["six_patches"]["lower"]-q["four_patches"]["upper"])) < 1e-12
    assert abs(q["six_minus_four"]["upper"]-
        (q["six_patches"]["upper"]-q["four_patches"]["lower"])) < 1e-12
    assert r["inference"]["missingness_ranges_are_confidence_intervals"] is False
    assert r["inference"]["sampling_block_randomization_based_inference_performed"] is False
    assert r["inference"]["causal_mechanism_identified"] is False

def test_confirmatory_submission_is_still_closed():
    r=json.loads(RESULT.read_text())
    assert r["execution"]["tests"]=="3 passed"
    assert r["source_2022_original"]["excluded_unassigned_source_row"]=="6HoLM1"
    assert r["source_2022_original"]["analysis_rows"]==175
    assert r["source_2022_original"]["source_file_changed"] is False
    assert r["execution"]["original_v209_and_v210_failed_gates_still_terminal"] is True
    assert r["inference"]["fresh_confirmatory"] is False
    assert r["inference"]["independent_mammal_topology_validation"] is False
    assert all(v is False for k,v in r["policy"].items())
