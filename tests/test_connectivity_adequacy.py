from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

from structural import (
    ConnectivityCoordinate,
    ConnectivityEvidenceLevel,
    FavorableDirection,
    IncrementalEvidence,
    IncrementalVerdict,
    OperatorConnectivityState,
    PortabilityVerdict,
    SeparationOrigin,
    audit_portability,
    classify_incremental,
    declared_operator_transition,
    scalar_insufficiency_witness,
)


def ev(operator: str, effect: float, lo: float, hi: float, family: str, shared: str | None = None):
    return IncrementalEvidence(
        coordinate=ConnectivityCoordinate(
            name="typed_connectivity",
            operator=operator,
            endpoint="future_loss",
            origin=SeparationOrigin.HABITAT_FRAGMENTATION,
        ),
        reference_id="current_state_v1",
        metric="log_loss",
        effect=effect,
        ci_low=lo,
        ci_high=hi,
        favorable_direction=FavorableDirection.NEGATIVE,
        evidence_family_id=family,
        shared_reference_group=shared,
    )


def test_incremental_classification_for_loss_metric():
    assert classify_incremental(ev("pollen", -0.04, -0.06, -0.02, "a")) is IncrementalVerdict.EARNED
    assert classify_incremental(ev("pollen", +0.04, +0.01, +0.07, "a")) is IncrementalVerdict.ADVERSE
    assert classify_incremental(ev("pollen", -0.01, -0.03, +0.01, "a")) is IncrementalVerdict.INDETERMINATE


def test_one_operator_is_not_a_portability_test():
    out = audit_portability([ev("pollen", -0.04, -0.06, -0.02, "fresh-pollen")])
    assert out.portability is PortabilityVerdict.NOT_TESTED


def test_mixed_operator_results_falsify_scalar_portability():
    rows = [
        ev("allele_mixing", -0.04, -0.06, -0.02, "fresh-allele"),
        ev("pollen_flow", -0.01, -0.03, +0.01, "shared-substitutions", "historical-A"),
        ev("whole_individual", +0.04, +0.01, +0.07, "shared-substitutions", "historical-A"),
    ]
    out = audit_portability(rows)
    assert out.portability is PortabilityVerdict.NOT_PORTABLE_IN_DECLARED_SET
    assert out.independent_evidence_families == 2
    assert out.shared_reference_groups == ("historical-A",)
    assert dict(out.verdicts)["allele_mixing"] is IncrementalVerdict.EARNED
    assert dict(out.verdicts)["pollen_flow"] is IncrementalVerdict.INDETERMINATE
    assert dict(out.verdicts)["whole_individual"] is IncrementalVerdict.ADVERSE


def test_all_earned_supports_only_declared_operator_set():
    rows = [
        ev("pollen_flow", -0.04, -0.06, -0.02, "a"),
        ev("whole_individual", -0.03, -0.05, -0.01, "b"),
    ]
    assert audit_portability(rows).portability is PortabilityVerdict.SUPPORTED_WITHIN_DECLARED_SET


def test_origin_is_typed_not_collapsed():
    island = ConnectivityCoordinate(
        name="source_network",
        operator="structural_graph",
        endpoint="incidence",
        origin=SeparationOrigin.PRE_EXISTING_ISOLATION,
    )
    fragment = ConnectivityCoordinate(
        name="matrix_flow",
        operator="whole_individual",
        endpoint="occupancy",
        origin=SeparationOrigin.HABITAT_FRAGMENTATION,
    )
    assert island.origin is not fragment.origin
    assert island.evidence_level is ConnectivityEvidenceLevel.STRUCTURAL_GEOMETRY


def test_invalid_interval_fails_closed():
    with pytest.raises(ValueError, match="ci_low"):
        ev("pollen", -0.04, -0.02, -0.06, "a")


def test_equal_scalar_connectivity_can_hide_operator_specific_future():
    a = OperatorConnectivityState((("pollen_flow", 0.9), ("whole_individual", 0.1)))
    b = OperatorConnectivityState((("pollen_flow", 0.1), ("whole_individual", 0.9)))

    assert a.collapsed_mean == b.collapsed_mean == 0.5
    assert declared_operator_transition(a, "pollen_flow") == 0.9
    assert declared_operator_transition(b, "pollen_flow") == 0.1

    witness = scalar_insufficiency_witness(a, b, "pollen_flow")
    assert witness.collapsed_value == 0.5
    assert witness.transition_a == 0.9
    assert witness.transition_b == 0.1
    assert witness.transition_difference == pytest.approx(0.8)


def test_scalar_witness_fails_if_operator_specific_future_is_same():
    a = OperatorConnectivityState((("pollen_flow", 0.5), ("whole_individual", 0.5)))
    b = OperatorConnectivityState((("pollen_flow", 0.5), ("whole_individual", 0.5)))
    with pytest.raises(ValueError, match="transitions must differ"):
        scalar_insufficiency_witness(a, b, "pollen_flow")


def test_known_truth_fixture_replays_exactly():
    path = ROOT / "benchmarks/run_connectivity_scalar_insufficiency_v0_1.py"
    spec = importlib.util.spec_from_file_location("connectivity_known_truth", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.run()

    assert result["collapsed_mean_a"] == 0.5
    assert result["collapsed_mean_b"] == 0.5
    assert result["operator"] == "pollen_flow"
    assert result["transition_a"] == 0.9
    assert result["transition_b"] == 0.1
    assert result["transition_difference"] == pytest.approx(0.8)
    assert result["conclusion"] == "collapsed_connectivity_not_transition_sufficient_for_declared_operator"


def test_connectivity_level_is_explicit():
    structural = ConnectivityCoordinate(
        name="archipelago_graph",
        operator="unidentified_structural",
        endpoint="incidence",
        origin=SeparationOrigin.PRE_EXISTING_ISOLATION,
        evidence_level=ConnectivityEvidenceLevel.STRUCTURAL_GEOMETRY,
    )
    process = ConnectivityCoordinate(
        name="resistance_flow",
        operator="whole_individual",
        endpoint="occupancy",
        origin=SeparationOrigin.HABITAT_FRAGMENTATION,
        evidence_level=ConnectivityEvidenceLevel.PROCESS_MODEL,
    )
    realized = ConnectivityCoordinate(
        name="observed_gene_flow",
        operator="gene_flow",
        endpoint="offspring_genotype",
        origin=SeparationOrigin.HABITAT_FRAGMENTATION,
        evidence_level=ConnectivityEvidenceLevel.REALIZED_OBSERVATION,
    )
    assert len({structural.evidence_level, process.evidence_level, realized.evidence_level}) == 3


def test_crosswalk_preserves_programme_and_operator_boundaries():
    import json

    crosswalk = json.loads(
        (ROOT / "development/connectivity_crosswalk_v0_1.json").read_text(encoding="utf-8")
    )
    rows = crosswalk["entries"]
    assert rows
    assert all(row["origin"] for row in rows)
    assert all(row["evidence_level"] in {
        "structural_geometry", "process_model", "realized_observation"
    } for row in rows)
    assert all(row["operator"] for row in rows)

    structural = [row for row in rows if row["programme"] == "Structural"]
    egwe = [row for row in rows if row["programme"] == "EGWE"]
    assert {row["system"] for row in structural} == {"A-Islands", "Tanzania forest fragments"}
    assert all(row.get("imported_as_structural_evidence") is False for row in egwe)
    assert any(row["origin"] == "pre_existing_isolation" for row in structural)
    assert any(row["origin"] == "habitat_fragmentation" for row in structural)
    assert "shared connectivity labels do not imply operator equivalence" in crosswalk["invariants"]
