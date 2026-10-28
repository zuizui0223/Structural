"""Synthetic-only fair 8-site Beetle comparator against Spider 8-site baseline."""
import copy,json,sys,math
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from biomoni_fair_eight_beetle_spider_v1_309 import reconstruct_event_cohort,score_sets,original_score
from biomoni_spider_eight_site_event_v1_307 import qualify as spider_event_gate
from test_biomoni_spider_eight_site_event_v1_307 import build
from test_biomoni_terceira_event_colocation_v1_298 import fixtures as beetle_fixture
from biomoni_common_method_terceira_v1_299 import evaluate as beetle_event_gate
from biomoni_colocated_woody_beetle_beta_v1_300 import _jaccard,_geokm,_lopo

def contracts():
    def read(p):return json.loads((ROOT/"development"/p).read_text(encoding="utf-8"))
    return (
        read("biomoni_fair_eight_beetle_spider_comparator_protocol_v1_309.json"),
        read("biomoni_spider_eight_site_source_gate_v1_307.json"),
        read("biomoni_common_method_study_design_v1_299.json"),
        read("biomoni_terceira_colocated_event_gate_v1_298.json"),
        read("biomoni_colocated_woody_beetle_beta_transfer_protocol_v1_300.json")
    )

def synthetic_events():
    tree,spider=build()
    _,beetle=beetle_fixture()
    for site in range(10):
        rows=[r for r in beetle if r["source_coreid"].startswith(f"b-ter-{site}-")]
        rows.sort(key=lambda r:r["source_coreid"])
        for i,rec in enumerate(rows):
            if i==0:rec["samplingProtocol"]="AAS"
            elif i<5:rec["samplingProtocol"]="PIT"
            elif i==5:rec["samplingProtocol"]="GWS"
            else:rec["samplingProtocol"]=f"private_{site}"
    p,sp,be,old,v300=contracts()
    spider_receipt=spider_event_gate(tree,spider,sp)
    beetle_receipt=beetle_event_gate(tree,beetle,be,old)
    assert beetle_receipt["status"]=="EXPLORATORY_TEN_PLOTS_SIX_COMMON_METHOD_BEETLE_EVENTS_EACH_RESPONSE_SEALED"
    v300["frozen_event_receipt"]["selected_beetle_Event_coreids_sha256"]=beetle_receipt["selected_original_Event_coreids_sha256"]
    v300["frozen_event_receipt"]["original_full_site_woody_beetle_crosswalk_sha256"]=beetle_receipt["full_original_tree_beetle_Event_crosswalk_SHA256"]
    return tree,beetle,spider,p,sp,spider_receipt,be,old,v300

def paired_sets():
    woody=[{"tree common","tree even" if i%2==0 else "tree odd"} for i in range(8)]
    beetle=[{"beetle common","beetle even" if i%2==0 else "beetle odd"} for i in range(8)]
    coords=[(38.700+i*0.004,-27.200-i*0.003) for i in range(8)]
    pairs=[(i,j) for i in range(8) for j in range(i+1,8)]
    w={p:_jaccard(woody[p[0]],woody[p[1]]) for p in pairs}
    b={p:_jaccard(beetle[p[0]],beetle[p[1]]) for p in pairs}
    dist={p:_geokm(coords[p[0]],coords[p[1]]) for p in pairs}
    baseline,_=_lopo(w,b,dist,8)
    return woody,beetle,coords,baseline

def test_source_only_8_of_10_woody_sites_get_exact_48_original_beetle_events():
    tree,beetle,spider,p,sp,receipt,be,old,v300=synthetic_events()
    tw,bm,xy,metadata=reconstruct_event_cohort(tree,beetle,spider,sp,receipt,be,old,v300,p)
    assert len(tw)==8 and len(bm)==48 and len(xy)==8
    assert set(tw.values())==set(range(8))
    assert set(bm.values())==set(range(8))
    assert metadata["old_v1_298_full_method_gate_remains_terminal"]
    assert "TREE_SITE_SECRET" not in str(metadata)

