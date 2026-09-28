from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/freeze_boreal_19island_dual_isolation_operator_v1_00.py"
GEOMETRY = ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
GEOMETRY_FREEZE = ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
SPATIAL_FREEZE = ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
STATE_FREEZE = ROOT / "development/boreal_19island_state_reference_freeze_v0_99.json"
CONTRACT = ROOT / "development/boreal_19island_dual_isolation_operator_contract_v1_00.json"
LEGACY = ROOT / "development/boreal_dual_isolation_operator_contract_v0_83.json"
WORKFLOW = ROOT / ".github/workflows/boreal-19island-source-operator-v1_00.yml"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal19_operator_v100", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v100_exact_replays_spatial_and_freezes_cross_block_source_graph():
    module = load_script()
    spatial = json.loads(SPATIAL_FREEZE.read_text(encoding="utf-8"))
    state = json.loads(STATE_FREEZE.read_text(encoding="utf-8"))
    operator, receipt = module.freeze(
        GEOMETRY,
        geometry_freeze=json.loads(GEOMETRY_FREEZE.read_text(encoding="utf-8")),
        spatial_freeze=spatial,
        state_freeze=state,
        contract=json.loads(CONTRACT.read_text(encoding="utf-8")),
        legacy=json.loads(LEGACY.read_text(encoding="utf-8")),
        spatial_freeze_sha256=module._sha256_file(SPATIAL_FREEZE),
        state_freeze_sha256=module._sha256_file(STATE_FREEZE),
    )

    assert receipt["status"] == (
        "DUAL_ISOLATION_OPERATOR_FROZEN_RESPONSE_INDEPENDENTLY"
    )
    assert operator["selected_k"] >= 1
    assert receipt["selected_k"] == operator["selected_k"]
    assert receipt["edge_count"] == len(operator["edges"])
    assert receipt["cross_validation_block_edge_count"] >= 1
    assert receipt["validation_radius_reused"] is False
    assert receipt["legacy_v083_rule_reused_without_tuning"] is True
    assert receipt["species_occurrence_used_to_build_operator"] is False
    assert receipt["counts_as_empirical_evidence"] is False
    assert receipt["pilot_response_authorized"] is False
    assert receipt["confirmatory_response_authorized"] is False


def test_v100_committed_spatial_freeze_has_estimable_transfer_support():
    x = json.loads(SPATIAL_FREEZE.read_text(encoding="utf-8"))
    assert x["selected_quantile"] == "q75"
    assert x["selected_radius_km"] == 7.4
    assert x["spatial_block_count"] == 10
    assert len(x["pilot_block_ids"]) == 3
    assert len(x["confirmatory_block_ids"]) == 7
    assert len(x["pilot_islands"]) == 6
    assert len(x["confirmatory_islands"]) == 13
    assert set(x["pilot_islands"]).isdisjoint(x["confirmatory_islands"])
    assert len(x["island_to_block"]) == 19


def test_v100_workflow_is_response_independent():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "exact-replay spatial split" in text.lower()
    assert "freeze_boreal_19island_dual_isolation_operator_v1_00.py" in text
    assert "beetles_speciesmatrix_presenceabsence.csv" not in text
    assert "DRYAD" not in text
