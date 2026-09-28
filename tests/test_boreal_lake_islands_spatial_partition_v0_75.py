from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path

import pytest

from structural.boreal_spatial_partition import (
    BorealSpatialPartitionError,
    candidate_radii,
    connected_components,
    freeze_spatial_partition,
    haversine_km,
    round_up_tenth_km,
    type7_quantile,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/freeze_boreal_spatial_partition_v0_75.py"
CONTRACT = ROOT / "development/boreal_lake_islands_spatial_partition_contract_v0_75.json"
STATUS = ROOT / "development/current_status_v0_75.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_75.json"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal_spatial_v075", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ten_pair_coordinates(n_pairs: int = 10):
    coords = {}
    for i in range(n_pairs):
        lat = -20.0 + i * 4.0
        coords[f"I{i:02d}A"] = (lat, 0.0)
        coords[f"I{i:02d}B"] = (lat, 0.005)
    return coords


def geometry_text(coords):
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["Island", "Lat", "Long"])
    for island in sorted(coords):
        lat, lon = coords[island]
        writer.writerow([island, float(lat).hex(), float(lon).hex()])
    return out.getvalue()


def test_type7_quantile_and_upward_rounding_are_frozen():
    assert type7_quantile([1.0, 2.0, 3.0, 4.0], 0.25) == pytest.approx(1.75)
    assert type7_quantile([1.0, 2.0, 3.0, 4.0], 0.50) == pytest.approx(2.5)
    assert type7_quantile([1.0, 2.0, 3.0, 4.0], 0.90) == pytest.approx(3.7)
    assert round_up_tenth_km(1.7000001) == 1.8
    assert round_up_tenth_km(1.7) == 1.7


def test_haversine_is_symmetric_and_zero_on_same_point():
    assert haversine_km(55.0, -105.0, 55.0, -105.0) == 0.0
    a = haversine_km(55.0, -105.0, 55.1, -105.2)
    b = haversine_km(55.1, -105.2, 55.0, -105.0)
    assert a == pytest.approx(b)
    assert a > 0


def test_ten_tight_pairs_yield_ten_spatial_components_and_3_7_split():
    coords = ten_pair_coordinates(10)

    result = freeze_spatial_partition(
        coords,
        minimum_total_blocks=9,
        minimum_pilot_blocks=3,
        minimum_confirmatory_blocks=6,
        pilot_fraction=0.20,
        ranking_salt="boreal-v0.75-pilot-split",
    )

    assert result["status"] == "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY"
    assert result["selected_quantile"] == "q90"
    assert result["spatial_block_count"] == 10
    assert result["pilot_block_count"] == 3
    assert result["confirmatory_block_count"] == 7
    assert len(result["pilot_islands"]) == 6
    assert len(result["confirmatory_islands"]) == 14
    assert set(result["pilot_islands"]).isdisjoint(result["confirmatory_islands"])
    assert len(result["island_to_block"]) == 20

    selected = result["selected_radius_km"]
    assert len(connected_components(coords, selected)) == 10


def test_partition_is_invariant_to_input_dictionary_order():
    coords = ten_pair_coordinates(10)
    reverse_coords = dict(reversed(list(coords.items())))

    a = freeze_spatial_partition(coords)
    b = freeze_spatial_partition(reverse_coords)

    for key in (
        "candidate_radii",
        "candidate_audits",
        "selected_quantile",
        "selected_radius_km",
        "blocks",
        "island_to_block",
        "pilot_block_ids",
        "confirmatory_block_ids",
        "pilot_islands",
        "confirmatory_islands",
    ):
        assert a[key] == b[key]


def test_too_few_components_stops_before_partition():
    coords = ten_pair_coordinates(8)

    with pytest.raises(
        BorealSpatialPartitionError,
        match="retains enough spatial blocks",
    ):
        freeze_spatial_partition(
            coords,
            minimum_total_blocks=9,
            minimum_pilot_blocks=3,
            minimum_confirmatory_blocks=6,
        )


