from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/analyze_boreal_19island_secondary_diagnostic_v1_15.py"
CONTRACT = ROOT / "development/boreal_19island_secondary_diagnostic_contract_v1_15.json"
RESULT = ROOT / "development/boreal_19island_confirmatory_scoring_result_v1_14.json"
PRIMARY_FREEZE = ROOT / "development/boreal_19island_confirmatory_result_freeze_v1_14.json"
PREDICTIONS = ROOT / "development/boreal_19island_confirmatory_predictions_v1_10.csv"
PRECONFIRM = ROOT / "development/boreal_19island_preconfirmatory_freeze_v1_10.json"
STATE = ROOT / "development/boreal_19island_state_reference_v0_99.csv"
STATE_FREEZE = ROOT / "development/boreal_19island_state_reference_freeze_v0_99.json"
SPATIAL = ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
FREEZE = ROOT / "development/boreal_19island_secondary_diagnostic_freeze_v1_16.json"


def load_module():
    spec = importlib.util.spec_from_file_location("boreal19_v116", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def reproduce():
    module = load_module()
    return module.analyze(
        result=load(RESULT),
        primary_freeze=load(PRIMARY_FREEZE),
        predictions_path=PREDICTIONS,
        preconfirmatory_freeze=load(PRECONFIRM),
        state_path=STATE,
        state_freeze=load(STATE_FREEZE),
        spatial=load(SPATIAL),
        contract=load(CONTRACT),
        result_file_sha256=module.sha256_file(RESULT),
    )


def test_v116_freeze_matches_recomputed_v115_diagnostic():
    out = reproduce()
    freeze = load(FREEZE)
    summary = freeze["diagnostic_summary"]
    pattern = out["pattern_summary"]

    assert freeze["status"] == "POSTHOC_DIAGNOSTIC_COMMITTED_PRIMARY_UNCHANGED"
    assert out["status"] == (
        "POSTHOC_DIAGNOSTIC_COMPLETE_PRIMARY_REMAINS_NOT_SUPPORTED"
    )
    assert pattern["worsening_block_count"] == summary["worsening_block_count"]
    assert pattern["improving_block_count"] == summary["improving_block_count"]
    assert pattern["worsening_blocks"] == summary["worsening_blocks"]
    assert pattern["improving_blocks"] == summary["improving_blocks"]
    assert (
        pattern["all_worsening_blocks_C_probability_higher_fraction_min_hex"]
        == summary[
            "minimum_fraction_C_probability_higher_in_worsening_blocks_hex"
        ]
    )
    assert (
        pattern["correlation_loss_with_signed_probability_shift_hex"]
        == summary["correlation_loss_with_signed_probability_shift_hex"]
    )
    assert (
        pattern["correlation_loss_with_absolute_probability_shift_hex"]
        == summary["correlation_loss_with_absolute_probability_shift_hex"]
    )
    assert (
        pattern["correlation_loss_with_rms_probability_shift_hex"]
        == summary["correlation_loss_with_rms_probability_shift_hex"]
    )
    assert (
        pattern["correlation_loss_with_log_area_z_hex"]
        == summary["correlation_loss_with_log_area_z_hex"]
    )
    assert (
        pattern["correlation_loss_with_log_mainland_distance_z_hex"]
        == summary["correlation_loss_with_log_mainland_distance_z_hex"]
    )


def test_v116_cannot_rescue_or_modify_primary():
    out = reproduce()
    freeze = load(FREEZE)
    lock = freeze["primary_lock"]
    assert lock["primary_supported"] is False
    assert lock["fresh_system_denominator_contribution"] == 0
    assert lock["secondary_analysis_may_change_primary_status"] is False
    assert lock["mechanism_claim_authorized"] is False
    assert lock["causal_dispersal_claim_authorized"] is False
    assert lock["raw_confirmatory_response_reopened"] is False
    assert lock["row_level_confirmatory_targets_used"] is False

    assert out["primary_supported"] is False
    assert out["fresh_system_denominator_contribution"] == 0
    assert out["secondary_analysis_may_change_primary_status"] is False
    assert out["mechanism_claim_authorized"] is False


def test_descriptive_signal_is_strong_but_not_mechanistic():
    freeze = load(FREEZE)
    s = freeze["diagnostic_summary"]
    assert float.fromhex(
        s["correlation_loss_with_signed_probability_shift_hex"]
    ) > 0.98
    assert float.fromhex(
        s["correlation_loss_with_absolute_probability_shift_hex"]
    ) > 0.94
    assert float.fromhex(
        s["minimum_fraction_C_probability_higher_in_worsening_blocks_hex"]
    ) > 0.96
    assert freeze["ecological_interpretation"]["not_established"]
