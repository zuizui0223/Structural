from __future__ import annotations

import pytest

from structural.temporal_response_firewall import (
    TemporalAccessAction,
    TemporalAccessError,
    TemporalAccessStage,
    TemporalAccessState,
    TemporalResponseProtocol,
    advance_temporal_access,
    future_target_may_inform_features,
    lagged_state_may_inform_connectivity,
)


def protocol() -> TemporalResponseProtocol:
    return TemporalResponseProtocol(
        protocol_id="pnw-2012-2013-v0.14",
        lagged_state_time="2012",
        future_target_time="2013",
        ecological_unit="site",
        endpoint_id="future_occupancy",
        species_or_taxon_rule="freeze_before_lagged_state_open",
        geometry_rule_id="pnw_median_2012_utm_common150_v0.13",
        reference_rule_id="frozen_2012_reference_v1",
        connectivity_rule_id="frozen_operator_scale_worldset_v1",
        split_rule_id="frozen_sitewise_scoring_v1",
        metric_id="log_loss",
    )


def test_lagged_state_can_open_before_future_target():
    state = TemporalAccessState(protocol())
    state = advance_temporal_access(
        state,
        TemporalAccessAction.OPEN_LAGGED_STATE,
        receipt_or_fingerprint="lagged-sha",
    )
    assert state.stage is TemporalAccessStage.LAGGED_STATE_OPENED
    assert lagged_state_may_inform_connectivity(state) is True
    assert future_target_may_inform_features(state) is False


def test_future_target_cannot_open_before_feature_freeze():
    state = TemporalAccessState(protocol())
    with pytest.raises(TemporalAccessError, match="frozen features"):
        advance_temporal_access(
            state,
            TemporalAccessAction.OPEN_FUTURE_TARGET,
            receipt_or_fingerprint="target-sha",
        )


def test_full_sequence_is_irreversible():
    state = TemporalAccessState(protocol())
    state = advance_temporal_access(
        state,
        TemporalAccessAction.OPEN_LAGGED_STATE,
        receipt_or_fingerprint="lagged-sha",
    )
    state = advance_temporal_access(
        state,
        TemporalAccessAction.FREEZE_FEATURES,
        receipt_or_fingerprint="feature-sha",
    )
    assert state.stage is TemporalAccessStage.FEATURES_FROZEN
    state = advance_temporal_access(
        state,
        TemporalAccessAction.OPEN_FUTURE_TARGET,
        receipt_or_fingerprint="target-sha",
    )
    assert state.stage is TemporalAccessStage.FUTURE_TARGET_OPENED
    assert state.lagged_state_receipt == "lagged-sha"
    assert state.feature_fingerprint == "feature-sha"
    assert state.future_target_receipt == "target-sha"

    with pytest.raises(TemporalAccessError):
        advance_temporal_access(
            state,
            TemporalAccessAction.OPEN_LAGGED_STATE,
            receipt_or_fingerprint="again",
        )


def test_equal_lagged_and_target_time_is_invalid():
    p = TemporalResponseProtocol(
        protocol_id="x",
        lagged_state_time="2012",
        future_target_time="2012",
        ecological_unit="site",
        endpoint_id="occupancy",
        species_or_taxon_rule="rule",
        geometry_rule_id="geometry",
        reference_rule_id="reference",
        connectivity_rule_id="connectivity",
        split_rule_id="split",
        metric_id="log_loss",
    )
    with pytest.raises(TemporalAccessError, match="must differ"):
        advance_temporal_access(
            TemporalAccessState(p),
            TemporalAccessAction.OPEN_LAGGED_STATE,
            receipt_or_fingerprint="r",
        )
