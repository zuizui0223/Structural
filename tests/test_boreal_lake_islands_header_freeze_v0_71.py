from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "development/boreal_lake_islands_header_freeze_contract_v0_71.json"
SCRIPT = ROOT / "scripts/audit_boreal_mixed_headers_v0_71.py"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal_header_audit_v071", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def synthetic_contract(alpha: Path, rda: Path) -> dict:
    return {
        "schema": "structural.boreal_lake_islands_header_freeze_contract.v0_71",
        "candidate_id": "synthetic-boreal-header-test",
        "files": {
            "alpha_diversity_ALL_islands.csv": {
                "expected_size_bytes": alpha.stat().st_size,
                "expected_sha256": sha256(alpha),
                "safe_pre_response_columns": ["Island", "Lat", "Long"],
                "protected_response_columns": ["beetle.richness"],
            },
            "RDA_environmental_variables.csv": {
                "expected_size_bytes": rda.stat().st_size,
                "expected_sha256": sha256(rda),
                "safe_pre_response_columns": ["Island", "Basal.area"],
                "protected_response_columns": ["plant.richness"],
            },
        },
    }


def test_v071_contract_pins_exact_dryad_files_and_keeps_rows_closed():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    alpha = x["files"]["alpha_diversity_ALL_islands.csv"]
    rda = x["files"]["RDA_environmental_variables.csv"]

    assert alpha["dryad_file_id"] == 4569034
    assert alpha["expected_size_bytes"] == 3441
    assert alpha["expected_sha256"] == (
        "f63b37b3c4c9d5453c53b0b565c4bfb7b8485e017f257fbeea663b20cbf6bddf"
    )
    assert rda["dryad_file_id"] == 4569033
    assert rda["expected_size_bytes"] == 8594
    assert rda["expected_sha256"] == (
        "30b296c8243d433b8c4aaa2e934dcb9d57b0f909094ad03cfc645babbab61046"
    )

    assert x["stage_A_header_only"][
        "success_does_not_authorize_safe_row_projection"
    ] is True
    assert x["stage_B_safe_row_projection"]["authorized_now"] is False
    assert x["stage_B_safe_row_projection"][
        "same_run_header_discovery_and_row_projection_forbidden"
    ] is True
    assert x["response_firewall"]["safe_row_values_opened"] is False
    assert x["response_firewall"]["v0_11_intake_authorized"] is False


def test_v071_geometry_and_habitat_scopes_are_conservative():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    alpha = x["files"]["alpha_diversity_ALL_islands.csv"]
    rda = x["files"]["RDA_environmental_variables.csv"]

    assert alpha["projection_after_separate_manifest_freeze"] == [
        "Island", "Lat", "Long"
    ]
    assert "beetle.richness" in alpha["protected_response_columns"]
    assert "buffer_1" in alpha["closed_even_if_present"]
    assert "buffer_10" in alpha["closed_even_if_present"]

    assert rda["projection_after_separate_manifest_freeze"][0] == "Island"
    assert "Basal.area" in rda["safe_pre_response_columns"]
    assert "plant.richness" in rda["protected_response_columns"]
    assert "cwd.dc1" in rda["closed_even_if_present"]


def test_boreal_header_audit_decodes_no_data_rows(tmp_path: Path):
    module = load_script()
    alpha = tmp_path / "alpha.csv"
    rda = tmp_path / "rda.csv"

    alpha.write_bytes(
        b"Island,Lat,Long,beetle.richness,mystery\n"
        + bytes([0xFF, 0xFE])
        + b"\n"
    )
    rda.write_bytes(
        b"Island,Basal.area,plant.richness,other\n"
        + bytes([0xFF, 0xFE])
        + b"\n"
    )
    contract = synthetic_contract(alpha, rda)

    result = module.audit(alpha, rda, contract=contract)

    assert result["status"] == "qualified_to_freeze_header_manifests_only"
    assert result["data_rows_semantically_opened"] == 0
    assert result["safe_row_values_opened"] is False
    assert result["protected_response_values_opened"] is False
    assert result["safe_row_projection_authorized"] is False
    assert result["v0_11_intake_authorized"] is False
    assert result["files"]["alpha_diversity_ALL_islands.csv"][
        "closed_unclassified_columns"
    ] == ["mystery"]
    assert result["files"]["RDA_environmental_variables.csv"][
        "closed_unclassified_columns"
    ] == ["other"]
    assert result["files"]["alpha_diversity_ALL_islands.csv"][
        "candidate_manifest"
    ] is not None


def test_boreal_header_audit_stops_on_missing_protected_column(tmp_path: Path):
    module = load_script()
    alpha = tmp_path / "alpha.csv"
    rda = tmp_path / "rda.csv"

    alpha.write_text("Island,Lat,Long\n", encoding="utf-8")
    rda.write_text("Island,Basal.area,plant.richness\n", encoding="utf-8")
    contract = synthetic_contract(alpha, rda)

    result = module.audit(alpha, rda, contract=contract)

    assert result["status"] == "STOP_header_classification_mismatch"
    assert result["safe_row_projection_authorized"] is False
    a = result["files"]["alpha_diversity_ALL_islands.csv"]
    assert a["missing_protected_columns"] == ["beetle.richness"]
    assert a["candidate_manifest"] is None


def test_boreal_header_audit_stops_on_byte_size_mismatch(tmp_path: Path):
    module = load_script()
    alpha = tmp_path / "alpha.csv"
    rda = tmp_path / "rda.csv"

    alpha.write_text("Island,Lat,Long,beetle.richness\n", encoding="utf-8")
    rda.write_text("Island,Basal.area,plant.richness\n", encoding="utf-8")
    contract = synthetic_contract(alpha, rda)
    contract["files"]["alpha_diversity_ALL_islands.csv"][
        "expected_size_bytes"
    ] += 1

    with pytest.raises(module.BorealHeaderAuditError, match="byte-size mismatch"):
        module.audit(alpha, rda, contract=contract)
