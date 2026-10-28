#!/usr/bin/env python3
"""v1.309: fair SAME eight Terceira plots Beetle vs already scored Spider.

This is a declared retrospective, post-outcome SPATIAL SUBSET sensitivity.
Previously original 10-site Beetle result +4.93%; Spider 8-site result -14.6%.
We only recompute Beetle on the same source-coordinate-qualified 8 Tree sites
to tell whether the original Beetle advantage survives subset restriction.
No Spider species/Occurrence is reopened and original full-method STOP remains.
"""
from __future__ import annotations
import argparse,hashlib,json,math,random,urllib.request,statistics
from collections import Counter
from pathlib import Path
from biomoni_terceira_event_colocation_v1_298 import (
    extract_event_core_only,summarize_site_samples,MAX_BYTES,norm
)
from biomoni_common_method_terceira_v1_299 import evaluate as beetle_source_gate
from biomoni_spider_eight_site_beta_v1_308 import match_source_event_ids
from biomoni_spider_eight_site_event_v1_307 import event_index
from biomoni_colocated_woody_beetle_beta_v1_300 import (
    original_occurrence_body,_jaccard,_geokm,_lopo,_q
)

SOURCES={
  "woody":("https://ipt.gbif.pt/ipt/archive.do?r=biomoni_trees&v=1.7",
      "4574d02727654ec5a319f6d1218ff9243080b0128c517d01c905065cbefd6f82",30),
  "beetle":("https://ipt.gbif.pt/ipt/archive.do?r=biomoni_beetles&v=1.3",
      "e518beb6f529067cc2f38013e03c4f833e86133fddface1df6f9ba7c532885e8",308),
  "spider":("https://ipt.gbif.pt/ipt/archive.do?r=spiders_macaronesia_azores&v=1.8",
      "17f65284214ae35a302fee2fa42747e2ecfabb8d04bf9ec8394b6d33c5c4f7b5",423)
}
PERMUTATIONS=999
SEED=20261028
WOODY_RANKS={"species","subspecies"}

def reconstruct_event_cohort(t,b,s,event_contract,spider_receipt,v299,v298,v300,contract):
    tree_map,_,coords,design=match_source_event_ids(t,s,event_contract,spider_receipt)
    old=beetle_source_gate(t,b,v299,v298)
    if (old["status"]!="EXPLORATORY_TEN_PLOTS_SIX_COMMON_METHOD_BEETLE_EVENTS_EACH_RESPONSE_SEALED"
        or old["selected_original_Event_coreids_sha256"]!=v300["frozen_event_receipt"]["selected_beetle_Event_coreids_sha256"]
        or old["full_original_tree_beetle_Event_crosswalk_SHA256"]!=v300["frozen_event_receipt"]["original_full_site_woody_beetle_crosswalk_sha256"]):
        raise ValueError("Original v1.299 ten-wide fixed Beetle sampling receipt mismatch")
    ti,_=event_index(t,"woody")
    bs=summarize_site_samples(b,"beetle")
    selected_site=[next(k for k in ti if ti[k][0]["core"]==core)
                   for core,_ in sorted(tree_map.items(),key=lambda z:z[1])]
    if len(selected_site)!=8 or len(set(selected_site))!=8:
        raise ValueError("Eight original physical source sites not preserved")
    if any(k not in bs for k in selected_site):
        raise ValueError("Original 8 tree plot ids missing in Beetle source")
    common=set.intersection(*(set(r["method"] for r in bs[k]) for k in bs))
    minimum={mode:min(sum(r["method"]==mode for r in bs[k]) for k in bs) for mode in common}
    if (len(common)!=3 or sorted(minimum.values())!=[1,1,4]):
        raise ValueError("Original common Beetle sampling modes changed")
    all60=[];beetle_map={}
    for k in sorted(bs):
        sub=[]
        for mode in sorted(common):
            sub.extend(sorted(r["core"] for r in bs[k] if r["method"]==mode)[:minimum[mode]])
        all60.extend(sub)
    if hashlib.sha256("\n".join(sorted(all60)).encode()).hexdigest()!=v300["frozen_event_receipt"]["selected_beetle_Event_coreids_sha256"]:
        raise ValueError("Old 60 Beetle Event-source fingerprint does not replay")
    for index,k in enumerate(selected_site):
        chosen=[]
        for mode in sorted(common):
            chosen.extend(sorted(r["core"] for r in bs[k] if r["method"]==mode)[:minimum[mode]])
        if len(chosen)!=6:raise ValueError("Original Beetle 6 Events per matched physical plot not realized")
        for core in chosen:
            if core in beetle_map: raise ValueError("Duplicate original Beetle source core ID")
            beetle_map[core]=index
    if len(beetle_map)!=48:
        raise ValueError("Eight original source plot × six Beetle sampling events missing")
    if set(tree_map.values())!=set(range(8)):
        raise ValueError("Tree original source plot indices not equivalent")
    return tree_map,beetle_map,coords,old

