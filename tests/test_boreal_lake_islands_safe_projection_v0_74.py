from __future__ import annotations

import csv
import importlib.util
import io
import json
from pathlib import Path

import pytest

from structural.mixed_csv_firewall import header_sha256, sha256_file


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/project_boreal_safe_rows_v0_74.py"
CONTRACT = ROOT / "development/boreal_lake_islands_safe_projection_contract_v0_74.json"
V071 = ROOT / "development/boreal_lake_islands_header_freeze_contract_v0_71.json"
STATUS = ROOT / "development/current_status_v0_74.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_74.json"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal_projection_v074", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def synthetic_setup(tmp_path: Path, *, two_eligible: bool = False):
    alpha = tmp_path / "alpha.csv"
    rda = tmp_path / "rda.csv"

    alpha_header = [
        "Island", "Lat", "Long", "safe.extra", "beetle.richness", "mystery"
    ]
    write_csv(
        alpha,
        alpha_header,
        [
            ["A", "55.1", "-105.1", "x", "DO_NOT_RETURN_A", "closed-a"],
            ["B", "55.2", "-105.2", "y", "DO_NOT_RETURN_B", "closed-b"],
            ["C", "55.3", "-105.3", "z", "DO_NOT_RETURN_C", "closed-c"],
        ],
    )

    rda_header = ["Island", "h1", "h2", "h3", "response", "mystery"]
    h2_b = "2" if two_eligible else ""
    write_csv(
        rda,
        rda_header,
        [
            ["A", "1", "1", "5", "SECRET_A", "closed-a"],
            ["B", "2", h2_b, "5", "SECRET_B", "closed-b"],
            ["C", "4", "3", "5", "SECRET_C", "closed-c"],
        ],
    )

    contract = {
        "schema": "structural.boreal_lake_islands_safe_projection_contract.v0_74",
        "candidate_id": "synthetic",
        "required_manifest_schema": (
            "structural.boreal_lake_islands_header_manifest_freeze.v0_74"
        ),
        "required_manifest_status": "header_manifests_frozen_before_row_projection",
        "projection": {
            "alpha_diversity_ALL_islands.csv": {
                "safe_columns": ["Island", "Lat", "Long"]
            },
            "RDA_environmental_variables.csv": {
                "safe_columns": ["Island", "h1", "h2", "h3"]
            },
        },
    }

    v071 = {
        "files": {
            "alpha_diversity_ALL_islands.csv": {
                "expected_sha256": sha256_file(alpha),
                "safe_pre_response_columns": [
                    "Island", "Lat", "Long", "safe.extra"
                ],
                "protected_response_columns": ["beetle.richness"],
            },
            "RDA_environmental_variables.csv": {
                "expected_sha256": sha256_file(rda),
                "safe_pre_response_columns": ["Island", "h1", "h2", "h3"],
                "protected_response_columns": ["response"],
            },
        }
    }

    freeze = {
        "schema": contract["required_manifest_schema"],
        "status": contract["required_manifest_status"],
        "safe_row_projection_authorized": True,
        "files": {
            "alpha_diversity_ALL_islands.csv": {
                "file_sha256": sha256_file(alpha),
                "header_sha256": header_sha256(tuple(alpha_header)),
                "safe_pre_response_columns": (
                    v071["files"]["alpha_diversity_ALL_islands.csv"][
                        "safe_pre_response_columns"
                    ]
                ),
                "protected_response_columns": ["beetle.richness"],
            },
            "RDA_environmental_variables.csv": {
                "file_sha256": sha256_file(rda),
                "header_sha256": header_sha256(tuple(rda_header)),
                "safe_pre_response_columns": ["Island", "h1", "h2", "h3"],
                "protected_response_columns": ["response"],
            },
        },
    }
    return alpha, rda, contract, v071, freeze


def test_safe_projection_returns_only_geometry_and_eligible_habitat(tmp_path: Path):
    module = load_script()
    alpha, rda, contract, v071, freeze = synthetic_setup(tmp_path)

    result = module.project(
        alpha,
        rda,
        manifest_freeze=freeze,
        contract=contract,
        v071=v071,
        universe=("A", "B", "C"),
    )

    assert result["status"] == "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED"
    assert result["geometry"]["row_count"] == 3
    assert result["geometry"]["unique_island_count"] == 3
    assert result["habitat"]["eligible_columns"] == ["h1"]
    assert result["habitat"]["incomplete_columns"] == ["h2"]
    assert result["habitat"]["zero_variance_columns"] == ["h3"]
    assert result["habitat"]["reference_mode"] == "single_population_z_variable"
    assert result["habitat"]["pca_required"] is False
    assert result["protected_response_values_opened"] is False
    assert result["unclassified_values_returned"] is False
    assert result["counts_as_empirical_evidence"] is False
    assert result["v0_11_intake_authorized"] is False

    geometry = result["geometry_csv"]
    habitat = result["habitat_csv"]
    assert geometry.splitlines()[0] == "Island,Lat,Long"
    assert habitat.splitlines()[0] == "Island,h1"
    joined = geometry + habitat
    assert "DO_NOT_RETURN" not in joined
    assert "SECRET_" not in joined
    assert "closed-" not in joined
    assert "safe.extra" not in joined
    assert "response" not in joined
    assert "mystery" not in joined


