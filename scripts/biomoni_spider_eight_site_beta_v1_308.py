#!/usr/bin/env python3
"""v1.308: exploratory eight-site Spider→Woody turnover prediction.

This is NOT v1.304 original all-ten-site endpoint and is NOT geographic
replication or a causal plant-to-spider effect. The eight sites were selected
by declared original Event coordinate QA before opening spider Occurrence
values. The original 10-site coordinate/time gate remains terminal.
"""
from __future__ import annotations
import argparse,hashlib,json,math,random,urllib.request,statistics
from collections import Counter
from pathlib import Path
from biomoni_spider_eight_site_event_v1_307 import (
    SOURCE,event_index,qualify as event_qualify,MAX_BYTES
)
from biomoni_terceira_event_colocation_v1_298 import extract_event_core_only,norm
from biomoni_colocated_woody_beetle_beta_v1_300 import (
    original_occurrence_body,_jaccard,_geokm,_lopo,_q
)

LAMBDA=0.1
PERMUTATIONS=999
SEED=20261028
SOURCE_OCC={"woody":402,"spider":1639}
TREE_RANKS={"species","subspecies"}
SPIDER_RANKS={"species","subspecies","morphospecies"}

def match_source_event_ids(tree_events,spider_events,source_contract,receipt):
    design=event_qualify(tree_events,spider_events,source_contract)
    if (design["status"]!="NEW_EXPLORATORY_EIGHT_PHYSICAL_PLOTS_EQUAL_SPIDER_METHODS_RESPONSE_SEALED"
        or receipt.get("status")!=design["status"]
        or receipt.get("source_original_qualified_tree_coreids_sha256")!=design["source_original_qualified_tree_coreids_sha256"]
        or receipt.get("source_original_qualified_spider_coreids_sha256")!=design["source_original_qualified_spider_coreids_sha256"]
        or receipt.get("source_original_physical_plot_and_subevent_join_sha256")!=design["source_original_physical_plot_and_subevent_join_sha256"]):
        raise ValueError("Original Event-only eight-site cohort does not match frozen source receipt")
    t,_=event_index(tree_events,"woody")
    s,_=event_index(spider_events,"spider")
    common=set.intersection(*(set(v["method"] for v in s[k]) for k in s))
    minimum={mode:min(sum(v["method"]==mode for v in s[k]) for k in s)
             for mode in common}
    chosen=[]
    for k in sorted(t):
        tr=t[k][0]
        if all(max(abs(tr["lat"]-v["lat"]),abs(tr["lon"]-v["lon"]))<=0.0003 for v in s[k]):
            chosen.append(k)
    if len(chosen)!=8:raise ValueError("Exact original eight physical sites no longer supported")
    tree_to_site={t[k][0]["core"]:i for i,k in enumerate(chosen)}
    spider_to_site={}
    for i,k in enumerate(chosen):
        for method in sorted(common):
            cores=sorted(v["core"] for v in s[k] if v["method"]==method)
            for core in cores[:minimum[method]]:
                if core in spider_to_site:raise ValueError("Original source Event duplicated across spider plots")
                spider_to_site[core]=i
    if len(spider_to_site)!=184 or len(tree_to_site)!=8:
        raise ValueError("Wrong frozen response-independent source 8×23 Event sample")
    if hashlib.sha256("\n".join(sorted(spider_to_site)).encode()).hexdigest()!=receipt["source_original_qualified_spider_coreids_sha256"]:
        raise ValueError("Original spider subset hash changed")
    coords=[(t[k][0]["lat"],t[k][0]["lon"]) for k in chosen]
    return tree_to_site,spider_to_site,coords,design

