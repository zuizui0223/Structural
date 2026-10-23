"""Exact finite-population richness rarefaction with NO biological source re-access."""
from itertools import product
from fractions import Fraction
from math import comb
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores_MOVECLIM_2013_rarefaction_bounds_v1_279 import bounds,report_from_freeze


def expected(n,k,m):
    return Fraction(1,1)-Fraction(comb(n-k,m) if n-k>=m else 0,comb(n,m))

def test_exact_extremal_bounds_match_bruteforce_unknown_taxon_plot_allocation():
    for n in (3,4,5):
        for T in (1,2,3):
            for P in range(T,n*T+1):
                possibilities=[a for a in product(range(1,n+1),repeat=T) if sum(a)==P]
                for m in (1,n//2,n):
                    l,u=bounds(n,T,P,m)
                    actual=[sum((expected(n,k,m) for k in p),Fraction(0)) for p in possibilities]
                    assert l==min(actual)
                    assert u==max(actual)
                    assert l<=u

def test_pico_frozen_richness_bounds_and_uniform_10_plot_expectations():
    assert bounds(24,5,26,10)==(Fraction(8,3),Fraction(25115,5244))
    assert bounds(10,1,7,10)==(Fraction(1),Fraction(1))
    assert bounds(12,1,3,10)==(Fraction(1),Fraction(1))
    assert bounds(12,1,9,10)==(Fraction(1),Fraction(1))
    assert bounds(24,5,26,8)[0]==Fraction(7,3)

def test_impossible_recorded_plot_occupancy_fails():
    for n,t,p,m in ((0,1,1,1),(4,0,3,2),(4,2,1,2),(4,2,9,2),(4,2,5,5)):
        try:bounds(n,t,p,m)
        except ValueError:pass
        else:raise AssertionError("Invalid original plot×taxon counts were accepted")

def test_robust_pico_sample_effort_corrected_fractional_enrichment():
    from json import loads
    path=Path(__file__).resolve().parents[1]/"development/azores_MOVECLIM_2013_native_plot_field_result_freeze_v1_278.json"
    result=report_from_freeze(loads(path.read_text(encoding="utf-8")))
    assert result["m10"]["Pico"]["historical_affected_taxa"]["expected_lower_fraction"]=="8/3"
    assert result["m10"]["Flores"]["historical_affected_taxa"]["expected_upper_float"]==1.
    assert result["m10"]["Pico"]["minimum_possible_ratio_of_expected_affected_to_total_native"]>0.053
    assert result["m10"]["Pico"]["minimum_possible_ratio_of_expected_affected_to_total_native"]>max(
        x["maximum_possible_ratio_of_expected_affected_to_total_native"] for island,x in result["m10"].items() if island!="Pico")
    assert result["m10"]["Pico"]["source_free_not_field_resampling"] is True
    assert result["protected_biological_rows_opened_this_run"]==0
    assert result["not_actual_population_persistence_or_rescue"] is True
