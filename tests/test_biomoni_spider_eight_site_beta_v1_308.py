"""Synthetic-only v1.308 eight-site spider to original tree compositional beta."""
import copy,json,sys,math
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from biomoni_spider_eight_site_beta_v1_308 import (
    beta_sets,match_source_event_ids,analyse_original
)
from biomoni_spider_eight_site_event_v1_307 import qualify
from test_biomoni_spider_eight_site_event_v1_307 import build

def cfg():
    bet=json.loads((ROOT/"development/biomoni_spider_eight_site_beta_contract_v1_308.json").read_text())
    ev=json.loads((ROOT/"development/biomoni_spider_eight_site_source_gate_v1_307.json").read_text())
    return bet,ev

def synthetic_sets():
    w=[{"woody common","woody even" if i%2==0 else "woody odd"} for i in range(8)]
    s=[{"spider common","spider even" if i%2==0 else "spider odd"} for i in range(8)]
    coords=[(38.7+i*.004,-27.2-i*.003) for i in range(8)]
    return w,s,coords

def synthetic_source():
    t,s=build()
    beta,event=cfg()
    r=qualify(t,s,event)
    selected_tree,selected_spider,coords,design=match_source_event_ids(t,s,event,r)
    tree_occ=[]
    for core,i in selected_tree.items():
        tree_occ.extend([
           {"source_coreid":core,"scientificName":"Woody common","taxonRank":"species"},
           {"source_coreid":core,"scientificName":"Woody even" if i%2==0 else "Woody odd","taxonRank":"species"}
        ])
    tree_other=next(q["source_coreid"] for q in t if q["island"]=="Tenerife")
    tree_occ.extend([{"source_coreid":tree_other,"scientificName":"Other island tree","taxonRank":"species"}]*(402-len(tree_occ)))
    spider_occ=[]
    bysite={}
    for core,i in selected_spider.items():
        bysite.setdefault(i,[]).append(core)
    for i,cores in bysite.items():
        cores.sort()
        spider_occ.extend([
          {"source_coreid":cores[0],"scientificName":"Spider common","taxonRank":"species"},
          {"source_coreid":cores[1],"scientificName":"Spider even" if i%2==0 else "Spider odd","taxonRank":"species"}
        ])
    spider_other=next(q["source_coreid"] for q in s if q["island"]=="Pico")
    spider_occ.extend([{"source_coreid":spider_other,"scientificName":"Pico source spider","taxonRank":"species"}]*(1639-len(spider_occ)))
    assert len(tree_occ)==402 and len(spider_occ)==1639
    return t,s,tree_occ,spider_occ,beta,event,r

def test_known_truth_eight_plot_LOPO_and_999_independent_site_label_nulls():
    beta,_=cfg()
    w,s,coords=synthetic_sets()
    result=beta_sets(w,s,coords,beta)
    assert result["status"]=="OBSERVED_EIGHT_PLOT_EXPLORATORY_SPIDER_BETA_SCORE"
    assert result["source_original_independent_plots"]==8
    assert result["dependent_plot_pairs"]==28
    assert result["baseline_geographic_only_eight_LOPO_MSE"]>result["augmented_geographic_plus_spider_eight_LOPO_MSE"]
    assert result["original_spider_incremental_eight_LOPO_MSE_gain"]>0
    assert result["fixed_plot_label_permutations"]==999
    assert result["permutation_seed"]==20261028
    assert 0<result["original_plot_label_permutation_exceedance_rank"]<=1

def test_frozen_eight_author_site_fingerprint_before_original_taxon_access():
    t,s,w,sp,beta,ev,r=synthetic_source()
    result=analyse_original(t,s,w,sp,beta,ev,r)
    assert result["status"]=="OBSERVED_EIGHT_PLOT_EXPLORATORY_SPIDER_BETA_SCORE"
    assert result["source_original_independent_plots"]==8
    assert result["selected_original_spider_Event_subset_n"]==184
    assert result["original_tree_Occurrence_rows_reopened"]==402
    assert result["original_spider_Occurrence_rows_opened"]==1639
    assert result["original_selected_spider_occurrences"]==16
    assert result["original_unresolved_spider_fraction"]==0
    assert result["v1_303_and_v1_304_all_ten_site_GATE"]=="TERMINAL"
    assert result["new_confirmatory_systems"]==0 and result["GEB_scientific_HOLD"] and not result["eBird_used"]
    assert "Woody common" not in json.dumps(result)
    assert "TER_NFBF" not in json.dumps(result)
    assert result["no_original_species_site_identifiers_or_coordinates_exported"]

def test_original_frozen_site_subset_hash_cannot_be_reselected_after_response():
    t,s,w,sp,beta,ev,r=synthetic_source()
    r=copy.deepcopy(r)
    r["source_original_qualified_spider_coreids_sha256"]="bad-sha"
    with pytest.raises(ValueError,match="Event-only"):
        analyse_original(t,s,w,sp,beta,ev,r)

def test_empty_biological_site_returns_stop_not_jaccard_zero():
    beta,_=cfg()
    w,s,coords=synthetic_sets()
    s[0]=set()
    r=beta_sets(w,s,coords,beta)
    assert r["status"]=="STOP_FROZEN_SPIDER_TAXA_EIGHT_SITE_ESTIMABILITY"
    assert "original_spider_incremental_eight_LOPO_MSE_gain" not in r

def test_original_event_core_coverage_is_strict():
    t,s,w,sp,beta,ev,r=synthetic_source()
    for row in sp[:40]:
        row["source_coreid"]="unmatched-observation"
    out=analyse_original(t,s,w,sp,beta,ev,r)
    assert out["status"]=="STOP_ORIGINAL_RESPONSE_JOIN_OR_RANK_QUALITY"
    assert "original_spider_incremental_eight_LOPO_MSE_gain" not in out
    assert out["spider_Event_occurrence_join_fraction"]<.98
