from pathlib import Path
import csv
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/freeze_boreal_birds_topology_nulls_v1_158.py"
CONTRACT = (
    ROOT / "development/boreal_19island_birds_topology_sensitivity_contract_v1_158.json"
)
GEOMETRY = ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
OPERATOR = ROOT / "development/boreal_19island_source_operator_freeze_v1_01.json"


def load_module():
    spec = importlib.util.spec_from_file_location("bird_null_v158", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_keeps_bird_response_sealed_and_ebird_out_of_route():
    contract = json.loads(CONTRACT.read_text())
    assert contract["response_boundary"]["bird_pilot_response_opened"] is False
    assert contract["response_boundary"]["bird_confirmatory_response_opened"] is False
    assert contract["matched_topology_null"]["null_count"] == 20
    assert contract["frozen_geography"]["pilot_source_candidate_count_M"] == 6
    priority = json.loads(
        (ROOT / "development/structural_active_priority_v1_158.json").read_text()
    )
    assert priority["policy_change"]["ebird"] == "DEPRIORITIZED_BY_RESEARCH_DIRECTION"
    assert priority["active_pre_response_route"]["candidate_id"] == (
        "lac_la_ronge_boreal_19island_birds_topology_2026"
    )


def test_real_geometry_produces_twenty_unique_matched_nulls():
    module = load_module()
    contract = json.loads(CONTRACT.read_text())
    operator = json.loads(OPERATOR.read_text())
    freeze, surface = module.freeze(
        contract=contract,
        geometry=module.load_geometry(GEOMETRY),
        operator_freeze=operator,
    )
    assert freeze["status"] == "RESPONSE_INDEPENDENT_TOPOLOGY_NULLS_FROZEN"
    assert freeze["null_count"] == 20
    assert freeze["actual_edge_count"] == 35
    assert freeze["edge_length_bin_counts"] == {
        "1": 7,
        "2": 7,
        "3": 7,
        "4": 7,
        "5": 7,
    }
    signatures = {
        tuple((edge["left"], edge["right"]) for edge in null["edges"])
        for null in freeze["nulls"]
    }
    assert len(signatures) == 20
    assert all(null["accepted_swaps"] == 70 for null in freeze["nulls"])
    assert len(surface) == 13
    assert min(row["H"] for row in surface) > 0.52
    assert max(row["H"] for row in surface) < 2.70
    assert freeze["bird_response_values_opened"] == 0


def test_cli_writes_only_response_free_objects(tmp_path):
    module = load_module()
    out_nulls = tmp_path / "nulls.json"
    out_surface = tmp_path / "surface.csv"
    freeze, surface = module.freeze(
        contract=json.loads(CONTRACT.read_text()),
        geometry=module.load_geometry(GEOMETRY),
        operator_freeze=json.loads(OPERATOR.read_text()),
    )
    out_nulls.write_text(json.dumps(freeze))
    module.write_surface(out_surface, surface)
    assert json.loads(out_nulls.read_text())["bird_response_values_opened"] == 0
    rows = list(csv.DictReader(out_surface.open()))
    assert len(rows) == 13
    assert set(rows[0]) == {
        "Island",
        "M",
        "mu_hex",
        "variance_hex",
        "H_hex",
        "nearest_possible_source_km_hex",
        "furthest_possible_source_km_hex",
    }