def score_sets(woody,beetle,coords,proto,spider_freeze):
    if len(woody)!=8 or len(beetle)!=8 or len(coords)!=8:
        raise ValueError("Exactly eight paired source sites required")
    wcount=[len(x) for x in woody];bcount=[len(x) for x in beetle]
    minimum=proto["analysis"]
    if (min(wcount)<1 or min(bcount)<1
        or sum(x>=2 for x in wcount)<6
        or sum(x>=2 for x in bcount)<6):
        return {"status":"STOP_FROZEN_FAIR_BEETLE_EIGHT_SITE_TAXON_SUPPORT",
                "woody_eligible_sites_2plus":sum(x>=2 for x in wcount),
                "beetle_eligible_sites_2plus":sum(x>=2 for x in bcount)}
    pairs=[(i,j) for i in range(8) for j in range(i+1,8)]
    wdist={p:_jaccard(woody[p[0]],woody[p[1]]) for p in pairs}
    bdist={p:_jaccard(beetle[p[0]],beetle[p[1]]) for p in pairs}
    geo={p:_geokm(coords[p[0]],coords[p[1]]) for p in pairs}
    if sum(x>0 for x in wdist.values())<5 or sum(x>0 for x in bdist.values())<5:
        return {"status":"STOP_FROZEN_FAIR_BEETLE_EIGHT_SITE_TAXON_SUPPORT",
                "stop_reason":"Original source paired Jaccard dissimilarities insufficient"}
    baseline,beetle_augmented=_lopo(wdist,bdist,geo,8)
    fixed=spider_freeze["baseline_distance_only_LOPO_MSE"]
    if not math.isclose(baseline,fixed,rel_tol=0,abs_tol=1e-10):
        return {"status":"STOP_BASELINE_WOODY_RESPONSE_NOT_REPRODUCED",
                "original_spider_baseline_LOPO_MSE":fixed,
                "new_beetle_matching_baseline_LOPO_MSE":baseline}
    gain=baseline-beetle_augmented
    rng=random.Random(SEED);null=[]
    for _ in range(PERMUTATIONS):
        perm=rng.sample(range(8),8)
        bperm={p:_jaccard(beetle[perm[p[0]]],beetle[perm[p[1]]]) for p in pairs}
        _,mean_square=_lopo(wdist,bperm,geo,8)
        null.append(baseline-mean_square)
    null.sort()
    q95=_q(null,.95)
    spider_gain=spider_freeze["spider_delta_LOPO_MSE"]
    return {
      "status":"OBSERVED_FAIR_EIGHT_SITE_BEETLE_SPATIAL_SUBSET_COMPARATOR",
      "source_independent_woody_plots":8,
      "source_dependent_plot_pairs":28,
      "source_woody_operational_taxa_total":len(set.union(*woody)),
      "source_beetle_operational_taxa_total":len(set.union(*beetle)),
      "original_geography_only_LOPO_MSE":baseline,
      "original_woody_spider_reference_baseline_MSE_reproduced":True,
      "beetle_added_LOPO_MSE":beetle_augmented,
      "beetle_eight_incremental_LOPO_MSE_gain":gain,
      "beetle_eight_relative_LOPO_MSE_gain":gain/baseline,
      "beetle_plot_label_null_permutations":PERMUTATIONS,
      "beetle_plot_label_fixed_seed":SEED,
      "beetle_plot_label_null_gain_95pct":q95,
      "beetle_plot_label_exceedance_rank":(1+sum(z>=gain for z in null))/1000,
      "beetle_eight_positive_against_frozen_null":gain>0 and gain>q95,
      "already_observed_spider_same_eight_gain":spider_gain,
      "beetle_minus_spider_same_eight_gain":gain-spider_gain,
      "spider_site_or_taxa_replayed_in_v309":False,
      "beetle_v300_prior_ten_site_gain_not_comparable_without_same_eight_recompute":True,
      "guild_effect_descriptive_not_causal_or_independent_geographic_confirmation":True
    }

