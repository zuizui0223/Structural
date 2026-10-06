from pathlib import Path
import csv
import io
import json
import importlib.util

from structural.boreal_19island_bird_pilot_router import (
    build_boreal_19island_bird_pilot_surface,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "development/boreal_bird_pilot_contract_v1_163.json"
TOPO = ROOT / "development/boreal_19island_topology_sensitivity_freeze_v1_162.json"
SPATIAL = ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
GEOM = ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
FULL = ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
RUNNER = ROOT / "scripts/run_boreal_bird_pilot_v1_163.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("bird163", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_csv():
    spatial = json.loads(SPATIAL.read_text())
    full = json.loads(FULL.read_text())["current_study_island_universe"]["codes"]
    pilot = set(spatial["pilot_islands"])
    species = [f"sp{j:02d}" for j in range(54)]
    # First 15 species qualify with n cycling over 2,3,4,5,6.
    patterns = {}
    pilot_order = sorted(pilot)
    for j in range(15):
        n = 2 + (j % 5)
        patterns[j] = set(pilot_order[:n])

    out = io.StringIO(newline="")
    w = csv.writer(out, lineterminator="\n")
    w.writerow(["Island", *species])
    for island in full:
        row = [island]
        for j in range(54):
            if island in pilot:
                row.append("1" if island in patterns.get(j, set()) else "0")
            else:
                # Deliberately invalid if parsed: proves non-pilot cells stay opaque.
                row.append("NOT_OPENED")
        w.writerow(row)
    return out.getvalue().encode()


def test_contract_freezes_exact_324_cell_pilot_scope():
    x = json.loads(CONTRACT.read_text())
    assert x["semantic_access"]["expected_pilot_occurrence_cells_parsed"] == 324
    assert x["semantic_access"]["required_confirmatory_occurrence_cells_parsed"] == 0
    assert x["semantic_access"]["required_excluded_occurrence_cells_parsed"] == 0
    assert x["response_boundary"]["eBird_enabled"] is False


def test_router_leaves_all_nonpilot_occurrence_bytes_opaque():
    spatial = json.loads(SPATIAL.read_text())
    full = json.loads(FULL.read_text())["current_study_island_universe"]["codes"]
    analysis = json.loads(GEOM.read_text())["island_order"]
    routed = build_boreal_19island_bird_pilot_surface(
        response_csv_bytes=synthetic_csv(),
        full_expected_islands=full,
        analysis_expected_islands=analysis,
        analysis_island_to_block=spatial["island_to_block"],
        pilot_partition=spatial["pilot_block_ids"],
        confirmatory_partition=spatial["confirmatory_block_ids"],
        expected_species_count=54,
    )
    assert routed.pilot_target_values_parsed == 324
    assert routed.confirmatory_target_values_parsed == 0
    assert routed.excluded_target_values_parsed == 0
    assert routed.pilot_species_universe_count == 15


def test_gate_recovers_multiple_n_and_positive_S_variance():
    m = load_runner()
    spatial = json.loads(SPATIAL.read_text())
    full = json.loads(FULL.read_text())["current_study_island_universe"]["codes"]
    analysis = json.loads(GEOM.read_text())["island_order"]
    routed = build_boreal_19island_bird_pilot_surface(
        response_csv_bytes=synthetic_csv(),
        full_expected_islands=full,
        analysis_expected_islands=analysis,
        analysis_island_to_block=spatial["island_to_block"],
        pilot_partition=spatial["pilot_block_ids"],
        confirmatory_partition=spatial["confirmatory_block_ids"],
        expected_species_count=54,
    )
    contract = json.loads(CONTRACT.read_text())
    contract["frozen_confirmatory_islands"] = spatial["confirmatory_islands"]
    snapshot, gate = m.evaluate_gate(
        routed=routed,
        topology=json.loads(TOPO.read_text()),
        contract=contract,
    )
    assert gate["gate_passed"] is True
    assert snapshot["fixed_species_count"] == 15
    assert snapshot["distinct_n_count"] == 5
    assert float.fromhex(snapshot["S_standardization"]["population_sd_hex"]) > 0


def test_pilot_contract_does_not_reopen_beetle_or_enable_ebird():
    x = json.loads(CONTRACT.read_text())
    assert x["response_boundary"]["beetle_response_reopened"] is False
    assert x["response_boundary"]["eBird_enabled"] is False
    assert x["qualified_ceiling"]["bird_confirmatory_response_authorized"] is False
