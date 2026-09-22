from __future__ import annotations

import json
from pathlib import Path
from zipfile import ZipFile

from structural.file_inventory import inventory_source, to_mapping


def test_directory_inventory_reads_no_semantic_content(tmp_path: Path):
    (tmp_path / "a.csv").write_text("response,value\n1,2\n", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested/site.geojson").write_text('{"type":"FeatureCollection"}', encoding="utf-8")

    result = inventory_source(tmp_path)
    payload = to_mapping(result)

    assert payload["source_type"] == "directory"
    assert payload["file_count"] == 2
    assert payload["semantic_text_parse_count"] == 0
    assert payload["response_value_parse_count"] == 0
    assert payload["model_fit_count"] == 0
    assert [row["relative_path"] for row in payload["entries"]] == [
        "a.csv", "nested/site.geojson"
    ]


def test_zip_inventory_hashes_entries_without_parsing(tmp_path: Path):
    archive = tmp_path / "bundle.zip"
    with ZipFile(archive, "w") as z:
        z.writestr("data/response.csv", "species,present\nx,1\n")
        z.writestr("data/sites.csv", "site,lat,long\na,1,2\n")

    payload = to_mapping(inventory_source(archive))
    assert payload["source_type"] == "zip"
    assert payload["file_count"] == 2
    assert all(len(row["sha256"]) == 64 for row in payload["entries"])
    assert payload["response_value_parse_count"] == 0


def test_inventory_is_deterministic(tmp_path: Path):
    (tmp_path / "b.txt").write_bytes(b"bbb")
    (tmp_path / "a.txt").write_bytes(b"aaa")
    first = to_mapping(inventory_source(tmp_path))
    second = to_mapping(inventory_source(tmp_path))
    assert first["entries"] == second["entries"]


def test_cli_contract_can_be_serialized_without_file_roles(tmp_path: Path):
    (tmp_path / "unknown.dat").write_bytes(b"123")
    payload = to_mapping(inventory_source(tmp_path))
    encoded = json.dumps(payload)
    assert "response" not in encoded.lower()
    assert "unknown.dat" in encoded