def test_eight_original_physical_plot_known_truth_reproduces_geographic_baseline():
    proto,*_=contracts()
    w,b,coords,m0=paired_sets()
    prev={"baseline_distance_only_LOPO_MSE":m0,
          "spider_delta_LOPO_MSE":-0.01}
    r=score_sets(w,b,coords,proto,prev)
    assert r["status"]=="OBSERVED_FAIR_EIGHT_SITE_BEETLE_SPATIAL_SUBSET_COMPARATOR"
    assert r["source_independent_woody_plots"]==8 and r["source_dependent_plot_pairs"]==28
    assert r["original_woody_spider_reference_baseline_MSE_reproduced"]
    assert r["beetle_eight_incremental_LOPO_MSE_gain"]>0
    assert r["beetle_plot_label_null_permutations"]==999
    assert r["beetle_plot_label_fixed_seed"]==20261028
    assert r["beetle_minus_spider_same_eight_gain"]>0

def test_wrong_baseline_is_not_a_new_favorable_model_tune():
    proto,*_=contracts()
    w,b,xy,m0=paired_sets()
    r=score_sets(w,b,xy,proto,{"baseline_distance_only_LOPO_MSE":m0+0.01,
                                 "spider_delta_LOPO_MSE":-0.02})
    assert r["status"]=="STOP_BASELINE_WOODY_RESPONSE_NOT_REPRODUCED"
    assert "beetle_eight_incremental_LOPO_MSE_gain" not in r

def test_original_response_reader_restricts_to_same_eight_plot_and_no_spider_species():
    tree,beetle,spider,p,sp,receipt,be,old,v300=synthetic_events()
    tw,bm,coords,_=reconstruct_event_cohort(tree,beetle,spider,sp,receipt,be,old,v300,p)
    wood=[]
    for core,i in tw.items():
        wood.extend([
          {"source_coreid":core,"scientificName":"Tree shared","taxonRank":"species"},
          {"source_coreid":core,"scientificName":"Tree even" if i%2==0 else "Tree odd","taxonRank":"species"}
        ])
    wood_other=next(r["source_coreid"] for r in tree if r["island"]=="Tenerife")
    wood.extend([{"source_coreid":wood_other,"scientificName":"Tree out","taxonRank":"species"}]*(402-len(wood)))
    beet=[]
    bysite={}
    for core,i in bm.items():bysite.setdefault(i,[]).append(core)
    for i,ids in bysite.items():
        ids.sort()
        beet.extend([
          {"source_coreid":ids[0],"scientificName":"Beetle shared","taxonRank":"species"},
          {"source_coreid":ids[1],"scientificName":"Beetle even" if i%2==0 else "Beetle odd","taxonRank":"species"}
        ])
    other=next(r["source_coreid"] for r in beetle if r["island"]=="Pico")
    beet.extend([{"source_coreid":other,"scientificName":"Beetle elsewhere","taxonRank":"species"}]*(539-len(beet)))
    assert len(wood)==402 and len(beet)==539
    pairs=[(i,j) for i in range(8) for j in range(i+1,8)]
    # Reconstruct the same original target baseline with exact eight plot index.
    wsets=[{"tree shared","tree even" if i%2==0 else "tree odd"} for i in range(8)]
    bsets=[{"beetle shared","beetle even" if i%2==0 else "beetle odd"} for i in range(8)]
    wd={z:_jaccard(wsets[z[0]],wsets[z[1]]) for z in pairs}
    bd={z:_jaccard(bsets[z[0]],bsets[z[1]]) for z in pairs}
    gd={z:_geokm(coords[z[0]],coords[z[1]]) for z in pairs}
    original_m0,_=_lopo(wd,bd,gd,8)
    old_spider={"baseline_distance_only_LOPO_MSE":original_m0,
                "spider_delta_LOPO_MSE":-0.002}
    r=original_score(tree,beetle,spider,wood,beet,p,sp,receipt,be,old,v300,old_spider)
    assert r["status"]=="OBSERVED_FAIR_EIGHT_SITE_BEETLE_SPATIAL_SUBSET_COMPARATOR"
    assert r["source_original_beetle_selected_8_events"]==48
    assert r["original_spider_Occurrence_rows_reopened"]==0
    assert r["original_beetle_Occurrence_rows_reopened"]==539
    assert r["original_woody_Occurrence_rows_reopened"]==402
    assert r["source_exact_8_coordinate_qualified_tree_plots"]==8
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]
    assert "Tree shared" not in json.dumps(r)
    assert r["original_taxon_plot_id_coordinates_omitted"]
