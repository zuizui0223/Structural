from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "development/global_mammals_opaque_transport_receipt_v1_18.json"
FREEZE = ROOT / "development/global_mammals_opaque_transport_freeze_v1_18.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: dict) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def test_exact_v117_receipt_is_durably_frozen():
    receipt = load(RECEIPT)
    freeze = load(FREEZE)
    files = freeze["files"]["transport_receipt"]

    assert sha(RECEIPT) == files["committed_json_sha256"] == (
        "8a8312451cb4f66b4b2d733090c7279f099f06f75cbab74592364fd8ef98f717"
    )
    assert canonical_sha(receipt) == files["canonical_json_sha256"] == (
        "e24b16c622687bc9878d9d1a0579e1ce3984e899400b082798694cbc55dc0d4c"
    )
    assert freeze["source_execution"]["workflow_run_id"] == 36510453244
    assert freeze["source_execution"]["workflow_head_sha"] == (
        "ee5c20524ce9f761fa4687f7472a31ec7cc0a2c5"
    )
    assert freeze["source_execution"]["artifact_id"] == 11009231174
    assert freeze["source_execution"]["artifact_digest"] == (
        "sha256:1388d0279822a465e371f42f4be09bfab51750653dd46e713d79008dd74480d6"
    )


def test_transport_success_opened_zero_response_semantics():
    receipt = load(RECEIPT)
    boundary = load(FREEZE)["semantic_boundary"]

    assert receipt["status"] == "EXACT_RESPONSE_BYTES_VERIFIED_SEMANTICS_UNOPENED"
    assert receipt["response_bytes_read_as_opaque"] == 60486843
    assert receipt["target"] == {
        "dryad_file_id": 3242161,
        "name": "Appendix_1_presence_absence.csv",
        "sha256": (
            "32bf3f077af7e66ddcbf05fc675d6c51656f59111c27cd37129e14c658430fa6"
        ),
        "size_bytes": 60486843,
    }
    assert receipt["header_decoded"] is False
    assert receipt["routing_ids_decoded"] == 0
    assert receipt["species_header_fields_decoded"] == 0
    assert receipt["occurrence_values_decoded"] == 0
    assert receipt["biological_response_values_opened"] is False
    assert receipt["counts_as_empirical_evidence"] is False
    assert receipt["fresh_system_denominator_contribution"] == 0
    assert boundary["opaque_response_bytes_verified"] is True
    assert boundary["biological_response_values_opened"] is False


def test_only_separate_id_crosswalk_is_authorized_next():
    x = load(FREEZE)["next_gate"]
    assert x["authorized"] is True
    assert x["species_header_decode_authorized"] is False
    assert x["occurrence_value_decode_authorized"] is False
    assert x["same_revision_response_crosswalk_performed"] is False
    assert "first CSV field" in x["action"]
    assert "expected 5592 data rows" in x["action"]
