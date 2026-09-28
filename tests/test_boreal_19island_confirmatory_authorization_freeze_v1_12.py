from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUTH = (
    ROOT / "development/boreal_19island_confirmatory_authorization_v1_12.json"
)
FREEZE = (
    ROOT
    / "development/boreal_19island_confirmatory_authorization_freeze_v1_12.json"
)
SCRIPT = (
    ROOT
    / "scripts/authorize_boreal_19island_confirmatory_response_v1_11.py"
)
CONTRACT = (
    ROOT
    / "development/boreal_19island_confirmatory_authorization_contract_v1_11.json"
)
PRECONFIRM = (
    ROOT / "development/boreal_19island_preconfirmatory_freeze_v1_10.json"
)
PREDICTIONS = (
    ROOT / "development/boreal_19island_confirmatory_predictions_v1_10.csv"
)
MODEL = (
    ROOT
    / "development/boreal_19island_preconfirmatory_model_receipt_v1_10.json"
)
SNAPSHOT = (
    ROOT / "development/boreal_19island_pilot_training_snapshot_v1_08.json"
)
SPATIAL = (
    ROOT / "development/boreal_19island_spatial_partition_freeze_v1_00.json"
)
METADATA = (
    ROOT / "development/boreal_lake_islands_dryad_metadata_result_v0_65.json"
)
FULL = ROOT / "development/boreal_lake_islands_thesis_safe_table_v0_69.json"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("boreal19_auth_v111_freeze", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v112_exact_authorization_file_identity_and_fingerprint():
    auth = load(AUTH)
    freeze = load(FREEZE)

    assert sha(AUTH) == (
        "0b5bd2fefdc7fdfa2d0e0384fd97d70ed6185196be4e331250ade20fa89c9791"
    )
    assert auth["authorization_fingerprint"] == (
        "9c298caa914dac454ff5cda3229abbdc971e299791e6dc582c83a10f1a12146d"
    )
    core = dict(auth)
    fingerprint = core.pop("authorization_fingerprint")
    module = load_module()
    assert module.canonical_sha256(core) == fingerprint

    assert freeze["status"] == (
        "CONFIRMATORY_AUTHORIZATION_COMMITTED_BY_FINGERPRINT_RESPONSE_UNOPENED"
    )
    assert freeze["authorization"]["authorization_json_sha256"] == sha(AUTH)
    assert freeze["authorization"]["authorization_fingerprint"] == fingerprint
    assert freeze["response_boundary"] == {
        "response_file_downloaded_by_authorization_workflow": False,
        "response_values_opened": False,
        "confirmatory_response_authorized": True,
        "authorization_consumed": False,
        "counts_as_empirical_evidence": False,
        "predictive_denominator_contribution": 0,
    }
    assert freeze["scoring_execution_may_be_built"] is True


def test_v112_authorization_exact_replays_from_committed_v110():
    module = load_module()
    rebuilt = module.authorize(
        preconfirmatory_freeze=load(PRECONFIRM),
        model_receipt=load(MODEL),
        predictions_text=PREDICTIONS.read_text(encoding="utf-8"),
        pilot_snapshot=load(SNAPSHOT),
        spatial_freeze=load(SPATIAL),
        metadata=load(METADATA),
        full_universe=load(FULL),
        contract=load(CONTRACT),
        preconfirmatory_freeze_sha256=sha(PRECONFIRM),
        model_receipt_sha256=sha(MODEL),
        predictions_sha256=sha(PREDICTIONS),
    )
    assert rebuilt == load(AUTH)


def test_v112_source_artifact_provenance_is_exact():
    freeze = load(FREEZE)
    assert freeze["source_execution"] == {
        "workflow": (
            ".github/workflows/"
            "boreal-19island-confirmatory-authorization-v1_11.yml"
        ),
        "run_id": 36483040760,
        "head_sha": "7e86ced326f00f7cb57b60862b6459c15d879a8f",
        "artifact_id": 10997491142,
        "artifact_digest": (
            "sha256:98f2f28553137df56747037ebe27da8478011c47a88ebe384d4b7789591b4316"
        ),
    }
