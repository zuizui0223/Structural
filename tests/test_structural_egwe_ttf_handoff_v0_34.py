from __future__ import annotations

import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
C=ROOT/"development/structural_egwe_ttf_handoff_contract_v0_34.json"


def load():
    return json.loads(C.read_text())


def test_three_programme_roles_stay_distinct():
    x=load()
    assert set(x["programme_roles"])=={"Structural","EGWE","TTF"}
    assert "within-system" in x["programme_roles"]["Structural"]
    assert "future-state" in x["programme_roles"]["EGWE"]
    assert "out-of-species" in x["programme_roles"]["TTF"]


def test_outcome_favorable_species_selection_is_forbidden():
    x=load()
    assert "never select TTF species because within-species C-minus-R was favorable" in x["anti_leakage"]


def test_ttf_genetic_result_is_not_structural_replication():
    x=load()
    b=x["current_empirical_boundaries"]
    assert b["pooling_forbidden"] is True
    assert "not a replication of Structural connectivity" in b["note"]


def test_handoff_has_distinct_transition_and_predictor_lanes():
    x=load()
    assert set(x["transfer_lanes"])=={"transition_field","typed_connectivity_increment"}
    assert x["transfer_lanes"]["typed_connectivity_increment"]["comparison"]=="T_(R+C) minus T_R"


def test_estimability_precedes_transfer():
    x=load()
    spine=x["methodological_spine"]
    assert spine.index("endpoint-transition estimability") < spine.index("species-disjoint transferability")
