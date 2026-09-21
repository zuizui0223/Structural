from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_davis_schema_v0_7.py"


def load_module():
    spec = importlib.util.spec_from_file_location("davis_schema_audit", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def make_archive(root: Path, *, patch_names=("A", "B"), years=("2020", "2021")) -> Path:
    genetic_header = [
        "Mom_ID", "Year", "Pop", "n_Seeds", "h_Pollen_Pool", "Bootstrap_SE",
        "Outcrossing", "Outcrossing_SE", "Biparental_Inbreeding",
        "Biparental_Inbreeding_SE", "Area_ha", "Percent_Forest", "Elevation",
        "Proportion_High_Mobility", "SE_High_Mobility",
    ]
    rows = []
    for i, (pop, year) in enumerate(zip(patch_names * len(years), years * len(patch_names))):
        rows.append([
            f"M{i}", year, pop, "10", "0.5", "0.1", "0.8", "0.1",
            "0.1", "0.02", "5", "60", "100", "0.4", "0.05",
        ])
    write_csv(root / "nested/Genetic_Data_Master.csv", genetic_header, rows)

    hummingbird_header = [
        "Patch", "Area_ha", "Percent_Forest", "Elevation",
        "Proportion_High_Mobility", "SE_High_Mobility",
    ]
    write_csv(
        root / "nested/Hummingbird_Data.csv",
        hummingbird_header,
        [[p, "5", "60", "100", "0.4", "0.05"] for p in patch_names],
    )

    patch_header = [
        "Pop", "n_Seeds", "Area_ha", "Percent_Forest", "Elevation",
        "Proportion_High_Mobility", "SE_High_Mobility",
    ]
    write_csv(
        root / "nested/Data_Patches.csv",
        patch_header,
        [[p, "20", "5", "60", "100", "0.4", "0.05"] for p in patch_names],
    )

    (root / "nested/whole_landscape_metrics.RData").write_bytes(b"not-read-by-schema-audit")
    (root / "nested/patch_based_metrics.RData").write_bytes(b"not-read-by-schema-audit")
    return root


def test_schema_audit_reports_no_model_or_endpoint_summary(tmp_path: Path):
    module = load_module()
    result = module.audit(make_archive(tmp_path))
    assert result["status"] == "schema_only_no_model_fit"
    assert result["counts_as_fresh_evidence"] is False
    assert result["model_fit_count"] == 0
    assert result["candidate_ranking_count"] == 0
    assert result["endpoint_value_summary_count"] == 0
    assert result["identifier_summary"]["genetic_pop_count"] == 2
    assert result["identifier_summary"]["repeated_year_structure_present"] is True


def test_literal_patch_pop_equality_is_diagnostic_not_semantic_proof(tmp_path: Path):
    module = load_module()
    result = module.audit(make_archive(tmp_path))
    rel = result["literal_patch_pop_relation"]
    assert rel["hummingbird_patch_equals_genetic_pop"] is True
    assert "literal string-set comparison only" in rel["interpretation"]


def test_mismatched_patch_names_are_retained_not_repaired(tmp_path: Path):
    module = load_module()
    root = make_archive(tmp_path, patch_names=("A", "B"))
    hummingbird = root / "nested/Hummingbird_Data.csv"
    write_csv(
        hummingbird,
        ["Patch", "Area_ha", "Percent_Forest", "Elevation",
         "Proportion_High_Mobility", "SE_High_Mobility"],
        [["A", "5", "60", "100", "0.4", "0.05"],
         ["B_ALIAS", "5", "60", "100", "0.4", "0.05"]],
    )
    result = module.audit(root)
    rel = result["literal_patch_pop_relation"]
    assert rel["hummingbird_patch_equals_genetic_pop"] is False
    assert rel["genetic_pop_only"] == ["B"]
    assert rel["hummingbird_patch_only"] == ["B_ALIAS"]


def test_missing_required_header_stops(tmp_path: Path):
    module = load_module()
    root = make_archive(tmp_path)
    path = root / "nested/Genetic_Data_Master.csv"
    header = list(module.EXPECTED_HEADERS["genetic"] - {"h_Pollen_Pool"})
    write_csv(path, header, [])
    with pytest.raises(module.SchemaAuditError, match="required header mismatch"):
        module.audit(root)


def test_duplicate_basename_stops(tmp_path: Path):
    module = load_module()
    root = make_archive(tmp_path)
    duplicate = root / "other/Genetic_Data_Master.csv"
    duplicate.parent.mkdir(parents=True)
    duplicate.write_text("x\n", encoding="utf-8")
    with pytest.raises(module.SchemaAuditError, match="exactly one"):
        module.audit(root)
