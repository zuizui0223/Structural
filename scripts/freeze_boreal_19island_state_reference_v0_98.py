#!/usr/bin/env python3
"""Build a response-independent R0/R1 state reference for the boreal 19-island system."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from structural.boreal_habitat_reference import (
    BorealHabitatReferenceError,
    deterministic_pca,
    population_mean_sd,
)
from structural.mixed_csv_firewall import (
    MixedCSVColumnManifest,
    MixedCSVFirewallError,
    audit_mixed_csv_header,
    project_safe_columns,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_state_reference_contract_v0_98.json"
)
DEFAULT_GEOMETRY_FREEZE = (
    ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
)
DEFAULT_THESIS = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)


class Boreal19StateError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19StateError(f"{path.name} must contain a JSON object")
    return value


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _csv_text(header: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(list(header))
    writer.writerows(rows)
    return out.getvalue()


def _finite_float(value: object, *, label: str) -> float:
    text = str(value).strip()
    if not text:
        raise Boreal19StateError(f"{label} is missing")
    try:
        out = float(text)
    except ValueError as exc:
        raise Boreal19StateError(f"{label} is not numeric") from exc
    if not math.isfinite(out):
        raise Boreal19StateError(f"{label} is nonfinite")
    return out


def _zscore(values: Sequence[float], *, label: str) -> tuple[list[float], dict]:
    mean, sd = population_mean_sd(values)
    if not math.isfinite(sd) or sd <= 0.0:
        raise Boreal19StateError(f"{label} has zero/nonfinite population SD")
    return (
        [(x - mean) / sd for x in values],
        {
            "mean_hex": float(mean).hex(),
            "population_sd_hex": float(sd).hex(),
            "n": len(values),
        },
    )


def _validate_contract(contract: Mapping) -> None:
    if contract.get("schema") != (
        "structural.boreal_19island_state_reference_contract.v0_98"
    ):
        raise Boreal19StateError("unexpected v0.98 contract schema")
    source = contract["habitat_source"]
    if source.get("dryad_file_id") != 4569033:
        raise Boreal19StateError("RDA file identity drift")
    if source.get("expected_size_bytes") != 8594:
        raise Boreal19StateError("RDA byte-size identity drift")
    if source.get("expected_sha256") != (
        "30b296c8243d433b8c4aaa2e934dcb9d57b0f909094ad03cfc645babbab61046"
    ):
        raise Boreal19StateError("RDA SHA identity drift")
    if source.get("expected_header_sha256") != (
        "549dd51e1793ee2ea71cff1a3e9fef84b3b44a3b7aa1a7d274e36ef5b2d5822d"
    ):
        raise Boreal19StateError("RDA header SHA identity drift")


def _load_universes(
    geometry_freeze: Mapping,
    thesis: Mapping,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, dict]]:
    if geometry_freeze.get("schema") != (
        "structural.boreal_19island_safe_geometry_freeze.v0_97"
    ):
        raise Boreal19StateError("unexpected 19-island geometry freeze schema")
    if geometry_freeze.get("status") != (
        "SAFE_GEOMETRY_COMMITTED_RESPONSE_INDEPENDENTLY"
    ):
        raise Boreal19StateError("19-island geometry freeze did not qualify")
    if geometry_freeze.get("biological_response_values_opened") is not False:
        raise Boreal19StateError("geometry response boundary violated")

    islands19 = tuple(geometry_freeze["island_order"])
    if len(islands19) != 19 or len(set(islands19)) != 19:
        raise Boreal19StateError("unexpected 19-island universe")

    if thesis.get("schema") != (
        "structural.boreal_lake_islands_thesis_safe_table.v0_69"
    ):
        raise Boreal19StateError("unexpected v0.69 thesis-safe schema")
    islands42 = tuple(thesis["current_study_island_universe"]["codes"])
    if len(islands42) != 42 or len(set(islands42)) != 42:
        raise Boreal19StateError("unexpected frozen 42-island universe")
    if not set(islands19) <= set(islands42):
        raise Boreal19StateError("19-island universe is not a subset of frozen 42")

    safe_rows = thesis.get("rows")
    if not isinstance(safe_rows, list) or len(safe_rows) != 42:
        raise Boreal19StateError("unexpected thesis-safe row support")
    by_id: dict[str, dict] = {}
    for row in safe_rows:
        island = str(row.get("island", "")).strip()
        if not island or island in by_id:
            raise Boreal19StateError("blank/duplicate thesis-safe island")
        by_id[island] = dict(row)
    if set(by_id) != set(islands42):
        raise Boreal19StateError("thesis-safe island identity drift")
    return islands19, islands42, by_id


def _project_habitat(
    rda_csv: Path,
    *,
    contract: Mapping,
    islands19: Sequence[str],
    islands42: Sequence[str],
) -> tuple[
    list[str],
    list[str],
    list[str],
    list[list[float]],
    dict[str, dict],
    str,
]:
    source = contract["habitat_source"]
    manifest = MixedCSVColumnManifest(
        file_sha256=source["expected_sha256"],
        header_sha256=source["expected_header_sha256"],
        safe_pre_response_columns=tuple(source["safe_columns"]),
        protected_response_columns=tuple(source["protected_columns"]),
    )
    audit = audit_mixed_csv_header(rda_csv, manifest)
    if set(audit.closed_unclassified_columns) != set(source["closed_columns"]):
        raise Boreal19StateError("RDA closed-column classification drift")

    rows = project_safe_columns(rda_csv, manifest)
    if len(rows) != 42:
        raise Boreal19StateError("RDA safe projection is not 42 rows")

    by_id: dict[str, Mapping[str, str]] = {}
    for row in rows:
        island = str(row.get("island", "")).strip()
        if not island or island in by_id:
            raise Boreal19StateError("blank/duplicate RDA island")
        by_id[island] = row
    if set(by_id) != set(islands42):
        raise Boreal19StateError("RDA island support differs from frozen 42")

    candidate_columns = [
        x for x in source["safe_columns"] if x != "island"
    ]
    eligible: list[str] = []
    incomplete: list[str] = []
    zero_variance: list[str] = []
    raw_by_column: dict[str, list[float]] = {}
    constants: dict[str, dict] = {}

    for column in candidate_columns:
        values: list[float] = []
        complete = True
        for island in islands19:
            raw = str(by_id[island].get(column, "")).strip()
            if not raw:
                complete = False
                break
            try:
                value = float(raw)
            except ValueError:
                complete = False
                break
            if not math.isfinite(value):
                complete = False
                break
            values.append(value)
        if not complete:
            incomplete.append(column)
            continue
        mean, sd = population_mean_sd(values)
        if not math.isfinite(sd) or sd <= 0.0:
            zero_variance.append(column)
            continue
        eligible.append(column)
        raw_by_column[column] = values
        constants[column] = {
            "mean_hex": float(mean).hex(),
            "population_sd_hex": float(sd).hex(),
            "n": len(values),
        }

    if not eligible:
        raise Boreal19StateError(
            "no complete nonconstant habitat variable survives on 19 islands"
        )

    matrix = [
        [raw_by_column[column][i] for column in eligible]
        for i in range(len(islands19))
    ]
    safe_text = _csv_text(
        ("Island", *eligible),
        [
            (
                island,
                *(float(value).hex() for value in matrix[i]),
            )
            for i, island in enumerate(islands19)
        ],
    )
    return (
        eligible,
        incomplete,
        zero_variance,
        matrix,
        constants,
        safe_text,
    )


def _habitat_reference(
    matrix: Sequence[Sequence[float]],
    eligible: Sequence[str],
    islands19: Sequence[str],
    *,
    contract: Mapping,
) -> tuple[list[str], list[list[float]], dict, str]:
    rule = contract["habitat_reference_rule"]
    if len(eligible) == 1:
        values = [float(row[0]) for row in matrix]
        z, constants = _zscore(values, label=str(eligible[0]))
        scores = [[x] for x in z]
        columns = ["HAB1"]
        method = {
            "mode": "single_population_z_variable",
            "source_columns": list(eligible),
            "retained_component_count": 1,
            "standardization": constants,
        }
    else:
        pca = deterministic_pca(
            matrix,
            variance_threshold=float(rule["variance_threshold"]),
            jacobi_tolerance=float(rule["jacobi_tolerance"]),
            jacobi_max_iterations=int(rule["jacobi_max_iterations"]),
        )
        k = int(pca["retained_component_count"])
        columns = [f"PC{i+1}" for i in range(k)]
        scores = [
            [float(x) for x in row]
            for row in pca["retained_scores"]
        ]
        method = {
            "mode": "deterministic_population_correlation_pca",
            "source_columns": list(eligible),
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

    reference_text = _csv_text(
        ("Island", *columns),
        [
            (
                island,
                *(float(x).hex() for x in scores[i]),
            )
            for i, island in enumerate(islands19)
        ],
    )
    return columns, scores, method, reference_text


def _external_state(
    islands19: Sequence[str],
    thesis_by_id: Mapping[str, Mapping],
) -> tuple[dict[str, list[float]], dict[str, dict]]:
    tsf = [
        _finite_float(
            thesis_by_id[island]["tsf_2020_years"],
            label=f"{island}.tsf_2020_years",
        )
        for island in islands19
    ]
    log_area = [
        math.log10(
            _finite_float(
                thesis_by_id[island]["area_ha"],
                label=f"{island}.area_ha",
            ) + 1.0
        )
        for island in islands19
    ]
    log_distance = [
        math.log1p(
            _finite_float(
                thesis_by_id[island]["distance_to_mainland_km"],
                label=f"{island}.distance_to_mainland_km",
            )
        )
        for island in islands19
    ]

    tsf_z, tsf_c = _zscore(tsf, label="TSF")
    area_z, area_c = _zscore(log_area, label="log_area")
    distance_z, distance_c = _zscore(
        log_distance, label="log_mainland_distance"
    )
    return (
        {
            "TSF_Z": tsf_z,
            "LOG_AREA_Z": area_z,
            "LOG_MAINLAND_DISTANCE_Z": distance_z,
        },
        {
            "TSF_Z": tsf_c,
            "LOG_AREA_Z": area_c,
            "LOG_MAINLAND_DISTANCE_Z": distance_c,
        },
    )


def run(
    rda_csv: Path,
    *,
    contract: Mapping,
    geometry_freeze: Mapping,
    thesis: Mapping,
) -> dict:
    _validate_contract(contract)
    if rda_csv.stat().st_size != int(
        contract["habitat_source"]["expected_size_bytes"]
    ):
        raise Boreal19StateError("RDA byte-size mismatch")

    islands19, islands42, thesis_by_id = _load_universes(
        geometry_freeze, thesis
    )
    (
        eligible,
        incomplete,
        zero_variance,
        habitat_matrix,
        habitat_constants,
        safe_habitat_text,
    ) = _project_habitat(
        rda_csv,
        contract=contract,
        islands19=islands19,
        islands42=islands42,
    )
    habitat_columns, habitat_scores, habitat_method, habitat_reference_text = (
        _habitat_reference(
            habitat_matrix,
            eligible,
            islands19,
            contract=contract,
        )
    )
    external, external_constants = _external_state(
        islands19, thesis_by_id
    )

    state_columns = [
        *habitat_columns,
        "TSF_Z",
        "LOG_AREA_Z",
        "LOG_MAINLAND_DISTANCE_Z",
    ]
    state_text = _csv_text(
        ("Island", *state_columns),
        [
            (
                island,
                *(float(x).hex() for x in habitat_scores[i]),
                float(external["TSF_Z"][i]).hex(),
                float(external["LOG_AREA_Z"][i]).hex(),
                float(external["LOG_MAINLAND_DISTANCE_Z"][i]).hex(),
            )
            for i, island in enumerate(islands19)
        ],
    )

    return {
        "schema": "structural.boreal_19island_state_reference_result.v0_98",
        "status": "STATE_REFERENCE_FROZEN_RESPONSE_INDEPENDENTLY",
        "candidate_id": contract["candidate_id"],
        "island_order": list(islands19),
        "island_count": len(islands19),
        "habitat": {
            "eligible_columns": eligible,
            "incomplete_columns": incomplete,
            "zero_variance_columns": zero_variance,
            "standardization_constants": habitat_constants,
            "safe_habitat_sha256": _sha256_text(safe_habitat_text),
            "reference_columns": habitat_columns,
            "reference_method": habitat_method,
            "reference_sha256": _sha256_text(habitat_reference_text),
        },
        "external_state": {
            "columns": [
                "TSF_Z",
                "LOG_AREA_Z",
                "LOG_MAINLAND_DISTANCE_Z",
            ],
            "standardization_constants": external_constants,
            "source": "v0.69 thesis-safe table",
        },
        "state_reference": {
            "columns": state_columns,
            "sha256": _sha256_text(state_text),
            "R0_columns": [*habitat_columns, "TSF_Z"],
            "R1_add_columns": [
                "LOG_AREA_Z",
                "LOG_MAINLAND_DISTANCE_Z",
            ],
        },
        "safe_habitat_csv": safe_habitat_text,
        "habitat_reference_csv": habitat_reference_text,
        "state_reference_csv": state_text,
        "species_occurrence_used": False,
        "richness_values_returned": False,
        "protected_response_values_exposed": False,
        "counts_as_empirical_evidence": False,
        "pilot_response_authorized": False,
        "confirmatory_response_authorized": False,
        "next_action": (
            "commit the exact safe state reference and freeze the 19-island "
            "generic/source-continuity operator before response-sealed intake"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rda_csv", type=Path)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument(
        "--geometry-freeze", type=Path, default=DEFAULT_GEOMETRY_FREEZE
    )
    parser.add_argument("--thesis", type=Path, default=DEFAULT_THESIS)
    parser.add_argument("--safe-habitat-output", type=Path)
    parser.add_argument("--habitat-reference-output", type=Path)
    parser.add_argument("--state-reference-output", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        result = run(
            args.rda_csv,
            contract=_load(args.contract),
            geometry_freeze=_load(args.geometry_freeze),
            thesis=_load(args.thesis),
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        MixedCSVFirewallError,
        BorealHabitatReferenceError,
        Boreal19StateError,
    ) as exc:
        result = {
            "schema": "structural.boreal_19island_state_reference_result.v0_98",
            "status": "STOP",
            "reason": str(exc),
            "species_occurrence_used": False,
            "richness_values_returned": False,
            "protected_response_values_exposed": False,
            "counts_as_empirical_evidence": False,
            "pilot_response_authorized": False,
            "confirmatory_response_authorized": False,
        }
        code = 2
    else:
        safe_text = result.pop("safe_habitat_csv")
        habitat_text = result.pop("habitat_reference_csv")
        state_text = result.pop("state_reference_csv")
        for path, text in (
            (args.safe_habitat_output, safe_text),
            (args.habitat_reference_output, habitat_text),
            (args.state_reference_output, state_text),
        ):
            if path is not None:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8")
        code = 0

    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
