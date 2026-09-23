#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from structural.mechanism_auxiliary_estimability import (  # noqa: E402
    M3,
    M4,
    GeneticPopulation,
    GeneticSourcePair,
    audit_environment_predictor_support,
    audit_genetic_sampling_design,
)
from scripts.validate_mechanism_protocol_v0_1 import (  # noqa: E402
    MechanismProtocolError,
    validate_future_protocol,
)


SCHEMA = "structural.mechanism_auxiliary_gate_result.v0_3"


def _zero_evidence(**extra) -> dict:
    return {
        "schema": SCHEMA,
        **extra,
        "effect_size": None,
        "prediction_score": None,
        "genetic_outcome_opened": False,
        "confirmatory_response_opened": False,
        "predictive_denominator_contribution": 0,
        "mechanism_claim_contribution": 0,
        "confirmatory_response_authorized": False,
    }


def _positive_int(block: dict, key: str) -> int:
    value = block.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{key} must be integer >=1")
    return value


def _validate_extension(protocol: dict) -> dict:
    validate_future_protocol(protocol)
    aux = protocol.get("auxiliary_estimability")
    if not isinstance(aux, dict):
        raise ValueError("auxiliary_estimability must be a JSON object")

    requested = [
        lane
        for lane in protocol["mechanism_lanes_authorized"]
        if lane in {M3, M4}
    ]
    if not requested:
        raise ValueError("auxiliary mechanism gate requires M3 and/or M4")

    settings: dict[str, object] = {"requested": requested}

    if M3 in requested:
        m3 = aux.get(M3)
        if not isinstance(m3, dict):
            raise ValueError("M3 auxiliary estimability block missing")
        if m3.get("genetic_outcomes_accessed") is not False:
            raise ValueError("M3 genetic outcomes must remain unopened")
        if m3.get("sample_selection_used_structural_outcome") is not False:
            raise ValueError(
                "M3 sample selection may not use Structural outcome direction"
            )
        settings[M3] = {
            key: _positive_int(m3, key)
            for key in (
                "minimum_sample_n_focal",
                "minimum_sample_n_source",
                "minimum_eligible_focal_populations",
                "minimum_eligible_source_populations",
                "minimum_focal_blocks",
                "minimum_graph_connected_sources_per_focal",
                "minimum_alternative_sources_per_focal",
            )
        }

    if M4 in requested:
        m4 = aux.get(M4)
        if not isinstance(m4, dict):
            raise ValueError("M4 auxiliary estimability block missing")
        if m4.get("confirmatory_response_accessed") is not False:
            raise ValueError("M4 confirmatory response must remain unopened")
        if m4.get("predictors_selected_after_response") is not False:
            raise ValueError("M4 predictors must be selected before response")
        if m4.get("topology_outcome_used_to_select_predictors") is not False:
            raise ValueError(
                "M4 predictors may not be selected using topology outcome direction"
            )
        if m4.get("environment_predictors_are_non_topological") is not True:
            raise ValueError("M4 enriched predictors must be non-topological")

        fraction = m4.get("minimum_nonmissing_fraction")
        if (
            isinstance(fraction, bool)
            or not isinstance(fraction, (int, float))
            or not (0 < float(fraction) <= 1)
        ):
            raise ValueError("minimum_nonmissing_fraction must be in (0,1]")

        enriched = protocol.get("enriched_environment_predictors_if_M4")
        strong = protocol.get("strong_reference_predictors")
        if not isinstance(enriched, list) or not enriched:
            raise ValueError("M4 enriched predictor list missing")
        if not all(isinstance(x, str) and x.strip() for x in enriched):
            raise ValueError("M4 enriched predictors must be non-empty strings")
        if len(enriched) != len(set(enriched)):
            raise ValueError("M4 enriched predictors contain duplicates")
        if not isinstance(strong, list):
            raise ValueError("strong_reference_predictors must be a list")
        overlap = sorted(set(enriched) & set(strong))
        if overlap:
            raise ValueError(
                "M4 enriched predictors overlap strong reference: "
                + ", ".join(overlap)
            )

        settings[M4] = {
            "predictors": enriched,
            "minimum_nonmissing_fraction": float(fraction),
            **{
                key: _positive_int(m4, key)
                for key in (
                    "minimum_units",
                    "minimum_blocks",
                    "minimum_unique_values",
                    "minimum_complete_rows_per_block",
                    "minimum_blocks_with_complete_rows",
                )
            },
        }

    return settings


def _read_genetic_populations(path: Path) -> list[GeneticPopulation]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = ["population_id", "block", "role", "sample_n"]
        if reader.fieldnames != required:
            raise ValueError(
                "genetic population CSV header must be exactly: "
                + ", ".join(required)
            )
        rows = []
        for row in reader:
            raw_n = (row.get("sample_n") or "").strip()
            try:
                n = int(raw_n)
            except ValueError as exc:
                raise ValueError(f"invalid sample_n: {raw_n!r}") from exc
            rows.append(
                GeneticPopulation(
                    population_id=(row.get("population_id") or "").strip(),
                    block=(row.get("block") or "").strip(),
                    role=(row.get("role") or "").strip(),
                    sample_n=n,
                )
            )
    return rows


def _read_genetic_pairs(path: Path) -> list[GeneticSourcePair]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = [
            "focal_population",
            "source_population",
            "comparison_class",
        ]
        if reader.fieldnames != required:
            raise ValueError(
                "genetic source-pair CSV header must be exactly: "
                + ", ".join(required)
            )
        return [
            GeneticSourcePair(
                focal_population=(row.get("focal_population") or "").strip(),
                source_population=(row.get("source_population") or "").strip(),
                comparison_class=(row.get("comparison_class") or "").strip(),
            )
            for row in reader
        ]


