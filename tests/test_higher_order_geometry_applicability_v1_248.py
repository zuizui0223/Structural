"""Response-free, exact-fraction regression tests for the source-order applicability audit."""
from fractions import Fraction as F
from itertools import product
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from higher_order_geometry_applicability_v1_248 import (
    source_budget, no_establishment, signed_world_delta,
    direct_enumeration, eligible_sets, analyze_frozen,
)


PILOT = {
    "population": {
        "species": 529,
        "pilot_positive_cells": 877,
        "nominal_source_count_species": {"1": 317, "2": 116, "3": 56, "4": 40},
    },
    "response_boundary": {"heldout_occurrence_values_opened": False,
                          "heldout_geometry_targets_used": 4126},
}
GRAPH = {
    "graph_construct": {
        "retained_islands": 5401,
        "edges": 73162,
        "bioregions": 12,
        "graph": "undirected symmetrized k-nearest-neighbor graph, with the minimum k producing a connected component within each bioregion",
        "selected_k_by_bioregion": {f"region{i}": i for i in range(1, 13)},
        "empirical_movement_edges": False,
    }
}


def test_source_order_population_spectrum_exact():
    x = source_budget(PILOT, heldout_islands=4126)
    assert x["at_most_two_sources_species"] == 433
    assert x["at_most_two_sources_fraction"] == F(433, 529)
    assert x["three_or_four_sources_species"] == 96
    assert x["four_sources_species"] == 40
    assert x["at_most_two_sources_possible_holdout_cells"] == 1_786_558
    assert x["three_or_four_sources_possible_holdout_cells"] == 96 * 4126
    assert sum(x["source_count_species"].values()) == 529


def test_budget_rejects_any_mismatched_response_counts():
    bad = {"population": {**PILOT["population"], "pilot_positive_cells": 878},
           "response_boundary": PILOT["response_boundary"]}
    try:
        source_budget(bad, heldout_islands=4126)
    except ValueError as exc:
        assert "source" in str(exc).lower() or "sum" in str(exc).lower()
    else:
        raise AssertionError("Must reject mismatched frozen pilot totals")


def test_graph_connected_components_cannot_support_overlap_and_turnover():
    # Two connected components: same-component receivers have identical all-reachable sources;
    # other-component receivers have disjoint ones. No {1,2,3} vs {1,2,4} motif.
    edges = [(0,1),(1,2),(2,3),(4,5)]
    sets = eligible_sets(range(6), edges, {0,2,4})
    assert sets[0] == sets[1] == sets[2] == sets[3] == frozenset({0,2})
    assert sets[4] == sets[5] == frozenset({4})
    assert sets[1].isdisjoint(sets[5])


def test_original_signed_worlds_exact_four_donor_formula():
    qvals = [F(0), F(1,10), F(1,2), F(1)]
    for qs in product(qvals, repeat=4):
        for sign in (-1, +1):
            assert no_establishment(sign, qs) == direct_enumeration(sign, qs)
            assert F(0) <= no_establishment(sign, qs) <= F(1)
        assert no_establishment(+1, qs)-no_establishment(-1, qs) == signed_world_delta(qs)


def test_equal_success_probabilities_cannot_differentiate_the_worlds():
    for q in [F(0), F(1,10), F(1,4), F(1,2), F(9,10), F(1)]:
        qs = (q,q,q,q)
        assert signed_world_delta(qs) == 0
        assert no_establishment(-1,qs) == no_establishment(+1,qs)
        assert no_establishment(-1,qs) == (1-q/2)**4


def test_geographic_transfer_asymmetry_reverses_the_world_specific_difference():
    a = (F(1,2), F(1,2), F(4,5), F(1,5))
    b = (F(1,2), F(1,2), F(1,5), F(4,5))
    assert signed_world_delta(a) == F(3,160)
    assert signed_world_delta(b) == -F(3,160)
    assert no_establishment(+1,a) == F(501,1600)
    assert no_establishment(-1,a) == F(471,1600)
    assert no_establishment(+1,b) == F(471,1600)
    assert no_establishment(-1,b) == F(501,1600)
    assert signed_world_delta((F(0),F(1),F(1),F(0))) == 0


def test_analyze_freezes_strict_geometry_and_no_new_data():
    r = analyze_frozen(PILOT,GRAPH)
    assert r["species_eligibility"]["at_most_two_sources_species"] == 433
    assert r["geometry_operator"]["hard_reachability_rank_swap_available_within_regions"] is False
    assert r["geometry_operator"]["weighted_delivery_heterogeneity_not_measured"] is True
    assert r["safety"]["new_heldout_response_accesses"] == 0
    assert r["safety"]["new_biological_effects_estimated"] == 0
    assert r["known_truth_only"]["receiver_A_world_plus_no_establishment"] == "501/1600"
