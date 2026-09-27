from __future__ import annotations

import json
from pathlib import Path


ROOT=Path(__file__).resolve().parents[1]
STATUS=ROOT/"development/current_status_v0_51.json"
GATE=ROOT/"development/zenodo_318_island_mammals_heldout_scoring_gate_v0_51.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_v051_keeps_heldout_response_sealed():
    s=load(STATUS)
    row=s["mammal_stress_test"]
    assert row["heldout_response_accessed"] is False
    assert row["heldout_response_authorized"] is False
    assert row["model_refit_authorized"] is False
    assert row["counts_as_fresh_confirmation"] is False
    assert s["fresh_empirical_state"]["confirmatory_eligible_count"]==0


def test_scoring_gate_binds_exact_prediction_surface_and_population():
    g=load(GATE)
    assert g["preheldout_artifact"]["heldout_prediction_surface_sha256"]==(
        "a5fe8326172e39ca4cf1d3d7afe9b9bd679076ffc10ec08aaa7c2da2fddeaad9"
    )
    assert g["frozen_scoring_population"]["heldout_islands"]==244
    assert g["frozen_scoring_population"]["fixed_species"]==233
    assert g["frozen_scoring_population"]["expected_scored_rows"]==56852
    assert g["frozen_scoring_population"]["target_domain"]==["0","1"]


def test_bootstrap_and_no_refit_rules_are_frozen():
    g=load(GATE)
    b=g["bootstrap"]
    assert b["unit"]=="Archipielago"
    assert b["expected_cluster_count"]==8
    assert b["replicates"]==10000
    assert b["seed"]==20260927
    assert b["rng"]=="python.random.Random (MT19937)"
    assert b["quantile_method"]=="linear"
    assert g["scoring_implementation"]["model_refit_allowed"] is False
    assert g["heldout_response_authorized"] is False
    assert g["rerun_after_heldout_access_authorized"] is False
