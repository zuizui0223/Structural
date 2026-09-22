from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "development/pnw_temporal_connectivity_protocol_v0_15.json"
COLUMNS = ROOT / "development/pnw_mixed_column_manifest_v0_15.json"


def test_pnw_protocol_is_frozen_before_lagged_state_open():
    x = json.loads(PROTOCOL.read_text())
    assert x["status"] == "frozen_before_lagged_state_open"
    assert x["evidence_class"] == "response_unopened_design_exposed"
    assert x["counts_as_pristine_fresh_evidence"] is False
    assert x["temporal_firewall"]["lagged_state_time"] == "2012"
    assert x["temporal_firewall"]["future_target_time"] == "2013"


def test_scale_worldset_is_fixed_and_not_selected():
    x = json.loads(PROTOCOL.read_text())
    assert x["scale_worldset_m"] == [250, 500, 1000, 1500, 5000]
    assert x["scale_selection"]["tuned_on_dataset"] is False
    assert x["scale_selection"]["winner_selected"] is False


def test_primary_contrast_is_typed_connectivity_beyond_generic_geometry():
    x = json.loads(PROTOCOL.read_text())
    ladder = x["reference_ladder"]
    assert ladder["primary_contrast"] == "C minus R2"
    assert "generic_pond_pressure_mean_across_scale_worldset" in ladder["R2"]
    assert "occupied_source_pressure_mean_across_scale_worldset" in ladder["C"]


def test_future_geometry_and_target_are_sealed():
    x = json.loads(PROTOCOL.read_text())
    assert x["geometry"]["use_2013_geometry"] is False
    assert x["temporal_firewall"]["future_target_may_inform_features"] is False
    assert "use 2013 response to choose source anchors" in x["prohibited"]


def test_column_manifest_separates_safe_stage1_stage2():
    x = json.loads(COLUMNS.read_text())
    assert "species" not in x["safe_pre_response_columns"]
    assert "species" in x["stage1_lagged_state_columns"]
    assert "species" in x["stage2_future_target_columns"]
    assert x["access_rule"].startswith("safe_pre_response")
