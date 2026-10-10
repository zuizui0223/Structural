"""v1.217 fixed 4-replicate missingness accounting and no respecified endpoint."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from wolfe_regime_interaction_v1_217 import cell, compute

def zero_groups():
    return {(n, h, m, c): [(0, 0, 0)] * 4
            for n in (4, 6) for h in ("homogeneous", "heterogeneous")
            for m in ("none", "low", "high")
            for c in ("none", "low", "high")}

def test_cell_missing_binary_extremes():
    g = zero_groups()
    g[(6, "heterogeneous", "low", "low")] = [(1, 1, 1)] * 3
    g[(6, "homogeneous", "low", "low")] = [(0, 0, 0)] * 3
    r = cell(g, 6, "low", "low")
    assert r["observed_only_difference"] == 1
    assert r["missing_lower"] == .5
    assert r["missing_upper"] == 1
    assert r["unobserved_or_unassigned_units"] == 2

def test_disjoint_corridor_bounds_exact():
    g = zero_groups()
    g[(6, "heterogeneous", "low", "low")] = [(1, 1, 1)] * 4
    g[(6, "homogeneous", "low", "high")] = [(0, 0, 0)] * 3
    # Exactly five focal unknown entries, like the source, distributed across
    # non-overlapping test cells.
    for c in [("none", "none"), ("none", "low"), ("high", "none"), ("high", "high")]:
        g[(4, "homogeneous", *c)] = [(0, 0, 0)] * 3
    r = compute(g)
    x = r["six_patch_local_low_minus_high_heterogeneity_interaction"]
    assert abs(x["missing_lower"] - (1/3 - 0)) < 1e-12
    assert abs(x["missing_upper"] - (1/3 - (-1/12))) < 1e-12
    assert r["tested_hypothesis_preregistered"] is False

def test_reject_invalid_response_or_replicate_count():
    g = zero_groups()
    g[(4, "heterogeneous", "none", "none")] = [(1, 1, 3)] * 4
    try:
        cell(g, 4, "none", "none")
    except ValueError:
        pass
    else:
        raise AssertionError("Nonbinary response was accepted")
