#!/usr/bin/env python3
"""Freeze boreal R0-R3-C models and confirmatory predictions before response."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from scripts.freeze_boreal_spatial_partition_v0_75 import (
    load_geometry,
    load_universe,
)
from structural.boreal_beetle_pilot_router import (
    decode_binary_vector_hex,
)
from structural.boreal_confirmatory_model import (
    BorealConfirmatoryModelError,
    apply_standardization,
    fit_mapping,
    fit_ridge_logistic,
    freeze_standardization,
    logit_jeffreys,
    predict_probability,
)
from structural.boreal_dual_isolation_operator import (
    BorealDualIsolationOperatorError,
    source_features,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_preconfirmatory_model_contract_v0_85.json"
)
DEFAULT_EXTERNAL = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)


class BorealPreconfirmatoryFreezeError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BorealPreconfirmatoryFreezeError(
            f"{path.name} must contain a JSON object"
        )
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_sha256(value: Mapping) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def parse_number(value: object) -> float:
    text = str(value).strip()
    if text.lower().startswith(("0x", "+0x", "-0x")):
        number = float.fromhex(text)
    else:
        number = float(text)
    if not math.isfinite(number):
        raise BorealPreconfirmatoryFreezeError(
            "nonfinite numeric predictor"
        )
    return number


def parse_habitat_reference(
    path: Path,
    receipt: Mapping,
    universe: Sequence[str],
) -> tuple[tuple[str, ...], dict[str, dict[str, float]]]:
    if receipt.get("schema") != (
        "structural.boreal_lake_islands_habitat_reference_result.v0_76"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "unexpected v0.76 habitat receipt"
        )
    if receipt.get("status") != (
        "HABITAT_REFERENCE_FROZEN_RESPONSE_INDEPENDENTLY"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "v0.76 habitat reference did not qualify"
        )
    if receipt.get("candidate_id") != (
        "lac_la_ronge_boreal_island_beetles_2026"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "v0.76 candidate identity mismatch"
        )
    for key in (
        "species_occurrence_used",
        "richness_used",
        "protected_response_values_opened",
        "counts_as_empirical_evidence",
        "pilot_response_authorized",
        "confirmatory_response_authorized",
    ):
        if receipt.get(key) is not False:
            raise BorealPreconfirmatoryFreezeError(
                f"v0.76 boundary violated: {key}"
            )

    text = path.read_text(encoding="utf-8")
    if sha256_text(text) != receipt.get("reference_sha256"):
        raise BorealPreconfirmatoryFreezeError(
            "habitat reference SHA mismatch"
        )
    rows = list(csv.DictReader(text.splitlines()))
    if not rows or not rows[0]:
        raise BorealPreconfirmatoryFreezeError(
            "empty habitat reference"
        )
    fields = tuple(rows[0].keys())
    if not fields or fields[0] != "Island" or len(fields) < 2:
        raise BorealPreconfirmatoryFreezeError(
            "invalid habitat reference schema"
        )
    habitat_columns = fields[1:]

    by_id = {}
    for row in rows:
        island = str(row["Island"]).strip()
        if not island or island in by_id:
            raise BorealPreconfirmatoryFreezeError(
                "blank/duplicate habitat island"
            )
        by_id[island] = {
            column: parse_number(row[column])
            for column in habitat_columns
        }
    if set(by_id) != set(universe):
        raise BorealPreconfirmatoryFreezeError(
            "habitat reference island universe mismatch"
        )
    return habitat_columns, by_id


def parse_external_state(
    external: Mapping,
    universe: Sequence[str],
) -> dict[str, dict[str, float]]:
    if external.get("schema") != (
        "structural.boreal_lake_islands_thesis_safe_table.v0_69"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "unexpected v0.69 external table"
        )
    if external.get("candidate_id") != (
        "lac_la_ronge_boreal_island_beetles_2026"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "v0.69 candidate identity mismatch"
        )
    firewall = external.get("biological_response_firewall", {})
    if firewall.get("beetle_matrix_opened") is not False:
        raise BorealPreconfirmatoryFreezeError(
            "v0.69 response boundary violated"
        )

    by_id = {}
    for row in external.get("rows", []):
        island = str(row["island"])
        if island in by_id:
            raise BorealPreconfirmatoryFreezeError(
                "duplicate v0.69 island"
            )
        area = float(row["area_ha"])
        distance = float(row["distance_to_mainland_km"])
        tsf = float(row["tsf_2020_years"])
        if area < 0 or distance < 0 or tsf < 0:
            raise BorealPreconfirmatoryFreezeError(
                "negative external-state predictor"
            )
        by_id[island] = {
            "tsf_years": tsf,
            "log10_area_plus1": math.log10(area + 1.0),
            "log1p_mainland_distance": math.log1p(distance),
        }
    if set(by_id) != set(universe):
        raise BorealPreconfirmatoryFreezeError(
            "v0.69 island universe mismatch"
        )
    return by_id


def validate_snapshot(
    execution: Mapping,
    snapshot: Mapping,
    *,
    candidate_id: str,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, tuple[int, ...]]]:
    if execution.get("schema") != (
        "structural.boreal_beetle_burned_pilot_execution.v0_84"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "unexpected v0.84 pilot execution schema"
        )
    if execution.get("status") != (
        "QUALIFIED_TO_FREEZE_CONFIRMATORY_PROTOCOL_WITH_MODEL_SNAPSHOT"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "v0.84 pilot did not qualify"
        )
    if execution.get("authorization_consumed") is not True:
        raise BorealPreconfirmatoryFreezeError(
            "v0.84 pilot authorization not consumed"
        )
    if execution.get("confirmatory_target_values_parsed") != 0:
        raise BorealPreconfirmatoryFreezeError(
            "v0.84 confirmatory parse boundary violated"
        )
    if execution.get("confirmatory_response_authorized") is not False:
        raise BorealPreconfirmatoryFreezeError(
            "v0.84 confirmatory ceiling violated"
        )
    if execution.get("model_snapshot_frozen") is not True:
        raise BorealPreconfirmatoryFreezeError(
            "v0.84 model snapshot missing"
        )

    if snapshot.get("schema") != (
        "structural.boreal_beetle_pilot_training_snapshot.v0_84"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "unexpected v0.84 snapshot schema"
        )
    if snapshot.get("status") != (
        "PILOT_TRAINING_SNAPSHOT_FROZEN_FROM_SINGLE_OPEN"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "v0.84 snapshot did not qualify"
        )
    if snapshot.get("candidate_id") != candidate_id:
        raise BorealPreconfirmatoryFreezeError(
            "v0.84 snapshot candidate mismatch"
        )
    if snapshot.get("confirmatory_target_values_parsed") != 0:
        raise BorealPreconfirmatoryFreezeError(
            "snapshot confirmatory parse boundary violated"
        )
    if snapshot.get("confirmatory_occurrence_values_stored") is not False:
        raise BorealPreconfirmatoryFreezeError(
            "snapshot confirmatory storage boundary violated"
        )
    if snapshot.get("qualified_for_confirmatory_model_freeze") is not True:
        raise BorealPreconfirmatoryFreezeError(
            "snapshot not qualified for model freeze"
        )

    expected_fingerprint = execution.get("model_snapshot_fingerprint")
    raw = dict(snapshot)
    observed_fingerprint = raw.pop("snapshot_fingerprint", None)
    recomputed = canonical_sha256(raw)
    if (
        observed_fingerprint != recomputed
        or expected_fingerprint != recomputed
    ):
        raise BorealPreconfirmatoryFreezeError(
            "v0.84 snapshot fingerprint mismatch"
        )

    species = tuple(snapshot.get("pilot_species_universe") or ())
    islands = tuple(snapshot.get("pilot_island_order") or ())
    if not species or len(species) != len(set(species)):
        raise BorealPreconfirmatoryFreezeError(
            "invalid fixed species universe"
        )
    if not islands or len(islands) != len(set(islands)):
        raise BorealPreconfirmatoryFreezeError(
            "invalid pilot island order"
        )
    if snapshot.get("target_bit_count") != len(species):
        raise BorealPreconfirmatoryFreezeError(
            "snapshot target bit count mismatch"
        )

    encoded = snapshot.get("targets_hex_by_island")
    if not isinstance(encoded, dict) or tuple(encoded) != islands:
        raise BorealPreconfirmatoryFreezeError(
            "snapshot target island order mismatch"
        )
    matrix = {
        island: decode_binary_vector_hex(encoded[island], len(species))
        for island in islands
    }
    return species, islands, matrix


def validate_operator(
    operator: Mapping,
    receipt: Mapping,
    *,
    candidate_id: str,
    universe: Sequence[str],
) -> None:
    if receipt.get("schema") != (
        "structural.boreal_dual_isolation_operator_result.v0_83"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "unexpected v0.83 operator receipt"
        )
    if receipt.get("status") != (
        "DUAL_ISOLATION_OPERATOR_FROZEN_RESPONSE_INDEPENDENTLY"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "v0.83 operator did not qualify"
        )
    if receipt.get("candidate_id") != candidate_id:
        raise BorealPreconfirmatoryFreezeError(
            "v0.83 candidate mismatch"
        )
    if receipt.get("confirmatory_response_used_to_build_operator") is not False:
        raise BorealPreconfirmatoryFreezeError(
            "v0.83 confirmatory response boundary violated"
        )
    if receipt.get("cross_v075_block_edge_count", 0) < 1:
        raise BorealPreconfirmatoryFreezeError(
            "v0.83 source graph lacks cross-block support"
        )
    if receipt.get("operator_fingerprint") != canonical_sha256(operator):
        raise BorealPreconfirmatoryFreezeError(
            "v0.83 operator fingerprint mismatch"
        )
    if tuple(operator.get("island_order") or ()) != tuple(sorted(universe)):
        raise BorealPreconfirmatoryFreezeError(
            "v0.83 operator island universe mismatch"
        )


def _base_rows(
    *,
    universe: Sequence[str],
    habitat_columns: Sequence[str],
    habitat: Mapping[str, Mapping[str, float]],
    external: Mapping[str, Mapping[str, float]],
    operator: Mapping,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    dict[str, dict[str, float]],
]:
    r0 = tuple(f"hab_{name}" for name in habitat_columns) + (
        "tsf_years",
    )
    r1_add = (
        "log10_area_plus1",
        "log1p_mainland_distance",
    )
    r2_add = (
        "graph_degree_fraction",
        "graph_mean_shortest_path_km",
        "graph_closeness_per_km",
    )
    rows = {}
    context = operator.get("generic_node_context")
    if not isinstance(context, dict):
        raise BorealPreconfirmatoryFreezeError(
            "v0.83 generic graph context missing"
        )
    for island in universe:
        raw = {
            f"hab_{name}": float(habitat[island][name])
            for name in habitat_columns
        }
        raw.update(external[island])
        node = context.get(island)
        if not isinstance(node, dict):
            raise BorealPreconfirmatoryFreezeError(
                f"v0.83 generic context missing island: {island}"
            )
        raw.update({
            "graph_degree_fraction": float(node["degree_fraction"]),
            "graph_mean_shortest_path_km": float(
                node["mean_shortest_path_km"]
            ),
            "graph_closeness_per_km": float(node["closeness_per_km"]),
        })
        rows[island] = raw
    return r0, r1_add, r2_add, rows


def _source_raw(
    *,
    target_island: str,
    species_index: int,
    pilot_islands: Sequence[str],
    pilot_matrix: Mapping[str, Sequence[int]],
    coordinates: Mapping[str, tuple[float, float]],
    operator: Mapping,
    training_row: bool,
) -> dict[str, float]:
    positives = [
        island
        for island in pilot_islands
        if int(pilot_matrix[island][species_index]) == 1
    ]
    if training_row:
        successes = sum(
            int(pilot_matrix[island][species_index]) == 1
            for island in pilot_islands
            if island != target_island
        )
        trials = len(pilot_islands) - 1
    else:
        successes = len(positives)
        trials = len(pilot_islands)

    features = source_features(
        target=target_island,
        occupied_sources=positives,
        coordinates=coordinates,
        operator=operator,
    )
    return {
        "global_occupancy_logit": logit_jeffreys(successes, trials),
        "log1p_nearest_euclidean_source_km": math.log1p(
            features.nearest_euclidean_km
        ),
        "log1p_euclidean_source_pressure": math.log1p(
            features.euclidean_source_pressure
        ),
        "log1p_nearest_graph_path_km": math.log1p(
            features.nearest_graph_path_km
        ),
        "log1p_graph_source_pressure": math.log1p(
            features.graph_source_pressure
        ),
    }


def _csv_text(header: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(list(header))
    writer.writerows(rows)
    return out.getvalue()


def freeze(
    *,
    pilot_execution: Mapping,
    pilot_snapshot: Mapping,
    geometry_csv: Path,
    projection_receipt: Mapping,
    habitat_reference_csv: Path,
    habitat_receipt: Mapping,
    spatial_receipt: Mapping,
    operator: Mapping,
    operator_receipt: Mapping,
    external: Mapping,
    contract: Mapping,
) -> tuple[dict, str]:
    candidate = contract["candidate_id"]
    species, pilot_islands, pilot_matrix = validate_snapshot(
        pilot_execution,
        pilot_snapshot,
        candidate_id=candidate,
    )

    universe = load_universe()
    if projection_receipt.get("schema") != (
        "structural.boreal_lake_islands_safe_projection_result.v0_74"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "unexpected v0.74 projection receipt"
        )
    if projection_receipt.get("status") != (
        "SAFE_ROWS_PROJECTED_RESPONSE_REMAINS_SEALED"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "v0.74 projection did not qualify"
        )
    if projection_receipt.get("candidate_id") != candidate:
        raise BorealPreconfirmatoryFreezeError(
            "v0.74 candidate identity mismatch"
        )
    for key in (
        "protected_response_values_opened",
        "counts_as_empirical_evidence",
        "pilot_response_authorized",
        "confirmatory_response_authorized",
    ):
        if projection_receipt.get(key) is not False:
            raise BorealPreconfirmatoryFreezeError(
                f"v0.74 response/evidence boundary violated: {key}"
            )
    geometry_meta = projection_receipt.get("geometry", {})
    geometry_sha = geometry_meta.get("sha256")
    if not isinstance(geometry_sha, str):
        raise BorealPreconfirmatoryFreezeError(
            "v0.74 geometry SHA missing"
        )
    coordinates = load_geometry(
        geometry_csv,
        expected_sha256=geometry_sha,
        universe=universe,
    )

    habitat_columns, habitat = parse_habitat_reference(
        habitat_reference_csv,
        habitat_receipt,
        universe,
    )
    external_rows = parse_external_state(external, universe)
    validate_operator(
        operator,
        operator_receipt,
        candidate_id=candidate,
        universe=universe,
    )

    if spatial_receipt.get("schema") != (
        "structural.boreal_lake_islands_spatial_partition_result.v0_75"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "unexpected v0.75 spatial receipt"
        )
    if spatial_receipt.get("status") != (
        "SPATIAL_PARTITION_FROZEN_RESPONSE_INDEPENDENTLY"
    ):
        raise BorealPreconfirmatoryFreezeError(
            "v0.75 spatial partition did not qualify"
        )
    if spatial_receipt.get("candidate_id") != candidate:
        raise BorealPreconfirmatoryFreezeError(
            "v0.75 candidate mismatch"
        )
    for key in (
        "species_occurrence_used",
        "richness_used",
        "habitat_values_used",
        "counts_as_empirical_evidence",
        "pilot_response_authorized",
        "confirmatory_response_authorized",
    ):
        if spatial_receipt.get(key) is not False:
            raise BorealPreconfirmatoryFreezeError(
                f"v0.75 response/evidence boundary violated: {key}"
            )
    island_to_block = spatial_receipt.get("island_to_block")
    if not isinstance(island_to_block, dict) or set(island_to_block) != set(universe):
        raise BorealPreconfirmatoryFreezeError(
            "invalid v0.75 island-to-block mapping"
        )

    frozen_pilot = set(spatial_receipt.get("pilot_islands") or ())
    frozen_confirmatory = set(
        spatial_receipt.get("confirmatory_islands") or ()
    )
    if set(pilot_islands) != frozen_pilot:
        raise BorealPreconfirmatoryFreezeError(
            "v0.84 pilot island set differs from v0.75"
        )
    if frozen_pilot & frozen_confirmatory:
        raise BorealPreconfirmatoryFreezeError(
            "v0.75 pilot/confirmatory island overlap"
        )
    if frozen_pilot | frozen_confirmatory != set(universe):
        raise BorealPreconfirmatoryFreezeError(
            "v0.75 island partition does not cover universe"
        )

    r0_raw, r1_add_raw, r2_add_raw, base_raw = _base_rows(
        universe=universe,
        habitat_columns=habitat_columns,
        habitat=habitat,
        external=external_rows,
        operator=operator,
    )
    all_base_columns = r0_raw + r1_add_raw + r2_add_raw
    base_constants = freeze_standardization(
        [base_raw[island] for island in universe],
        all_base_columns,
    )

    source_columns = (
        "global_occupancy_logit",
        "log1p_nearest_euclidean_source_km",
        "log1p_euclidean_source_pressure",
        "log1p_nearest_graph_path_km",
        "log1p_graph_source_pressure",
    )
    source_rows = []
    training_records = []
    y = []

    for island in pilot_islands:
        for species_index, species_name in enumerate(species):
            source = _source_raw(
                target_island=island,
                species_index=species_index,
                pilot_islands=pilot_islands,
                pilot_matrix=pilot_matrix,
                coordinates=coordinates,
                operator=operator,
                training_row=True,
            )
            source_rows.append(source)
            training_records.append(
                (island, species_name, species_index, source)
            )
            y.append(int(pilot_matrix[island][species_index]))

    source_constants = freeze_standardization(
        source_rows,
        source_columns,
    )

    r0_columns = ("intercept",) + tuple(
        f"z_{column}" for column in r0_raw
    )
    r1_columns = r0_columns + tuple(
        f"z_{column}" for column in r1_add_raw
    )
    r2_columns = r1_columns + tuple(
        f"z_{column}" for column in r2_add_raw
    )
    r3_source = source_columns[:3]
    c_source = source_columns[3:]
    r3_columns = r2_columns + tuple(
        f"z_{column}" for column in r3_source
    )
    c_columns = r3_columns + tuple(
        f"z_{column}" for column in c_source
    )

    matrices = {
        "R0": [],
        "R1": [],
        "R2": [],
        "R3": [],
        "C": [],
    }
    for island, _, _, source in training_records:
        z_base = apply_standardization(
            base_raw[island],
            columns=all_base_columns,
            constants=base_constants,
        )
        base_map = dict(zip(all_base_columns, z_base))
        r0_values = tuple(base_map[column] for column in r0_raw)
        r1_values = r0_values + tuple(
            base_map[column] for column in r1_add_raw
        )
        r2_values = r1_values + tuple(
            base_map[column] for column in r2_add_raw
        )
        z_source = apply_standardization(
            source,
            columns=source_columns,
            constants=source_constants,
        )
        source_map = dict(zip(source_columns, z_source))
        r3_values = r2_values + tuple(
            source_map[column] for column in r3_source
        )
        c_values = r3_values + tuple(
            source_map[column] for column in c_source
        )
        matrices["R0"].append((1.0,) + r0_values)
        matrices["R1"].append((1.0,) + r1_values)
        matrices["R2"].append((1.0,) + r2_values)
        matrices["R3"].append((1.0,) + r3_values)
        matrices["C"].append((1.0,) + c_values)

    settings = contract["fitting"]
    fits = {
        "R0": fit_ridge_logistic(
            matrices["R0"], y, columns=r0_columns,
            ridge_lambda=settings["ridge_lambda"],
            max_iterations=settings["max_iterations"],
            tolerance=settings["tolerance"],
        ),
        "R1": fit_ridge_logistic(
            matrices["R1"], y, columns=r1_columns,
            ridge_lambda=settings["ridge_lambda"],
            max_iterations=settings["max_iterations"],
            tolerance=settings["tolerance"],
        ),
        "R2": fit_ridge_logistic(
            matrices["R2"], y, columns=r2_columns,
            ridge_lambda=settings["ridge_lambda"],
            max_iterations=settings["max_iterations"],
            tolerance=settings["tolerance"],
        ),
        "R3": fit_ridge_logistic(
            matrices["R3"], y, columns=r3_columns,
            ridge_lambda=settings["ridge_lambda"],
            max_iterations=settings["max_iterations"],
            tolerance=settings["tolerance"],
        ),
        "C": fit_ridge_logistic(
            matrices["C"], y, columns=c_columns,
            ridge_lambda=settings["ridge_lambda"],
            max_iterations=settings["max_iterations"],
            tolerance=settings["tolerance"],
        ),
    }

    prediction_rows = []
    confirmatory_blocks = tuple(
        spatial_receipt.get("confirmatory_block_ids") or ()
    )
    confirmatory_islands_by_block = {
        block: sorted(
            island
            for island in universe
            if island_to_block[island] == block
        )
        for block in confirmatory_blocks
    }
    if any(not islands for islands in confirmatory_islands_by_block.values()):
        raise BorealPreconfirmatoryFreezeError(
            "empty confirmatory spatial block"
        )

    clip = tuple(settings["probability_clip"])
    for block in confirmatory_blocks:
        for island in confirmatory_islands_by_block[block]:
            z_base = apply_standardization(
                base_raw[island],
                columns=all_base_columns,
                constants=base_constants,
            )
            base_map = dict(zip(all_base_columns, z_base))
            r0_values = tuple(base_map[column] for column in r0_raw)
            r1_values = r0_values + tuple(
                base_map[column] for column in r1_add_raw
            )
            r2_values = r1_values + tuple(
                base_map[column] for column in r2_add_raw
            )

            for species_index, species_name in enumerate(species):
                source = _source_raw(
                    target_island=island,
                    species_index=species_index,
                    pilot_islands=pilot_islands,
                    pilot_matrix=pilot_matrix,
                    coordinates=coordinates,
                    operator=operator,
                    training_row=False,
                )
                z_source = apply_standardization(
                    source,
                    columns=source_columns,
                    constants=source_constants,
                )
                source_map = dict(zip(source_columns, z_source))
                r3_values = r2_values + tuple(
                    source_map[column] for column in r3_source
                )
                c_values = r3_values + tuple(
                    source_map[column] for column in c_source
                )

                vectors = {
                    "R0": (1.0,) + r0_values,
                    "R1": (1.0,) + r1_values,
                    "R2": (1.0,) + r2_values,
                    "R3": (1.0,) + r3_values,
                    "C": (1.0,) + c_values,
                }
                probabilities = {
                    name: predict_probability(
                        vectors[name],
                        fits[name],
                        clip=clip,
                    )
                    for name in ("R0", "R1", "R2", "R3", "C")
                }
                prediction_rows.append((
                    island,
                    block,
                    species_name,
                    *(float(probabilities[name]).hex()
                      for name in ("R0", "R1", "R2", "R3", "C")),
                ))

    header = (
        "island",
        "block",
        "species",
        "p_R0_hex",
        "p_R1_hex",
        "p_R2_hex",
        "p_R3_hex",
        "p_C_hex",
    )
    prediction_text = _csv_text(header, prediction_rows)

    def constants_hex(constants):
        return {
            column: {
                "mean_hex": float(values["mean"]).hex(),
                "sd_hex": float(values["sd"]).hex(),
            }
            for column, values in constants.items()
        }

    receipt = {
        "schema": "structural.boreal_preconfirmatory_model_freeze.v0_85",
        "status": "CONFIRMATORY_PREDICTIONS_FROZEN_BEFORE_RESPONSE",
        "candidate_id": candidate,
        "pilot_snapshot_fingerprint": pilot_snapshot["snapshot_fingerprint"],
        "operator_fingerprint": operator_receipt["operator_fingerprint"],
        "habitat_reference_sha256": habitat_receipt["reference_sha256"],
        "geometry_sha256": geometry_sha,
        "species_count": len(species),
        "pilot_island_count": len(pilot_islands),
        "confirmatory_island_count": len(frozen_confirmatory),
        "confirmatory_block_count": len(confirmatory_blocks),
        "training_row_count": len(y),
        "prediction_row_count": len(prediction_rows),
        "base_standardization": constants_hex(base_constants),
        "source_standardization": constants_hex(source_constants),
        "models": {
            name: fit_mapping(fits[name])
            for name in ("R0", "R1", "R2", "R3", "C")
        },
        "prediction_surface_sha256": sha256_text(prediction_text),
        "prediction_surface_columns": list(header),
        "primary_scoring": dict(contract["primary_scoring"]),
        "confirmatory_target_values_opened": 0,
        "confirmatory_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "counts_as_empirical_evidence": False,
        "next_action": (
            "commit this receipt and exact prediction surface; only then may "
            "a separate one-shot confirmatory response authorization be considered"
        ),
    }
    return receipt, prediction_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot_execution", type=Path)
    parser.add_argument("pilot_snapshot", type=Path)
    parser.add_argument("geometry_csv", type=Path)
    parser.add_argument("projection_receipt", type=Path)
    parser.add_argument("habitat_reference_csv", type=Path)
    parser.add_argument("habitat_receipt", type=Path)
    parser.add_argument("spatial_receipt", type=Path)
    parser.add_argument("operator_json", type=Path)
    parser.add_argument("operator_receipt", type=Path)
    parser.add_argument("--external", type=Path, default=DEFAULT_EXTERNAL)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_preconfirmatory_model_contract.v0_85"
        ):
            raise BorealPreconfirmatoryFreezeError(
                "unexpected v0.85 contract schema"
            )
        receipt, prediction_text = freeze(
            pilot_execution=_load(args.pilot_execution),
            pilot_snapshot=_load(args.pilot_snapshot),
            geometry_csv=args.geometry_csv,
            projection_receipt=_load(args.projection_receipt),
            habitat_reference_csv=args.habitat_reference_csv,
            habitat_receipt=_load(args.habitat_receipt),
            spatial_receipt=_load(args.spatial_receipt),
            operator=_load(args.operator_json),
            operator_receipt=_load(args.operator_receipt),
            external=_load(args.external),
            contract=contract,
        )
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealConfirmatoryModelError,
        BorealDualIsolationOperatorError,
        BorealPreconfirmatoryFreezeError,
    ) as exc:
        receipt = {
            "schema": "structural.boreal_preconfirmatory_model_freeze.v0_85",
            "status": "STOP",
            "reason": str(exc),
            "confirmatory_target_values_opened": 0,
            "confirmatory_response_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "counts_as_empirical_evidence": False,
        }
        prediction_text = None
        code = 2
    else:
        code = 0

    if prediction_text is not None and args.predictions is not None:
        args.predictions.parent.mkdir(parents=True, exist_ok=True)
        args.predictions.write_text(prediction_text, encoding="utf-8")

    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(text, encoding="utf-8")
    print(text, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
