#!/usr/bin/env python3
"""Freeze boreal-bird R3, actual-C and 20 null-C predictions before confirmatory access."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Mapping, Sequence

from scripts.freeze_boreal_birds_topology_nulls_v1_158 import (
    freeze as freeze_nulls,
    load_geometry,
)
from structural.boreal_beetle_pilot_router import decode_binary_vector_hex
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
    freeze_connected_knn_operator,
    source_features,
)
from structural.boreal_spatial_partition import (
    EARTH_RADIUS_KM,
    pairwise_distances,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_birds_prediction_freeze_contract_v1_163.json"
)
DEFAULT_SCIENTIFIC = (
    ROOT / "development/boreal_19island_birds_topology_sensitivity_contract_v1_158.json"
)
DEFAULT_NULL_RECEIPT = (
    ROOT / "development/boreal_19island_birds_topology_null_receipt_v1_158.json"
)
DEFAULT_SENSITIVITY = (
    ROOT / "development/boreal_19island_birds_configuration_sensitivity_v1_158.csv"
)
DEFAULT_PILOT_FREEZE = (
    ROOT / "development/boreal_19island_bird_pilot_freeze_v1_162.json"
)
DEFAULT_PILOT_EXECUTION = (
    ROOT / "development/boreal_19island_bird_pilot_execution_v1_162.json"
)
DEFAULT_PILOT_SNAPSHOT = (
    ROOT / "development/boreal_19island_bird_pilot_snapshot_v1_162.json"
)
DEFAULT_STATE = ROOT / "development/boreal_19island_state_reference_v0_99.csv"
DEFAULT_STATE_FREEZE = (
    ROOT / "development/boreal_19island_state_reference_freeze_v0_99.json"
)
DEFAULT_GEOMETRY = ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
DEFAULT_GEOMETRY_FREEZE = (
    ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
)
DEFAULT_SPATIAL = (
    ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
)
DEFAULT_OPERATOR_FREEZE = (
    ROOT / "development/boreal_19island_source_operator_freeze_v1_01.json"
)


class BirdPredictionFreezeError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise BirdPredictionFreezeError(f"{path.name} must contain a JSON object")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_sha256(value: Mapping) -> str:
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def parse_number(value: object) -> float:
    text = str(value).strip()
    try:
        out = (
            float.fromhex(text)
            if text.lower().startswith(("0x", "+0x", "-0x"))
            else float(text)
        )
    except ValueError as exc:
        raise BirdPredictionFreezeError(f"invalid numeric value: {text!r}") from exc
    if not math.isfinite(out):
        raise BirdPredictionFreezeError("nonfinite numeric value")
    return out


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_pilot(
    *,
    freeze: Mapping,
    execution: Mapping,
    snapshot: Mapping,
    execution_path: Path,
    snapshot_path: Path,
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, tuple[int, ...]], dict[str, int]]:
    if freeze.get("schema") != "structural.boreal_19island_bird_pilot_freeze.v1_162":
        raise BirdPredictionFreezeError("unexpected pilot freeze schema")
    if freeze.get("status") != "BIRD_PILOT_COMMITTED_CONFIRMATORY_REMAINS_SEALED":
        raise BirdPredictionFreezeError("pilot freeze status drift")
    if freeze.get("files", {}).get("execution_result", {}).get("sha256") != sha256_file(execution_path):
        raise BirdPredictionFreezeError("pilot execution file SHA drift")
    if freeze.get("files", {}).get("pilot_snapshot", {}).get("sha256") != sha256_file(snapshot_path):
        raise BirdPredictionFreezeError("pilot snapshot file SHA drift")

    if execution.get("status") != "BIRD_PILOT_V161_QUALIFIED_TO_FREEZE_CONFIRMATORY_PREDICTIONS":
        raise BirdPredictionFreezeError("pilot execution did not qualify")
    if execution.get("authorization_consumed") is not True:
        raise BirdPredictionFreezeError("pilot authorization was not consumed")
    if execution.get("confirmatory_target_values_parsed") != 0:
        raise BirdPredictionFreezeError("confirmatory target boundary violated")
    if execution.get("excluded_target_values_parsed") != 0:
        raise BirdPredictionFreezeError("excluded target boundary violated")
    if execution.get("confirmatory_response_authorized") is not False:
        raise BirdPredictionFreezeError("confirmatory response already authorized")

    if snapshot.get("status") != "BIRD_PILOT_SNAPSHOT_FROZEN_CONFIRMATORY_REMAINS_SEALED":
        raise BirdPredictionFreezeError("pilot snapshot status drift")
    if snapshot.get("confirmatory_target_values_parsed") != 0:
        raise BirdPredictionFreezeError("snapshot confirmatory boundary violated")
    if snapshot.get("excluded_target_values_parsed") != 0:
        raise BirdPredictionFreezeError("snapshot excluded boundary violated")
    if snapshot.get("confirmatory_occurrence_values_stored") is not False:
        raise BirdPredictionFreezeError("snapshot stores confirmatory occurrence")
    if snapshot.get("excluded_occurrence_values_stored") is not False:
        raise BirdPredictionFreezeError("snapshot stores excluded occurrence")

    fingerprint = str(snapshot.get("snapshot_fingerprint", ""))
    core = dict(snapshot)
    core.pop("snapshot_fingerprint", None)
    if canonical_sha256(core) != fingerprint:
        raise BirdPredictionFreezeError("pilot snapshot fingerprint mismatch")
    if execution.get("snapshot_fingerprint") != fingerprint:
        raise BirdPredictionFreezeError("pilot execution/snapshot fingerprint mismatch")
    if freeze.get("snapshot_fingerprint") != fingerprint:
        raise BirdPredictionFreezeError("pilot freeze/snapshot fingerprint mismatch")

    species = tuple(snapshot.get("eligible_species") or ())
    if len(species) != 18 or len(set(species)) != 18:
        raise BirdPredictionFreezeError("fixed bird species universe drift")
    if snapshot.get("eligible_species_sha256") != (
        "f623652815edea90404c9a6a306699deaf2f0a7ce5b56cb7d6f6b379f4204080"
    ):
        raise BirdPredictionFreezeError("fixed bird species SHA drift")

    pilot_order = tuple(snapshot.get("pilot_island_order") or ())
    if pilot_order != ("DN", "FD", "HU", "IL", "IS", "PP"):
        raise BirdPredictionFreezeError("pilot island order drift")

    encoded_rows = snapshot.get("pilot_targets_hex_by_island")
    if not isinstance(encoded_rows, list) or len(encoded_rows) != 6:
        raise BirdPredictionFreezeError("pilot target snapshot drift")
    encoded = {
        str(row["island"]): str(row["targets_hex"])
        for row in encoded_rows
    }
    if set(encoded) != set(pilot_order):
        raise BirdPredictionFreezeError("pilot target island drift")
    matrix = {
        island: decode_binary_vector_hex(encoded[island], len(species))
        for island in pilot_order
    }

    support_rows = snapshot.get("pilot_support_counts")
    if not isinstance(support_rows, list) or len(support_rows) != len(species):
        raise BirdPredictionFreezeError("pilot support snapshot drift")
    supports = {
        str(row["species"]): int(row["pilot_presences"])
        for row in support_rows
    }
    if tuple(supports) != species:
        raise BirdPredictionFreezeError("pilot support species order drift")
    decoded_support = {
        species[index]: sum(int(matrix[island][index]) for island in pilot_order)
        for index in range(len(species))
    }
    if decoded_support != supports:
        raise BirdPredictionFreezeError("pilot support counts do not replay")
    if any(not 1 <= count <= 4 for count in supports.values()):
        raise BirdPredictionFreezeError("pilot support outside frozen 1-4 rule")
    return species, pilot_order, matrix, supports


def load_state(path: Path, freeze: Mapping) -> tuple[tuple[str, ...], dict[str, dict[str, float]]]:
    if freeze.get("schema") != "structural.boreal_19island_state_reference_freeze.v0_99":
        raise BirdPredictionFreezeError("unexpected state freeze schema")
    if freeze.get("status") != "STATE_REFERENCE_COMMITTED_RESPONSE_INDEPENDENTLY":
        raise BirdPredictionFreezeError("state freeze did not qualify")
    if sha256_file(path) != freeze.get("state_reference_sha256"):
        raise BirdPredictionFreezeError("state reference SHA drift")
    rows = load_csv(path)
    header = (
        "Island", "PC1", "PC2", "PC3", "TSF_Z",
        "LOG_AREA_Z", "LOG_MAINLAND_DISTANCE_Z"
    )
    if tuple(rows[0]) != header:
        raise BirdPredictionFreezeError("state reference header drift")
    order = tuple(str(row["Island"]) for row in rows)
    if order != tuple(freeze.get("island_order") or ()):
        raise BirdPredictionFreezeError("state island order drift")
    state = {}
    for row in rows:
        island = str(row["Island"])
        state[island] = {
            column: parse_number(row[column])
            for column in header
            if column != "Island"
        }
    return order, state


def distance_between(
    distances: Mapping[tuple[str, str], float],
    left: str,
    right: str,
) -> float:
    if left == right:
        return 0.0
    return float(distances[tuple(sorted((left, right)))])


def make_null_operator(
    null_row: Mapping,
    *,
    island_order: Sequence[str],
    kernel_scale: float,
) -> dict:
    return {
        "operator": "matched_degree_and_edge_length_bin_rewire",
        "selected_k": None,
        "kernel_scale_rule": "reuse frozen actual topology kernel scale",
        "kernel_scale_km": float(kernel_scale),
        "island_order": list(island_order),
        "edges": [
            {
                "left": edge["left"],
                "right": edge["right"],
                "distance_km": float.fromhex(edge["distance_km_hex"]),
            }
            for edge in null_row["edges"]
        ],
    }


def common_source_raw(
    *,
    target: str,
    species_index: int,
    pilot_order: Sequence[str],
    matrix: Mapping[str, Sequence[int]],
    pairwise: Mapping[tuple[str, str], float],
    scale: float,
    training_row: bool,
    euclidean_empty_sentinel: float,
) -> dict[str, float]:
    if training_row:
        allowed = [island for island in pilot_order if island != target]
    else:
        allowed = list(pilot_order)
    successes = sum(int(matrix[island][species_index]) for island in allowed)
    occupied = [
        island for island in allowed
        if int(matrix[island][species_index]) == 1
    ]
    if occupied:
        distances = [distance_between(pairwise, target, source) for source in occupied]
        nearest = min(distances)
        pressure = math.fsum(math.exp(-value / scale) for value in distances)
    else:
        nearest = euclidean_empty_sentinel
        pressure = 0.0
    return {
        "occupancy_logit": logit_jeffreys(successes, len(allowed)),
        "log1p_nearest_euclidean_source_km": math.log1p(nearest),
        "log1p_euclidean_source_pressure": math.log1p(pressure),
    }


def graph_source_raw(
    *,
    target: str,
    species_index: int,
    pilot_order: Sequence[str],
    matrix: Mapping[str, Sequence[int]],
    coordinates: Mapping[str, tuple[float, float]],
    operator: Mapping,
    training_row: bool,
    graph_empty_sentinel: float,
) -> dict[str, float]:
    if training_row:
        allowed = [island for island in pilot_order if island != target]
    else:
        allowed = list(pilot_order)
    occupied = [
        island for island in allowed
        if int(matrix[island][species_index]) == 1
    ]
    if occupied:
        features = source_features(
            target=target,
            occupied_sources=occupied,
            coordinates=coordinates,
            operator=operator,
        )
        nearest = features.nearest_graph_path_km
        pressure = features.graph_source_pressure
    else:
        nearest = graph_empty_sentinel
        pressure = 0.0
    return {
        "log1p_nearest_graph_source_km": math.log1p(nearest),
        "log1p_graph_source_pressure": math.log1p(pressure),
    }


def constants_hex(constants: Mapping[str, Mapping[str, float]]) -> dict:
    return {
        column: {
            "mean_hex": float(values["mean"]).hex(),
            "sd_hex": float(values["sd"]).hex(),
        }
        for column, values in constants.items()
    }


def csv_text(header: Sequence[str], rows: Sequence[Sequence[object]]) -> str:
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(list(header))
    writer.writerows(rows)
    return out.getvalue()


def freeze(
    *,
    contract: Mapping,
    scientific_contract: Mapping,
    null_receipt: Mapping,
    sensitivity_rows: Sequence[Mapping[str, str]],
    pilot_freeze: Mapping,
    pilot_execution: Mapping,
    pilot_snapshot: Mapping,
    pilot_execution_path: Path,
    pilot_snapshot_path: Path,
    state_path: Path,
    state_freeze: Mapping,
    geometry_path: Path,
    geometry_freeze: Mapping,
    spatial_freeze: Mapping,
    operator_freeze: Mapping,
) -> tuple[dict, str]:
    if contract.get("schema") != (
        "structural.boreal_19island_birds_prediction_freeze_contract.v1_163"
    ):
        raise BirdPredictionFreezeError("unexpected prediction contract schema")
    if contract["response_boundary"]["confirmatory_target_values_opened"] != 0:
        raise BirdPredictionFreezeError("confirmatory response already opened")

    species, pilot_order, matrix, supports = validate_pilot(
        freeze=pilot_freeze,
        execution=pilot_execution,
        snapshot=pilot_snapshot,
        execution_path=pilot_execution_path,
        snapshot_path=pilot_snapshot_path,
    )

    state_order, state = load_state(state_path, state_freeze)
    coordinates = load_geometry(geometry_path)
    if sha256_file(geometry_path) != geometry_freeze.get("geometry_sha256"):
        raise BirdPredictionFreezeError("geometry SHA drift")
    if set(state_order) != set(coordinates):
        raise BirdPredictionFreezeError("state/geometry population mismatch")

    if spatial_freeze.get("status") != "SPATIAL_PARTITION_COMMITTED_RESPONSE_INDEPENDENTLY":
        raise BirdPredictionFreezeError("spatial freeze did not qualify")
    if tuple(spatial_freeze.get("pilot_islands") or ()) != tuple(sorted(pilot_order)):
        raise BirdPredictionFreezeError("pilot spatial split drift")
    confirmatory_islands = tuple(spatial_freeze.get("confirmatory_islands") or ())
    if len(confirmatory_islands) != 13:
        raise BirdPredictionFreezeError("confirmatory island count drift")
    confirmatory_blocks = tuple(spatial_freeze.get("confirmatory_block_ids") or ())
    if len(confirmatory_blocks) != 7:
        raise BirdPredictionFreezeError("confirmatory block count drift")
    island_to_block = spatial_freeze["island_to_block"]

    actual_operator = freeze_connected_knn_operator(coordinates)
    actual_fingerprint = canonical_sha256(actual_operator)
    if actual_fingerprint != operator_freeze.get("operator_fingerprint"):
        raise BirdPredictionFreezeError("actual source operator fingerprint drift")
    scale = float(actual_operator["kernel_scale_km"])
    if scale.hex() != operator_freeze.get("kernel_scale_km_hex"):
        raise BirdPredictionFreezeError("kernel scale drift")

    replay_nulls, replay_surface = freeze_nulls(
        contract=scientific_contract,
        geometry=coordinates,
        operator_freeze=operator_freeze,
    )
    if replay_nulls.get("null_count") != 20:
        raise BirdPredictionFreezeError("null count drift")
    if null_receipt.get("actual_operator_fingerprint") != actual_fingerprint:
        raise BirdPredictionFreezeError("committed null/actual identity drift")
    for observed, expected in zip(replay_nulls["nulls"], null_receipt["nulls"]):
        payload = "\n".join(
            f'{edge["left"]}|{edge["right"]}' for edge in observed["edges"]
        ).encode("utf-8")
        if hashlib.sha256(payload).hexdigest() != expected["edge_set_sha256"]:
            raise BirdPredictionFreezeError("null edge-set replay mismatch")

    sensitivity = {
        str(row["Island"]): float.fromhex(str(row["H_hex"]))
        for row in sensitivity_rows
    }
    replay_H = {str(row["Island"]): float(row["H"]) for row in replay_surface}
    if set(sensitivity) != set(confirmatory_islands):
        raise BirdPredictionFreezeError("sensitivity target universe drift")
    for island in sensitivity:
        if sensitivity[island].hex() != replay_H[island].hex():
            raise BirdPredictionFreezeError(f"sensitivity H replay mismatch: {island}")

    base_raw = {}
    for island in state_order:
        node = actual_operator["generic_node_context"][island]
        row = dict(state[island])
        row.update({
            "graph_degree_fraction": float(node["degree_fraction"]),
            "graph_mean_shortest_path_km": float(node["mean_shortest_path_km"]),
            "graph_closeness_per_km": float(node["closeness_per_km"]),
        })
        base_raw[island] = row

    base_columns = (
        "PC1", "PC2", "PC3", "TSF_Z",
        "LOG_AREA_Z", "LOG_MAINLAND_DISTANCE_Z",
        "graph_degree_fraction", "graph_mean_shortest_path_km",
        "graph_closeness_per_km",
    )
    base_constants = freeze_standardization(
        [base_raw[island] for island in state_order],
        base_columns,
    )

    pairwise = pairwise_distances(coordinates)
    empty_rule = contract["empty_source_semantics"]
    euclidean_empty = math.pi * EARTH_RADIUS_KM + scale
    max_actual_edge = max(float(edge["distance_km"]) for edge in actual_operator["edges"])
    graph_empty = (len(state_order) - 1) * max_actual_edge + scale
    if not empty_rule["same_graph_empty_sentinel_for_actual_and_all_nulls"]:
        raise BirdPredictionFreezeError("graph-empty sentinel policy drift")

    common_columns = (
        "occupancy_logit",
        "log1p_nearest_euclidean_source_km",
        "log1p_euclidean_source_pressure",
    )
    graph_columns = (
        "log1p_nearest_graph_source_km",
        "log1p_graph_source_pressure",
    )

    training_common = []
    y = []
    training_keys = []
    for island in pilot_order:
        for species_index, species_name in enumerate(species):
            common = common_source_raw(
                target=island,
                species_index=species_index,
                pilot_order=pilot_order,
                matrix=matrix,
                pairwise=pairwise,
                scale=scale,
                training_row=True,
                euclidean_empty_sentinel=euclidean_empty,
            )
            training_common.append(common)
            training_keys.append((island, species_name, species_index))
            y.append(int(matrix[island][species_index]))
    if len(y) != 108:
        raise BirdPredictionFreezeError("training row count drift")
    common_constants = freeze_standardization(training_common, common_columns)

    r3_rows = []
    r3_columns = (
        "intercept",
        *(f"z_{column}" for column in base_columns),
        *(f"z_{column}" for column in common_columns),
    )
    for (island, _, _), common in zip(training_keys, training_common):
        z_base = apply_standardization(
            base_raw[island], columns=base_columns, constants=base_constants
        )
        z_common = apply_standardization(
            common, columns=common_columns, constants=common_constants
        )
        r3_rows.append((1.0,) + z_base + z_common)

    fit_settings = contract["fitting"]
    fit_r3 = fit_ridge_logistic(
        r3_rows,
        y,
        columns=r3_columns,
        ridge_lambda=float(fit_settings["ridge_lambda"]),
        max_iterations=int(fit_settings["max_iterations"]),
        tolerance=float(fit_settings["tolerance"]),
    )

    prediction_keys = []
    prediction_r3_vectors = []
    prediction_common = []
    for block in confirmatory_blocks:
        islands = sorted(
            island for island in confirmatory_islands
            if island_to_block[island] == block
        )
        if not islands:
            raise BirdPredictionFreezeError("empty confirmatory block")
        for island in islands:
            for species_index, species_name in enumerate(species):
                common = common_source_raw(
                    target=island,
                    species_index=species_index,
                    pilot_order=pilot_order,
                    matrix=matrix,
                    pairwise=pairwise,
                    scale=scale,
                    training_row=False,
                    euclidean_empty_sentinel=euclidean_empty,
                )
                z_base = apply_standardization(
                    base_raw[island], columns=base_columns, constants=base_constants
                )
                z_common = apply_standardization(
                    common, columns=common_columns, constants=common_constants
                )
                prediction_keys.append((island, block, species_name, species_index))
                prediction_common.append(common)
                prediction_r3_vectors.append((1.0,) + z_base + z_common)

    if len(prediction_keys) != 234:
        raise BirdPredictionFreezeError("prediction row count drift")
    clip = tuple(float(value) for value in fit_settings["probability_clip"])
    p_r3 = [
        predict_probability(vector, fit_r3, clip=clip)
        for vector in prediction_r3_vectors
    ]

    candidate_models = []
    candidate_predictions = []

    topology_rows = [("actual", actual_operator)]
    for null_row in replay_nulls["nulls"]:
        topology_rows.append((
            f'null_{int(null_row["null_index"]):02d}',
            make_null_operator(
                null_row,
                island_order=actual_operator["island_order"],
                kernel_scale=scale,
            ),
        ))

    c_columns = r3_columns + tuple(f"z_{column}" for column in graph_columns)
    for topology_name, topology_operator in topology_rows:
        training_graph = []
        for island, _, species_index in training_keys:
            training_graph.append(graph_source_raw(
                target=island,
                species_index=species_index,
                pilot_order=pilot_order,
                matrix=matrix,
                coordinates=coordinates,
                operator=topology_operator,
                training_row=True,
                graph_empty_sentinel=graph_empty,
            ))
        graph_constants = freeze_standardization(training_graph, graph_columns)
        x_c = []
        for r3_vector, graph in zip(r3_rows, training_graph):
            z_graph = apply_standardization(
                graph, columns=graph_columns, constants=graph_constants
            )
            x_c.append(r3_vector + z_graph)
        fit_c = fit_ridge_logistic(
            x_c,
            y,
            columns=c_columns,
            ridge_lambda=float(fit_settings["ridge_lambda"]),
            max_iterations=int(fit_settings["max_iterations"]),
            tolerance=float(fit_settings["tolerance"]),
        )

        predictions = []
        for r3_vector, (island, _, _, species_index) in zip(
            prediction_r3_vectors, prediction_keys
        ):
            graph = graph_source_raw(
                target=island,
                species_index=species_index,
                pilot_order=pilot_order,
                matrix=matrix,
                coordinates=coordinates,
                operator=topology_operator,
                training_row=False,
                graph_empty_sentinel=graph_empty,
            )
            z_graph = apply_standardization(
                graph, columns=graph_columns, constants=graph_constants
            )
            predictions.append(
                predict_probability(r3_vector + z_graph, fit_c, clip=clip)
            )
        candidate_models.append({
            "topology": topology_name,
            "graph_standardization": constants_hex(graph_constants),
            "model": fit_mapping(fit_c),
        })
        candidate_predictions.append(predictions)

    if len(candidate_predictions) != 21:
        raise BirdPredictionFreezeError("candidate prediction count drift")

    header = list(contract["prediction_surface"]["columns"])
    rows = []
    for row_index, (island, block, species_name, species_index) in enumerate(prediction_keys):
        n = int(supports[species_name])
        h_value = float(sensitivity[island])
        factor = (6 - n) / (n * 5)
        s_value = factor * h_value
        row = [
            island,
            block,
            species_name,
            n,
            h_value.hex(),
            s_value.hex(),
            float(p_r3[row_index]).hex(),
            float(candidate_predictions[0][row_index]).hex(),
        ]
        row.extend(
            float(candidate_predictions[index][row_index]).hex()
            for index in range(1, 21)
        )
        rows.append(row)
    prediction_text = csv_text(header, rows)

    models = {
        "R3": fit_mapping(fit_r3),
        "candidates": candidate_models,
    }
    receipt = {
        "schema": "structural.boreal_19island_birds_prediction_freeze.v1_163",
        "status": contract["success_ceiling"]["status"],
        "candidate_id": contract["candidate_id"],
        "pilot_snapshot_fingerprint": pilot_snapshot["snapshot_fingerprint"],
        "eligible_species_count": len(species),
        "eligible_species_sha256": pilot_snapshot["eligible_species_sha256"],
        "support_distribution": pilot_freeze["support_distribution"],
        "training_row_count": len(y),
        "prediction_row_count": len(rows),
        "confirmatory_island_count": len(confirmatory_islands),
        "confirmatory_block_count": len(confirmatory_blocks),
        "null_topology_count": 20,
        "base_standardization": constants_hex(base_constants),
        "common_source_standardization": constants_hex(common_constants),
        "empty_source_semantics": {
            "euclidean_empty_km_hex": float(euclidean_empty).hex(),
            "graph_empty_km_hex": float(graph_empty).hex(),
            "same_graph_empty_sentinel_for_actual_and_all_nulls": True,
        },
        "models": models,
        "models_fingerprint": canonical_sha256(models),
        "prediction_surface_sha256": sha256_text(prediction_text),
        "prediction_surface_columns": header,
        "sensitivity_H_min_hex": min(sensitivity.values()).hex(),
        "sensitivity_H_max_hex": max(sensitivity.values()).hex(),
        "confirmatory_target_values_opened": 0,
        "confirmatory_response_authorized": False,
        "counts_as_empirical_evidence": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return receipt, prediction_text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    ap.add_argument("--scientific-contract", type=Path, default=DEFAULT_SCIENTIFIC)
    ap.add_argument("--null-receipt", type=Path, default=DEFAULT_NULL_RECEIPT)
    ap.add_argument("--sensitivity", type=Path, default=DEFAULT_SENSITIVITY)
    ap.add_argument("--pilot-freeze", type=Path, default=DEFAULT_PILOT_FREEZE)
    ap.add_argument("--pilot-execution", type=Path, default=DEFAULT_PILOT_EXECUTION)
    ap.add_argument("--pilot-snapshot", type=Path, default=DEFAULT_PILOT_SNAPSHOT)
    ap.add_argument("--state", type=Path, default=DEFAULT_STATE)
    ap.add_argument("--state-freeze", type=Path, default=DEFAULT_STATE_FREEZE)
    ap.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY)
    ap.add_argument("--geometry-freeze", type=Path, default=DEFAULT_GEOMETRY_FREEZE)
    ap.add_argument("--spatial-freeze", type=Path, default=DEFAULT_SPATIAL)
    ap.add_argument("--operator-freeze", type=Path, default=DEFAULT_OPERATOR_FREEZE)
    ap.add_argument("--predictions", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    args = ap.parse_args()

    try:
        receipt, prediction_text = freeze(
            contract=load_json(args.contract),
            scientific_contract=load_json(args.scientific_contract),
            null_receipt=load_json(args.null_receipt),
            sensitivity_rows=load_csv(args.sensitivity),
            pilot_freeze=load_json(args.pilot_freeze),
            pilot_execution=load_json(args.pilot_execution),
            pilot_snapshot=load_json(args.pilot_snapshot),
            pilot_execution_path=args.pilot_execution,
            pilot_snapshot_path=args.pilot_snapshot,
            state_path=args.state,
            state_freeze=load_json(args.state_freeze),
            geometry_path=args.geometry,
            geometry_freeze=load_json(args.geometry_freeze),
            spatial_freeze=load_json(args.spatial_freeze),
            operator_freeze=load_json(args.operator_freeze),
        )
        code = 0
    except (
        OSError,
        KeyError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        BorealConfirmatoryModelError,
        BirdPredictionFreezeError,
    ) as exc:
        receipt = {
            "schema": "structural.boreal_19island_birds_prediction_freeze.v1_163",
            "status": "STOP_BEFORE_CONFIRMATORY_RESPONSE",
            "reason": str(exc),
            "confirmatory_target_values_opened": 0,
            "confirmatory_response_authorized": False,
            "counts_as_empirical_evidence": False,
        }
        prediction_text = None
        code = 2

    if prediction_text is not None:
        args.predictions.parent.mkdir(parents=True, exist_ok=True)
        args.predictions.write_text(prediction_text, encoding="utf-8")
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
