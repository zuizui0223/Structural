from pathlib import Path
import importlib.util
import json

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/freeze_boreal_19island_topology_sensitivity_v1_162.py"
CONTRACT = ROOT / "development/boreal_bird_topology_sensitivity_contract_v1_162.json"
FREEZE = ROOT / "development/boreal_19island_topology_sensitivity_freeze_v1_162.json"
GEOMETRY = ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
GEOMETRY_FREEZE = ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
SPATIAL = ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
OPERATOR_FREEZE = ROOT / "development/boreal_19island_source_operator_freeze_v1_01.json"


def load_module():
    spec = importlib.util.spec_from_file_location("b162", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_protocol_keeps_bird_confirmatory_response_sealed():
    x = json.loads(CONTRACT.read_text())
    assert x["response_boundary"]["bird_pilot_opened"] is False
    assert x["response_boundary"]["bird_confirmatory_opened"] is False
    assert x["response_boundary"]["eBird_enabled"] is False
    assert x["pilot_gate"]["fixed_species_rule"].startswith(
        "include every bird species present on at least two"
    )
    assert x["primary"]["favourable_direction"] == "negative"
    assert x["claim_boundary"]["cannot_support"][-1] == (
        "reversal or rescue of the completed beetle primary"
    )


def test_response_free_topology_freeze_exactly_replays():
    m = load_module()
    observed = m.freeze(
        geometry_path=GEOMETRY,
        geometry_freeze=m.load_json(GEOMETRY_FREEZE),
        spatial=m.load_json(SPATIAL),
        operator_freeze=m.load_json(OPERATOR_FREEZE),
        contract=m.load_json(CONTRACT),
    )
    expected = json.loads(FREEZE.read_text())
    assert observed == expected


def test_twenty_nulls_are_unique_and_exactly_matched():
    x = json.loads(FREEZE.read_text())
    actual = x["actual_graph"]
    nulls = x["null_ensemble"]
    assert actual["edge_count"] == 35
    assert actual["edge_length_bin_counts"] == [7, 7, 7, 7, 7]
    assert nulls["count"] == 20
    assert nulls["unique_topologies"] == 20
    assert nulls["all_connected"] is True
    assert nulls["degree_sequence_exactly_preserved"] is True
    assert nulls["edge_length_bin_counts_exactly_preserved"] is True
    assert len({row["edge_fingerprint"] for row in nulls["nulls"]}) == 20
    assert all(row["accepted_swaps"] == 80 for row in nulls["nulls"])


def test_configuration_sensitivity_declines_with_n_for_every_target():
    x = json.loads(FREEZE.read_text())
    targets = x["configuration_sensitivity"]["targets"]
    assert len(targets) == 13
    for row in targets.values():
        values = [float.fromhex(row["S_by_n_hex"][str(n)]) for n in range(2, 7)]
        assert all(a >= b for a, b in zip(values, values[1:]))
        assert values[-1] == 0.0


def test_geometry_only_freeze_opens_no_biological_response():
    x = json.loads(FREEZE.read_text())
    assert x["response_boundary"] == {
        "bird_values_read": 0,
        "beetle_values_reopened": 0,
        "plant_values_read": 0,
        "eBird_enabled": False,
        "counts_as_empirical_evidence": False,
    }
