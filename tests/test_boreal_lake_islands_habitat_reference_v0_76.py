from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path

import pytest

from structural.boreal_habitat_reference import (
    deterministic_pca,
    population_mean_sd,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/freeze_boreal_habitat_reference_v0_76.py"
CONTRACT = ROOT / "development/boreal_lake_islands_habitat_reference_contract_v0_76.json"
PROJECTION_V074 = ROOT / "development/boreal_lake_islands_safe_projection_contract_v0_74.json"
STATUS = ROOT / "development/current_status_v0_76.json"
PRIORITY = ROOT / "development/structural_active_priority_v0_76.json"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal_habitat_v076", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def habitat_text(islands, columns, matrix):
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["Island", *columns])
    for island, row in zip(islands, matrix):
        writer.writerow([island, *(float(x).hex() for x in row)])
    return out.getvalue()


def projection_receipt(text, columns, matrix):
    constants = {}
    for j, column in enumerate(columns):
        mean, sd = population_mean_sd([row[j] for row in matrix])
        constants[column] = {
            "mean_hex": float(mean).hex(),
            "population_sd_hex": float(sd).hex(),
            "n": len(matrix),
        }
    return {
        "schema": "structural.boreal_lake_islands_safe_projection_result.v0_74",
        "status": "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED",
        "protected_response_values_opened": False,
        "habitat": {
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "eligible_columns": list(columns),
            "standardization_constants": constants,
        },
    }


def synthetic_contract():
    return {
        "candidate_id": "synthetic",
        "pca_rule": {
            "variance_threshold": 0.8,
            "jacobi_tolerance": 1e-14,
            "jacobi_max_iterations": 10000,
        },
    }


def test_population_mean_sd_uses_denominator_n():
    mean, sd = population_mean_sd([1.0, 2.0, 3.0])
    assert mean == 2.0
    assert sd == pytest.approx(math.sqrt(2.0 / 3.0))


def test_perfectly_collinear_two_variable_pca_retains_one_component():
    rows = [
        [1.0, 2.0],
        [2.0, 4.0],
        [3.0, 6.0],
        [4.0, 8.0],
    ]
    pca = deterministic_pca(rows)

    assert pca["retained_component_count"] == 1
    assert pca["eigenvalues"][0] == pytest.approx(2.0, abs=1e-12)
    assert pca["eigenvalues"][1] == pytest.approx(0.0, abs=1e-12)
    assert pca["explained_variance_fraction"][0] == pytest.approx(1.0)
    loading = pca["loadings"][0]
    assert loading[0] > 0
    assert loading[1] > 0
    assert abs(loading[0]) == pytest.approx(2 ** -0.5)
    assert abs(loading[1]) == pytest.approx(2 ** -0.5)


def test_pca_loadings_and_eigenvalues_are_invariant_to_row_order():
    rows = [
        [1.0, 2.0, 5.0],
        [2.0, 1.0, 6.0],
        [3.0, 4.0, 7.0],
        [5.0, 3.0, 9.0],
        [8.0, 7.0, 10.0],
    ]
    a = deterministic_pca(rows)
    b = deterministic_pca(list(reversed(rows)))

    assert [float(x).hex() for x in a["eigenvalues"]] == [
        float(x).hex() for x in b["eigenvalues"]
    ]
    assert [
        [float(x).hex() for x in vector]
        for vector in a["loadings"]
    ] == [
        [float(x).hex() for x in vector]
        for vector in b["loadings"]
    ]
    assert a["retained_component_count"] == b["retained_component_count"]


def test_single_variable_runner_emits_population_z_axis(tmp_path: Path):
    module = load_script()
    islands = ("A", "B", "C")
    columns = ("h1",)
    matrix = [[1.0], [2.0], [4.0]]
    text = habitat_text(islands, columns, matrix)
    path = tmp_path / "safe_habitat.csv"
    path.write_text(text, encoding="utf-8")
    receipt = projection_receipt(text, columns, matrix)

    result = module.run(
        path,
        receipt,
        contract=synthetic_contract(),
        universe=islands,
    )

    assert result["status"] == "HABITAT_REFERENCE_FROZEN_RESPONSE_INDEPENDENTLY"
    assert result["method"]["mode"] == "single_population_z_variable"
    assert result["method"]["retained_component_count"] == 1
    assert result["reference_csv"].splitlines()[0] == "Island,HAB1"
    assert result["species_occurrence_used"] is False
    assert result["richness_used"] is False
    assert result["protected_response_values_opened"] is False
    assert result["counts_as_empirical_evidence"] is False
    assert result["v0_11_intake_authorized"] is False

    rows = list(csv.DictReader(result["reference_csv"].splitlines()))
    scores = [float.fromhex(row["HAB1"]) for row in rows]
    assert sum(scores) / len(scores) == pytest.approx(0.0, abs=1e-15)
    assert math.sqrt(sum(x * x for x in scores) / len(scores)) == pytest.approx(1.0)


