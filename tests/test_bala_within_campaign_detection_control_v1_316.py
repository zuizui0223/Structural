"""v1.316 original-source-free synthetic split-half detection control regression."""
import json
import sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_within_campaign_detection_control_v1_316 import (
    _partition,_score_split,evaluate_selected,SALTS
)
from bala_equal_original_event_samples_v1_313 import METHODS,ISLANDS

COUNTS={"fai":3,"flo":4,"pic":4,"sjg":4,"smg":4,"smr":2,"ter":8}

def contract():
    return json.loads((ROOT/"development/bala_within_campaign_detection_control_protocol_v1_316.json").read_text())

def synthetic(time_shift=True,beetle_detected=True):
    sites=set()
    selected={}
    source_taxa={}
    for island,n in COUNTS.items():
        for siteid in range(n):
            site=f"ANON_SOURCE_{siteid}"
            sites.add((island,site))
            for method in METHODS:
                for phase in ("B1","B2","B3"):
                    for j in range(10):
                        core=f"{island}-{site}-{method}-{phase}-trap{j:02d}"
                        selected[core]=(island,site,method,phase)
                        # Every split-half has two guild taxa in B1/B3;
                        # changing only one taxon between B1/B3 yields
                        # positive across-minus-within detection calibration.
                        first={"common spider","old spider"}
                        last={"common spider","new spider"} if time_shift else first
                        source_taxa[(core,"araneae")]=last if phase=="B3" else first
                        if beetle_detected:
                            old={"common beetle","old beetle"}
                            new={"common beetle","new beetle"} if time_shift else old
                            source_taxa[(core,"coleoptera")]=new if phase=="B3" else old
    assert len(sites)==29
    return selected,sites,source_taxa

def test_four_half_sets_have_zero_within_and_positive_temporal_replacement():
    v=_score_split({"a","b"},{"a","b"},{"a","c"},{"a","c"})
    assert v["within_sorensen"]==0
    assert v["across_sorensen"]==0.5
    assert v["delta_sorensen"]==0.5
    assert v["within_simpson"]==0
    assert v["delta_simpson"]==0.5
    assert _score_split(set(),{"a"},{"a"},{"b"}) is None

def test_all_seven_islands_positive_if_source_species_change_beyond_noise():
    selected,sites,taxa=synthetic(time_shift=True)
    r=evaluate_selected(selected,sites,taxa,contract())
    assert r["source_original_transects"]==29
    assert r["source_islands"]==7
    for guild in ("araneae","coleoptera"):
        g=r["main_pitfall"][guild]
        assert g["status"]=="RETROSPECTIVE_PAIRED_SAMPLING_CONTROL_SCORED"
        assert g["original_sites_observed_in_four_halves_at_least_five_of_nine_salts"]==29
        assert g["islands_with_at_least_one_eligible_original_site"]==7
        assert g["islands_positive_excess_temporal_dissimilarity"]==7
        assert g["island_equal_delta_sorensen"]==.5
        assert g["island_equal_delta_simpson_replacement"]==.5
        assert g["island_equal_within_campaign_sorensen"]==0
        assert g["island_equal_across_campaign_sorensen"]==.5
        assert g["original_sites_valid_salt_count_histogram"]=={"9":29}
        assert sum(x["original_transects_passing_half_sample_detection_gate"]
                   for x in g["per_island"].values())==29
    assert r["same_original_species_source_as_v1_314_not_independent_confirmation"]
    assert r["old_v1_314_original_one_shot_workflow_remains_SEALED"]
    assert r["new_confirmatory_systems"]==0 and r["GEB_scientific_HOLD"] and not r["eBird_used"]
    assert "ANON_SOURCE" not in json.dumps(r)

def test_if_true_species_membership_stable_differences_not_invented():
    selected,sites,taxa=synthetic(time_shift=False)
    r=evaluate_selected(selected,sites,taxa,contract())
    for guild in ("araneae","coleoptera"):
        x=r["main_pitfall"][guild]
        assert x["island_equal_across_campaign_sorensen"]==0
        assert x["island_equal_within_campaign_sorensen"]==0
        assert x["island_equal_delta_sorensen"]==0
        assert x["islands_positive_excess_temporal_dissimilarity"]==0

def test_empty_taxon_halves_stop_without_pseudo_zero():
    selected,sites,taxa=synthetic(beetle_detected=False)
    r=evaluate_selected(selected,sites,taxa,contract())
    g=r["main_pitfall"]["coleoptera"]
    assert g["status"]=="STOP_INSUFFICIENT_HALF_SAMPLE_GUILD_DETECTION_SUPPORT"
    assert g["island_equal_delta_sorensen"] is None
    assert g["original_sites_observed_in_four_halves_at_least_five_of_nine_salts"]==0
    assert g["original_sites_valid_salt_count_histogram"]=={"0":29}
    assert r["main_pitfall"]["araneae"]["island_equal_delta_sorensen"]==.5

def test_source_ID_partition_and_halves_are_biologically_response_blind():
    coreids=[f"source_Event_{i:03}" for i in range(11)]
    a,b=_partition(coreids,SALTS[0])
    assert len(a)==len(b)==5
    assert not set(a)&set(b)
    assert set(a+b).issubset(set(coreids))
    assert _partition(coreids,SALTS[0])==(a,b)
    with pytest.raises(ValueError,match="minimum"):
        _partition(coreids[:8],SALTS[0])
