from __future__ import annotations

import json
from pathlib import Path

from structural.file_roles import (
    FileRole,
    FileRoleAssignment,
    apply_file_role_firewall,
)

ROOT = Path(__file__).resolve().parents[1]
ROLE_MANIFEST = ROOT / "development/pnw_file_role_manifest_v0_13.json"
RECEIPT = ROOT / "development/pnw_physical_schema_receipt_v0_13.json"


def test_pnw_role_manifest_marks_master_csv_mixed():
    x = json.loads(ROLE_MANIFEST.read_text())
    roles = {row["relative_path"]: row["role"] for row in x["assignments"]}
    assert roles["Ryan_mastersheet.csv"] == "mixed"
    assert roles["Ryan_Logistic_and_Occupancy_Code.R"] == "code"
    assert roles["amphibianOccupancy_fgdc.xml"] == "metadata"


def test_pnw_receipt_advances_only_with_design_exposure_caveat():
    x = json.loads(RECEIPT.read_text())
    assert x["status"] == "advance_to_protocol_freeze_with_design_exposure_caveat"
    assert x["evidence_class"] == "response_unopened_design_exposed"
    assert x["counts_as_pristine_fresh_evidence"] is False
    assert x["physical_schema_gates"]["advance_to_protocol_freeze"] is True
    assert x["safe_column_audit"]["protected_response_values_summarized"] is False
    assert x["safe_column_audit"]["model_fit_count"] == 0


def test_pnw_dynamic_geometry_uses_only_2012_predictor_time_coordinates():
    x = json.loads(RECEIPT.read_text())
    g = x["safe_geometry_summary"]
    assert g["sites_present_both_years"] == 150
    assert g["baseline_geometry_year"] == 2012
    assert g["baseline_missing_coordinate_rows"] == 0
    assert "never use 2013 coordinates" in g["baseline_coordinate_rule"]


def test_file_role_firewall_keeps_mixed_and_code_closed():
    x = json.loads(ROLE_MANIFEST.read_text())
    inventory = {
        "entries": [
            {
                "relative_path": row["relative_path"],
                "sha256": row["sha256"],
            }
            for row in x["assignments"]
        ]
    }
    assignments = tuple(
        FileRoleAssignment(
            row["relative_path"],
            row["sha256"],
            FileRole(row["role"]),
        )
        for row in x["assignments"]
    )
    result = apply_file_role_firewall(inventory, assignments)
    assert "Ryan_mastersheet.csv" in result.mixed_files
    assert "Ryan_mastersheet.csv" in result.denied_for_semantic_open
    assert "Ryan_Logistic_and_Occupancy_Code.R" in result.code_files
