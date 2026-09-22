from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"development/pnw_stage2_result_v0_21.json"
C=ROOT/"development/connectivity_candidate_registry_v0_21.json"

def test_pnw_stage2_is_terminal_non_estimable():
    x=json.loads(R.read_text())
    assert x["status"]=="terminal_non_estimable_after_authorized_2013_target_open"
    assert x["model_fit_count"]==0
    assert x["estimable_regions"]==[]
    assert len(x["non_estimable_regions"])==10
    assert x["primary"]["decision"]=="non_estimable"

def test_target_variation_is_insufficient_under_frozen_gate():
    x=json.loads(R.read_text())
    assert x["target_counts_150"]=={"positive":117,"negative":3,"non_estimable":30}
    assert x["applicability"]["joint_target_pos"]==108
    assert x["applicability"]["joint_target_neg"]==3
    assert all(f["train_neg"]<5 for f in x["folds"])

def test_zero_model_fit_means_no_predictive_direction():
    x=json.loads(R.read_text())
    assert all(x["model_summary"][m]["region_macro_log_loss"] is None for m in ("R0","R1","R2","C"))
    assert x["primary"]["region_macro_log_loss_difference"] is None
    assert x["rerun_with_changed_design_allowed"] is False

def test_candidate_registry_closes_pnw_and_keeps_rmnp_pristine():
    x=json.loads(C.read_text())
    assert x["closed_design_exposed_lane"][0]["candidate_id"]=="usgs_pnw_montane_ponds_2012_2013"
    assert x["closed_design_exposed_lane"][0]["model_fit_count"]==0
    assert x["pristine_fresh_lane"][0]["candidate_id"]=="usgs_rmnp_amphibian_surveys_1986_2022"
