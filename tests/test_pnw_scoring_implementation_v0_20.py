from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/pnw_scoring_implementation_v0_20.json"

def test_primary_contrast_and_model_are_fixed():
    x=json.loads(P.read_text())
    assert x["scoring"]["primary_contrast"]=="C minus R2"
    assert x["model"]["solver"]=="lbfgs"
    assert x["model"]["C"]==1.0
    assert x["model"]["penalty"]=="l2"

def test_preprocessing_is_frozen_before_target():
    x=json.loads(P.read_text())
    assert x["preprocessing"]["binary_unstandardized"]==["lagged_state_2012"]
    assert x["preprocessing"]["fish_encoding"]["levels"]==["yes","no","missing"]
    assert "training-fold median" in x["preprocessing"]["numeric_missing"]
    assert "unstandardized" in x["preprocessing"]["numeric_missing_indicator"]

def test_no_post_target_tuning_allowed():
    x=json.loads(P.read_text())
    assert "retune C" in x["prohibited"]
    assert "change solver after seeing 2013 target" in x["prohibited"]
