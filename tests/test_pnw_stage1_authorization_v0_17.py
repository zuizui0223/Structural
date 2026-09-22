from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUTH = ROOT / "development/pnw_stage1_authorization_v0_17.json"


def load():
    return json.loads(AUTH.read_text())


def test_stage1_is_2012_only():
    x=load()
    assert x["status"] == "authorized_once_for_2012_lagged_state_only"
    assert x["allowed_access"]["year"] == "2012 only"
    assert x["forbidden_access"]["years"] == ["2013"]


def test_stage1_taxon_and_worldset_are_locked():
    x=load()
    assert x["locked_inputs"]["species_token"] == "RACA"
    assert x["locked_inputs"]["scale_worldset_m"] == [250,500,1000,1500,5000]


def test_future_target_cannot_change_design():
    x=load()
    banned=x["forbidden_access"]["actions"]
    assert "summarize or inspect 2013 species/obs/survtype values" in banned
    assert "change movement scale worldset" in banned
    assert "change R0/R1/R2/C definitions" in banned


def test_stage1_remains_non_pristine():
    x=load()
    assert x["counts_as_pristine_fresh_evidence"] is False
    assert x["evidence_class"] == "response_unopened_design_exposed"
