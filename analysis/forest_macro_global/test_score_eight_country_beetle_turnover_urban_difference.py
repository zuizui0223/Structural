"""Known-truth tests: species replacement vs urban difference, no pair-level pseudo-p."""
import importlib.util,json
from pathlib import Path
import pytest

p=Path(__file__).with_name("score_eight_country_beetle_turnover_urban_difference.py")
spec=importlib.util.spec_from_file_location("beetle_turnover",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def site(contrast=True, n=16, same=False):
    # Groups separated along urban score, but species richness is fixed at 5
    # for all traps: a contrast is pure turnover, never richness loss.
    arr=[]
    for i in range(n):
        if same:species=frozenset(["same"+str(k) for k in range(5)])
        elif contrast:species=frozenset(["early"+str(k) if i < n//2 else "late"+str(k) for k in range(5)])
        else:species=frozenset(["early"+str(k) if i%2 else "late"+str(k) for k in range(5)])
        arr.append((float(i),species))
    return arr


def test_simpson_turnover_ignores_pure_nestedness_but_not_replacement():
    assert m.simpson_turnover({"A","B"},{"A"})==0
    assert m.simpson_turnover({"A","B"},{"B","C"})==.5
    assert m.simpson_turnover({"A"},{"C"})==1
    assert m.jaccard({"A","B"},{"A"})==.5
    assert m.jaccard({"A","B"},{"B","C"})==2/3


def test_pure_turnover_positive_relationship_in_16_and_15_trap_landscapes():
    for n in (15,16):
        q=m.source_study(site(n=n))
        assert q["source_traps"]==n
        assert q["turnover_pairs"]==n*(n-1)//2
        assert q["main_slope"]>0.05
        assert q["mean_family_free_species_Simpson_turnover"]>0.45
        assert q["mean_Jaccard_dissimilarity_secondary"]==q["mean_family_free_species_Simpson_turnover"]


def test_species_homogeneous_landscape_has_zero_turnover_slope():
    q=m.source_study(site(same=True))
    assert q["main_slope"]==0
    assert q["mean_family_free_species_Simpson_turnover"]==0


def test_known_13_landscapes_supports_turnover_difference_without_pair_pseudoreplication():
    actual={f"SECRET_LANDSCAPE_{i}":m.source_study(site(n=15 if i==0 else 16))
            for i in range(13)}
    q=m.inference(actual,permutations=249,bootstraps=300)
    assert q["estimable_landscapes"]==13
    assert q["equal_landscape_mean_Simpson_turnover_slope_per_SD_urban_difference"]>0
    assert q["landscape_bootstrap_95CI"][0]>0
    assert q["within_landscape_complete_exposure_label_permutation_two_sided_p_conditional"]<=.05
    assert q["single_predeclared_exploratory_support_criterion_met"]
    assert q["all_trap_pairwise_dependence_preserved_within_label_permutation"]
    assert "SECRET_LANDSCAPE_" not in json.dumps(q)


def test_no_urbanization_variation_is_source_eligibility_stop():
    with pytest.raises(ValueError,match="no_urbanization_variation"):
        m.source_study([(3.,frozenset({"A","B"})) for i in range(16)])


def test_reject_wrong_study_count_no_redefinition_after_score():
    incomplete={f"site{i}":m.source_study(site()) for i in range(12)}
    with pytest.raises(ValueError,match="not_13_original_landscapes"):
        m.inference(incomplete,permutations=5,bootstraps=20)


def test_one_piecewise_difference_is_not_automatically_species_turnover_evidence():
    y=[(0,0.9),(1,0.3),(2,0.2),(3,0.1),(4,0.1),
       (5,0.2),(6,0.1),(7,0.2),(8,0.15),(9,0.1)]
    assert m.slope(y)<0
