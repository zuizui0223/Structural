from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_boreal_19island_confirmatory_result_v1_14.py"
RESULT = (
    ROOT / "development/boreal_19island_confirmatory_scoring_result_v1_14.json"
)
FREEZE = (
    ROOT / "development/boreal_19island_confirmatory_result_freeze_v1_14.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("boreal19_v114", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_real_frozen_result_exact_replays_primary_without_response():
    module = load_module()
    receipt = module.verify(
        load(RESULT),
        load(FREEZE),
        result_file_sha256=module.sha256_file(RESULT),
    )
    assert receipt["status"] == "VERIFIED_FRESH_RESULT_PRIMARY_NOT_SUPPORTED"
    assert receipt["primary_supported"] is False
    assert receipt["point_estimate_hex"] == "0x1.39924c7e170fep-7"
    assert receipt["ci95_lower_hex"] == "0x1.0a92c7c5aaa77p-8"
    assert receipt["ci95_upper_hex"] == "0x1.de25df9bfda78p-7"
    assert receipt["confirmatory_block_count"] == 7
    assert receipt["confirmatory_target_count"] == 1287
    assert receipt["fresh_system_denominator_contribution"] == 1
    assert receipt["counts_as_fresh_confirmatory_evidence"] is True
    assert receipt["mechanism_claim_authorized"] is False
    assert receipt["secondary_analysis_may_change_primary_status"] is False
    assert receipt["rerun_authorized"] is False
    assert receipt["raw_response_reopened_by_verifier"] is False


def test_result_direction_is_strictly_opposite_favourable_direction():
    result = load(RESULT)
    primary = result["primary"]
    point = float.fromhex(primary["point_estimate_hex"])
    lower = float.fromhex(primary["ci95_lower_hex"])
    upper = float.fromhex(primary["ci95_upper_hex"])
    assert primary["favourable_direction"] == "negative"
    assert point > 0.0
    assert lower > 0.0
    assert upper > 0.0
    assert primary["primary_supported"] is False


def test_fresh_evidence_accounting_is_exactly_one_valid_system():
    result = load(RESULT)
    assert result["counts_as_fresh_confirmatory_evidence"] is True
    assert result["counts_as_primary_confirmatory_evidence"] is True
    assert result["fresh_system_denominator_contribution"] == 1
    assert result["confirmatory_response_opened"] is True
    assert result["authorization_consumed"] is True
    assert result["rerun_authorized"] is False
    assert result["secondary_analysis_may_change_primary_status"] is False
    assert result["mechanism_claim_authorized"] is False
    assert result["confirmatory_target_values_parsed"] == 1287
    assert result["pilot_target_values_parsed"] == 0
    assert result["excluded_target_values_parsed"] == 0
    assert result["nonfocal_confirmatory_target_values_parsed"] == 0


def test_block_delta_tamper_fails_closed():
    module = load_module()
    result = load(RESULT)
    result["primary"]["block_summaries"][0][
        "mean_C_minus_R3_hex"
    ] = "0x0.0p+0"
    with pytest.raises(
        module.Boreal19ResultVerificationError,
        match="canonical result fingerprint mismatch|block C-minus-R3 inconsistency|point estimate replay drift",
    ):
        module.verify(
            result,
            load(FREEZE),
            result_file_sha256=module.sha256_file(RESULT),
        )


def test_primary_status_cannot_be_relabelled_after_result():
    module = load_module()
    result = load(RESULT)
    result["primary_supported"] = True
    with pytest.raises(
        module.Boreal19ResultVerificationError,
        match="canonical result fingerprint mismatch|boundary/accounting mismatch",
    ):
        module.verify(
            result,
            load(FREEZE),
            result_file_sha256=module.sha256_file(RESULT),
        )
