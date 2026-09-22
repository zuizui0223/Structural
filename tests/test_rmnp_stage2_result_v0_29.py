from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"development/rmnp_stage2_result_v0_29.json"
C=ROOT/"development/connectivity_candidate_registry_v0_29.json"

def test_rmnp_stage2_is_terminal_non_estimable():
    x=json.loads(R.read_text())
    assert x["status"]=="terminal_non_estimable_after_authorized_2022_AMMA_target_open"
    assert x["model_fit_count"]==0
    assert x["estimable_blocks"]==[]
    assert len(x["non_estimable_blocks"])==6
    assert x["primary"]["decision"]=="non_estimable"

def test_rmnp_target_variation_fails_frozen_gate():
    x=json.loads(R.read_text())
    assert x["target_counts_69"]=={"positive":3,"negative":66,"non_estimable":0}
    assert x["applicability"]["joint_target_pos"]==3
    assert x["applicability"]["joint_target_neg"]==66
    assert all(f["train_pos"]<5 for f in x["folds"])

def test_zero_fit_has_no_predictive_direction():
    x=json.loads(R.read_text())
    assert all(x["model_summary"][m]["block_macro_log_loss"] is None for m in ("R0","R1","R2","C"))
    assert x["primary"]["block_macro_log_loss_difference"] is None
    assert x["rerun_with_changed_design_allowed"] is False

def test_registry_has_no_active_empirical_candidate():
    x=json.loads(C.read_text())
    assert x["active_empirical_candidates"]==[]
    assert len(x["closed_empirical_lanes"])==2
    assert x["closed_empirical_lanes"][0]["target_class_collapse"]=="positive_dominant"
    assert x["closed_empirical_lanes"][1]["target_class_collapse"]=="negative_dominant"
