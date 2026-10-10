"""Known-truth tightness tests. Intentionally NO raw biological responses."""
import itertools
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from wolfe_terminal_identifiability_v1_220 import (
    overlap_bounds, allocate_extreme, landscape_endpoint, patch_transition, run
)

def test_exact_overlap_bounds_up_to_six_patches():
    for n in range(1, 7):
        for g in range(n+1):
            for s in range(n+1):
                actual = [
                    len(set(x)&set(y))
                    for x in itertools.combinations(range(n),g)
                    for y in itertools.combinations(range(n),s)
                ]
                assert overlap_bounds(n,g,s) == (min(actual),max(actual))
                assert allocate_extreme(n,g,s,"lower")["co_occupied_patches"] == min(actual)
                assert allocate_extreme(n,g,s,"upper")["co_occupied_patches"] == max(actual)

def test_identical_terminal_binary_and_patch_marginals_can_hide_segregation():
    a=allocate_extreme(6,2,2,"lower")
    b=allocate_extreme(6,2,2,"upper")
    assert landscape_endpoint(a)==landscape_endpoint(b)
    assert a["co_occupied_patches"]==0 and b["co_occupied_patches"]==2

def test_same_terminal_patch_occupancy_cannot_identify_colonization():
    a=patch_transition([0,1],[0,1],6)
    b=patch_transition([1],[0,1],6)
    assert a["occupied_at_t1"]==b["occupied_at_t1"]==2
    assert a["local_0_to_1"]==0 and b["local_0_to_1"]==1

def test_guards_no_fake_observations_and_invalid_values():
    d=run()
    assert not d["raw_Wolfe_outcomes_accessed"]
    assert d["local_colonization_unidentifiable_from_t1_only"]
    assert d["tight_local_joint_patch_count_bounds"]==[0,2]
    with pytest.raises(ValueError):
        overlap_bounds(6,7,1)
    with pytest.raises(TypeError):
        overlap_bounds(6,1.5,2)
    with pytest.raises(ValueError):
        allocate_extreme(6,1,1,"invalid")