def test_two_variable_runner_uses_deterministic_pca(tmp_path: Path):
    module = load_script()
    islands = ("A", "B", "C", "D")
    columns = ("h1", "h2")
    matrix = [
        [1.0, 2.0],
        [2.0, 4.0],
        [3.0, 6.0],
        [4.0, 8.0],
    ]
    text = habitat_text(islands, columns, matrix)
    path = tmp_path / "safe_habitat.csv"
    path.write_text(text, encoding="utf-8")
    receipt = projection_receipt(text, columns, matrix)

    result = module.run(
        path,
        receipt,
        contract=synthetic_contract(),
        universe=islands,
    )

    assert result["method"]["mode"] == "deterministic_population_correlation_pca"
    assert result["method"]["retained_component_count"] == 1
    assert result["reference_csv"].splitlines()[0] == "Island,PC1"
    assert len(result["method"]["eigenvalues_hex"]) == 2
    assert len(result["method"]["loadings_hex"]) == 2
    assert result["reference_sha256"] == hashlib.sha256(
        result["reference_csv"].encode("utf-8")
    ).hexdigest()


def test_projection_constant_mismatch_stops_before_reference(tmp_path: Path):
    module = load_script()
    islands = ("A", "B", "C")
    columns = ("h1",)
    matrix = [[1.0], [2.0], [4.0]]
    text = habitat_text(islands, columns, matrix)
    path = tmp_path / "safe_habitat.csv"
    path.write_text(text, encoding="utf-8")
    receipt = projection_receipt(text, columns, matrix)
    receipt["habitat"]["standardization_constants"]["h1"]["mean_hex"] = (
        float(999).hex()
    )

    with pytest.raises(
        module.BorealHabitatFreezeError,
        match="do not exact-replay",
    ):
        module.run(
            path,
            receipt,
            contract=synthetic_contract(),
            universe=islands,
        )


def test_habitat_sha_mismatch_stops_before_reference(tmp_path: Path):
    module = load_script()
    islands = ("A", "B", "C")
    columns = ("h1",)
    matrix = [[1.0], [2.0], [4.0]]
    text = habitat_text(islands, columns, matrix)
    path = tmp_path / "safe_habitat.csv"
    path.write_text(text, encoding="utf-8")
    receipt = projection_receipt(text, columns, matrix)
    receipt["habitat"]["sha256"] = "0" * 64

    with pytest.raises(
        module.BorealHabitatFreezeError,
        match="habitat SHA mismatch",
    ):
        module.run(
            path,
            receipt,
            contract=synthetic_contract(),
            universe=islands,
        )


def test_real_v076_contract_freezes_pca_before_safe_rows():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert x["standardization"]["method"] == "population z-score"
    assert "math.fsum" in x["standardization"]["summation"]
    assert x["pca_rule"]["eigendecomposition"] == (
        "deterministic symmetric Jacobi rotations"
    )
    assert x["pca_rule"]["jacobi_tolerance"] == 1e-14
    assert x["pca_rule"]["jacobi_max_iterations"] == 10000
    assert x["pca_rule"]["variance_threshold"] == 0.8
    assert "math.fsum" in x["pca_rule"]["correlation_summation"]
    assert x["response_independence"]["species_occurrence_used"] is False
    assert x["response_independence"]["richness_used"] is False
    assert x["response_independence"][
        "protected_response_values_opened"
    ] is False
    assert x["success_ceiling"]["v0_11_intake_authorized"] is False


def test_v076_status_keeps_human_gate_and_denominator_zero():
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    priority = json.loads(PRIORITY.read_text(encoding="utf-8"))

    assert status["fresh_empirical_state"] == {
        "active_candidates": [],
        "confirmatory_eligible_count": 0,
        "live_confirmatory_queue_entries": 0,
    }
    boreal = status["boreal_lake_island_preintake"]
    assert boreal["habitat_reference_runner_frozen"] is True
    assert boreal["stage_A_workflow_executed"] is False
    assert boreal["safe_row_projection_executed"] is False
    assert boreal["spatial_partition_executed"] is False
    assert boreal["habitat_reference_executed"] is False
    assert boreal["biological_response_values_opened"] is False
    assert boreal["v0_11_intake_authorized"] is False
    assert priority["fresh_active_empirical_candidate"] is None
    assert priority["fresh_confirmatory_eligible_count"] == 0


def test_v074_and_v076_share_the_same_stable_population_standardization():
    projection = json.loads(PROJECTION_V074.read_text(encoding="utf-8"))
    habitat = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert "math.fsum" in projection["habitat_gate"][
        "standardization_accumulation"
    ]
    assert "math.fsum" in habitat["standardization"]["summation"]
    assert "denominator n" in projection["habitat_gate"][
        "standardization_accumulation"
    ]
    assert "denominator n" in habitat["standardization"]["sd"]
