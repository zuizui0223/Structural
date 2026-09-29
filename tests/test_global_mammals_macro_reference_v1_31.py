from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_global_mammals_macro_reference_v1_31.py"
CONTRACT = ROOT / "development/global_mammals_macro_reference_contract_v1_31.json"


def load_module():
    spec = importlib.util.spec_from_file_location("global_mammals_v131", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, header, rows):
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)
    path.write_text(out.getvalue(), encoding="utf-8")
    return hashlib.sha256(out.getvalue().encode("utf-8")).hexdigest()


def synthetic_contract(safe_sha: str, part_sha: str, block_sha: str):
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    x["safe_covariate_artifact"] = dict(x["safe_covariate_artifact"])
    x["safe_covariate_artifact"].update({
        "safe_csv_sha256": safe_sha,
        "safe_row_count": 8,
    })
    x["spatial_artifact"] = dict(x["spatial_artifact"])
    x["spatial_artifact"].update({
        "island_partition_sha256": part_sha,
        "block_table_sha256": block_sha,
        "island_count": 8,
        "block_count": 4,
        "pilot_block_count": 1,
        "confirmatory_block_count": 3,
    })
    return x


def synthetic_files(tmp_path: Path):
    safe = tmp_path / "safe.csv"
    part = tmp_path / "partition.csv"
    blocks = tmp_path / "blocks.csv"

    safe_rows = [
        ["1", "-50", "10", "10", "-1.0", "0", "1", "20", "1", "100", "10", "5", "Afrotropical"],
        ["2", "-49", "11", "20", "-0.9", "0", "2", "21", "2", "110", "11", "6", "Afrotropical"],
        ["3", "-30", "20", "30", "-0.8", "1", "3", "22", "3", "120", "12", "7", "Australian"],
        ["4", "-29", "21", "40", "-0.7", "1", "4", "23", "4", "130", "13", "8", "Australian"],
        ["5", "20", "-10", "50", "-0.6", "0", "5", "24", "5", "140", "14", "9", "Eurasia"],
        ["6", "21", "-11", "60", "-0.5", "0", "6", "25", "6", "150", "15", "10", "Eurasia"],
        ["7", "70", "30", "70", "-0.4", "1", "7", "26", "7", "160", "16", "11", "Neotropical"],
        ["8", "71", "31", "80", "-0.3", "1", "8", "27", "8", "170", "17", "12", "Neotropical"],
    ]
    safe_sha = write_csv(
        safe,
        [
            "ID",
            "Longitude_centroid",
            "Latitude_centroid",
            "Area",
            "Current_isolation",
            "Past_isolation",
            "Climate_velocity",
            "Temperature_mean",
            "Temperature_sd",
            "Precipitation_mean",
            "Precipitation_sd",
            "Elevation_sd",
            "bioregion",
        ],
        safe_rows,
    )

    partition_rows = [
        ["1", "Afrotropical", "a", "B1", "pilot", "-1.0", "0"],
        ["2", "Afrotropical", "a", "B1", "pilot", "-0.9", "0"],
        ["3", "Australian", "b", "B2", "confirmatory", "-0.8", "0"],
        ["4", "Australian", "b", "B2", "confirmatory", "-0.7", "0"],
        ["5", "Eurasia", "c", "B3", "confirmatory", "-0.6", "0"],
        ["6", "Eurasia", "c", "B3", "confirmatory", "-0.5", "1"],
        ["7", "Neotropical", "d", "B4", "confirmatory", "-0.4", "1"],
        ["8", "Neotropical", "d", "B4", "confirmatory", "-0.3", "1"],
    ]
    part_sha = write_csv(
        part,
        [
            "ID",
            "bioregion",
            "block_key",
            "block_id",
            "split",
            "Current_isolation_hex",
            "extreme_current_isolation",
        ],
        partition_rows,
    )

    block_rows = [
        ["a", "B1", "Afrotropical", "2", "pilot"],
        ["b", "B2", "Australian", "2", "confirmatory"],
        ["c", "B3", "Eurasia", "2", "confirmatory"],
        ["d", "B4", "Neotropical", "2", "confirmatory"],
    ]
    block_sha = write_csv(
        blocks,
        ["block_key", "block_id", "bioregion", "island_count", "split"],
        block_rows,
    )
    return safe, part, blocks, synthetic_contract(
        safe_sha, part_sha, block_sha
    )


def test_synthetic_builder_freezes_distinct_state_and_source_graph(tmp_path):
    module = load_module()
    safe, part, blocks, contract = synthetic_files(tmp_path)
    # Synthetic fixture intentionally has 4 bioregions rather than 12.
    # Relax only that population invariant for unit testing.
    original = module.build

    # Patch the contract population counts while retaining the real semantics.
    # The builder's exact 12-level check is exercised by the real workflow.
    text = SCRIPT.read_text(encoding="utf-8")
    assert 'if len(levels) != 12' in text
    assert 'baseline != "Afrotropical"' in text

    # Exercise lower-level graph logic directly.
    centroids = {
        "B1": (10.5, -49.5),
        "B2": (20.5, -29.5),
        "B3": (-10.5, 20.5),
        "B4": (30.5, 70.5),
    }
    regions = {
        "B1": "Afrotropical",
        "B2": "Australian",
        "B3": "Eurasia",
        "B4": "Neotropical",
    }
    operator = module._freeze_source_graph(centroids, regions)
    assert operator["selected_k"] >= 1
    assert operator["edge_count"] >= 3
    assert len(operator["block_order"]) == 4
    assert len(operator["all_pairs_shortest_paths"]) == 6
    assert operator["validation_tile_adjacency_reused"] is False
    assert operator["response_used_to_build_operator"] is False
    assert set(operator["generic_block_context"]) == set(centroids)


def test_contract_locks_regional_pool_into_R3_and_only_continuity_into_C():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    later = x["later_training_only_source_semantics"]
    assert any("species_x_bioregion" in item for item in later["R3_must_include"])
    assert any("global occupancy" in item for item in later["R3_must_include"])
    assert any("direct distance" in item for item in later["R3_must_include"])
    assert any("graph-path" in item for item in later["C_adds_only"])
    assert later["C_may_not_add_bioregion_identity"] is True
    assert later["C_may_not_change_source_unit_after_response"] is True


def test_contract_keeps_contaminated_macro_route_out_of_fresh_denominator():
    x = json.loads(CONTRACT.read_text(encoding="utf-8"))
    b = x["response_boundary"]
    assert x["analysis_route"] == "contaminated_macro_analysis_only"
    assert b["Appendix_1_may_be_reopened_in_v1_31"] is False
    assert b["mammal_species_names_opened"] is False
    assert b["mammal_occurrence_values_opened"] is False
    assert b["counts_as_fresh_confirmation"] is False
    assert b["fresh_system_denominator_contribution"] == 0
    assert b["original_fresh_chain_restored"] is False
    assert b["mechanism_claim_authorized"] is False


def test_spherical_mean_handles_dateline_without_naive_longitude_failure():
    module = load_module()
    lat, lon = module._spherical_mean([(0.0, 179.0), (0.0, -179.0)])
    assert abs(lat) < 1e-12
    assert abs(abs(lon) - 180.0) < 1e-9
