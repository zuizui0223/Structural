from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "development/boreal_19island_source_operator_freeze_v1_01.json"
SCRIPT = ROOT / "scripts/freeze_boreal_19island_dual_isolation_operator_v1_00.py"
GEOMETRY = ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
GEOMETRY_FREEZE = ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
SPATIAL_FREEZE = ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
STATE_FREEZE = ROOT / "development/boreal_19island_state_reference_freeze_v0_99.json"
CONTRACT = ROOT / "development/boreal_19island_dual_isolation_operator_contract_v1_00.json"
LEGACY = ROOT / "development/boreal_dual_isolation_operator_contract_v0_83.json"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal19_operator_v101", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v101_operator_fingerprint_exact_replays_committed_freeze():
    module = load_script()
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))
    operator, receipt = module.freeze(
        GEOMETRY,
        geometry_freeze=json.loads(GEOMETRY_FREEZE.read_text(encoding="utf-8")),
        spatial_freeze=json.loads(SPATIAL_FREEZE.read_text(encoding="utf-8")),
        state_freeze=json.loads(STATE_FREEZE.read_text(encoding="utf-8")),
        contract=json.loads(CONTRACT.read_text(encoding="utf-8")),
        legacy=json.loads(LEGACY.read_text(encoding="utf-8")),
        spatial_freeze_sha256=module._sha256_file(SPATIAL_FREEZE),
        state_freeze_sha256=module._sha256_file(STATE_FREEZE),
    )
    assert receipt["operator_fingerprint"] == frozen["operator_fingerprint"]
    assert operator["selected_k"] == frozen["selected_k"]
    assert receipt["kernel_scale_km_hex"] == frozen["kernel_scale_km_hex"]
    assert receipt["edge_count"] == frozen["edge_count"]
    assert receipt["cross_validation_block_edge_count"] == (
        frozen["cross_validation_block_edge_count"]
    )


def test_v101_response_boundary_and_prepilot_unlock():
    x = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert x["status"] == (
        "SOURCE_OPERATOR_COMMITTED_BY_FINGERPRINT_RESPONSE_INDEPENDENTLY"
    )
    assert x["selected_k"] == 3
    assert x["edge_count"] == 35
    assert x["cross_validation_block_edge_count"] == 21
    assert x["validation_radius_reused"] is False
    assert x["legacy_v083_rule_reused_without_tuning"] is True
    assert x["response_boundary"]["species_occurrence_used_to_build_operator"] is False
    assert x["response_boundary"]["counts_as_empirical_evidence"] is False
    assert x["response_boundary"]["pilot_response_authorized"] is False
    assert x["response_boundary"]["confirmatory_response_authorized"] is False
    assert x["prepilot_intake_may_be_built"] is True
