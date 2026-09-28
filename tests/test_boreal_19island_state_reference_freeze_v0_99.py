from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "development/boreal_19island_state_reference_v0_99.csv"
FREEZE = ROOT / "development/boreal_19island_state_reference_freeze_v0_99.json"


def test_v099_state_reference_exact_identity_and_schema():
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    raw = STATE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == freeze["state_reference_sha256"]
    rows = list(csv.DictReader(STATE.read_text(encoding="utf-8").splitlines()))
    assert len(rows) == 19
    assert [row["Island"] for row in rows] == freeze["island_order"]
    assert tuple(rows[0]) == (
        "Island",
        "PC1",
        "PC2",
        "PC3",
        "TSF_Z",
        "LOG_AREA_Z",
        "LOG_MAINLAND_DISTANCE_Z",
    )


def test_v099_preserves_response_independent_ceiling():
    x = json.loads(FREEZE.read_text(encoding="utf-8"))
    assert x["status"] == "STATE_REFERENCE_COMMITTED_RESPONSE_INDEPENDENTLY"
    assert x["habitat"]["eligible_column_count"] == 6
    assert x["habitat"]["incomplete_column_count"] == 0
    assert x["habitat"]["zero_variance_column_count"] == 0
    assert x["habitat"]["retained_component_count"] == 3
    assert x["model_roles"]["R0_columns"] == ["PC1", "PC2", "PC3", "TSF_Z"]
    assert x["model_roles"]["R1_add_columns"] == [
        "LOG_AREA_Z",
        "LOG_MAINLAND_DISTANCE_Z",
    ]
    assert x["response_boundary"]["species_occurrence_used"] is False
    assert x["response_boundary"]["counts_as_empirical_evidence"] is False
    assert x["response_boundary"]["pilot_response_authorized"] is False
    assert x["response_boundary"]["confirmatory_response_authorized"] is False
    assert x["source_operator_may_be_frozen"] is True
