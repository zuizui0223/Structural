from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/"development/rmnp_stage2_authorization_v0_28.json"

def test_stage2_pins_feature_and_scoring_contracts():
    x=json.loads(A.read_text())
    locked=x["locked_inputs"]
    assert locked["feature_table_sha256"]=="e45ad76a41126fed7dea2c147c094e2d5998dda548f99ac3efc700c68b900a1c"
    assert locked["scoring_v0_27_blob_sha"]=="89a1598df87f97cc4fbf87c4739d16305ca7631e"

def test_stage2_is_2022_AMMA_only():
    x=json.loads(A.read_text())
    assert x["allowed_access"]["year"]==2022
    assert x["allowed_access"]["columns"]==["date","site_name","perc_surveyed","amma"]
    assert "PSMA" in " ".join(x["forbidden"]) or "psma" in " ".join(x["forbidden"]).lower()

def test_stage2_applicability_and_gates_are_fixed():
    x=json.loads(A.read_text())
    assert x["applicability"]["require_frozen_69_site_universe"] is True
    assert x["applicability"]["no_other_post_response_filtering"] is True
    assert x["scoring"]["minimum_applicable_test_rows"]==3
    assert x["scoring"]["training_positive_minimum"]==5
    assert x["scoring"]["training_negative_minimum"]==5

def test_stage2_no_rescue():
    x=json.loads(A.read_text())
    assert "rerun under a modified design as confirmation" in x["forbidden"]
    assert x["counts_as_pristine_fresh_evidence"] is False
