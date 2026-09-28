from __future__ import annotations

import csv
import importlib.util
import io
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/freeze_boreal_19island_preconfirmatory_model_v1_09.py"
CONTRACT = ROOT / "development/boreal_19island_preconfirmatory_model_contract_v1_09.json"
PILOT_FREEZE = ROOT / "development/boreal_19island_pilot_freeze_v1_08.json"
PILOT_EXECUTION = ROOT / "development/boreal_19island_pilot_execution_v1_08.json"
PILOT_SNAPSHOT = ROOT / "development/boreal_19island_pilot_training_snapshot_v1_08.json"
STATE = ROOT / "development/boreal_19island_state_reference_v0_99.csv"
STATE_FREEZE = ROOT / "development/boreal_19island_state_reference_freeze_v0_99.json"
GEOMETRY = ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
GEOMETRY_FREEZE = ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
SPATIAL_FREEZE = ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
OPERATOR_FREEZE = ROOT / "development/boreal_19island_source_operator_freeze_v1_01.json"
OPERATOR_CONTRACT = ROOT / "development/boreal_19island_dual_isolation_operator_contract_v1_00.json"
LEGACY_OPERATOR = ROOT / "development/boreal_dual_isolation_operator_contract_v0_83.json"


def load_module():
    spec = importlib.util.spec_from_file_location("boreal19_v109", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_real():
    module = load_module()
    return module, module.freeze(
        pilot_freeze=load(PILOT_FREEZE),
        pilot_execution=load(PILOT_EXECUTION),
        pilot_snapshot=load(PILOT_SNAPSHOT),
        pilot_execution_file_sha256=module.sha256_file(PILOT_EXECUTION),
        pilot_snapshot_file_sha256=module.sha256_file(PILOT_SNAPSHOT),
        state_path=STATE,
        state_freeze_path=STATE_FREEZE,
        state_freeze=load(STATE_FREEZE),
        geometry_path=GEOMETRY,
        geometry_freeze=load(GEOMETRY_FREEZE),
        spatial_freeze_path=SPATIAL_FREEZE,
        spatial_freeze=load(SPATIAL_FREEZE),
        operator_freeze=load(OPERATOR_FREEZE),
        operator_contract=load(OPERATOR_CONTRACT),
        legacy_operator=load(LEGACY_OPERATOR),
        contract=load(CONTRACT),
    )


def test_real_v108_snapshot_freezes_complete_1287_row_prediction_surface():
    _, (receipt, text) = build_real()

    assert receipt["status"] == (
        "CONFIRMATORY_PREDICTIONS_FROZEN_BEFORE_RESPONSE"
    )
    assert receipt["species_count"] == 99
    assert receipt["pilot_island_count"] == 6
    assert receipt["confirmatory_island_count"] == 13
    assert receipt["confirmatory_block_count"] == 7
    assert receipt["training_row_count"] == 594
    assert receipt["prediction_row_count"] == 1287
    assert receipt["pilot_snapshot_fingerprint"] == (
        "c9a1b2760fcc907f24466ff05a883c08336a362159ffb208418ae9f7cf034722"
    )
    assert receipt["pilot_species_universe_sha256"] == (
        "b223ec140491216a724039cd1eb1e0b5771466c91785d066195a3b90091f66d5"
    )
    assert receipt["source_operator_fingerprint"] == (
        "82e1afbd728bd677d4d7b0af65ece16be12a0dc8ae39505bbbac3d5ae151b621"
    )
    assert set(receipt["models"]) == {"R0", "R1", "R2", "R3", "C"}
    assert len(receipt["models_fingerprint"]) == 64
    assert len(receipt["prediction_surface_sha256"]) == 64
    assert receipt["confirmatory_target_values_opened"] == 0
    assert receipt["excluded_target_values_opened"] == 0
    assert receipt["confirmatory_response_authorized"] is False
    assert receipt["effect_size"] is None
    assert receipt["prediction_score"] is None
    assert receipt["predictive_denominator_contribution"] == 0
    assert receipt["counts_as_empirical_evidence"] is False

    rows = list(csv.DictReader(io.StringIO(text)))
    assert len(rows) == 1287
    assert tuple(rows[0]) == (
        "island",
        "block",
        "species",
        "p_R0_hex",
        "p_R1_hex",
        "p_R2_hex",
        "p_R3_hex",
        "p_C_hex",
    )
    spatial = load(SPATIAL_FREEZE)
    pilot = set(spatial["pilot_islands"])
    confirmatory = set(spatial["confirmatory_islands"])
    assert {row["island"] for row in rows} == confirmatory
    assert not ({row["island"] for row in rows} & pilot)
    assert {row["block"] for row in rows} == set(
        spatial["confirmatory_block_ids"]
    )

    counts = {}
    for row in rows:
        counts[row["island"]] = counts.get(row["island"], 0) + 1
        for key in ("p_R0_hex", "p_R1_hex", "p_R2_hex", "p_R3_hex", "p_C_hex"):
            p = float.fromhex(row[key])
            assert 0.0 < p < 1.0
    assert set(counts.values()) == {99}


def test_real_model_freeze_is_deterministic():
    _, (receipt1, text1) = build_real()
    _, (receipt2, text2) = build_real()
    assert text1 == text2
    assert receipt1 == receipt2


def test_pilot_snapshot_tamper_fails_closed():
    module = load_module()
    snapshot = load(PILOT_SNAPSHOT)
    snapshot["targets_hex_by_island"]["DN"] = "0" * len(
        snapshot["targets_hex_by_island"]["DN"]
    )
    with pytest.raises(
        module.Boreal19PreconfirmatoryError,
        match="snapshot fingerprint",
    ):
        module.freeze(
            pilot_freeze=load(PILOT_FREEZE),
            pilot_execution=load(PILOT_EXECUTION),
            pilot_snapshot=snapshot,
            pilot_execution_file_sha256=module.sha256_file(PILOT_EXECUTION),
            pilot_snapshot_file_sha256=module.sha256_file(PILOT_SNAPSHOT),
            state_path=STATE,
            state_freeze_path=STATE_FREEZE,
            state_freeze=load(STATE_FREEZE),
            geometry_path=GEOMETRY,
            geometry_freeze=load(GEOMETRY_FREEZE),
            spatial_freeze_path=SPATIAL_FREEZE,
            spatial_freeze=load(SPATIAL_FREEZE),
            operator_freeze=load(OPERATOR_FREEZE),
            operator_contract=load(OPERATOR_CONTRACT),
            legacy_operator=load(LEGACY_OPERATOR),
            contract=load(CONTRACT),
        )


def test_contract_preserves_primary_v055_scoring_rule():
    contract = load(CONTRACT)
    primary = contract["primary_scoring"]
    assert primary["estimand"].startswith(
        "equal-weight mean across seven confirmatory"
    )
    assert primary["favourable_direction"] == "negative"
    assert primary["bootstrap_replicates"] == 10000
    assert primary["bootstrap_seed"] == 20260928
    assert primary["external_isolation_interaction_required"] is False
    assert primary["secondary_moderator_may_rescue_failed_primary"] is False
