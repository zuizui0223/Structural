from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.run_transition_pilot_v0_32 import run as run_v032
from structural.atoll_pilot_router import build_atoll_burned_pilot_surface
from structural.response_quality_attrition import (
    ResponseQualityContractStatus,
    contract_fingerprint,
    contract_from_mapping,
    evaluate_response_quality_contract,
)
from structural.transition_pilot_protocol import (
    PilotProtocolStatus,
    evaluate_transition_pilot_protocol,
    protocol_fingerprint,
    protocol_from_mapping,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "development/indo_pacific_atoll_transition_pilot_protocol_v0_31b.json"
QUALITY = ROOT / "development/indo_pacific_atoll_response_quality_contract_v0_42b.json"
ROUTER = ROOT / "development/indo_pacific_atoll_pilot_router_contract_v0_20.json"
RETIRED = ROOT / "development/indo_pacific_atoll_retired_prepilot_protocol_v0_19.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_replacement_contracts_are_clean_and_bound_before_response():
    protocol = protocol_from_mapping(load(PROTOCOL))
    quality = contract_from_mapping(load(QUALITY))

    p = evaluate_transition_pilot_protocol(protocol)
    q = evaluate_response_quality_contract(protocol=protocol, contract=quality)

    assert p.status is PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT
    assert p.protocol_fingerprint == (
        "ee8cccc38fb8f4602e05e97d9d875c5ad8773280460c0dafca36ac03fe5871f5"
    )
    assert protocol_fingerprint(protocol) == p.protocol_fingerprint
    assert q.status is ResponseQualityContractStatus.QUALIFIED_TO_OPEN_PILOT
    assert contract_fingerprint(quality) == (
        "1b3ad5da960ceac60e594b3ed664a39835e2f49ba1f7d70bfd32ee1c54e28fc6"
    )

    assert len(protocol.pilot_partition) == 13
    assert len(protocol.confirmatory_partition) == 50
    assert protocol.minimum_estimable_blocks == 3
    assert quality.minimum_response_qualified_blocks == 3


def test_old_fold_specific_protocol_is_retired_without_response_access():
    retired = load(RETIRED)

    assert retired["status"] == "retired_before_any_response_access"
    assert retired["response_accessed"] is False
    assert retired["pilot_consumed"] is False
    assert retired["effect_size"] is None
    assert retired["prediction_score"] is None
    assert retired["predictive_denominator_contribution"] == 0
    assert "complement arithmetic" in retired["reason"]


def test_fixed_species_universe_is_shared_across_all_blocks():
    # spA is native in P1/P2, spB in P1/P3: both qualify for the fixed pool.
    # spC is native only in P1 and is excluded prospectively by the >=2-block rule.
    raw = (
        b"atoll,species,presence\n"
        b"A,spA,N\n"
        b"A,spB,N\n"
        b"A,spC,N\n"
        b"B,spA,N\n"
        b"B,spB,I\n"
        b"C,spA,I\n"
        b"C,spB,N\n"
        b"D,\xff,\xfe\n"
        b"X,\xff,\xfe\n"
    )
    routed = build_atoll_burned_pilot_surface(
        response_csv_bytes=raw,
        atoll_to_block={"A": "P1", "B": "P2", "C": "P3", "D": "C1"},
        excluded_model_target_atolls={"X"},
        pilot_partition=["P1", "P2", "P3"],
        confirmatory_partition=["C1"],
    )

    assert routed.pilot_species_universe == ("spA", "spB")
    assert routed.pilot_species_universe_count == 2
    assert routed.pilot_species_universe_sha256 == hashlib.sha256(
        b"spA\nspB\n"
    ).hexdigest()
    assert routed.confirmatory_species_values_parsed == 0
    assert routed.confirmatory_presence_values_parsed == 0
    assert routed.excluded_species_values_parsed == 0
    assert routed.excluded_presence_values_parsed == 0

    assert routed.csv_text == (
        "partition_unit,block,target\n"
        "P1,P1,1\n"
        "P1,P1,1\n"
        "P2,P2,1\n"
        "P2,P2,0\n"
        "P3,P3,0\n"
        "P3,P3,1\n"
    )


def test_fixed_surface_is_valid_for_v032_complement_arithmetic(tmp_path: Path):
    raw = (
        b"atoll,species,presence\n"
        b"A,spA,N\n"
        b"A,spB,N\n"
        b"B,spA,N\n"
        b"B,spB,I\n"
        b"C,spA,I\n"
        b"C,spB,N\n"
    )
    routed = build_atoll_burned_pilot_surface(
        response_csv_bytes=raw,
        atoll_to_block={"A": "P1", "B": "P2", "C": "P3"},
        excluded_model_target_atolls=set(),
        pilot_partition=["P1", "P2", "P3"],
        confirmatory_partition=["C1"],
    )

    protocol = {
        "protocol_id": "synthetic-fixed-universe",
        "system_id": "synthetic-atoll",
        "partition_axis": "spatial",
        "pilot_partition": ["P1", "P2", "P3"],
        "confirmatory_partition": ["C1"],
        "endpoint_id": "fixed_species_occurrence",
        "endpoint_semantics": "same fixed species universe in every block",
        "heldout_design_id": "leave_one_block_out",
        "minimum_test_rows": 2,
        "minimum_train_positive": 2,
        "minimum_train_negative": 1,
        "minimum_estimable_blocks": 3,
        "pilot_response_accessed": False,
        "confirmatory_response_accessed": False,
        "pilot_used_for_effect_estimation": False,
    }
    protocol_path = tmp_path / "protocol.json"
    pilot_path = tmp_path / "pilot.csv"
    protocol_path.write_text(json.dumps(protocol), encoding="utf-8")
    pilot_path.write_text(routed.csv_text, encoding="utf-8")

    code, result = run_v032(protocol_path, pilot_path)

    assert code == 0
    assert result["status"] == "qualified_for_new_confirmatory_protocol"
    assert result["applicable_rows"] == 6
    assert result["positive"] == 4
    assert result["negative"] == 2
    assert result["estimable_blocks"] == 3
    assert result["minimum_estimable_blocks"] == 3
    assert result["effect_size"] is None
    assert result["prediction_score"] is None
    assert result["predictive_denominator_contribution"] == 0


def test_router_contract_freezes_same_universe_and_sealed_confirmation():
    router = load(ROUTER)

    assert router["fixed_pilot_species_universe"]["eligibility"] == (
        "species has native presence code N in at least two distinct frozen burned-pilot spatial blocks"
    )
    assert router["fixed_pilot_species_universe"][
        "same_species_universe_for_every_heldout_pilot_block"
    ] is True
    assert router["fixed_pilot_species_universe"][
        "confirmatory_response_may_not_define_species_universe"
    ] is True
    assert router["confirmatory_firewall"]["confirmatory_species_values_parsed"] == 0
    assert router["confirmatory_firewall"]["confirmatory_presence_values_parsed"] == 0
    assert router["pilot_response_authorized"] is False
    assert router["confirmatory_response_authorized"] is False