def test_candidate_radii_are_response_independent_geometry_only():
    coords = ten_pair_coordinates(10)
    radii = candidate_radii(coords)

    assert tuple(radii) == ("q25", "q50", "q75", "q90")
    assert all(x["rounded_up_km"] >= x["raw_km"] for x in radii.values())
    assert all(x["rounded_up_km"] > 0 for x in radii.values())


def test_cli_run_binds_geometry_sha_and_keeps_v011_closed(tmp_path: Path):
    module = load_script()
    coords = ten_pair_coordinates(10)
    text = geometry_text(coords)
    path = tmp_path / "safe_geometry.csv"
    path.write_text(text, encoding="utf-8")
    sha = hashlib.sha256(text.encode("utf-8")).hexdigest()

    receipt = {
        "schema": "structural.boreal_lake_islands_safe_projection_result.v0_74",
        "status": "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED",
        "protected_response_values_opened": False,
        "geometry": {
            "sha256": sha,
        },
    }
    contract = {
        "candidate_id": "synthetic",
        "partition_rule": {
            "minimum_total_blocks": 9,
            "minimum_pilot_blocks": 3,
            "minimum_confirmatory_blocks": 6,
            "pilot_fraction": 0.20,
        },
    }

    result = module.run(
        path,
        receipt,
        contract=contract,
        universe=tuple(sorted(coords)),
    )

    assert result["spatial_block_count"] == 10
    assert result["pilot_block_count"] == 3
    assert result["confirmatory_block_count"] == 7
    assert result["source_geometry_sha256"] == sha
    assert result["species_occurrence_used"] is False
    assert result["richness_used"] is False
    assert result["habitat_values_used"] is False
    assert result["counts_as_empirical_evidence"] is False
    assert result["v0_11_intake_authorized"] is False
    assert result["pilot_response_authorized"] is False
    assert result["confirmatory_response_authorized"] is False


def test_geometry_sha_mismatch_stops_before_graph(tmp_path: Path):
    module = load_script()
    coords = ten_pair_coordinates(10)
    path = tmp_path / "safe_geometry.csv"
    path.write_text(geometry_text(coords), encoding="utf-8")

    receipt = {
        "schema": "structural.boreal_lake_islands_safe_projection_result.v0_74",
        "status": "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED",
        "protected_response_values_opened": False,
        "geometry": {
            "sha256": "0" * 64,
        },
    }
    contract = {
        "candidate_id": "synthetic",
        "partition_rule": {
            "minimum_total_blocks": 9,
            "minimum_pilot_blocks": 3,
            "minimum_confirmatory_blocks": 6,
            "pilot_fraction": 0.20,
        },
    }

    with pytest.raises(
        module.BorealSpatialFreezeError,
        match="geometry SHA mismatch",
    ):
        module.run(
            path,
            receipt,
            contract=contract,
            universe=tuple(sorted(coords)),
        )


def test_real_v075_contract_freezes_3_plus_6_before_coordinates():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    rule = x["partition_rule"]

    assert x["radius_rule"]["quantiles"] == ["q25", "q50", "q75", "q90"]
    assert x["radius_rule"]["candidate_selection_order"] == [
        "q90", "q75", "q50", "q25"
    ]
    assert rule["minimum_total_blocks"] == 9
    assert rule["minimum_pilot_blocks"] == 3
    assert rule["minimum_confirmatory_blocks"] == 6
    assert rule["pilot_fraction"] == 0.2
    assert x["response_independence"]["species_occurrence_used"] is False
    assert x["response_independence"]["richness_used"] is False
    assert x["response_independence"]["habitat_values_used"] is False
    assert x["success_ceiling"]["v0_11_intake_authorized"] is False
    assert x["success_ceiling"]["counts_as_empirical_evidence"] is False


def test_v075_status_keeps_human_gate_and_denominator_zero():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))

    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["spatial_partition_runner_frozen"] is True
    assert boreal["stage_A_workflow_executed"] is False
    assert boreal["safe_row_projection_executed"] is False
    assert boreal["spatial_partition_executed"] is False
    assert boreal["biological_response_values_opened"] is False
    assert boreal["v0_11_intake_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
