"""v1.318 source-free synthetic spatial homogenization/differentiation tests.

A high within-site temporal beta can accompany EITHER spatial direction:
intra-island species sets becoming more alike or more different. Nine hash
partition salts are NOT independent ecological samples.
"""
from collections import defaultdict
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_original_island_spatial_beta_v1_318 import (
    pair_beta,one_guild_spatial,site_period_sets,
    MAIN_METHOD,CANOPY_METHOD,ISLANDS,GUILDS
)

def protocol():
    return json.loads((ROOT/"development/bala_spatial_homogenization_pre_response_protocol_v1_318.json").read_text(encoding="utf-8"))

COUNTS={"fai":3,"flo":4,"pic":4,"sjg":4,"smg":4,"smr":2,"ter":8}

def artificial(direction="different"):
    original_sites=set()
    selected={}
    source_taxa=defaultdict(set)
    for isl,n in COUNTS.items():
        for site in range(n):
            name="site_"+str(site)
            original_sites.add((isl,name))
            for method in (MAIN_METHOD,CANOPY_METHOD):
                for phase in ("B1","B3"):
                    for event in range(10):
                        core=f"{isl}|{name}|{method}|{phase}|{event}"
                        selected[core]=(isl,name,method,phase)
                        unique=f"unique_{isl}_{site}"
                        shared=f"shared_{isl}"
                        if direction=="different":
                            species={shared,"old_shared"} if phase=="B1" else {shared,unique}
                        else:
                            species={shared,unique} if phase=="B1" else {shared,"new_shared"}
                        for guild in GUILDS:
                            source_taxa[(core,guild)]=set(species)
    return selected,original_sites,source_taxa

def test_fixed_29_source_sites_can_differentiate_despite_constant_alpha():
    sel,sites,taxa=artificial("different")
    sets=site_period_sets(sel,taxa)
    res=one_guild_spatial(sets,sites,MAIN_METHOD,"araneae",protocol(),sel,taxa)
    assert res["status"]=="OBSERVED_WITHIN_ISLAND_SPATIAL_BETA_CHANGE"
    assert res["physical_sites_with_two_phase_detected_guild"]==29
    assert res["dependent_source_island_site_pairs"]==56
    assert res["eligible_islands"]==7
    assert res["islands_differentiating_simpson"]==7
    assert res["islands_homogenizing_simpson"]==0
    assert math.isclose(res["primary_island_equal_spatial_simpson_delta"],0.5)
    assert math.isclose(res["secondary_island_equal_spatial_sorensen_delta"],0.5)
    for island in ISLANDS:
        x=res["per_island"][island]
        assert x["source_phase_richness"]["B1"]["mean_original_source_plot_species_richness"]==2
        assert x["source_phase_richness"]["B3"]["mean_original_source_plot_species_richness"]==2
    sensitivity=res["source_9_partition_sensitivity"]
    assert sensitivity["valid_half_estimates_with_all_seven_islands"]==18
    assert sensitivity["source_half_simpson_same_direction_as_full_primary"]==18
    assert sensitivity["source_half_simpson_same_direction_fraction"]==1.0
    assert sensitivity["source_half_deltas_simpson_min_max"]==[0.5,0.5]

def test_same_richness_can_homogenize_not_differentiate():
    sel,sites,taxa=artificial("similar")
    sets=site_period_sets(sel,taxa)
    res=one_guild_spatial(sets,sites,MAIN_METHOD,"coleoptera",protocol(),sel,taxa)
    assert res["status"]=="OBSERVED_WITHIN_ISLAND_SPATIAL_BETA_CHANGE"
    assert res["primary_island_equal_spatial_simpson_delta"]==-0.5
    assert res["islands_homogenizing_simpson"]==7
    assert res["islands_differentiating_simpson"]==0
    assert res["source_9_partition_sensitivity"]["source_half_simpson_same_direction_as_full_primary"]==18

def test_rare_same_site_group_stops_instead_of_dropping_an_island():
    sel,sites,taxa=artificial()
    for core,group in sel.items():
        island,site,method,phase=group
        if island=="smr" and site=="site_1" and phase=="B3":
            taxa[(core,"araneae")]=set()
    res=one_guild_spatial(site_period_sets(sel,taxa),sites,MAIN_METHOD,"araneae",protocol(),sel,taxa)
    assert res["status"]=="STOP_FROZEN_GUILD_SPATIAL_PAIR_ESTIMABILITY"
    assert res["primary_island_equal_spatial_simpson_delta"] is None
    assert res["per_island"]["smr"]["status"]=="STOP_TOO_FEW_WITHIN_ISLAND_NONEMPTY_SOURCE_SITE_PAIRS"
    assert res["source_9_partition_sensitivity"] is None

def test_pairwise_jaccard_like_beta_not_false_local_extinction():
    value=pair_beta({"shared","a"},{"shared","b"})
    assert value=={"sorensen":0.5,"simpson":0.5}
    value=pair_beta({"a","b"},{"a"})
    assert math.isclose(value["sorensen"],1/3)
    assert value["simpson"]==0
    assert pair_beta(set(),{"a"}) is None
