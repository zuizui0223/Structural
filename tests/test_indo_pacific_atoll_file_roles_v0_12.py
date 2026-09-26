from __future__ import annotations

import json
from pathlib import Path

from structural.file_roles import apply_file_role_firewall, assignments_from_mapping


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "development/indo_pacific_atoll_archive_inventory_v0_11.json"
ROLES = ROOT / "development/indo_pacific_atoll_file_roles_v0_12.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_atoll_file_roles_cover_exact_inventory_and_fail_closed():
    inventory = load(INVENTORY)
    roles = load(ROLES)
    result = apply_file_role_firewall(
        inventory,
        assignments_from_mapping(roles),
    )

    assert inventory["file_count"] == 25
    assert inventory["semantic_text_parse_count"] == 0
    assert inventory["response_value_parse_count"] == 0
    assert inventory["model_fit_count"] == 0

    assert len(result.response_files) == 14
    assert len(result.code_files) == 1
    assert len(result.allowed_for_semantic_open) == 10
    assert result.unknown_files == ()
    assert result.mixed_files == ()


def test_all_biodiversity_and_seabird_tables_remain_closed():
    inventory = load(INVENTORY)
    roles = load(ROLES)
    result = apply_file_role_firewall(
        inventory,
        assignments_from_mapping(roles),
    )

    denied = set(result.denied_for_semantic_open)
    for entry in inventory["entries"]:
        name = Path(entry["relative_path"]).name
        if name.startswith("atoll_diversity_") or name.startswith(
            "atoll_seabird_population_"
        ):
            assert entry["relative_path"] in denied
            assert entry["relative_path"] in result.response_files

    plant = (
        "Steibl_2026_Indo_Pacific_Atolls_Dataset/"
        "atoll_diversity_plants.csv"
    )
    assert plant in result.response_files
    assert plant not in result.allowed_for_semantic_open


def test_notebook_closed_and_geometry_safe():
    inventory = load(INVENTORY)
    roles = load(ROLES)
    result = apply_file_role_firewall(
        inventory,
        assignments_from_mapping(roles),
    )

    notebook = (
        "Steibl_2026_Indo_Pacific_Atolls_Dataset/notebook.ipynb"
    )
    kml = (
        "Steibl_2026_Indo_Pacific_Atolls_Dataset/atoll_shapefiles.kml"
    )

    assert notebook in result.code_files
    assert notebook in result.denied_for_semantic_open
    assert kml in result.allowed_for_semantic_open
