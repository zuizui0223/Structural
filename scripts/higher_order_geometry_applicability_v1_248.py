#!/usr/bin/env python3
"""Response-free source-order limit and four-donor, weighted-delivery exact check.

Not an ecological outcome analysis; only reads existing frozen pilot counts and
geography-built graph metadata. All probabilities are explicitly hypothetical.
"""
import argparse
from collections import deque
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path


def _q4(probs):
    if len(probs) != 4:
        raise ValueError("Exactly four donor-specific success probabilities required")
    q = tuple(F(str(v)) for v in probs)
    if any(not F(0) <= a <= F(1) for a in q):
        raise ValueError("Donor success probabilities must be within [0,1]")
    return q


def signed_world_delta(probs):
    """Q(+) - Q(-), for same accessible four donors and given q_ij."""
    a,b,c,d = _q4(probs)
    return a*b*(c-d)/8


def no_establishment(sign, probs):
    """Exact P(no successful colonist) for original four-donor signed worlds."""
    if sign not in (-1,1):
        raise ValueError("Only the two previously defined donor-law signs allowed")
    a,b,c,d = _q4(probs)
    return (1-a/2)*(1-b/2)*(1-c/2)*(1-d/2) + sign*a*b*(c-d)/16


def direct_enumeration(sign, probs):
    """Independent 16-state product expectation, used as a mathematical check."""
    if sign not in (-1,1):
        raise ValueError("Invalid signed world")
    qs = _q4(probs)
    total = F(0)
    for x in product((0,1), repeat=4):
        parity123 = (-1)**sum(x[:3])
        parity124 = (-1)**(x[0]+x[1]+x[3])
        px = F(1,16) + sign*F(parity123-parity124,32)
        event = F(1)
        for a,p in zip(x,qs):
            event *= (1-a*p)
        total += px*event
    return total


def source_budget(frozen, heldout_islands):
    """Upper source-order budgets; never read heldout species × island cells."""
    p = frozen["population"]
    spectrum = {int(k):int(v) for k,v in p["nominal_source_count_species"].items()}
    if set(spectrum) != {1,2,3,4} or any(v < 0 for v in spectrum.values()):
        raise ValueError("Frozen source-count spectrum changed")
    n = sum(spectrum.values())
    if n != p["species"] or sum(k*v for k,v in spectrum.items()) != p["pilot_positive_cells"]:
        raise ValueError("Frozen source-count totals mismatch")
    if (frozen["response_boundary"]["heldout_occurrence_values_opened"] is not False
        or heldout_islands != frozen["response_boundary"]["heldout_geometry_targets_used"]):
        raise ValueError("Heldout boundary mismatch; cannot use target response")
    if n != 529 or heldout_islands != 4126:
        raise ValueError("This audit is bound to the frozen 529-species / 4,126-target geometry")
    few = spectrum[1]+spectrum[2]
    multi = spectrum[3]+spectrum[4]
    return {
        "total_species": n,
        "source_count_species": spectrum,
        "at_most_two_sources_species":few,
        "at_most_two_sources_fraction": F(few,n),
        "three_or_four_sources_species":multi,
        "four_sources_species":spectrum[4],
        "at_most_two_sources_possible_holdout_cells": few*heldout_islands,
        "three_or_four_sources_possible_holdout_cells": multi*heldout_islands,
    }


def eligible_sets(nodes, undirected_edges, occupied_sources):
    """Component-level binary reachability; NOT the graph's weighted proximity."""
    node_list = list(nodes)
    adjacency = {x:set() for x in node_list}
    if len(adjacency) != len(node_list):
        raise ValueError("Duplicate node identifier")
    sources = set(occupied_sources)
    if not sources <= set(adjacency):
        raise ValueError("Sources outside nodes")
    for a,b in undirected_edges:
        if a not in adjacency or b not in adjacency:
            raise ValueError("Edge points outside nodes")
        adjacency[a].add(b); adjacency[b].add(a)
    seen = set()
    output = {}
    for node in node_list:
        if node in seen: continue
        reach = {node}
        queue = deque([node]); seen.add(node)
        while queue:
            a=queue.popleft()
            for b in adjacency[a]:
                if b not in seen:
                    seen.add(b); reach.add(b); queue.append(b)
        common = frozenset(reach & sources)
        for v in reach:
            output[v] = common
    return output


