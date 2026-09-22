from __future__ import annotations

import pytest

from structural.transition_pilot_protocol import (
    PilotProtocolStatus,
    TransitionPilotProtocol,
    evaluate_transition_pilot_protocol,
    protocol_fingerprint,
)


def protocol(**changes):
    data = dict(
        protocol_id="future-v1",
        system_id="system-x",
        partition_axis="time_window",
        pilot_partition=("2010-2011",),
        confirmatory_partition=("2014-2015",),
        endpoint_id="annual_site_use",
        endpoint_semantics="1=detected; 0=surveyed non-detection; else non-estimable",
        heldout_design_id="leave-one-spatial-block-out",
        minimum_test_rows=3,
        minimum_train_positive=5,
        minimum_train_negative=5,
        minimum_estimable_blocks=3,
        pilot_response_accessed=False,
        confirmatory_response_accessed=False,
        pilot_used_for_effect_estimation=False,
    )
    data.update(changes)
    return TransitionPilotProtocol(**data)


def test_clean_disjoint_protocol_can_open_pilot():
    result = evaluate_transition_pilot_protocol(protocol())
    assert result.status is PilotProtocolStatus.QUALIFIED_TO_OPEN_PILOT
    assert result.reasons == ()
    assert len(result.protocol_fingerprint) == 64


def test_overlap_fails_at_construction():
    with pytest.raises(ValueError, match="disjoint"):
        protocol(confirmatory_partition=("2010-2011",))


def test_opened_confirmatory_response_stops():
    result = evaluate_transition_pilot_protocol(
        protocol(confirmatory_response_accessed=True)
    )
    assert result.status is PilotProtocolStatus.STOP
    assert "confirmatory_response_already_accessed" in result.reasons


def test_pilot_cannot_be_effect_evidence():
    result = evaluate_transition_pilot_protocol(
        protocol(pilot_used_for_effect_estimation=True)
    )
    assert result.status is PilotProtocolStatus.STOP
    assert "pilot_must_not_be_predictive_effect_evidence" in result.reasons


def test_protocol_fingerprint_changes_with_partition_or_gate():
    base = protocol()
    changed_partition = protocol(confirmatory_partition=("2016-2017",))
    changed_gate = protocol(minimum_train_positive=6)
    assert protocol_fingerprint(base) != protocol_fingerprint(changed_partition)
    assert protocol_fingerprint(base) != protocol_fingerprint(changed_gate)


def test_duplicate_partition_unit_fails():
    with pytest.raises(ValueError, match="duplicates"):
        protocol(pilot_partition=("2010-2011","2010-2011"))
