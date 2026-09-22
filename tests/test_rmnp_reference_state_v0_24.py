from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/"development/rmnp_reference_state_receipt_v0_24.json"

def test_rmnp_reference_is_response_free():
    x=json.loads(R.read_text())
    assert x["status"]=="pre_response_reference_frozen"
    assert x["response_access"]["amma_2021_opened"] is False
    assert x["response_access"]["amma_2022_opened"] is False
    assert x["response_access"]["model_fit_count"]==0

def test_identifier_normalization_is_exact_and_response_independent():
    x=json.loads(R.read_text())
    assert x["identifier_normalization"]["site_name_rule"]=="strip leading and trailing whitespace only"
    assert x["high_effort_universe"]["common_sites_before_geometry_gate"]==70
    assert x["high_effort_universe"]["evaluation_sites"]==69
    assert x["identifier_normalization"]["other_identifier_repairs_forbidden"] is True

def test_rmnp_reference_and_blocks_are_frozen():
    x=json.loads(R.read_text())
    assert x["derived_reference_table"]["rows"]==116
    assert x["derived_reference_table"]["sha256"]=="1680ffd22cb5c524b32be668f9bb1a7e19c8ffacdb9d3ef44c8eebdc7538769c"
    assert x["spatial_holdout"]["grid_size_m"]==15000
    assert x["spatial_holdout"]["evaluation_block_sizes"]=={
      "28_297":23,"28_298":14,"29_296":6,"29_297":16,"29_298":9,"30_296":1
    }

def test_reference_missingness_is_known_before_response():
    x=json.loads(R.read_text())
    assert x["local_reference"]["missing_counts_source_116"]=={
      "fish_ever_present":0,"site_length_m":4,"site_width_m":5,"max_depth_ordinal":0
    }
    assert x["local_reference"]["missing_counts_evaluation_69"]=={
      "fish_ever_present":0,"site_length_m":2,"site_width_m":2,"max_depth_ordinal":0
    }