def original_score(tree_events,beetle_events,spider_events,tree_occ,beetle_occ,
                   contract,event_contract,spider_receipt,v299,v298,v300,spider_result):
    tree_map,beetle_map,coords,old=reconstruct_event_cohort(
      tree_events,beetle_events,spider_events,event_contract,spider_receipt,v299,v298,v300,contract)
    if len(tree_occ)!=402 or len(beetle_occ)!=539:
        raise ValueError("Original woody and beetle Occurrence source denominator changed")
    t_cores={r["source_coreid"] for r in tree_events}
    b_cores={r["source_coreid"] for r in beetle_events}
    tjoin=sum(str(r.get("source_coreid","")).strip() in t_cores for r in tree_occ)/len(tree_occ)
    bjoin=sum(str(r.get("source_coreid","")).strip() in b_cores for r in beetle_occ)/len(beetle_occ)
    result={
       "schema":"structural.biomoni_fair_eight_beetle_comparator.v1_309",
       "status":"STOP_ORIGINAL_BEETLE_SOURCE_QUALITY",
       "original_woody_Occurrence_rows_reopened":len(tree_occ),
       "original_beetle_Occurrence_rows_reopened":len(beetle_occ),
       "original_spider_Occurrence_rows_reopened":0,
       "original_fixed_tree_and_beetle_original_event_rows":[len(tree_events),len(beetle_events)],
       "source_original_beetle_selected_8_events":len(beetle_map),
       "source_exact_8_coordinate_qualified_tree_plots":len(tree_map),
       "original_tree_Event_join_fraction":tjoin,
       "original_beetle_Event_join_fraction":bjoin,
       "old_beetle_full_method_v1_298":"TERMINAL",
       "old_spider_ten_site_v1_303_v1_304":"TERMINAL",
       "source_woody_beetle_spider_SHA256":{k:v[1] for k,v in SOURCES.items()},
       "not_new_independent_ecological_confirmation":True,
       "original_taxon_plot_id_coordinates_omitted":True,
       "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    if min(tjoin,bjoin)<.98:
        result["stop_reason"]="Original Event/Occurrence join completeness below 98%";return result
    w=[set() for _ in range(8)]
    b=[set() for _ in range(8)]
    for o in tree_occ:
        i=tree_map.get(str(o.get("source_coreid","")).strip())
        if i is None:continue
        if norm(o.get("taxonRank")) in ("species","subspecies"):
            taxon=norm(o.get("scientificName"))
            if taxon:w[i].add(taxon)
    nselected=0;nunresolved=0
    for o in beetle_occ:
        i=beetle_map.get(str(o.get("source_coreid","")).strip())
        if i is None:continue
        nselected+=1
        name=norm(o.get("scientificName"))
        if not name:nunresolved+=1
        else:b[i].add(name)
    result["selected_beetle_occurrence_rows"]=nselected
    result["unresolved_original_selected_beetle_taxa_fraction"]=nunresolved/nselected if nselected else 1
    if nselected==0 or result["unresolved_original_selected_beetle_taxa_fraction"]>.05:
        result["stop_reason"]="Original selected Beetle taxon labels do not meet old 5% resolution limit";return result
    result.update(score_sets(w,b,coords,contract,spider_result))
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for k in ("--contract","--spider-event-contract","--spider-event-receipt",
              "--beetle-method-contract","--beetle-older-crosswalk","--old-beetle-score-contract",
              "--original-spider-observation"):
        parser.add_argument(k,type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    cfg=json.loads(a.contract.read_text())
    event=json.loads(a.spider_event_contract.read_text())
    receipt=json.loads(a.spider_event_receipt.read_text())
    v299=json.loads(a.beetle_method_contract.read_text())
    v298=json.loads(a.beetle_older_crosswalk.read_text())
    v300=json.loads(a.old_beetle_score_contract.read_text())
    spider=json.loads(a.original_spider_observation.read_text())
    if (cfg.get("schema")!="structural.biomoni_terceira_eight_fair_beetle_versus_spider.v1_309"
        or cfg["status"]!="FROZEN_POST_SPIDER_OUTCOME_EXPLORATORY_SAME_8_PLOT_COMPARATOR_BEFORE_BEETLE_8_RECOMPUTATION"
        or any(cfg["source"][k+"_sha256"]!=SOURCES[k][1] for k in SOURCES)
        or cfg["source"]["v1_308_original_observation_JSON_sha256"]!=spider["original_original_artifact_JSON_sha256"]
        or receipt["status"]!="NEW_EXPLORATORY_EIGHT_PHYSICAL_PLOTS_EQUAL_SPIDER_METHODS_RESPONSE_SEALED"
        or spider["status"]!="OBSERVED_EIGHT_PLOT_EXPLORATORY_SPIDER_BETA_SCORE"):
        raise ValueError("Eight-site fair Beetle comparator not frozen against previous Spider outcome")
    result={
       "schema":"structural.biomoni_fair_eight_beetle_comparator.v1_309",
       "status":"SOURCE_OR_ORIGINAL_COMPARATOR_TECHNICAL_STOP",
       "original_spider_Occurrence_rows_reopened":0,
       "original_woody_Occurrence_rows_reopened":0,
       "original_beetle_Occurrence_rows_reopened":0,
       "old_spider_ten_site_v1_303_v1_304":"TERMINAL",
       "old_beetle_full_method_v1_298":"TERMINAL",
       "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        blob={};event_rows={}
        for k,(url,sha,count) in SOURCES.items():
            req=urllib.request.Request(url,headers={"User-Agent":"Structural-BioMonI-Eight-Site-Beetle-Fair-v1.309"})
            with urllib.request.urlopen(req,timeout=60) as remote:
                data=remote.read(MAX_BYTES+1)
            if len(data)>MAX_BYTES or hashlib.sha256(data).hexdigest()!=sha:
                raise ValueError("Original tree/Beetle/Spider Event source zip hash changed")
            event_rows[k]=extract_event_core_only(data)
            blob[k]=data if k in ("woody","beetle") else None
        reconstruct_event_cohort(event_rows["woody"],event_rows["beetle"],event_rows["spider"],
             event,receipt,v299,v298,v300,cfg)
        # Spider biological data NOT reopened. Old woody/beetle source responses
        # are already exposed, and used for one pre-frozen fair eight-site sensitivity.
        tree_occ=original_occurrence_body(blob["woody"])
        beetle_occ=original_occurrence_body(blob["beetle"])
        result["original_woody_Occurrence_rows_reopened"]=len(tree_occ)
        result["original_beetle_Occurrence_rows_reopened"]=len(beetle_occ)
        result=original_score(event_rows["woody"],event_rows["beetle"],event_rows["spider"],
            tree_occ,beetle_occ,cfg,event,receipt,v299,v298,v300,spider)
    except Exception as exc:
        result["stop_type"]=type(exc).__name__
        result["stop_reason"]=str(exc)[:330]
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:result.get(k) for k in (
       "status","source_exact_8_coordinate_qualified_tree_plots",
       "source_original_beetle_selected_8_events","selected_beetle_occurrence_rows",
       "original_geography_only_LOPO_MSE","beetle_added_LOPO_MSE",
       "beetle_eight_incremental_LOPO_MSE_gain","beetle_eight_positive_against_frozen_null",
       "already_observed_spider_same_eight_gain","beetle_plot_label_exceedance_rank",
       "stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_OR_ORIGINAL_COMPARATOR_TECHNICAL_STOP":raise SystemExit(2)
if __name__=="__main__":main()