def _parse_float_or_missing(text: str) -> float | None:
    value = text.strip()
    if value in {"", "NA", "NaN", "nan", "None"}:
        return None
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(f"environment value must be numeric/missing: {text!r}") from exc
    return number


def _read_environment(path: Path, predictors: list[str]) -> list[dict[str, object]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = ["unit_id", "block", *predictors]
        if reader.fieldnames != required:
            raise ValueError(
                "environment CSV header must be exactly: " + ", ".join(required)
            )
        rows: list[dict[str, object]] = []
        for row in reader:
            parsed: dict[str, object] = {
                "unit_id": (row.get("unit_id") or "").strip(),
                "block": (row.get("block") or "").strip(),
            }
            for name in predictors:
                parsed[name] = _parse_float_or_missing(row.get(name) or "")
            rows.append(parsed)
        return rows


def run(
    protocol_path: Path,
    *,
    genetic_populations_csv: Path | None = None,
    genetic_pairs_csv: Path | None = None,
    environment_csv: Path | None = None,
) -> tuple[int, dict]:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    try:
        settings = _validate_extension(protocol)
    except (ValueError, MechanismProtocolError) as exc:
        return 1, _zero_evidence(
            status="invalid_or_unqualified_protocol",
            reason=str(exc),
        )

    lane_results: list[dict] = []

    if M3 in settings["requested"]:
        if genetic_populations_csv is None or genetic_pairs_csv is None:
            return 1, _zero_evidence(
                status="invalid_input",
                reason="M3 requires genetic population and source-pair CSVs",
            )
        m3 = settings[M3]
        audit = audit_genetic_sampling_design(
            _read_genetic_populations(genetic_populations_csv),
            _read_genetic_pairs(genetic_pairs_csv),
            **m3,
        )
        lane_results.append({
            "lane": M3,
            "qualified": audit.qualified,
            "reasons": list(audit.reasons),
            "total_populations": audit.total_populations,
            "focal_population_count": audit.focal_population_count,
            "source_population_count": audit.source_population_count,
            "eligible_source_population_count":
                audit.eligible_source_population_count,
            "eligible_focal_population_count":
                audit.eligible_focal_population_count,
            "eligible_focal_blocks": audit.eligible_focal_blocks,
            "focal_audits": [
                {
                    "focal_population": row.focal_population,
                    "block": row.block,
                    "sample_n": row.sample_n,
                    "eligible_graph_connected_sources":
                        row.eligible_graph_connected_sources,
                    "eligible_alternative_sources":
                        row.eligible_alternative_sources,
                    "qualified": row.qualified,
                    "reasons": list(row.reasons),
                }
                for row in audit.focal_audits
            ],
            "genetic_outcome_opened": False,
        })

    if M4 in settings["requested"]:
        if environment_csv is None:
            return 1, _zero_evidence(
                status="invalid_input",
                reason="M4 requires environment predictor CSV",
            )
        m4 = settings[M4]
        audit = audit_environment_predictor_support(
            _read_environment(environment_csv, m4["predictors"]),
            predictors=m4["predictors"],
            minimum_units=m4["minimum_units"],
            minimum_blocks=m4["minimum_blocks"],
            minimum_nonmissing_fraction=m4["minimum_nonmissing_fraction"],
            minimum_unique_values=m4["minimum_unique_values"],
            minimum_complete_rows_per_block=m4[
                "minimum_complete_rows_per_block"
            ],
            minimum_blocks_with_complete_rows=m4[
                "minimum_blocks_with_complete_rows"
            ],
        )
        lane_results.append({
            "lane": M4,
            "qualified": audit.qualified,
            "reasons": list(audit.reasons),
            "total_rows": audit.total_rows,
            "unique_units": audit.unique_units,
            "blocks": audit.blocks,
            "blocks_with_minimum_complete_rows":
                audit.blocks_with_minimum_complete_rows,
            "predictor_audits": [
                {
                    "predictor": row.predictor,
                    "nonmissing_rows": row.nonmissing_rows,
                    "nonmissing_fraction": row.nonmissing_fraction,
                    "unique_values": row.unique_values,
                    "qualified": row.qualified,
                    "reasons": list(row.reasons),
                }
                for row in audit.predictor_audits
            ],
            "confirmatory_response_opened": False,
        })

    qualified = [row["lane"] for row in lane_results if row["qualified"]]
    requested = list(settings["requested"])
    if len(qualified) == len(requested):
        status = "qualified_to_freeze_auxiliary_confirmatory_mechanism_protocols"
        code = 0
    elif qualified:
        status = "partial_auxiliary_mechanism_estimability_only"
        code = 2
    else:
        status = "stop_auxiliary_mechanism_estimability"
        code = 2

    return code, _zero_evidence(
        status=status,
        requested_lanes=requested,
        qualified_lanes=qualified,
        lane_results=lane_results,
        next_action=(
            "freeze_separate_confirmatory_mechanism_protocols_only"
            if code == 0
            else "do_not_open_auxiliary_mechanism_outcomes"
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("protocol", type=Path)
    parser.add_argument("--genetic-populations", type=Path)
    parser.add_argument("--genetic-pairs", type=Path)
    parser.add_argument("--environment", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        code, payload = run(
            args.protocol,
            genetic_populations_csv=args.genetic_populations,
            genetic_pairs_csv=args.genetic_pairs,
            environment_csv=args.environment,
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        code, payload = 1, _zero_evidence(
            status="invalid_input",
            reason=str(exc),
        )

    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