def analyze_frozen(source_freeze, graph_freeze):
    b = source_budget(source_freeze, heldout_islands=4126)
    g = graph_freeze["graph_construct"]
    if (g["bioregions"] != len(g["selected_k_by_bioregion"]) or
        g["retained_islands"] != 5401 or g["edges"] != 73162 or
        "minimum k producing a connected component within each bioregion" not in g["graph"] or
        g["empirical_movement_edges"] is not False):
        raise ValueError("Changed graph provenance/semantics; fail closed")
    q_a=(F(1,2), F(1,2), F(4,5), F(1,5))
    q_b=(F(1,2), F(1,2), F(1,5), F(4,5))
    # Identities checked directly in every case, not treated as field evidence.
    for q in [q_a,q_b,(F(1,2),)*4]:
        for sign in (-1,1):
            if no_establishment(sign,q) != direct_enumeration(sign,q):
                raise AssertionError("Closed-form mismatch against exact 16-state enumeration")
    return {
        "schema":"structural.higher_order_geometry_applicability.v1_248",
        "evidence_class":"frozen_pilot_counts_plus_graph_metadata_and_known_truth_only",
        "species_eligibility": {
            **{k:v for k,v in b.items() if k != "at_most_two_sources_fraction"},
            "at_most_two_sources_fraction":str(b["at_most_two_sources_fraction"]),
            "at_most_two_sources_percentage":round(float(100*b["at_most_two_sources_fraction"]),2),
            "exact_four_donor_rank_swap_species_upper_bound":b["four_sources_species"],
            "interpretation":"At most 96 pilot species have >=3 identified donor endpoints; not a count of biologically independent extant sources",
        },
        "geometry_operator":{
            "islands":g["retained_islands"],
            "regional_components":g["bioregions"],
            "edges":g["edges"],
            "strict_binary_reachability_same_for_each_within_region_receiver":True,
            "hard_reachability_rank_swap_available_within_regions":False,
            "weighted_delivery_heterogeneity_not_measured":True,
            "comment":"Original graph uses distances and graph paths, not a 0/1 observed-dispersal eligibility set",
        },
        "known_truth_only":{
            "identical_q_for_all_four_sources":"Q(+) = Q(-) = (1-q/2)^4",
            "weighted_difference_formula":"Q(+) - Q(-) = q1*q2*(q3-q4)/8",
            "receiver_A_q":[str(x) for x in q_a],
            "receiver_B_q":[str(x) for x in q_b],
            "receiver_A_world_plus_no_establishment":str(no_establishment(1,q_a)),
            "receiver_A_world_minus_no_establishment":str(no_establishment(-1,q_a)),
            "receiver_B_world_plus_no_establishment":str(no_establishment(1,q_b)),
            "receiver_B_world_minus_no_establishment":str(no_establishment(-1,q_b)),
            "receiver_A_world_difference":str(signed_world_delta(q_a)),
            "receiver_B_world_difference":str(signed_world_delta(q_b)),
        },
        "safety":{
            "new_heldout_response_accesses":0,
            "new_biological_effects_estimated":0,
            "number_of_confirmatory_systems_admitted":0,
            "GEB_scientific_HOLD":True,
            "no_eBird":True,
        },
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    with (root/"development/global_mammals_ultrarare_source_leverage_freeze_v1_122.json").open(encoding="utf-8") as f:
        pilot=json.load(f)
    with (root/"development/global_mammals_graph_semantics_audit_v1_185.json").open(encoding="utf-8") as f:
        graph=json.load(f)
    result=analyze_frozen(pilot,graph)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["evidence_class"],
                      "at_most_two":result["species_eligibility"]["at_most_two_sources_species"],
                      "overlapping_triple_motif_supported_in_current_binary_graph":False,
                      "new_biology":False},sort_keys=True))


if __name__=="__main__": main()