def beta_sets(woody,spiders,coords,contract):
    if len(woody)!=8 or len(spiders)!=8 or len(coords)!=8:
        raise ValueError("Eight original paired physical forest plots required")
    minimum=contract["quality"]
    w_counts=[len(v) for v in woody];s_counts=[len(v) for v in spiders]
    if (min(w_counts,default=0)<1 or min(s_counts,default=0)<1
        or sum(v>=2 for v in w_counts)<minimum["at_least_six_eight_plots_each_taxon_two_or_more"]
        or sum(v>=2 for v in s_counts)<minimum["at_least_six_eight_plots_each_taxon_two_or_more"]):
        return {"status":"STOP_FROZEN_SPIDER_TAXA_EIGHT_SITE_ESTIMABILITY",
                "woody_plots_with_two_taxa":sum(v>=2 for v in w_counts),
                "spider_plots_with_two_taxa":sum(v>=2 for v in s_counts)}
    n=8;pairs=[(i,j) for i in range(n) for j in range(i+1,n)]
    dw={p:_jaccard(woody[p[0]],woody[p[1]]) for p in pairs}
    ds={p:_jaccard(spiders[p[0]],spiders[p[1]]) for p in pairs}
    dist={p:_geokm(coords[p[0]],coords[p[1]]) for p in pairs}
    if (sum(x>0 for x in dw.values())<minimum["at_least_five_nonzero_Jaccard_pairs_each_taxon"]
        or sum(x>0 for x in ds.values())<minimum["at_least_five_nonzero_Jaccard_pairs_each_taxon"]):
        return {"status":"STOP_FROZEN_SPIDER_TAXA_EIGHT_SITE_ESTIMABILITY",
                "stop_reason":"Insufficient nonzero pairwise source-community turnover"}
    m0,m1=_lopo(dw,ds,dist,8)
    gain=m0-m1
    rng=random.Random(SEED);null=[]
    for i in range(PERMUTATIONS):
        perm=rng.sample(range(n),n)
        sim={p:_jaccard(spiders[perm[p[0]]],spiders[perm[p[1]]]) for p in pairs}
        _,m_aug=_lopo(dw,sim,dist,8)
        null.append(m0-m_aug)
    null.sort();q95=_q(null,.95)
    return {
        "status":"OBSERVED_EIGHT_PLOT_EXPLORATORY_SPIDER_BETA_SCORE",
        "source_original_independent_plots":8,
        "dependent_plot_pairs":28,
        "source_woody_taxa_total":len(set.union(*woody)),
        "source_spider_taxa_total":len(set.union(*spiders)),
        "original_woody_plot_taxa_min_max":[min(w_counts),max(w_counts)],
        "original_spider_plot_taxa_min_max":[min(s_counts),max(s_counts)],
        "baseline_geographic_only_eight_LOPO_MSE":m0,
        "augmented_geographic_plus_spider_eight_LOPO_MSE":m1,
        "original_spider_incremental_eight_LOPO_MSE_gain":gain,
        "relative_MSE_gain_eight_plot_subset":gain/m0 if m0>0 else None,
        "fixed_plot_label_permutations":PERMUTATIONS,
        "permutation_seed":SEED,
        "original_permutation_null_gain_95th_percentile":q95,
        "original_plot_label_permutation_exceedance_rank":(1+sum(x>=gain for x in null))/1000,
        "positive_exploratory_spider_prediction":bool(gain>0 and gain>q95),
        "not_45_pair_independent_or_new_geographic_confirmation":True
    }

