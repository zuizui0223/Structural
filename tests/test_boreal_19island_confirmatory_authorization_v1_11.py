from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from structural.boreal_19island_confirmatory_router import (
    Boreal19ConfirmatoryRouterError,
    build_boreal_19island_confirmatory_surface,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT / "scripts/authorize_boreal_19island_confirmatory_response_v1_11.py"
)
CONTRACT = (
    ROOT / "development/boreal_19island_confirmatory_authorization_contract_v1_11.json"
)
FREEZE = (
    ROOT / "development/boreal_19island_preconfirmatory_freeze_v1_10.json"
)
PREDICTIONS = (
    ROOT / "development/boreal_19island_confirmatory_predictions_v1_10.csv"
)
MODEL_RECEIPT = (
    ROOT / "development/boreal_19island_preconfirmatory_model_receipt_v1_10.json"
)
PILOT_SNAPSHOT = (
    ROOT / "development/boreal_19island_pilot_training_snapshot_v1_08.json"
)
SPATIAL = (
    ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
)
METADATA = (
    ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
)
FULL = ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"


def load_module():
    spec = importlib.util.spec_from_file_location("boreal19_auth_v111", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_real_v110_bundle_builds_response_sealed_confirmatory_authorization():
    module = load_module()
    result = module.authorize(
        preconfirmatory_freeze=load(FREEZE),
        model_receipt=load(MODEL_RECEIPT),
        predictions_text=PREDICTIONS.read_text(encoding="utf-8"),
        pilot_snapshot=load(PILOT_SNAPSHOT),
        spatial_freeze=load(SPATIAL),
        metadata=load(METADATA),
        full_universe=load(FULL),
        contract=load(CONTRACT),
        preconfirmatory_freeze_sha256=sha(FREEZE),
        model_receipt_sha256=sha(MODEL_RECEIPT),
        predictions_sha256=sha(PREDICTIONS),
    )

    assert result["status"] == (
        "AUTHORIZED_ONE_SHOT_19ISLAND_CONFIRMATORY_RESPONSE"
    )
    assert result["prediction_surface_sha256"] == (
        "26e13914b69faa3a342ce0fc137a1b4b9badeb0f3ff2ec24aa82097780ba5ded"
    )
    assert result["models_fingerprint"] == (
        "2f94fd0ea0eda73013340d417d6827778ebcec97eec7686bdd9ddd59e07790ff"
    )
    assert result["fixed_species_universe_sha256"] == (
        "b223ec140491216a724039cd1eb1e0b5771466c91785d066195a3b90091f66d5"
    )
    assert result["fixed_species_count"] == 99
    assert result["prediction_row_count"] == 1287
    assert len(result["full_source_island_order"]) == 42
    assert len(result["analysis_island_order"]) == 19
    assert len(result["pilot_islands"]) == 6
    assert len(result["confirmatory_islands"]) == 13
    assert len(result["excluded_islands"]) == 23
    assert result["confirmatory_response_authorized"] is True
    assert result["authorization_consumed"] is False
    assert result["response_values_opened_by_authorization"] is False
    assert result["effect_size"] is None
    assert result["prediction_score"] is None
    assert result["predictive_denominator_contribution"] == 0
    assert result["counts_as_empirical_evidence"] is False
    assert len(result["authorization_fingerprint"]) == 64


def test_v111_prediction_tamper_fails_before_authorization():
    module = load_module()
    predictions = PREDICTIONS.read_text(encoding="utf-8")
    tampered = predictions.replace("0x", "0X", 1)
    with pytest.raises(
        module.Boreal19ConfirmatoryAuthorizationError,
        match="committed prediction file SHA drift|prediction surface content SHA drift",
    ):
        module.authorize(
            preconfirmatory_freeze=load(FREEZE),
            model_receipt=load(MODEL_RECEIPT),
            predictions_text=tampered,
            pilot_snapshot=load(PILOT_SNAPSHOT),
            spatial_freeze=load(SPATIAL),
            metadata=load(METADATA),
            full_universe=load(FULL),
            contract=load(CONTRACT),
            preconfirmatory_freeze_sha256=sha(FREEZE),
            model_receipt_sha256=sha(MODEL_RECEIPT),
            predictions_sha256=hashlib.sha256(
                tampered.encode("utf-8")
            ).hexdigest(),
        )


def synthetic_router_world():
    full = tuple(f"I{i:02d}" for i in range(1, 43))
    analysis = full[:19]
    pilot = analysis[:6]
    confirm = analysis[6:]
    pilot_blocks = ("P1", "P2", "P3")
    confirm_blocks = tuple(f"C{i}" for i in range(1, 8))
    mapping = {}
    for i, island in enumerate(pilot):
        mapping[island] = pilot_blocks[i % 3]
    for i, island in enumerate(confirm):
        mapping[island] = confirm_blocks[i % 7]

    fixed = ("sp1", "sp3")
    all_species = ["sp1", "sp2", "sp3"] + [
        f"nf{i:03d}" for i in range(463)
    ]
    assert len(all_species) == 466

    def row(island, *, focal1, focal3, other):
        values = []
        for species in all_species:
            if species == "sp1":
                values.append(focal1)
            elif species == "sp3":
                values.append(focal3)
            else:
                values.append(other)
        return island.encode() + b"," + b",".join(
            value if isinstance(value, bytes) else value.encode()
            for value in values
        ) + b"\n"

    raw = ("Island," + ",".join(all_species) + "\n").encode()
    for island in full:
        if island in confirm:
            # Only sp1/sp3 are valid UTF-8 0/1; all nonfocal cells are invalid
            # bytes so accidental semantic decoding would fail the test.
            raw += row(
                island,
                focal1="1",
                focal3="0",
                other=b"\xff",
            )
        else:
            # Pilot and excluded rows are entirely opaque after Island routing.
            raw += row(
                island,
                focal1=b"\xff",
                focal3=b"\xfe",
                other=b"\xff",
            )
    return (
        raw,
        full,
        analysis,
        mapping,
        pilot_blocks,
        confirm_blocks,
        fixed,
    )


def test_router_opens_only_fixed_species_on_13_confirmatory_islands():
    (
        raw,
        full,
        analysis,
        mapping,
        pilot_blocks,
        confirm_blocks,
        fixed,
    ) = synthetic_router_world()
    routed = build_boreal_19island_confirmatory_surface(
        response_csv_bytes=raw,
        full_expected_islands=full,
        analysis_expected_islands=analysis,
        analysis_island_to_block=mapping,
        pilot_partition=pilot_blocks,
        confirmatory_partition=confirm_blocks,
        fixed_species=fixed,
        expected_species_count=466,
    )

    assert routed.source_response_rows_seen == 42
    assert routed.routing_island_fields_decoded == 42
    assert routed.confirmatory_island_rows_semantically_parsed == 13
    assert routed.confirmatory_target_values_parsed == 26
    assert routed.pilot_target_values_parsed == 0
    assert routed.excluded_target_values_parsed == 0
    assert routed.nonfocal_confirmatory_target_values_parsed == 0
    assert routed.fixed_species_count == 2
    assert routed.confirmatory_island_count == 13
    assert routed.confirmatory_block_count == 7
    assert routed.excluded_island_count == 23
    lines = routed.csv_text.strip().splitlines()
    assert len(lines) == 1 + 26


def test_router_rejects_bad_fixed_confirmatory_value_only_when_opened():
    (
        raw,
        full,
        analysis,
        mapping,
        pilot_blocks,
        confirm_blocks,
        fixed,
    ) = synthetic_router_world()
    # Change a fixed focal cell on the first confirmatory island from 1 to X.
    confirmatory_island = analysis[6].encode()
    needle = confirmatory_island + b",1,"
    assert needle in raw
    bad = raw.replace(needle, confirmatory_island + b",X,", 1)
    with pytest.raises(
        Boreal19ConfirmatoryRouterError,
        match="unexpected confirmatory focal occurrence",
    ):
        build_boreal_19island_confirmatory_surface(
            response_csv_bytes=bad,
            full_expected_islands=full,
            analysis_expected_islands=analysis,
            analysis_island_to_block=mapping,
            pilot_partition=pilot_blocks,
            confirmatory_partition=confirm_blocks,
            fixed_species=fixed,
            expected_species_count=466,
        )
