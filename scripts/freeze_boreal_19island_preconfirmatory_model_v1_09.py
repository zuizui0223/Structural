#!/usr/bin/env python3
"""Freeze 19-island R0/R1/R2/R3/C models and confirmatory predictions."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
from typing import Mapping, Sequence

from scripts.freeze_boreal_19island_dual_isolation_operator_v1_00 import (
    freeze as freeze_operator,
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
    BorealDualIsolationOperatorError,
    source_features,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    ROOT / "development/boreal_19island_preconfirmatory_model_contract_v1_09.json"
)
DEFAULT_PILOT_FREEZE = (
    ROOT / "development/boreal_19island_pilot_freeze_v1_08.json"
)
DEFAULT_PILOT_EXECUTION = (
    ROOT / "development/boreal_19island_pilot_execution_v1_08.json"
)
DEFAULT_PILOT_SNAPSHOT = (
    ROOT / "development/boreal_19island_pilot_training_snapshot_v1_08.json"
)
DEFAULT_STATE = (
    ROOT / "development/boreal_19island_state_reference_v0_99.csv"
)
DEFAULT_STATE_FREEZE = (
    ROOT / "development/boreal_19island_state_reference_freeze_v0_99.json"
)
DEFAULT_GEOMETRY = (
    ROOT / "development/boreal_19island_safe_geometry_v0_97.csv"
)
DEFAULT_GEOMETRY_FREEZE = (
    ROOT / "development/boreal_19island_safe_geometry_freeze_v0_97.json"
)
DEFAULT_SPATIAL_FREEZE = (
    ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
)
DEFAULT_OPERATOR_FREEZE = (
    ROOT / "development/boreal_19island_source_operator_freeze_v1_01.json"
)
DEFAULT_OPERATOR_CONTRACT = (
    ROOT / "development/boreal_19island_dual_isolation_operator_contract_v1_00.json"
)
DEFAULT_LEGACY_OPERATOR = (
    ROOT / "development/boreal_dual_isolation_operator_contract_v0_83.json"
)
SHA64 = re.compile(r"^[0-9a-f]{64}$")


class Boreal19PreconfirmatoryError(RuntimeError):
    pass


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Boreal19PreconfirmatoryError(
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


def _require_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or not SHA64.fullmatch(value):
        raise Boreal19PreconfirmatoryError(f"invalid SHA-256: {label}")
    return value


def _parse_number(value: object) -> float:
    text = str(value).strip()
    try:
        out = (
            float.fromhex(text)
            if text.lower().startswith(("0x", "+0x", "-0x"))
            else float(text)
        )
    except ValueError as exc:
        raise Boreal19PreconfirmatoryError("invalid numeric predictor") from exc
    if not math.isfinite(out):
        raise Boreal19PreconfirmatoryError("nonfinite numeric predictor")
    return out


def _parse_table(
    path: Path,
    *,
    expected_sha256: str,
    expected_header: Sequence[str],
    expected_order: Sequence[str],
    label: str,
) -> dict[str, dict[str, float]]:
    if sha256_file(path) != expected_sha256:
        raise Boreal19PreconfirmatoryError(f"{label} file SHA mismatch")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != tuple(expected_header):
            raise Boreal19PreconfirmatoryError(f"{label} header drift")
        rows = list(reader)
    if [str(row["Island"]).strip() for row in rows] != list(expected_order):
        raise Boreal19PreconfirmatoryError(f"{label} island order drift")
    out: dict[str, dict[str, float]] = {}
    for row in rows:
        island = str(row["Island"]).strip()
        if not island or island in out:
            raise Boreal19PreconfirmatoryError(
                f"{label} blank/duplicate island"
            )
        out[island] = {
            column: _parse_number(row[column])
            for column in expected_header
            if column != "Island"
        }
    return out


def _parse_geometry(
    path: Path,
    freeze: Mapping,
) -> dict[str, tuple[float, float]]:
    if freeze.get("schema") != (
        "structural.boreal_19island_safe_geometry_freeze.v0_97"
    ):
        raise Boreal19PreconfirmatoryError("unexpected geometry freeze schema")
    if freeze.get("status") != (
        "SAFE_GEOMETRY_COMMITTED_RESPONSE_INDEPENDENTLY"
    ):
        raise Boreal19PreconfirmatoryError("geometry freeze did not qualify")
    expected_order = tuple(freeze.get("island_order") or ())
    rows = _parse_table(
        path,
        expected_sha256=_require_sha(
            freeze.get("geometry_sha256"),
            "geometry",
        ),
        expected_header=("Island", "Lat", "Long"),
        expected_order=expected_order,
        label="geometry",
    )
    return {
        island: (rows[island]["Lat"], rows[island]["Long"])
        for island in expected_order
    }


def _validate_state(
    path: Path,
    freeze: Mapping,
    *,
    required_identity: Mapping,
) -> tuple[tuple[str, ...], dict[str, dict[str, float]]]:
    if freeze.get("schema") != (
        "structural.boreal_19island_state_reference_freeze.v0_99"
    ):
        raise Boreal19PreconfirmatoryError("unexpected state freeze schema")
    if freeze.get("status") != (
        "STATE_REFERENCE_COMMITTED_RESPONSE_INDEPENDENTLY"
    ):
        raise Boreal19PreconfirmatoryError("state freeze did not qualify")
    state_sha = _require_sha(
        freeze.get("state_reference_sha256"),
        "state reference",
    )
    if state_sha != required_identity["state_reference_sha256"]:
        raise Boreal19PreconfirmatoryError("state reference identity drift")
    order = tuple(freeze.get("island_order") or ())
    if len(order) != 19 or len(set(order)) != 19:
        raise Boreal19PreconfirmatoryError("state population is not exact 19")
    header = (
        "Island",
        "PC1",
        "PC2",
        "PC3",
        "TSF_Z",
        "LOG_AREA_Z",
        "LOG_MAINLAND_DISTANCE_Z",
    )
    return order, _parse_table(
        path,
        expected_sha256=state_sha,
        expected_header=header,
        expected_order=order,
        label="state reference",
    )


def _validate_pilot(
    pilot_freeze: Mapping,
    execution: Mapping,
    snapshot: Mapping,
    *,
    required_identity: Mapping,
    execution_file_sha256: str,
    snapshot_file_sha256: str,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    dict[str, tuple[int, ...]],
]:
    if pilot_freeze.get("schema") != (
        "structural.boreal_19island_pilot_freeze.v1_08"
    ):
        raise Boreal19PreconfirmatoryError("unexpected pilot freeze schema")
    if pilot_freeze.get("status") != (
        "BURNED_PILOT_COMMITTED_MODEL_SNAPSHOT_READY"
    ):
        raise Boreal19PreconfirmatoryError("pilot freeze did not qualify")
    if pilot_freeze.get("confirmatory_model_freeze_may_be_built") is not True:
        raise Boreal19PreconfirmatoryError(
            "pilot freeze does not authorize model freeze"
        )
    if execution_file_sha256 != required_identity[
        "pilot_execution_file_sha256"
    ]:
        raise Boreal19PreconfirmatoryError("pilot execution file SHA drift")
    if snapshot_file_sha256 != required_identity[
        "pilot_snapshot_file_sha256"
    ]:
        raise Boreal19PreconfirmatoryError("pilot snapshot file SHA drift")
    if pilot_freeze.get("file_sha256", {}).get(
        "execution_receipt"
    ) != execution_file_sha256:
        raise Boreal19PreconfirmatoryError("pilot freeze/execution SHA mismatch")
    if pilot_freeze.get("file_sha256", {}).get(
        "training_snapshot"
    ) != snapshot_file_sha256:
        raise Boreal19PreconfirmatoryError("pilot freeze/snapshot SHA mismatch")

    if execution.get("schema") != (
        "structural.boreal_19island_burned_pilot_execution.v1_07"
    ):
        raise Boreal19PreconfirmatoryError("unexpected pilot execution schema")
    if execution.get("status") != (
        "QUALIFIED_TO_FREEZE_19ISLAND_CONFIRMATORY_MODEL_WITH_PILOT_SNAPSHOT"
    ):
        raise Boreal19PreconfirmatoryError("pilot execution did not qualify")
    if execution.get("authorization_consumed") is not True:
        raise Boreal19PreconfirmatoryError("pilot authorization not consumed")
    if execution.get("pilot_response_opened") is not True:
        raise Boreal19PreconfirmatoryError("pilot response opening not recorded")
    if execution.get("confirmatory_target_values_parsed") != 0:
        raise Boreal19PreconfirmatoryError(
            "confirmatory target boundary violated"
        )
    if execution.get("excluded_target_values_parsed") != 0:
        raise Boreal19PreconfirmatoryError("excluded target boundary violated")
    if execution.get("confirmatory_response_authorized") is not False:
        raise Boreal19PreconfirmatoryError(
            "confirmatory response already authorized"
        )
    if execution.get("counts_as_empirical_evidence") is not False:
        raise Boreal19PreconfirmatoryError("pilot evidence ceiling violated")
    if execution.get("predictive_denominator_contribution") != 0:
        raise Boreal19PreconfirmatoryError(
            "pilot predictive denominator is nonzero"
        )

    if snapshot.get("schema") != (
        "structural.boreal_19island_pilot_training_snapshot.v1_07"
    ):
        raise Boreal19PreconfirmatoryError("unexpected pilot snapshot schema")
    if snapshot.get("status") != (
        "PILOT_TRAINING_SNAPSHOT_FROZEN_FROM_SINGLE_OPEN"
    ):
        raise Boreal19PreconfirmatoryError("pilot snapshot did not qualify")
    if snapshot.get("qualified_for_confirmatory_model_freeze") is not True:
        raise Boreal19PreconfirmatoryError(
            "pilot snapshot does not qualify for model freeze"
        )
    if snapshot.get("confirmatory_target_values_parsed") != 0:
        raise Boreal19PreconfirmatoryError(
            "snapshot confirmatory target boundary violated"
        )
    if snapshot.get("excluded_target_values_parsed") != 0:
        raise Boreal19PreconfirmatoryError(
            "snapshot excluded target boundary violated"
        )
    if snapshot.get("confirmatory_occurrence_values_stored") is not False:
        raise Boreal19PreconfirmatoryError(
            "snapshot stores confirmatory occurrence"
        )
    if snapshot.get("excluded_occurrence_values_stored") is not False:
        raise Boreal19PreconfirmatoryError(
            "snapshot stores excluded occurrence"
        )

    fingerprint = _require_sha(
        snapshot.get("snapshot_fingerprint"),
        "pilot snapshot fingerprint",
    )
    snapshot_core = dict(snapshot)
    snapshot_core.pop("snapshot_fingerprint", None)
    if canonical_sha256(snapshot_core) != fingerprint:
        raise Boreal19PreconfirmatoryError(
            "pilot snapshot content/fingerprint mismatch"
        )
    if fingerprint != required_identity["pilot_snapshot_fingerprint"]:
        raise Boreal19PreconfirmatoryError("pilot snapshot fingerprint drift")
    if execution.get("model_snapshot_fingerprint") != fingerprint:
        raise Boreal19PreconfirmatoryError(
            "execution/snapshot fingerprint mismatch"
        )
    if pilot_freeze.get("model_snapshot_fingerprint") != fingerprint:
        raise Boreal19PreconfirmatoryError(
            "pilot freeze/snapshot fingerprint mismatch"
        )

    species = tuple(snapshot.get("pilot_species_universe") or ())
    if len(species) != required_identity["pilot_species_universe_count"]:
        raise Boreal19PreconfirmatoryError("pilot species count drift")
    if snapshot.get("pilot_species_universe_sha256") != required_identity[
        "pilot_species_universe_sha256"
    ]:
        raise Boreal19PreconfirmatoryError("pilot species SHA drift")
    if len(species) != len(set(species)) or any(
        not isinstance(name, str) or not name for name in species
    ):
        raise Boreal19PreconfirmatoryError("invalid pilot species universe")

    pilot_order = tuple(snapshot.get("pilot_island_order") or ())
    if len(pilot_order) != 6 or len(set(pilot_order)) != 6:
        raise Boreal19PreconfirmatoryError("pilot island order drift")
    encoded = snapshot.get("targets_hex_by_island")
    if not isinstance(encoded, dict) or set(encoded) != set(pilot_order):
        raise Boreal19PreconfirmatoryError("pilot target snapshot drift")
    matrix = {
        island: decode_binary_vector_hex(
            encoded[island],
            len(species),
        )
        for island in pilot_order
    }
    if sum(len(row) for row in matrix.values()) != 594:
        raise Boreal19PreconfirmatoryError("pilot training row count drift")
    return species, pilot_order, matrix


def _replay_operator(
    *,
    geometry_path: Path,
    geometry_freeze: Mapping,
    spatial_freeze_path: Path,
    spatial_freeze: Mapping,
    state_freeze_path: Path,
    state_freeze: Mapping,
    operator_freeze: Mapping,
    operator_contract: Mapping,
    legacy_operator: Mapping,
    required_identity: Mapping,
) -> dict:
    operator, receipt = freeze_operator(
        geometry_path,
        geometry_freeze=geometry_freeze,
        spatial_freeze=spatial_freeze,
        state_freeze=state_freeze,
        contract=operator_contract,
        legacy=legacy_operator,
        spatial_freeze_sha256=sha256_file(spatial_freeze_path),
        state_freeze_sha256=sha256_file(state_freeze_path),
    )
    fingerprint = _require_sha(
        receipt.get("operator_fingerprint"),
        "operator fingerprint",
    )
    if fingerprint != required_identity["source_operator_fingerprint"]:
        raise Boreal19PreconfirmatoryError("source operator fingerprint drift")
    if operator_freeze.get("operator_fingerprint") != fingerprint:
        raise Boreal19PreconfirmatoryError(
            "operator replay/freeze fingerprint mismatch"
        )
    rendered = json.dumps(operator, indent=2, sort_keys=True) + "\n"
    if sha256_text(rendered) != required_identity[
        "source_operator_json_sha256"
    ]:
        raise Boreal19PreconfirmatoryError("source operator JSON SHA drift")
    for key in (
        "selected_k",
        "edge_count",
        "cross_validation_block_edge_count",
    ):
        if receipt.get(key) != operator_freeze.get(key):
            raise Boreal19PreconfirmatoryError(
                f"operator replay mismatch: {key}"
            )
    if receipt.get("kernel_scale_km_hex") != operator_freeze.get(
        "kernel_scale_km_hex"
    ):
        raise Boreal19PreconfirmatoryError("operator kernel-scale drift")
    return operator


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


def _csv_text(
    header: Sequence[str],
    rows: Sequence[Sequence[object]],
) -> str:
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(list(header))
    writer.writerows(rows)
    return out.getvalue()


def _constants_hex(
    constants: Mapping[str, Mapping[str, float]],
) -> dict:
    return {
        column: {
            "mean_hex": float(values["mean"]).hex(),
            "sd_hex": float(values["sd"]).hex(),
        }
        for column, values in constants.items()
    }


def freeze(
    *,
    pilot_freeze: Mapping,
    pilot_execution: Mapping,
    pilot_snapshot: Mapping,
    pilot_execution_file_sha256: str,
    pilot_snapshot_file_sha256: str,
    state_path: Path,
    state_freeze_path: Path,
    state_freeze: Mapping,
    geometry_path: Path,
    geometry_freeze: Mapping,
    spatial_freeze_path: Path,
    spatial_freeze: Mapping,
    operator_freeze: Mapping,
    operator_contract: Mapping,
    legacy_operator: Mapping,
    contract: Mapping,
) -> tuple[dict, str]:
    candidate = contract["candidate_id"]
    required = contract["required_parent_identity"]

    species, pilot_islands, pilot_matrix = _validate_pilot(
        pilot_freeze,
        pilot_execution,
        pilot_snapshot,
        required_identity=required,
        execution_file_sha256=pilot_execution_file_sha256,
        snapshot_file_sha256=pilot_snapshot_file_sha256,
    )
    if pilot_freeze.get("candidate_id") != candidate:
        raise Boreal19PreconfirmatoryError("pilot candidate identity drift")

    universe, state = _validate_state(
        state_path,
        state_freeze,
        required_identity=required,
    )
    if sha256_file(state_freeze_path) != required["state_freeze_sha256"]:
        raise Boreal19PreconfirmatoryError("state freeze file SHA drift")

    coordinates = _parse_geometry(geometry_path, geometry_freeze)
    if geometry_freeze.get("geometry_sha256") != required["geometry_sha256"]:
        raise Boreal19PreconfirmatoryError("geometry identity drift")
    if set(coordinates) != set(universe):
        raise Boreal19PreconfirmatoryError(
            "geometry/state population mismatch"
        )

    if spatial_freeze.get("schema") != (
        "structural.boreal_19island_spatial_partition_freeze.v1_00"
    ):
        raise Boreal19PreconfirmatoryError("unexpected spatial freeze schema")
    if spatial_freeze.get("status") != (
        "SPATIAL_PARTITION_COMMITTED_RESPONSE_INDEPENDENTLY"
    ):
        raise Boreal19PreconfirmatoryError("spatial freeze did not qualify")
    if sha256_file(spatial_freeze_path) != required[
        "spatial_freeze_sha256"
    ]:
        raise Boreal19PreconfirmatoryError("spatial freeze file SHA drift")
    frozen_pilot = set(spatial_freeze.get("pilot_islands") or ())
    frozen_confirmatory = set(
        spatial_freeze.get("confirmatory_islands") or ()
    )
    if set(pilot_islands) != frozen_pilot:
        raise Boreal19PreconfirmatoryError(
            "pilot snapshot/spatial population mismatch"
        )
    if frozen_pilot & frozen_confirmatory:
        raise Boreal19PreconfirmatoryError(
            "pilot/confirmatory population overlap"
        )
    if frozen_pilot | frozen_confirmatory != set(universe):
        raise Boreal19PreconfirmatoryError(
            "spatial split does not cover state population"
        )
    island_to_block = spatial_freeze.get("island_to_block")
    if not isinstance(island_to_block, dict) or set(island_to_block) != set(
        universe
    ):
        raise Boreal19PreconfirmatoryError("invalid island-to-block mapping")

    operator = _replay_operator(
        geometry_path=geometry_path,
        geometry_freeze=geometry_freeze,
        spatial_freeze_path=spatial_freeze_path,
        spatial_freeze=spatial_freeze,
        state_freeze_path=state_freeze_path,
        state_freeze=state_freeze,
        operator_freeze=operator_freeze,
        operator_contract=operator_contract,
        legacy_operator=legacy_operator,
        required_identity=required,
    )

    ladder = contract["reference_ladder"]
    r0_raw = tuple(ladder["R0"])
    r1_add_raw = tuple(ladder["R1_add"])
    r2_raw = (
        "graph_degree_fraction",
        "graph_mean_shortest_path_km",
        "graph_closeness_per_km",
    )
    base_raw: dict[str, dict[str, float]] = {}
    for island in universe:
        node = operator.get("generic_node_context", {}).get(island)
        if not isinstance(node, dict):
            raise Boreal19PreconfirmatoryError(
                f"generic graph context missing: {island}"
            )
        row = dict(state[island])
        row.update({
            "graph_degree_fraction": float(node["degree_fraction"]),
            "graph_mean_shortest_path_km": float(
                node["mean_shortest_path_km"]
            ),
            "graph_closeness_per_km": float(node["closeness_per_km"]),
        })
        base_raw[island] = row

    base_columns = r0_raw + r1_add_raw + r2_raw
    base_constants = freeze_standardization(
        [base_raw[island] for island in universe],
        base_columns,
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

    if len(y) != contract["population"]["training_row_count"]:
        raise Boreal19PreconfirmatoryError("training row count drift")
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
        f"z_{column}" for column in r2_raw
    )
    r3_source = source_columns[:3]
    c_source = source_columns[3:]
    r3_columns = r2_columns + tuple(
        f"z_{column}" for column in r3_source
    )
    c_columns = r3_columns + tuple(
        f"z_{column}" for column in c_source
    )

    matrices = {name: [] for name in ("R0", "R1", "R2", "R3", "C")}
    for island, _, _, source in training_records:
        z_base = apply_standardization(
            base_raw[island],
            columns=base_columns,
            constants=base_constants,
        )
        base_map = dict(zip(base_columns, z_base))
        r0_values = tuple(base_map[column] for column in r0_raw)
        r1_values = r0_values + tuple(
            base_map[column] for column in r1_add_raw
        )
        r2_values = r1_values + tuple(
            base_map[column] for column in r2_raw
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
    columns = {
        "R0": r0_columns,
        "R1": r1_columns,
        "R2": r2_columns,
        "R3": r3_columns,
        "C": c_columns,
    }
    fits = {
        name: fit_ridge_logistic(
            matrices[name],
            y,
            columns=columns[name],
            ridge_lambda=float(settings["ridge_lambda"]),
            max_iterations=int(settings["max_iterations"]),
            tolerance=float(settings["tolerance"]),
        )
        for name in ("R0", "R1", "R2", "R3", "C")
    }

    confirmatory_blocks = tuple(
        spatial_freeze.get("confirmatory_block_ids") or ()
    )
    confirmatory_by_block = {
        block: sorted(
            island
            for island in universe
            if island_to_block[island] == block
        )
        for block in confirmatory_blocks
    }
    if any(not islands for islands in confirmatory_by_block.values()):
        raise Boreal19PreconfirmatoryError(
            "empty confirmatory spatial block"
        )

    prediction_rows = []
    clip = tuple(float(v) for v in settings["probability_clip"])
    for block in confirmatory_blocks:
        for island in confirmatory_by_block[block]:
            z_base = apply_standardization(
                base_raw[island],
                columns=base_columns,
                constants=base_constants,
            )
            base_map = dict(zip(base_columns, z_base))
            r0_values = tuple(base_map[column] for column in r0_raw)
            r1_values = r0_values + tuple(
                base_map[column] for column in r1_add_raw
            )
            r2_values = r1_values + tuple(
                base_map[column] for column in r2_raw
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

    if len(prediction_rows) != contract["population"][
        "prediction_row_count"
    ]:
        raise Boreal19PreconfirmatoryError("prediction row count drift")
    header = tuple(contract["prediction_surface"]["columns"])
    prediction_text = _csv_text(header, prediction_rows)

    models = {
        name: fit_mapping(fits[name])
        for name in ("R0", "R1", "R2", "R3", "C")
    }
    receipt = {
        "schema": (
            "structural.boreal_19island_preconfirmatory_model_freeze.v1_09"
        ),
        "status": contract["success_ceiling"]["status"],
        "candidate_id": candidate,
        "pilot_snapshot_fingerprint": pilot_snapshot[
            "snapshot_fingerprint"
        ],
        "pilot_species_universe_sha256": pilot_snapshot[
            "pilot_species_universe_sha256"
        ],
        "source_operator_fingerprint": operator_freeze[
            "operator_fingerprint"
        ],
        "state_reference_sha256": state_freeze[
            "state_reference_sha256"
        ],
        "geometry_sha256": geometry_freeze["geometry_sha256"],
        "species_count": len(species),
        "pilot_island_count": len(pilot_islands),
        "confirmatory_island_count": len(frozen_confirmatory),
        "confirmatory_block_count": len(confirmatory_blocks),
        "training_row_count": len(y),
        "prediction_row_count": len(prediction_rows),
        "base_standardization": _constants_hex(base_constants),
        "source_standardization": _constants_hex(source_constants),
        "models": models,
        "models_fingerprint": canonical_sha256(models),
        "prediction_surface_sha256": sha256_text(prediction_text),
        "prediction_surface_columns": list(header),
        "primary_scoring": dict(contract["primary_scoring"]),
        "confirmatory_target_values_opened": 0,
        "excluded_target_values_opened": 0,
        "confirmatory_response_authorized": False,
        "effect_size": None,
        "prediction_score": None,
        "predictive_denominator_contribution": 0,
        "counts_as_empirical_evidence": False,
        "next_action": contract["success_ceiling"]["next_action"],
    }
    return receipt, prediction_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--pilot-freeze", type=Path, default=DEFAULT_PILOT_FREEZE)
    parser.add_argument(
        "--pilot-execution", type=Path, default=DEFAULT_PILOT_EXECUTION
    )
    parser.add_argument(
        "--pilot-snapshot", type=Path, default=DEFAULT_PILOT_SNAPSHOT
    )
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument(
        "--state-freeze", type=Path, default=DEFAULT_STATE_FREEZE
    )
    parser.add_argument("--geometry", type=Path, default=DEFAULT_GEOMETRY)
    parser.add_argument(
        "--geometry-freeze", type=Path, default=DEFAULT_GEOMETRY_FREEZE
    )
    parser.add_argument(
        "--spatial-freeze", type=Path, default=DEFAULT_SPATIAL_FREEZE
    )
    parser.add_argument(
        "--operator-freeze", type=Path, default=DEFAULT_OPERATOR_FREEZE
    )
    parser.add_argument(
        "--operator-contract", type=Path, default=DEFAULT_OPERATOR_CONTRACT
    )
    parser.add_argument(
        "--legacy-operator", type=Path, default=DEFAULT_LEGACY_OPERATOR
    )
    parser.add_argument("--predictions", type=Path)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    try:
        contract = _load(args.contract)
        if contract.get("schema") != (
            "structural.boreal_19island_preconfirmatory_model_contract.v1_09"
        ):
            raise Boreal19PreconfirmatoryError(
                "unexpected v1.09 contract schema"
            )
        receipt, prediction_text = freeze(
            pilot_freeze=_load(args.pilot_freeze),
            pilot_execution=_load(args.pilot_execution),
            pilot_snapshot=_load(args.pilot_snapshot),
            pilot_execution_file_sha256=sha256_file(args.pilot_execution),
            pilot_snapshot_file_sha256=sha256_file(args.pilot_snapshot),
            state_path=args.state,
            state_freeze_path=args.state_freeze,
            state_freeze=_load(args.state_freeze),
            geometry_path=args.geometry,
            geometry_freeze=_load(args.geometry_freeze),
            spatial_freeze_path=args.spatial_freeze,
            spatial_freeze=_load(args.spatial_freeze),
            operator_freeze=_load(args.operator_freeze),
            operator_contract=_load(args.operator_contract),
            legacy_operator=_load(args.legacy_operator),
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
        Boreal19PreconfirmatoryError,
    ) as exc:
        receipt = {
            "schema": (
                "structural.boreal_19island_preconfirmatory_model_freeze.v1_09"
            ),
            "status": "STOP",
            "reason": str(exc),
            "confirmatory_target_values_opened": 0,
            "excluded_target_values_opened": 0,
            "confirmatory_response_authorized": False,
            "effect_size": None,
            "prediction_score": None,
            "predictive_denominator_contribution": 0,
            "counts_as_empirical_evidence": False,
        }
        prediction_text = None
        code = 2
    else:
        code = 0

    if prediction_text is not None and args.predictions is not None:
        args.predictions.parent.mkdir(parents=True, exist_ok=True)
        args.predictions.write_text(prediction_text, encoding="utf-8")
    rendered = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
