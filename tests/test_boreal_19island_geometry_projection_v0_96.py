from __future__ import annotations

import csv
import hashlib
import io
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/project_boreal_19island_geometry_v0_96.py"
CONTRACT = ROOT / "development/boreal_19island_geometry_projection_contract_v0_96.json"
FREEZE = ROOT / "development/boreal_19island_header_projection_freeze_v0_95.json"
UNIVERSE = ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
WORKFLOW = ROOT / ".github/workflows/boreal-19island-geometry-projection-v0_96.yml"


def load_script():
    spec = importlib.util.spec_from_file_location("boreal19_projection_v096", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_mixed_fixture(tmp_path: Path):
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    universe = json.loads(UNIVERSE.read_text(encoding="utf-8"))
    header = freeze["file"]["header"]
    islands = universe["current_study_island_universe"]["codes"][:19]

    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    for i, island in enumerate(islands):
        row = {name: "SECRET_CLOSED" for name in header}
        row.update({
            "Island": island,
            "Lat": f"{55.0 + i * 0.001:.6f}",
            "Long": f"{-105.0 - i * 0.001:.6f}",
            "beetle.richness": "999",
            "beetle.msom.richness": "998",
            "bird.richness": "997",
            "bird.msom.richness": "996",
            "plant.richness": "995",
        })
        writer.writerow(row)

    raw = out.getvalue().encode("utf-8")
    path = tmp_path / "mixed.csv"
    path.write_bytes(raw)
    return path, hashlib.sha256(raw).hexdigest(), islands, universe


def test_v096_projects_only_frozen_geometry_columns(tmp_path: Path):
    module = load_script()
    path, sha, islands, universe = build_mixed_fixture(tmp_path)
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    contract["target_file"]["expected_sha256"] = sha
    contract["target_file"]["expected_size_bytes"] = path.stat().st_size
    freeze["file"]["sha256"] = sha
    freeze["file"]["size_bytes"] = path.stat().st_size

    geometry, receipt = module.project_geometry(
        path,
        contract=contract,
        freeze=freeze,
        universe_mapping=universe,
    )

    assert receipt["status"] == (
        "SAFE_19_ISLAND_GEOMETRY_PROJECTED_RESPONSE_REMAINS_SEALED"
    )
    assert receipt["row_count"] == 19
    assert receipt["unique_island_count"] == 19
    assert receipt["island_order"] == sorted(islands)
    assert receipt["safe_columns_returned"] == ["Island", "Lat", "Long"]
    assert receipt["protected_response_values_exposed"] is False
    assert receipt["closed_unclassified_values_exposed"] is False
    assert receipt["biological_response_values_opened"] is False
    assert receipt["counts_as_empirical_evidence"] is False

    first = geometry.splitlines()[0]
    assert first == "Island,Lat,Long"
    assert "999" not in geometry
    assert "SECRET_CLOSED" not in geometry
    assert "beetle.richness" not in geometry
    assert "fire.stdev" not in geometry


def test_v096_contract_is_exactly_geometry_only():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert x["projection"]["safe_columns"] == ["Island", "Lat", "Long"]
    assert x["projection"]["expected_row_count"] == 19
    assert x["evidence_boundary"]["protected_response_values_may_be_exposed"] is False
    assert x["evidence_boundary"]["biological_response_values_opened"] is False
    assert x["evidence_boundary"]["counts_as_empirical_evidence"] is False


def test_v096_workflow_removes_raw_and_uploads_only_safe_surface():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "PYTHONPATH: ${{ github.workspace }}/src" in text
    assert "rm -rf build/boreal_v096/raw" in text
    upload = text.split("Upload safe geometry only", 1)[1]
    assert "safe_geometry.csv" in upload
    assert "projection_receipt.json" in upload
    assert "raw/alpha_diversity_model_selection_19islands.csv" not in upload
