from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"development/rmnp_stage1_result_v0_26.json"

def test_rmnp_stage1_freezes_source_state():
    x=json.loads(R.read_text())
    assert x["source_state"]["source_sites"]==116
    assert x["source_state"]["positive"]==4
    assert x["source_state"]["negative"]==112
    assert x["source_state"]["non_estimable"]==0
    assert x["source_state"]["state_table_sha256"]=="38018b783ebf03a20e08b7fa8adcc2c7a0473100ef7e83ad1e6c92cb2f5a2ca5"

def test_rmnp_stage1_freezes_feature_table_before_target():
    x=json.loads(R.read_text())
    assert x["feature_table"]["rows"]==69
    assert x["feature_table"]["sha256"]=="e45ad76a41126fed7dea2c147c094e2d5998dda548f99ac3efc700c68b900a1c"
    assert x["response_access"]["amma_2022_opened"] is False
    assert x["response_access"]["model_fit_count"]==0

def test_rmnp_occupied_source_connectivity_is_sparse_but_frozen():
    x=json.loads(R.read_text())
    assert x["source_state"]["occupied_source_set_count"]==4
    assert x["connectivity_feature_summary"]["occupied_source_reachability_positive_rows"]==5
    assert x["connectivity_feature_summary"]["movement_worldset_m"]==[500,1000]

def test_rmnp_stage1_evidence_ceiling_remains_context_exposed():
    x=json.loads(R.read_text())
    assert x["evidence_class"]=="focal_response_unseen_system_context_exposed"
    assert x["counts_as_pristine_fresh_evidence"] is False
