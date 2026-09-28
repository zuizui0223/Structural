#!/usr/bin/env python3
"""Freeze the response-independent boreal local-habitat reference."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path

from structural.boreal_habitat_reference import (
    BorealHabitatReferenceError,
    deterministic_pca,
    population_mean_sd,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_lake_islands_habitat_reference_contract_v0_76.json"
)
DEFAULT_UNIVERSE = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)


class BorealHabitatFreezeError(RuntimeError):
    pass


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_number(text: str) -> float:
    value = str(text).strip()
    if value.lower().startswith(("0x", "+0x", "-0x")):
        number = float.fromhex(value)
    else:
        number = float(value)
    if not math.isfinite(number):
        raise BorealHabitatFreezeError("nonfinite habitat value")
    return number


def load_universe(path: Path = DEFAULT_UNIVERSE) -> tuple[str, ...]:
    x = json.loads(path.read_text(encoding="utf-8"))
    codes = tuple(x["current_study_island_universe"]["codes"])
    if len(codes) != 42 or len(set(codes)) != 42:
        raise BorealHabitatFreezeError("unexpected frozen 42-island universe")
    return codes


def csv_text(header, rows) -> str:
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    return out.getvalue()


def run(
    habitat_csv: Path,
    projection_receipt: dict,
    *,
    contract: dict,
    universe: tuple[str, ...],
) -> dict:
    if projection_receipt.get("schema") != (
        "structural.boreal_lake_islands_safe_projection_result.v0_74"
    ):
        raise BorealHabitatFreezeError("unexpected v0.74 projection receipt")
    if projection_receipt.get("status") != (
        "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED"
    ):
        raise BorealHabitatFreezeError("safe projection did not qualify")
    if projection_receipt.get("protected_response_values_opened") is not False:
        raise BorealHabitatFreezeError("protected response boundary violated")

    habitat_meta = projection_receipt.get("habitat", {})
    expected_sha = habitat_meta.get("sha256")
    eligible = habitat_meta.get("eligible_columns")
    constants = habitat_meta.get("standardization_constants")
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise BorealHabitatFreezeError("habitat SHA missing")
    if not isinstance(eligible, list) or not eligible:
        raise BorealHabitatFreezeError("eligible habitat columns missing")
    if not isinstance(constants, dict):
        raise BorealHabitatFreezeError("habitat constants missing")

    text = habitat_csv.read_text(encoding="utf-8")
    if sha256_text(text) != expected_sha:
        raise BorealHabitatFreezeError("safe habitat SHA mismatch")
    rows = list(csv.DictReader(text.splitlines()))
    expected_header = ("Island", *eligible)
    if not rows or tuple(rows[0].keys()) != expected_header:
        raise BorealHabitatFreezeError("safe habitat schema mismatch")
    if len(rows) != len(universe):
        raise BorealHabitatFreezeError("safe habitat row count mismatch")

    by_id = {}
    for row in rows:
        island = row["Island"].strip()
        if not island or island in by_id:
            raise BorealHabitatFreezeError("blank/duplicate habitat island")
        by_id[island] = row
    if set(by_id) != set(universe):
        raise BorealHabitatFreezeError("safe habitat island-set mismatch")

    matrix = []
    for island in universe:
        matrix.append([
            parse_number(by_id[island][column])
            for column in eligible
        ])

    recomputed = {}
    for j, column in enumerate(eligible):
        mean, sd = population_mean_sd([row[j] for row in matrix])
        recomputed[column] = {
            "mean_hex": float(mean).hex(),
            "population_sd_hex": float(sd).hex(),
            "n": len(matrix),
        }
    if recomputed != constants:
        raise BorealHabitatFreezeError(
            "v0.74 standardization constants do not exact-replay"
        )

    if len(eligible) == 1:
        mean = float.fromhex(constants[eligible[0]]["mean_hex"])
        sd = float.fromhex(constants[eligible[0]]["population_sd_hex"])
        scores = [
            [(row[0] - mean) / sd]
            for row in matrix
        ]
        header = ("Island", "HAB1")
        reference_text = csv_text(
            header,
            [
                (island, float(scores[i][0]).hex())
                for i, island in enumerate(universe)
            ],
        )
        method = {
            "mode": "single_population_z_variable",
            "source_columns": eligible,
            "retained_component_count": 1,
        }
    else:
        pca = deterministic_pca(
            matrix,
            variance_threshold=contract["pca_rule"]["variance_threshold"],
            jacobi_tolerance=contract["pca_rule"]["jacobi_tolerance"],
            jacobi_max_iterations=contract["pca_rule"][
                "jacobi_max_iterations"
            ],
        )
        k = pca["retained_component_count"]
        header = ("Island", *(f"PC{i+1}" for i in range(k)))
        reference_text = csv_text(
            header,
            [
                (
                    island,
                    *(
                        float(value).hex()
                        for value in pca["retained_scores"][i]
                    ),
                )
                for i, island in enumerate(universe)
            ],
        )
        method = {
            "mode": "deterministic_population_correlation_pca",
            "source_columns": eligible,
            "retained_component_count": k,
            "jacobi_iterations": pca["jacobi_iterations"],
            "eigenvalues_hex": [
                float(x).hex() for x in pca["eigenvalues"]
            ],
            "explained_variance_fraction_hex": [
                float(x).hex()
                for x in pca["explained_variance_fraction"]
            ],
            "loadings_hex": [
                [float(x).hex() for x in vector]
                for vector in pca["loadings"]
            ],
        }

    return {
        "schema": "structural.boreal_lake_islands_habitat_reference_result.v0_76",
        "status": "HABITAT_REFERENCE_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": contract["candidate_id"],
        "source_habitat_sha256": expected_sha,
        "eligible_columns": eligible,
        "standardization_constants": recomputed,
        "method": method,
        "reference_csv": reference_text,
        "reference_sha256": sha256_text(reference_text),
        "species_occurrence_used": False,
        "richness_used": False,
        "protected_response_values_opened": False,
        "counts_as_empirical_evidence": False,
        "v0_11_intake_authorized": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "next_action": (
            "combine this frozen habitat reference with a successful v0.75 "
            "spatial partition in a separate preintake completeness gate"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("habitat_csv", type=Path)
    parser.add_argument("projection_receipt", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--output-reference", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = json.loads(args.contract.read_text(encoding="utf-8"))
        if contract.get("schema") != (
            "structural.boreal_lake_islands_habitat_reference_contract.v0_76"
        ):
            raise BorealHabitatFreezeError("unexpected v0.76 contract schema")
        receipt = json.loads(
            args.projection_receipt.read_text(encoding="utf-8")
        )
        result = run(
            args.habitat_csv,
            receipt,
            contract=contract,
            universe=load_universe(),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealHabitatReferenceError,
        BorealHabitatFreezeError,
    ) as exc:
        result = {
            "schema": "structural.boreal_lake_islands_habitat_reference_result.v0_76",
            "status": "STOP",
            "reason": str(exc),
            "counts_as_empirical_evidence": False,
            "v0_11_intake_authorized": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
        }
        code = 2
    else:
        reference_text = result.pop("reference_csv")
        if args.output_reference is not None:
            args.output_reference.parent.mkdir(parents=True, exist_ok=True)
            args.output_reference.write_text(reference_text, encoding="utf-8")
        result["reference_sha256"] = sha256_text(reference_text)
        code = 0

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