def analyse_original(tree_events,spider_events,tree_occ,spider_occ,contract,event_contract,receipt):
    tree_map,spider_map,coords,design=match_source_event_ids(tree_events,spider_events,event_contract,receipt)
    if len(tree_occ)!=402 or len(spider_occ)!=1639:
        raise ValueError("Original fixed Tree or Spider Occurrence count mismatch")
    tree_event_ids={r["source_coreid"] for r in tree_events}
    spider_event_ids={r["source_coreid"] for r in spider_events}
    tree_join=sum(str(r.get("source_coreid","")).strip() in tree_event_ids for r in tree_occ)/len(tree_occ)
    spider_join=sum(str(r.get("source_coreid","")).strip() in spider_event_ids for r in spider_occ)/len(spider_occ)
    result={
       "schema":"structural.biomoni_eight_spider_woody_observation.v1_308",
       "status":"STOP_ORIGINAL_RESPONSE_JOIN_OR_RANK_QUALITY",
       "original_tree_Occurrence_rows_reopened":len(tree_occ),
       "original_spider_Occurrence_rows_opened":len(spider_occ),
       "original_woody_Event_rows":len(tree_events),
       "original_spider_Event_rows":len(spider_events),
       "selected_original_spider_Event_subset_n":len(spider_map),
       "selected_original_tree_plots":len(tree_map),
       "tree_Event_occurrence_join_fraction":tree_join,
       "spider_Event_occurrence_join_fraction":spider_join,
       "v1_303_and_v1_304_all_ten_site_GATE":"TERMINAL",
       "design_post_original_Event_QA_not_confirmatory":True,
       "original_spider_woody_source_sha256":{k:SOURCE[k][1] for k in SOURCE},
       "no_original_species_site_identifiers_or_coordinates_exported":True,
       "new_confirmatory_systems":0,"GEB_scientific_HOLD":True,"eBird_used":False
    }
    if min(tree_join,spider_join)<contract["quality"]["all_Event_Occurrence_coreid_join_fraction_each_at_least"]:
        result["stop_reason"]="Source archive Event/Occurrence join fraction too low";return result
    woody=[set() for _ in range(8)];spiders=[set() for _ in range(8)]
    for r in tree_occ:
        site=tree_map.get(str(r.get("source_coreid","")).strip())
        if site is None:continue
        if norm(r.get("taxonRank")) in TREE_RANKS:
            name=norm(r.get("scientificName"))
            if name:woody[site].add(name)
    selected_spider_n=0;unresolved_spider_n=0
    for r in spider_occ:
        site=spider_map.get(str(r.get("source_coreid","")).strip())
        if site is None:continue
        selected_spider_n+=1
        name=norm(r.get("scientificName"))
        if not name or norm(r.get("taxonRank")) not in SPIDER_RANKS:
            unresolved_spider_n+=1
        else:spiders[site].add(name)
    result["original_selected_spider_occurrences"]=selected_spider_n
    result["original_unresolved_selected_spider_taxon_count"]=unresolved_spider_n
    result["original_unresolved_spider_fraction"]=unresolved_spider_n/selected_spider_n if selected_spider_n else 1
    if (selected_spider_n==0
        or result["original_unresolved_spider_fraction"]>contract["quality"]["unresolved_spider_taxon_max_fraction"]):
        result["stop_reason"]="Unresolved or empty Spider species-rank source records exceed frozen 5%";return result
    result.update(beta_sets(woody,spiders,coords,contract))
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract",type=Path,required=True)
    parser.add_argument("--event-contract",type=Path,required=True)
    parser.add_argument("--event-receipt",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    contract=json.loads(args.contract.read_text())
    event_contract=json.loads(args.event_contract.read_text())
    receipt=json.loads(args.event_receipt.read_text())
    if (contract.get("schema")!="structural.biomoni_spider_woody_eight_site_beta.v1_308"
        or contract.get("status")!="FROZEN_CONDITIONAL_TO_V1_307_EVENT_QUALIFICATION_BEFORE_FIRST_SPIDER_OCCURRENCE_READ"
        or contract["provenance"]["original_woody_SHA256"]!=SOURCE["woody"][1]
        or contract["provenance"]["original_spider_SHA256"]!=SOURCE["spider"][1]
        or event_contract.get("schema")!="structural.biomoni_terceira_spider_eight_site_metadata_sample.v1_307"):
        raise ValueError("Eight-site separate Spider ecology protocol not frozen")
    result={
       "schema":"structural.biomoni_eight_spider_woody_observation.v1_308",
       "status":"SOURCE_OR_ORIGINAL_RESPONSE_READER_STOP",
       "original_spider_Occurrence_rows_opened":0,
       "original_tree_Occurrence_rows_reopened":0,
       "v1_303_and_v1_304_all_ten_site_GATE":"TERMINAL",
       "new_confirmatory_systems":0,"GEB_scientific_HOLD":True,"eBird_used":False
    }
    try:
        original={};events={}
        for name,(url,sha,n) in SOURCE.items():
            request=urllib.request.Request(url,headers={"User-Agent":"Structural-BioMonI-Spider-Eight-v1.308-OneShot"})
            with urllib.request.urlopen(request,timeout=60) as remote:blob=remote.read(MAX_BYTES+1)
            if len(blob)>MAX_BYTES or hashlib.sha256(blob).hexdigest()!=sha:
                raise ValueError("Published original Spider or Woody ZIP SHA mismatch")
            events[name]=extract_event_core_only(blob);original[name]=blob
        # Site and effort fingerprint verified before first spider taxon record:
        match_source_event_ids(events["woody"],events["spider"],event_contract,receipt)
        w=original_occurrence_body(original["woody"])
        s=original_occurrence_body(original["spider"])
        result["original_spider_Occurrence_rows_opened"]=len(s)
        result["original_tree_Occurrence_rows_reopened"]=len(w)
        result=analyse_original(events["woody"],events["spider"],w,s,contract,event_contract,receipt)
    except Exception as e:
        result["stop_type"]=type(e).__name__
        result["stop_reason"]=str(e)[:280]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({k:result.get(k) for k in (
        "status","original_spider_Occurrence_rows_opened","original_tree_Occurrence_rows_reopened",
        "source_original_independent_plots","original_selected_spider_occurrences",
        "baseline_geographic_only_eight_LOPO_MSE","augmented_geographic_plus_spider_eight_LOPO_MSE",
        "original_spider_incremental_eight_LOPO_MSE_gain",
        "positive_exploratory_spider_prediction","original_plot_label_permutation_exceedance_rank",
        "stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_OR_ORIGINAL_RESPONSE_READER_STOP":raise SystemExit(2)
if __name__=="__main__":main()
