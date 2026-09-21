from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "benchmarks/run_connectivity_operator_prediction_v0_2.py"
EXPECTED = ROOT / "benchmarks/connectivity_operator_prediction_expected_v0_2.json"


def load_runner():
    spec = importlib.util.spec_from_file_location("connectivity_prediction_v02", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v02_known_truth_replays_frozen_values():
    result = load_runner().run()
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))["expected_results"]

    for target, exp in expected.items():
        scores = result["results"][target]["scores"]
        assert scores["reference"]["mse"] == exp["reference_mse"]
        assert scores["pollen"]["mse"] == exp["pollen_mse"]
        assert scores["whole_individual"]["mse"] == exp["whole_individual_mse"]
        assert scores["collapsed"]["mse"] == exp["collapsed_mse"]
        assert scores["typed_both"]["mse"] == exp["typed_both_mse"]
        assert scores["pollen"]["delta_mse_vs_reference"] == exp["pollen_delta"]
        assert scores["whole_individual"]["delta_mse_vs_reference"] == exp["whole_individual_delta"]
        assert scores["collapsed"]["delta_mse_vs_reference"] == exp["collapsed_delta"]
        assert scores["typed_both"]["delta_mse_vs_reference"] == exp["typed_both_delta"]


def test_operator_match_reverses_with_endpoint_truth():
    result = load_runner().run()["results"]
    pollen = result["pollen_flow"]["scores"]
    individual = result["whole_individual"]["scores"]

    assert pollen["pollen"]["delta_mse_vs_reference"] < -0.10
    assert abs(pollen["whole_individual"]["delta_mse_vs_reference"]) < 0.001
    assert pollen["pollen"]["mse"] < pollen["collapsed"]["mse"]

    assert individual["whole_individual"]["delta_mse_vs_reference"] < -0.10
    assert abs(individual["pollen"]["delta_mse_vs_reference"]) < 0.001
    assert individual["whole_individual"]["mse"] < individual["collapsed"]["mse"]


def test_typed_state_retains_matching_operator_without_scalar_collapse():
    result = load_runner().run()["results"]
    for target in ("pollen_flow", "whole_individual"):
        scores = result[target]["scores"]
        matching = "pollen" if target == "pollen_flow" else "whole_individual"
        assert abs(scores["typed_both"]["mse"] - scores[matching]["mse"]) < 1e-5
        assert scores["collapsed"]["mse"] > scores[matching]["mse"]