def test_two_complete_nonconstant_habitat_columns_require_pca(tmp_path: Path):
    module = load_script()
    alpha, rda, contract, v071, freeze = synthetic_setup(
        tmp_path, two_eligible=True
    )

    result = module.project(
        alpha,
        rda,
        manifest_freeze=freeze,
        contract=contract,
        v071=v071,
        universe=("A", "B", "C"),
    )

    assert result["habitat"]["eligible_columns"] == ["h1", "h2"]
    assert result["habitat"]["zero_variance_columns"] == ["h3"]
    assert result["habitat"]["reference_mode"] == (
        "pca_required_under_frozen_v0_68_rule"
    )
    assert result["habitat"]["pca_required"] is True
    assert result["habitat_csv"].splitlines()[0] == "Island,h1,h2"


def test_manifest_must_be_separately_frozen_and_authorized(tmp_path: Path):
    module = load_script()
    alpha, rda, contract, v071, freeze = synthetic_setup(tmp_path)
    freeze["safe_row_projection_authorized"] = False

    with pytest.raises(
        module.BorealSafeProjectionError,
        match="not authorized",
    ):
        module.project(
            alpha,
            rda,
            manifest_freeze=freeze,
            contract=contract,
            v071=v071,
            universe=("A", "B", "C"),
        )


def test_manifest_header_sha_must_be_frozen_sha256(tmp_path: Path):
    module = load_script()
    alpha, rda, contract, v071, freeze = synthetic_setup(tmp_path)
    freeze["files"]["alpha_diversity_ALL_islands.csv"]["header_sha256"] = "x"

    with pytest.raises(
        module.BorealSafeProjectionError,
        match="header SHA invalid",
    ):
        module.project(
            alpha,
            rda,
            manifest_freeze=freeze,
            contract=contract,
            v071=v071,
            universe=("A", "B", "C"),
        )


def test_geometry_island_set_mismatch_stops(tmp_path: Path):
    module = load_script()
    alpha, rda, contract, v071, freeze = synthetic_setup(tmp_path)

    with pytest.raises(
        module.BorealSafeProjectionError,
        match="island-set mismatch",
    ):
        module.project(
            alpha,
            rda,
            manifest_freeze=freeze,
            contract=contract,
            v071=v071,
            universe=("A", "B", "D"),
        )


def test_invalid_coordinate_stops_before_output(tmp_path: Path):
    module = load_script()
    alpha, rda, contract, v071, freeze = synthetic_setup(tmp_path)

    text = alpha.read_text(encoding="utf-8").replace("55.2", "95.2")
    alpha.write_text(text, encoding="utf-8")
    v071["files"]["alpha_diversity_ALL_islands.csv"]["expected_sha256"] = (
        sha256_file(alpha)
    )
    freeze["files"]["alpha_diversity_ALL_islands.csv"]["file_sha256"] = (
        sha256_file(alpha)
    )

    with pytest.raises(
        module.BorealSafeProjectionError,
        match=r"outside \[-90,90\]",
    ):
        module.project(
            alpha,
            rda,
            manifest_freeze=freeze,
            contract=contract,
            v071=v071,
            universe=("A", "B", "C"),
        )


def test_real_v074_contract_is_strict_subset_of_v071_safe_columns():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    v071 = json.loads(V071.read_text(encoding="utf-8"))

    for name, spec in contract["projection"].items():
        assert set(spec["safe_columns"]) <= set(
            v071["files"][name]["safe_pre_response_columns"]
        )
    assert contract["execution_authorized_now"] is False
    assert contract["response_firewall"][
        "protected_or_unclassified_columns_may_be_returned"
    ] is False
    assert contract["response_firewall"]["counts_as_empirical_evidence"] is False
    assert contract["response_firewall"]["v0_11_intake_authorized"] is False


def test_v074_status_keeps_stage_a_human_gate_and_denominator_zero():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))

    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["stage_B_runner_frozen"] is True
    assert boreal["stage_A_workflow_executed"] is False
    assert boreal["header_manifest_freeze_exists"] is False
    assert boreal["safe_row_projection_executed"] is False
    assert boreal["biological_response_values_opened"] is False
    assert boreal["v0_11_intake_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0
