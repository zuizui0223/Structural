from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from structural.file_inventory import inventory_source, to_mapping as inventory_mapping
from structural.safe_schema import (
    SafeSchemaAuditError,
    SafeSchemaRequest,
    audit_safe_schema,
    to_mapping,
)


def role_manifest(inventory: dict, safe_path: str, response_path: str | None = None):
    assignments = []
    for row in inventory["entries"]:
        if row["relative_path"] == safe_path:
            role = "safe_schema"
        elif response_path and row["relative_path"] == response_path:
            role = "response"
        else:
            role = "unknown"
        assignments.append({
            "relative_path": row["relative_path"],
            "sha256": row["sha256"],
            "role": role,
        })
    return {"assignments": assignments}


def test_safe_csv_header_and_id_time_counts(tmp_path: Path):
    (tmp_path / "sites.csv").write_text(
        "site_id,year,lat,long\nA,2020,1,2\nA,2021,1,2\nB,2021,3,4\n",
        encoding="utf-8",
    )
    (tmp_path / "responses.csv").write_text(
        "site_id,year,present\nA,2020,1\n", encoding="utf-8"
    )
    inventory = inventory_mapping(inventory_source(tmp_path))
    roles = role_manifest(inventory, "sites.csv", "responses.csv")

    entries = audit_safe_schema(
        tmp_path,
        inventory,
        roles,
        (SafeSchemaRequest("sites.csv", ("site_id",), ("year",)),),
    )
    payload = to_mapping(entries)
    assert payload["opened_files"] == ["sites.csv"]
    assert payload["entries"][0]["header"] == ["site_id", "year", "lat", "long"]
    assert payload["entries"][0]["row_count"] == 3
    assert payload["entries"][0]["unique_nonblank_counts"] == {
        "site_id": 2,
        "year": 2,
    }
    assert payload["entries"][0]["repeated_time_structure"] is True
    assert payload["response_files_opened"] == 0


def test_response_file_cannot_be_requested(tmp_path: Path):
    (tmp_path / "sites.csv").write_text("site_id\nA\n", encoding="utf-8")
    (tmp_path / "responses.csv").write_text("present\n1\n", encoding="utf-8")
    inventory = inventory_mapping(inventory_source(tmp_path))
    roles = role_manifest(inventory, "sites.csv", "responses.csv")

    with pytest.raises(SafeSchemaAuditError, match="semantic open denied"):
        audit_safe_schema(
            tmp_path,
            inventory,
            roles,
            (SafeSchemaRequest("responses.csv"),),
        )


def test_source_drift_is_detected_before_semantic_open(tmp_path: Path):
    (tmp_path / "sites.csv").write_text("site_id\nA\n", encoding="utf-8")
    inventory = inventory_mapping(inventory_source(tmp_path))
    roles = role_manifest(inventory, "sites.csv")
    (tmp_path / "sites.csv").write_text("site_id\nB\n", encoding="utf-8")

    with pytest.raises(SafeSchemaAuditError, match="does not match frozen"):
        audit_safe_schema(
            tmp_path,
            inventory,
            roles,
            (SafeSchemaRequest("sites.csv", ("site_id",)),),
        )


def test_missing_requested_id_column_stops(tmp_path: Path):
    (tmp_path / "sites.csv").write_text("x\n1\n", encoding="utf-8")
    inventory = inventory_mapping(inventory_source(tmp_path))
    roles = role_manifest(inventory, "sites.csv")

    with pytest.raises(SafeSchemaAuditError, match="missing requested schema columns"):
        audit_safe_schema(
            tmp_path,
            inventory,
            roles,
            (SafeSchemaRequest("sites.csv", ("site_id",)),),
        )


def test_zip_safe_schema_audit(tmp_path: Path):
    archive = tmp_path / "candidate.zip"
    with ZipFile(archive, "w") as z:
        z.writestr("tables/sites.tsv", "site\tyear\nA\t2020\nA\t2021\n")
        z.writestr("tables/response.csv", "present\n1\n")
    inventory = inventory_mapping(inventory_source(archive))
    roles = role_manifest(inventory, "tables/sites.tsv", "tables/response.csv")

    entries = audit_safe_schema(
        archive,
        inventory,
        roles,
        (SafeSchemaRequest("tables/sites.tsv", ("site",), ("year",)),),
    )
    assert entries[0].row_count == 2
    assert dict(entries[0].unique_nonblank_counts) == {"site": 1, "year": 2}
