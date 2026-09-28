from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path

from structural.mixed_csv_firewall import header_sha256


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/freeze_boreal_19island_state_reference_v0_98.py"
CONTRACT = ROOT / "development/boreal_19island_state_reference_contract_v0_98.json"
GEOMETRY = ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
THESIS = ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
WORKFLOW = ROOT / ".github/workflows/boreal-19island-state-reference-v0_98.yml"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal19_state_v098", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_protects_biological_columns_and_reuses_frozen_rules():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source = x["habitat_source"]
    assert source["dryad_file_id"] == 4569033
    assert source["expected_sha256"] == (
        "30b296c8243d433b8c4aaa2e934dcb9d57b0f909094ad03cfc645babbab61046"
    )
    assert source["expected_header_sha256"] == (
        "549dd51e1793ee2ea71cff1a3e9fef84b3b44a3b7aa1a7d274e36ef5b2d5822d"
    )
    assert set(source["protected_columns"]) == {
        "plant.richness",
        "insectivore.abund",
        "frugivore.abund",
        "bird.abundance",
        "beetle.catch.rate",
    }
    assert not set(source["protected_columns"]) & set(source["safe_columns"])
    assert x["habitat_reference_rule"]["source_rule"].endswith(
        "boreal_lake_islands_habitat_reference_contract_v0_76.json"
    )
    assert x["response_boundary"]["species_occurrence_used"] is False
    assert x["response_boundary"]["counts_as_empirical_evidence"] is False


def test_external_state_is_population_standardized_over_exact_19():
    module = load_script()
    geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    thesis = json.loads(THESIS.read_text(encoding="utf-8"))
    islands = tuple(geometry["island_order"])
    by_id = {row["island"]: row for row in thesis["rows"]}

    values, constants = module._external_state(islands, by_id)

    assert tuple(values) == (
        "TSF_Z",
        "LOG_AREA_Z",
        "LOG_MAINLAND_DISTANCE_Z",
    )
    for key, vector in values.items():
        assert len(vector) == 19
        assert math.isclose(math.fsum(vector), 0.0, abs_tol=1e-12)
        mean_sq = math.fsum(x * x for x in vector) / 19
        assert math.isclose(mean_sq, 1.0, rel_tol=1e-12, abs_tol=1e-12)
        assert constants[key]["n"] == 19


def test_synthetic_mixed_rda_never_returns_protected_values(
    tmp_path: Path, monkeypatch
):
    module = load_script()
    production = json.loads(CONTRACT.read_text(encoding="utf-8"))
    geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    thesis = json.loads(THESIS.read_text(encoding="utf-8"))
    islands42 = tuple(thesis["current_study_island_universe"]["codes"])

    source = production["habitat_source"]
    header = tuple(
        source["safe_columns"]
        + source["protected_columns"]
        + source["closed_columns"]
    )
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(header)
    for i, island in enumerate(islands42):
        row = []
        for name in header:
            if name == "island":
                row.append(island)
            elif name in source["safe_columns"]:
                row.append(str((i + 1) * (source["safe_columns"].index(name) + 1)))
            elif name in source["protected_columns"]:
                row.append(f"SECRET_PROTECTED_{i}_{name}")
            else:
                row.append(f"CLOSED_{i}_{name}")
        writer.writerow(row)
    raw = out.getvalue()
    path = tmp_path / "RDA_environmental_variables.csv"
    path.write_text(raw, encoding="utf-8")

    contract = json.loads(json.dumps(production))
    contract["habitat_source"]["expected_size_bytes"] = path.stat().st_size
    contract["habitat_source"]["expected_sha256"] = hashlib.sha256(
        path.read_bytes()
    ).hexdigest()
    contract["habitat_source"]["expected_header_sha256"] = header_sha256(header)

    monkeypatch.setattr(module, "_validate_contract", lambda x: None)
    result = module.run(
        path,
        contract=contract,
        geometry_freeze=geometry,
        thesis=thesis,
    )

    assert result["status"] == "STATE_REFERENCE_FROZEN_RESPONSE_INDEPENDENTLY"
    assert result["island_count"] == 19
    assert result["protected_response_values_exposed"] is False
    assert result["species_occurrence_used"] is False
    assert result["counts_as_empirical_evidence"] is False
    serialized = json.dumps(result)
    assert "SECRET_PROTECTED" not in serialized
    assert "CLOSED_" not in serialized
    assert result["habitat"]["eligible_columns"]
    assert result["state_reference"]["R1_add_columns"] == [
        "LOG_AREA_Z",
        "LOG_MAINLAND_DISTANCE_Z",
    ]


def test_workflow_deletes_raw_mixed_files_before_upload():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert 'PYTHONPATH: ${{ github.workspace }}/src' in text
    assert "fetch_boreal_mixed_files_v0_72.py" in text
    assert "freeze_boreal_19island_state_reference_v0_98.py" in text
    assert "rm -rf build/boreal_v098/raw" in text
    upload = text.split("Upload frozen response-independent state bundle", 1)[1]
    assert "build/boreal_v098/raw" not in upload
    assert "state_reference_19.csv" in upload
    assert "state_receipt.json" in upload
