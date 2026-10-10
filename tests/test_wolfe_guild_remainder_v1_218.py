"""v1.218 independent synthetic controls: missing-state enumeration, joint identity, bounds."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from wolfe_guild_remainder_v1_218 import compute, summarize, KEYS, MISSING_KEYS

def synthetic():
    groups={k:[(0,0,0)]*(3 if k in MISSING_KEYS else 4) for k in KEYS}
    return groups

def test_six_patch_exact_two_missing_and_focal_bounds():
    result=compute(synthetic())
    assert result["joint_missing_state_completions"]==16
    assert result["observed_source_microcosms"]["heterogeneous_high"]["observed_microcosms"]==11
    a=result["six_heterogeneous_low_minus_high_corridor"]
    assert a["G"]==[-1/12,0]
    assert a["S"]==[-1/12,0]
    assert a["J"]==[-1/12,0]
    b=result["heterogeneity_advantage_low_minus_high_corridor"]
    assert b["J"]==[-1/12,1/12]

def test_decomposition_exact_and_non_additive_extrema():
    groups=synthetic()
    groups[(6,"heterogeneous","low","low")]=[(1,1,1),(1,0,0),(0,1,0),(0,0,0)]
    cells={k:list(v) for k,v in groups.items()}
    for k in MISSING_KEYS: cells[k].append((0,0,0))
    het,adv,metrics=summarize(cells)
    x=metrics[("heterogeneous","low")]
    assert abs(x["marginal_product"]-1/48)<1e-12
    assert abs(x["association_remainder"]-1/16)<1e-12
    assert abs(x["J"]-1/12)<1e-12

def test_layout_and_invalid_joint_rejected():
    groups=synthetic()
    groups[(6,"heterogeneous","none","high")].append((0,0,0))
    with pytest.raises(ValueError,match="layout"):
        compute(groups)
    groups=synthetic()
    groups[(6,"heterogeneous","low","low")][0]=(1,1,0)
    with pytest.raises(ValueError,match="Invalid"):
        compute(groups)
