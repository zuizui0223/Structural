from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/authorize_boreal_19island_pilot_response_v1_05.py"
CONTRACT = (
    ROOT / "development/boreal_19island_pilot_response_authorization_contract_v1_05.json"
)
FREEZE = (
    ROOT / "development/boreal_19island_pilot_authorization_freeze_v1_06.json"
)
INTAKE = ROOT / "development/boreal_19island_response_sealed_intake_v1_02.json"
INTAKE_RECEIPT = (
    ROOT / "development/boreal_19island_response_sealed_intake_receipt_v1_02.json"
)
PREPILOT_FREEZE = ROOT / "development/boreal_19island_prepilot_freeze_v1_04.json"
PROTOCOL = ROOT / "development/boreal_19island_v031_protocol_v1_03.json"
QUALITY = ROOT / "development/boreal_19island_v042_quality_contract_v1_03.json"
PREPILOT_RECEIPT = (
    ROOT / "development/boreal_19island_prepilot_receipt_v1_03.json"
)
METADATA = ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
FULL_UNIVERSE = (
    ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"
)


def load_module():
    spec = importlib.util.spec_from_file_location("boreal19_auth_v105_freeze", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def regenerate():
    module = load_module()
    auth = module.authorize(
        load(INTAKE),
        load(INTAKE_RECEIPT),
        load(PREPILOT_FREEZE),
        load(PROTOCOL),
        load(QUALITY),
        load(PREPILOT_RECEIPT),
        load(METADATA),
        load(FULL_UNIVERSE),
        contract=load(CONTRACT),
        observed_file_sha256={
            "protocol": sha(PROTOCOL),
            "quality_contract": sha(QUALITY),
            "prepilot_receipt": sha(PREPILOT_RECEIPT),
        },
    )
    raw = (json.dumps(auth, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return auth, hashlib.sha256(raw).hexdigest()


def test_v106_freeze_exactly_replays_v105_authorization():
    freeze = load(FREEZE)
    auth, auth_sha = regenerate()

    expected = freeze["authorization"]
    assert auth["schema"] == expected["schema"]
    assert auth["status"] == expected["status"]
    assert auth["authorization_fingerprint"] == expected["authorization_fingerprint"]
    assert auth_sha == expected["authorization_json_sha256"]
    assert auth["parent_intake_fingerprint"] == expected["parent_intake_fingerprint"]
    assert auth["protocol_fingerprint"] == expected["protocol_fingerprint"]
    assert auth["quality_contract_fingerprint"] == (
        expected["quality_contract_fingerprint"]
    )
    assert auth["source_operator_fingerprint"] == (
        expected["source_operator_fingerprint"]
    )


def test_v106_population_and_response_ceiling_are_exact():
    freeze = load(FREEZE)
    assert freeze["population"] == {
        "full_source_island_count": 42,
        "analysis_island_count": 19,
        "pilot_island_count": 6,
        "confirmatory_island_count": 13,
        "excluded_island_count": 23,
        "pilot_block_count": 3,
        "confirmatory_block_count": 7,
    }
    boundary = freeze["response_boundary"]
    assert boundary["response_file_downloaded_by_authorization_workflow"] is False
    assert boundary["response_values_opened"] is False
    assert boundary["pilot_response_authorized"] is True
    assert boundary["confirmatory_response_authorized"] is False
    assert boundary["authorization_consumed"] is False
    assert boundary["counts_as_empirical_evidence"] is False
    assert boundary["predictive_denominator_contribution"] == 0
    assert freeze["execution_may_be_built"] is True


def test_v106_artifact_provenance_is_exact():
    freeze = load(FREEZE)
    source = freeze["source_execution"]
    assert source == {
        "workflow": ".github/workflows/boreal-19island-pilot-authorization-v1_05.yml",
        "run_id": 36444583063,
        "head_sha": "4f5148f3273aa88917e056b281742e7013982dea",
        "artifact_id": 10980520411,
        "artifact_digest": (
            "sha256:962b4c72991d223504de6c16916f43aff3344fe599f5139e4fe88fbfa8c757f4"
        ),
    }
