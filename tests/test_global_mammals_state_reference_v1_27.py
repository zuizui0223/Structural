from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import pytest

from scripts.freeze_global_mammals_state_reference_v1_27 import (
    GlobalMammalStateError,
    freeze,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "development/global_mammals_state_reference_contract_v1_27.json"


def load_contract():
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def synthetic_rows():
    levels = load_contract()["bioregion_encoding"]["levels_in_frozen_order"]
    safe = []
    part = []
    for i, region in enumerate(levels, start=1):
        # Two rows per realm so every continuous feature has cross-population variation.
        for j in range(2):
            island = str((i - 1) * 2 + j + 1)
            safe.append({
                "ID": island,
                "Longitude_centroid": "0",
                "Latitude_centroid": "0",
                "Area": str(1.0 + i + j),
                "Current_isolation": str(-2.0 + 0.05 * (i + j)),
                "Past_isolation": str((i + j) % 2),
                "Climate_velocity": str(float(i + j)),
                "Temperature_mean": str(5.0 + i + j),
                "Temperature_sd": str(0.5 + 0.1 * (i + j)),
                "Precipitation_mean": str(100.0 + 10 * (i + j)),
                "Precipitation_sd": str(5.0 + i + j),
                "Elevation_sd": str(2.0 + i + j),
                "bioregion": region,
            })
            split = "pilot" if (i + j) % 4 == 0 else "confirmatory"
            part.append({
                "ID": island,
                "bioregion": region,
                "block_id": f"B{island}",
                "split": split,
                "extreme_current_isolation": "0",
            })
    return safe, part


def test_real_contract_preserves_predeclared_reference_ladder():
    x = load_contract()
    assert x["bioregion_encoding"]["reference_level"] == "Afrotropical"
    assert len(x["bioregion_encoding"]["dummy_columns"]) == 11
    assert x["R0"]["continuous_source_columns"] == [
        "Temperature_mean",
        "Temperature_sd",
        "Precipitation_mean",
        "Precipitation_sd",
        "Elevation_sd",
    ]
    assert x["R1_add"]["source_columns"] == [
        "Area",
        "Current_isolation",
        "Past_isolation",
        "Climate_velocity",
    ]
    assert x["R1_add"]["transform_rules"]["Area"].startswith("log10(Area)")
    assert x["validation"]["Past_isolation_domain"] == [0, 1]
    assert x["response_boundary"]["Appendix_1_may_be_reopened"] is False
    assert x["response_boundary"]["fresh_system_denominator_contribution"] == 0


def test_synthetic_state_reference_has_fixed_dummy_and_R0_R1_columns():
    contract = load_contract()
    safe, part = synthetic_rows()
    pilot = sum(row["split"] == "pilot" for row in part)
    confirm = len(part) - pilot
    contract = json.loads(json.dumps(contract))
    contract["validation"]["partition_split_counts"] = {
        "pilot": pilot,
        "confirmatory": confirm,
    }

    receipt, text = freeze(safe, part, contract)
    rows = list(csv.DictReader(io.StringIO(text)))
    assert len(rows) == 24
    assert receipt["R0_feature_columns"] == contract["R0"]["feature_columns_in_order"]
    assert receipt["R1_add_feature_columns"] == (
        contract["R1_add"]["feature_columns_in_order"]
    )
    assert receipt["Past_isolation_domain"] == [0, 1]
    assert receipt["Appendix_1_reopened"] is False
    assert receipt["mammal_occurrence_values_opened"] is False

    first = rows[0]
    # Afrotropical is the fixed reference realm.
    assert first["bioregion"] == "Afrotropical"
    assert all(
        first[column] == "0"
        for column in contract["bioregion_encoding"]["dummy_columns"]
    )

    australian = next(row for row in rows if row["bioregion"] == "Australian")
    assert australian["realm_Australian"] == "1"
    assert sum(
        int(australian[column])
        for column in contract["bioregion_encoding"]["dummy_columns"]
    ) == 1


def test_standardized_continuous_features_are_centered_on_synthetic_population():
    contract = load_contract()
    safe, part = synthetic_rows()
    contract = json.loads(json.dumps(contract))
    contract["validation"]["partition_split_counts"] = {
        "pilot": sum(row["split"] == "pilot" for row in part),
        "confirmatory": sum(row["split"] == "confirmatory" for row in part),
    }
    receipt, text = freeze(safe, part, contract)
    rows = list(csv.DictReader(io.StringIO(text)))
    columns = [
        "z_Temperature_mean",
        "z_Temperature_sd",
        "z_Precipitation_mean",
        "z_Precipitation_sd",
        "z_Elevation_sd",
        "z_log10_Area",
        "z_Current_isolation",
        "z_Climate_velocity",
    ]
    for column in columns:
        values = [float.fromhex(row[column]) for row in rows]
        assert abs(sum(values) / len(values)) < 1e-12


def test_nonbinary_past_isolation_fails_closed():
    contract = load_contract()
    safe, part = synthetic_rows()
    contract = json.loads(json.dumps(contract))
    contract["validation"]["partition_split_counts"] = {
        "pilot": sum(row["split"] == "pilot" for row in part),
        "confirmatory": sum(row["split"] == "confirmatory" for row in part),
    }
    safe[0]["Past_isolation"] = "0.5"
    with pytest.raises(GlobalMammalStateError, match="exact 0/1"):
        freeze(safe, part, contract)
