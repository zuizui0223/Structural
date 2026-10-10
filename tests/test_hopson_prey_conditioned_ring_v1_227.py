"""Synthetic prey-density assay regression and model-input boundary tests."""
import math,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from hopson_prey_conditioned_ring_v1_227 import tet_per_ml

def test_undiluted_density():
    assert tet_per_ml(15,.3,0,0)==pytest.approx(50)
    assert tet_per_ml(0,.3,0,0)==0

def test_author_diluted_density_formula():
    x=tet_per_ml(100,.3,2.7,.1)
    assert x==pytest.approx(10000)
    assert tet_per_ml(0,.3,2.7,.1)==0

def test_inconsistent_assay_flags_stop():
    for args in [(10,.3,2.7,0),(10,.3,0,.1),(10,0,0,0),
                 (10,.3,-1,.1),(10,.3,1,-.1),(None,.3,0,0)]:
        with pytest.raises(ValueError):
            tet_per_ml(*args)

def test_assay_source_not_imputed():
    assert math.isfinite(tet_per_ml(1,.298,0,0))
    with pytest.raises(ValueError):tet_per_ml(10,.3,float("nan"),0)
