from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/"development/rmnp_stage1_authorization_v0_25.json"

def test_stage1_is_2021_AMMA_only():
    x=json.loads(A.read_text())
    assert x["status"]=="authorized_once_for_2021_AMMA_lagged_state_only"
    assert x["allowed_access"]["year"]==2021
    assert x["allowed_access"]["columns"]==["date","site_name","perc_surveyed","amma"]
    assert x["forbidden_access"]["years"]==[2022]

def test_na_is_not_negative():
    x=json.loads(A.read_text())
    c=x["endpoint_semantic_clarification"]
    assert c["metadata_values"]["NA"]=="no data"
    assert "AMMA=0" in c["negative"]
    assert c["otherwise"]=="non_estimable"

def test_stage1_pins_protocol_reference_and_worlds():
    x=json.loads(A.read_text())
    locked=x["locked_inputs"]
    assert locked["reference_table_sha256"]=="1680ffd22cb5c524b32be668f9bb1a7e19c8ffacdb9d3ef44c8eebdc7538769c"
    assert locked["movement_worldset_m"]==[500,1000]
    assert locked["source_pool_sites"]==116
    assert locked["evaluation_sites"]==69

def test_stage1_keeps_2022_and_other_taxa_sealed():
    x=json.loads(A.read_text())
    forbidden=set(x["forbidden_access"]["columns"])
    assert {"psma","lisy","amma_stage"} <= forbidden
    assert x["counts_as_pristine_fresh_evidence"] is False
