from __future__ import annotations

import json
from pathlib import Path

from scripts.authorize_mechanism_response_v0_6 import authorize


ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/mechanism_confirmatory_freeze_v0_5"
PARENT = ROOT / "tests/fixtures/mechanism_admission_v0_4/protocol.json"
STRUCTURAL_QUEUE = ROOT / "tests/fixtures/confirmatory_admission_v0_38/queue.json"
TRANSITION = ROOT / "tests/fixtures/mechanism_transition_pilot_v0_2/pilot.csv"
GENPOP = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_populations.csv"
GENPAIR = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/genetic_pairs.csv"
ENV = ROOT / "tests/fixtures/mechanism_auxiliary_gate_v0_3/environment.csv"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def authorize_lane(name: str, *, require_tracked_receipt: bool = True):
    return authorize(
        FIX / f"{name}.json",
        FIX / f"{name}_receipt.json",
        PARENT,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
        require_tracked_receipt=require_tracked_receipt,
    )


def test_all_four_tracked_freeze_receipts_authorize_exact_lane_once():
    expected = {
        "m1": "M1_contemporary_colonization",
        "m2": "M2_rescue_persistence",
        "m3": "M3_historical_colonization_legacy",
        "m4": "M4_environmental_proxy",
    }
    auth_ids = set()

    for name, lane in expected.items():
        code, out = authorize_lane(name)

        assert code == 0
        assert out["status"] == (
            "confirmatory_mechanism_response_access_authorized_once"
        )
        assert out["mechanism_lane"] == lane
        assert out["confirmatory_response_authorized"] is True
        assert out["mechanism_claim_authorized"] is False
        assert out["single_use"] is True
        assert out["response_access_consumed"] is False
        assert out["response_partition"] == ["confirm-B"]
        assert out["effect_size"] is None
        assert out["prediction_score"] is None
        assert out["predictive_denominator_contribution"] == 0
        assert out["mechanism_claim_contribution"] == 0
        assert out["ttf_handoff_authorized"] is False
        assert out["synthetic_ci_authorization"] is True
        assert out["counts_as_empirical_evidence"] is False
        assert out["next_action"] == (
            "open_exact_response_partition_once_then_record_access_before_scoring"
        )
        assert out["freeze_receipt_path"] == (
            f"tests/fixtures/mechanism_confirmatory_freeze_v0_5/"
            f"{name}_receipt.json"
        )
        assert len(out["freeze_receipt_sha256"]) == 64
        assert len(out["authorization_id"]) == 64
        auth_ids.add(out["authorization_id"])

    assert len(auth_ids) == 4


def test_untracked_freeze_receipt_is_rejected(tmp_path: Path):
    receipt = tmp_path / "receipt.json"
    receipt.write_text(
        (FIX / "m1_receipt.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    code, out = authorize(
        FIX / "m1.json",
        receipt,
        PARENT,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
        require_tracked_receipt=True,
    )

    assert code == 2
    assert out["status"] == "STOP_freeze_receipt_not_committed"
    assert out["confirmatory_response_authorized"] is False


def test_tampered_receipt_fails_exact_replay(tmp_path: Path):
    receipt = tmp_path / "receipt.json"
    value = load(FIX / "m1_receipt.json")
    value["success_rule"] = "tampered after freeze"
    write(receipt, value)

    code, out = authorize(
        FIX / "m1.json",
        receipt,
        PARENT,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
        require_tracked_receipt=False,
    )

    assert code == 2
    assert out["status"] == "STOP_committed_freeze_receipt_not_exact_replay"
    assert out["confirmatory_response_authorized"] is False


def test_protocol_drift_after_freeze_invalidates_committed_receipt(tmp_path: Path):
    protocol = load(FIX / "m1.json")
    protocol["scoring_rule"] = "changed after freeze"
    drifted = tmp_path / "m1.json"
    write(drifted, protocol)

    code, out = authorize(
        drifted,
        FIX / "m1_receipt.json",
        PARENT,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
        require_tracked_receipt=False,
    )

    assert code == 2
    assert out["status"] == "STOP_committed_freeze_receipt_not_exact_replay"


def test_response_opened_protocol_cannot_be_authorized_again(tmp_path: Path):
    protocol = load(FIX / "m2.json")
    protocol["confirmatory_response_accessed"] = True
    drifted = tmp_path / "m2.json"
    write(drifted, protocol)

    code, out = authorize(
        drifted,
        FIX / "m2_receipt.json",
        PARENT,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
        require_tracked_receipt=False,
    )

    assert code == 2
    assert out["status"] == "STOP_confirmatory_freeze_no_longer_replays"
    assert out["confirmatory_response_authorized"] is False


def test_authorization_scope_is_exact_partition_and_lane():
    code, out = authorize_lane("m3")

    assert code == 0
    assert out["authorization_scope"] == (
        "read_exact_frozen_response_partition_for_this_lane_protocol_only"
    )
    assert out["mechanism_lane"] == "M3_historical_colonization_legacy"
    assert out["response_partition"] == ["confirm-B"]
    assert out["single_use"] is True


def test_freeze_receipt_sha_contributes_to_authorization_identity(tmp_path: Path):
    code, original = authorize_lane("m4")
    assert code == 0

    receipt = tmp_path / "receipt.json"
    value = load(FIX / "m4_receipt.json")
    value["ttf_handoff_authorized"] = True
    write(receipt, value)

    code2, changed = authorize(
        FIX / "m4.json",
        receipt,
        PARENT,
        STRUCTURAL_QUEUE,
        transition_pilot_csv=TRANSITION,
        genetic_populations_csv=GENPOP,
        genetic_pairs_csv=GENPAIR,
        environment_csv=ENV,
        allow_synthetic_structural_queue=True,
        require_tracked_receipt=False,
    )

    assert code2 == 2
    assert changed["status"] == "STOP_committed_freeze_receipt_not_exact_replay"
    assert original["authorization_id"]
