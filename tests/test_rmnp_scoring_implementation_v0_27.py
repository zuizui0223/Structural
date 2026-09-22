from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/rmnp_scoring_implementation_v0_27.json"

def test_rmnp_scoring_primary_contrast_and_model_are_fixed():
    x=json.loads(P.read_text())
    assert x["metrics"]["primary_contrast"]=="C minus R2"
    assert x["model"]["solver"]=="lbfgs"
    assert x["model"]["C"]==1.0
    assert x["model"]["penalty"]=="l2"

def test_rmnp_scoring_preprocessing_is_frozen():
    x=json.loads(P.read_text())
    assert x["preprocessing"]["binary_unstandardized"]==["lagged_state_2021"]
    assert x["preprocessing"]["fish_encoding"]["levels"]==["yes","no","missing"]
    assert "training-fold median" in x["preprocessing"]["numeric_missing"]

def test_rmnp_block_and_class_gates_are_frozen():
    x=json.loads(P.read_text())
    gate=x["fold_estimability"]
    assert gate["minimum_applicable_test_rows"]==3
    assert gate["training_positive_minimum"]==5
    assert gate["training_negative_minimum"]==5
    assert gate["same_applicable_rows_for_all_models"] is True

def test_no_post_target_tuning_allowed():
    x=json.loads(P.read_text())
    assert "change solver after target open" in x["prohibited"]
    assert "drop sparse occupied-connectivity predictors after target open" in x["prohibited"]
