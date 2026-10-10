"""Check precommitted dual rules and source-match guard, not raw outcomes."""
import pytest,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from hopson_two_prey_rules_loso_v1_229 import prey_density,EXACT_V228_COUNTS

def test_exact_agreement_on_all_normal_diluted_and_undiluted_rows():
    for case in [(10,.3,0,0),(12,.3,2.7,.33),(0,.3,3,.33)]:
        assert prey_density(*case,"author_R_literal")==pytest.approx(
            prey_density(*case,"README_no_dilution"))

def test_only_discordant_dilution_zero_positive_subsample_differs():
    assert prey_density(10,.3,0,.33,"author_R_literal")==pytest.approx(10/.33)
    assert prey_density(10,.3,0,.33,"README_no_dilution")==pytest.approx(10/.3)

def test_fail_closed_source_and_invalid_counts():
    for args in [(None,.3,0,0),(1,-.1,0,0),(1,.3,float("nan"),.33),(1,.3,-2,0)]:
        with pytest.raises(ValueError):
            prey_density(*args,"author_R_literal")
    with pytest.raises(ValueError):
        prey_density(3,.3,2,0,"README_no_dilution")
    assert sum(EXACT_V228_COUNTS.values())==4830
