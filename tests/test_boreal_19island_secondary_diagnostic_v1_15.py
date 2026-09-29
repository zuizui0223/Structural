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


def load_module():
    spec = importlib.util.spec_from_file_location("boreal19_v115", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_real():
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


def test_posthoc_diagnostic_preserves_primary_and_evidence_boundaries():
    out = run_real()
    assert out["status"] == (
        "POSTHOC_DIAGNOSTIC_COMPLETE_PRIMARY_REMAINS_NOT_SUPPORTED"
    )
    assert out["primary_supported"] is False
    assert out["primary_status_locked"] == (
        "PRIMARY_NOT_SUPPORTED_INTERNAL_SOURCE_ISOLATION_NONREDUNDANT"
    )
    assert out["fresh_system_denominator_contribution"] == 0
    assert out["raw_confirmatory_response_reopened"] is False
    assert out["row_level_confirmatory_targets_used"] is False
    assert out["secondary_analysis_may_change_primary_status"] is False
    assert out["mechanism_claim_authorized"] is False
    assert out["causal_dispersal_claim_authorized"] is False


def test_probability_shift_pattern_tracks_loss_penalty_descriptively():
    out = run_real()
    p = out["pattern_summary"]
    assert p["worsening_block_count"] == 5
    assert p["improving_block_count"] == 2

    min_worse = float.fromhex(
        p["all_worsening_blocks_C_probability_higher_fraction_min_hex"]
    )
    r_signed = float.fromhex(
        p["correlation_loss_with_signed_probability_shift_hex"]
    )
    r_abs = float.fromhex(
        p["correlation_loss_with_absolute_probability_shift_hex"]
    )
    r_rms = float.fromhex(
        p["correlation_loss_with_rms_probability_shift_hex"]
    )

    assert min_worse > 0.96
    assert r_signed > 0.97
    assert r_abs > 0.94
    assert r_rms > 0.94


def test_two_improving_blocks_are_small_or_opposite_C_shifts():
    out = run_real()
    improving = set(out["pattern_summary"]["improving_blocks"])
    rows = {
        row["block"]: row
        for row in out["block_diagnostics"]
    }
    assert improving == {"SC_53a986e1b37a", "SC_088d2e949e6e"}

    wf = rows["SC_53a986e1b37a"]
    hfn = rows["SC_088d2e949e6e"]
    assert float.fromhex(wf["mean_probability_C_minus_R3_hex"]) < 0.0
    assert abs(float.fromhex(hfn["mean_probability_C_minus_R3_hex"])) < 0.001


def test_state_correlations_remain_explicitly_descriptive_only():
    out = run_real()
    p = out["pattern_summary"]
    r_area = float.fromhex(p["correlation_loss_with_log_area_z_hex"])
    r_mainland = float.fromhex(
        p["correlation_loss_with_log_mainland_distance_z_hex"]
    )
    assert r_area < -0.65
    assert r_mainland < -0.45
    assert out["mechanism_claim_authorized"] is False
