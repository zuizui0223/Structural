from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/freeze_boreal_19island_spatial_partition_v0_97.py"
GEOMETRY = ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
FREEZE = ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
CONTRACT = ROOT / "development/boreal_19island_spatial_partition_contract_v0_97.json"
LEGACY = ROOT / "development/boreal_lake_islands_spatial_partition_contract_v0_75.json"
WORKFLOW = ROOT / ".github/workflows/boreal-19island-spatial-partition-v0_97.yml"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal19_spatial_v097", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v097_exact_geometry_and_legacy_rule_are_estimable():
    module = load_script()
    result = module.run(
        GEOMETRY,
        freeze=json.loads(FREEZE.read_text(encoding="utf-8")),
        contract=json.loads(CONTRACT.read_text(encoding="utf-8")),
        legacy=json.loads(LEGACY.read_text(encoding="utf-8")),
    )

    assert result["status"] == "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY"
    assert result["selected_quantile"] == "q75"
    assert result["selected_radius_km"] == 7.4
    assert result["candidate_audits"]["q90"]["component_count"] == 7
    assert result["candidate_audits"]["q90"]["meets_minimum_total_blocks"] is False
    assert result["candidate_audits"]["q75"]["component_count"] == 10
    assert result["candidate_audits"]["q75"]["meets_minimum_total_blocks"] is True
    assert result["spatial_block_count"] == 10
    assert result["pilot_block_count"] == 3
    assert result["confirmatory_block_count"] == 7
    assert len(result["pilot_islands"]) + len(result["confirmatory_islands"]) == 19
    assert set(result["pilot_islands"]).isdisjoint(result["confirmatory_islands"])
    assert result["legacy_v075_rule_reused_without_tuning"] is True
    assert result["species_occurrence_used"] is False
    assert result["richness_used"] is False
    assert result["habitat_values_used"] is False
    assert result["counts_as_empirical_evidence"] is False
    assert result["pilot_response_authorized"] is False
    assert result["confirmatory_response_authorized"] is False


def test_v097_contract_reuses_v075_thresholds_and_salt():
    new = json.loads(CONTRACT.read_text(encoding="utf-8"))
    old = json.loads(LEGACY.read_text(encoding="utf-8"))
    assert new["radius_rule"]["candidate_selection_order"] == (
        old["radius_rule"]["candidate_selection_order"]
    )
    for key in (
        "minimum_total_blocks",
        "minimum_pilot_blocks",
        "minimum_confirmatory_blocks",
        "pilot_fraction",
    ):
        assert new["partition_rule"][key] == old["partition_rule"][key]
    assert new["partition_rule"]["ranking_salt"] == "boreal-v0.75-pilot-split"
    assert new["response_independence"]["post_geometry_threshold_tuning_authorized"] is False


def test_v097_workflow_has_no_response_or_secret_dependency():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "DRYAD_" not in text
    assert "beetles_speciesmatrix_presenceabsence.csv" not in text
    assert "freeze_boreal_19island_spatial_partition_v0_97.py" in text
    assert "spatial_receipt.json" in text
