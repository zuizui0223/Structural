from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from structural import AdmissionStatus, protocol_from_mapping

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/check_connectivity_empirical_protocol.py"


def load_cli():
    spec = importlib.util.spec_from_file_location("connectivity_admission_cli", CLI)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_qualified_example_returns_zero():
    code, payload = load_cli().check(
        ROOT / "examples/connectivity_empirical_protocol_qualified_v0_5.json"
    )
    assert code == 0
    assert payload["status"] == AdmissionStatus.QUALIFIED.value
    assert payload["reasons"] == []


def test_stop_example_returns_two():
    code, payload = load_cli().check(
        ROOT / "examples/connectivity_empirical_protocol_stop_v0_5.json"
    )
    assert code == 2
    assert payload["status"] == AdmissionStatus.STOP.value
    assert "response_already_accessed" in payload["reasons"]


def test_invalid_json_shape_returns_one(tmp_path: Path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"protocol_id": "x"}), encoding="utf-8")
    code, payload = load_cli().check(path)
    assert code == 1
    assert payload["status"] == "invalid_protocol"
    assert "missing protocol keys" in payload["reasons"][0]


def test_mapping_parser_rejects_non_boolean_flags():
    data = json.loads(
        (ROOT / "examples/connectivity_empirical_protocol_qualified_v0_5.json").read_text()
    )
    data["response_accessed"] = "false"
    with pytest.raises(ValueError, match="must be boolean"):
        protocol_from_mapping(data)
