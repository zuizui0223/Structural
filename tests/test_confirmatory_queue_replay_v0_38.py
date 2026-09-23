from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.validate_confirmatory_queue_v0_38 import (
    QueueValidationError,
    validate_queue,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/confirmatory_admission_v0_38/queue.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_nonempty_raw_pilot_replay_fixture_passes():
    assert validate_queue(FIXTURE) == 1


def test_wrong_raw_pilot_hash_stops_before_admission(tmp_path: Path):
    queue = load_fixture()
    queue["entries"][0]["pilot_input_sha256"] = "0" * 64
    path = tmp_path / "bad_hash_queue.json"
    path.write_text(json.dumps(queue), encoding="utf-8")

    with pytest.raises(QueueValidationError, match="SHA-256 mismatch"):
        validate_queue(path)


def test_tampered_raw_pilot_cannot_reuse_stored_pass_result(tmp_path: Path):
    queue = load_fixture()
    entry = queue["entries"][0]
    entry["pilot_input_path"] = (
        "tests/fixtures/confirmatory_admission_v0_38/pilot_tampered.csv"
    )
    entry["pilot_input_sha256"] = (
        "95b691de686a4717289a97f4b5e5f29552f6257256010a4f35af324e47bd2cad"
    )
    path = tmp_path / "tampered_replay_queue.json"
    path.write_text(json.dumps(queue), encoding="utf-8")

    with pytest.raises(QueueValidationError, match="not exact v0.32 replay"):
        validate_queue(path)
