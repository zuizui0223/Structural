from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/"development/rmnp_amma_temporal_connectivity_protocol_v0_23.json"

def test_rmnp_protocol_is_frozen_before_amma_response():
    x=json.loads(P.read_text())
    assert x["status"]=="frozen_before_any_AMMA_response_open"
    assert x["evidence_class"]=="focal_response_unseen_system_context_exposed"
    assert x["system"]["focal_AMMA_response_direction_seen"] is False

def test_transition_and_pools_are_fixed():
    x=json.loads(P.read_text())
    assert x["transition"]["source_year"]==2021
    assert x["transition"]["target_year"]==2022
    assert x["high_effort_rule"]["source_pool_sites"]==116
    assert x["high_effort_rule"]["evaluation_sites"]==69

def test_movement_worldset_is_external_and_not_tuned():
    x=json.loads(P.read_text())
    assert x["movement_worldset_m"]==[500,1000]
    assert x["movement_worldset_basis"]["tuned_on_RMNP_response"] is False

def test_primary_contrast_and_holdout_are_fixed():
    x=json.loads(P.read_text())
    assert x["reference_ladder"]["primary_contrast"]=="C minus R2"
    assert x["spatial_holdout"]["selected_grid_m"]==15000
    assert x["spatial_holdout"]["selected_block_count"]==6
    assert x["spatial_holdout"]["minimum_applicable_test_rows"]==3

def test_psma_lisy_are_forbidden_and_amma_is_bound():
    x=json.loads(P.read_text())
    assert x["system"]["physical_token"]=="AMMA"
    assert x["system"]["focal_taxon_current_release_identity"]=="Ambystoma mavortium"
    assert x["system"]["psma_status"].startswith("fresh_STOP")
    assert x["system"]["lisy_status"].startswith("fresh_STOP")
