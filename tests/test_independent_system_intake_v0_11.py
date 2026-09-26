from __future__ import annotations

import copy
import json
from pathlib import Path

from scripts.validate_independent_system_intake_v0_10 import validate_intake
from scripts.validate_independent_system_intake_v0_11 import validate_intake_v0_11


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/independent_system_intake_v0_10/valid_intake.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_clean_v010_intake_is_bridged_to_both_pre_pilot_contracts():
    intake = load_fixture()
    code, out = validate_intake_v0_11(intake)

    assert code == 0
    assert out["schema"] == "structural.independent_system_intake_receipt.v0_11"
    assert out["status"] == "eligible_to_construct_v0_31_and_v0_42_pre_pilot_contracts"
    assert out["eligible_action"] == (
        "construct_v0_31_protocol_then_bind_v0_42_quality_contract_only"
    )
    assert out["v0_31_protocol_construction_authorized"] is True
    assert out["v0_42_quality_contract_construction_authorized"] is True
    assert out["pilot_response_authorized"] is False
    assert out["confirmatory_response_authorized"] is False
    assert out["historical_systems_re_adjudicated"] is False


def test_historical_v010_receipt_semantics_remain_reproducible():
    intake = load_fixture()
    code, old = validate_intake(intake)

    assert code == 0
    assert old["schema"] == "structural.independent_system_intake_receipt.v0_10"
    assert old["status"] == "eligible_to_construct_v0_31_partition_protocol"
    assert old["eligible_action"] == "construct_v0_31_partition_protocol_only"
    assert "v0_42_quality_contract_construction_authorized" not in old


def test_closed_system_stop_cannot_gain_v042_construction_permission():
    intake = copy.deepcopy(load_fixture())
    intake["system_id"] = "usgs_pnw_montane_ponds_2012_2013"
    intake["is_prior_closed_system"] = True

    code, out = validate_intake_v0_11(intake)

    assert code == 2
    assert out["status"] == "STOP_prior_closed_system_cannot_reenter"
    assert out["v0_31_protocol_construction_authorized"] is False
    assert out["v0_42_quality_contract_construction_authorized"] is False
    assert out["pilot_response_authorized"] is False
    assert out["historical_systems_re_adjudicated"] is False
