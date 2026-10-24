#!/usr/bin/env python3
"""v1.300 cross-taxon turnover at EXACT 10 original Terceira forest plots.

Original woody/COBRA beetle responses are read ONCE only after the preserved
response-free 6 beetle sample events ×10 physical plot fingerprint passes.
The full original v1.298 beetle-survey method comparability gate remains
terminal. This is a descriptive spatial-ecology study, not evidence of
population rescue, causal plant-to-beetle interaction or island replication.
"""
from __future__ import annotations

import argparse,csv,hashlib,io,json,math,random,statistics,urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict,Counter
from pathlib import Path

from biomoni_terceira_event_colocation_v1_298 import (
    SOURCE,MAX_BYTES,extract_event_core_only,summarize_site_samples
)
from biomoni_common_method_terceira_v1_299 import evaluate as physical_evaluate

R_EARTH_KM=6371.0088
WOODY_ALLOWED_RANK={"species","subspecies"}
SOURCE_OCCURRENCE_ROWS={"woody":402,"beetle":539}
SOURCE_EVENT_ROWS={"woody":30,"beetle":308}
PERMUTATIONS=999
SEED=20261024
LAMBDA=0.1

def local(s):return s.rsplit("}",1)[-1]
def term(s):return s.rstrip("/").split("/")[-1].split("#")[-1]
def norm(s):return " ".join(str(s or "").casefold().strip().split())

def original_occurrence_body(blob):
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        xml=ET.fromstring(z.read("meta.xml"))
        ext=[e for e in xml if local(e.tag)=="extension"
             and e.attrib.get("rowType","").rstrip("/").endswith("/Occurrence")]
        if len(ext)!=1:raise ValueError("Exactly one author original occurrence extension required")
        node=ext[0];cols={};coreidx=None;member=None
        for e in node.iter():
            if local(e.tag)=="field" and "term" in e.attrib and "index" in e.attrib:
                cols[term(e.attrib["term"])]=int(e.attrib["index"])
            elif local(e.tag)=="coreid" and "index" in e.attrib:
                coreidx=int(e.attrib["index"])
            elif local(e.tag)=="location" and e.text:member=e.text.strip()
        if coreidx is None or not member or not {"scientificName","taxonRank"}.issubset(cols):
            raise ValueError("Original source taxonomy and Event linkage missing")
        sep=node.attrib.get("fieldsTerminatedBy",r"\t").replace(r"\t","\t")
        if len(sep)!=1:raise ValueError("Source taxonomic delimiter not supported")
        skip=int(node.attrib.get("ignoreHeaderLines","0"))
        if skip<0 or skip>2:raise ValueError("Source taxonomic header count unexpected")
        rows=[]
        with z.open(member) as src:
            with io.TextIOWrapper(src,encoding="utf-8-sig",newline="") as f:
                rd=csv.reader(f,delimiter=sep)
                for _ in range(skip):next(rd,None)
                for data in rd:
                    if not data or not any(data):continue
                    if max(coreidx,cols["scientificName"],cols["taxonRank"])>=len(data):
                        raise ValueError("Malformed original taxon occurrence record")
                    d={k:data[ix] for k,ix in cols.items() if ix<len(data)}
                    d["source_coreid"]=data[coreidx]
                    rows.append(d)
        return rows

def _jaccard(a,b):
    union=len(a|b)
    if union==0:raise ValueError("Cannot score two undetected communities")
    return 1-len(a&b)/union

def _geokm(a,b):
    lat1,lon1=map(math.radians,a);lat2,lon2=map(math.radians,b)
    v=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return R_EARTH_KM*2*math.atan2(math.sqrt(v),math.sqrt(max(0,1-v)))

def _ridge(train,test,cols):
    # Fit a frozen intercept plus standardized L2-penalized slopes, no CV tuning.
    y=[v["tree_d"] for v in train]
    mu=statistics.fmean(y)
    scales=[]
    for col in cols:
        xx=[v[col] for v in train]
        mean=statistics.fmean(xx)
        sd=math.sqrt(math.fsum((v-mean)**2 for v in xx)/len(xx))
        scales.append((mean,sd))
    def transformed(record):
        return [(record[col]-mean)/sd if sd>0 else 0.
                for col,(mean,sd) in zip(cols,scales)]
    z=[transformed(v) for v in train]
    rhs=[math.fsum(vec[i]*(yy-mu) for vec,yy in zip(z,y))
          for i in range(len(cols))]
    if len(cols)==1:
        a=math.fsum(vec[0]**2 for vec in z)+LAMBDA
        beta=[rhs[0]/a]
    elif len(cols)==2:
        a=math.fsum(vec[0]**2 for vec in z)+LAMBDA
        b=math.fsum(vec[0]*vec[1] for vec in z)
        d=math.fsum(vec[1]**2 for vec in z)+LAMBDA
        det=a*d-b*b
        if det<=0:raise ValueError("Ridge normal equation not invertible")
        beta=[(rhs[0]*d-rhs[1]*b)/det,
              (rhs[1]*a-rhs[0]*b)/det]
    else:raise ValueError("Only frozen one or two predictors allowed")
    predictions=[mu+math.fsum(zj*bj for zj,bj in zip(transformed(v),beta))
                 for v in test]
    return predictions

def _lopo(tree_d, beetle_d, distances, n):
    records=[{"i":i,"j":j,"tree_d":tree_d[(i,j)],
              "beetle_d":beetle_d[(i,j)],
              "geo_logkm":math.log1p(distances[(i,j)])}
             for i in range(n) for j in range(i+1,n)]
    mse0=[];mse1=[]
    for held in range(n):
        train=[q for q in records if held not in (q["i"],q["j"])]
        test=[q for q in records if held in (q["i"],q["j"])]
        if len(train)!=(n-1)*(n-2)//2 or len(test)!=n-1:
            raise ValueError("Wrong leave-one-plot-out pair grain")
        pred0=_ridge(train,test,["geo_logkm"])
        pred1=_ridge(train,test,["geo_logkm","beetle_d"])
        mse0.append(statistics.fmean((r["tree_d"]-v)**2 for r,v in zip(test,pred0)))
        mse1.append(statistics.fmean((r["tree_d"]-v)**2 for r,v in zip(test,pred1)))
    return statistics.fmean(mse0), statistics.fmean(mse1)

def _q(sorted_x,p):
    pos=p*(len(sorted_x)-1);i=int(pos);f=pos-i
    return sorted_x[i]*(1-f)+sorted_x[min(i+1,len(sorted_x)-1)]*f

def analyse_sets(woody_sets,beetle_sets,coords,contract):
    n=len(woody_sets)
    if n!=10 or len(beetle_sets)!=10 or len(coords)!=10:
        raise ValueError("Exactly 10 original physical plot units required")
    wr=[len(s) for s in woody_sets]
    br=[len(s) for s in beetle_sets]
    floor=contract["quality_before_model"]
    if (min(wr)<floor["all_ten_original_woody_and_beetle_plots_min_unique_taxa"]
        or min(br)<floor["all_ten_original_woody_and_beetle_plots_min_unique_taxa"]
        or sum(v>=2 for v in wr)<8 or sum(v>=2 for v in br)<8):
        return {"status":"STOP_FROZEN_BIOLOGICAL_ESTIMABILITY_NO_CROSS_TAXON_SCORE",
                "stop_reason":"Fewer than ten detected plots or fewer than eight with two taxa in either taxon group",
                "original_beetle_plots_with_two_or_more_taxa":sum(v>=2 for v in br),
                "original_woody_plots_with_two_or_more_taxa":sum(v>=2 for v in wr)}
    pairs=[(i,j) for i in range(n) for j in range(i+1,n)]
    wd={pair:_jaccard(woody_sets[pair[0]],woody_sets[pair[1]]) for pair in pairs}
    bd={pair:_jaccard(beetle_sets[pair[0]],beetle_sets[pair[1]]) for pair in pairs}
    geo={pair:_geokm(coords[pair[0]],coords[pair[1]]) for pair in pairs}
    if (sum(v>0 for v in wd.values())<floor["woody_Jaccard_pair_range_above_zero_min_pairs"]
        or sum(v>0 for v in bd.values())<floor["beetle_Jaccard_pair_range_above_zero_min_pairs"]):
        return {"status":"STOP_FROZEN_BIOLOGICAL_ESTIMABILITY_NO_CROSS_TAXON_SCORE",
                "stop_reason":"Insufficient nonzero community-turnover plot pairs"}
    old,new=_lopo(wd,bd,geo,n)
    gain=old-new
    rng=random.Random(SEED)
    null=[]
    for _ in range(PERMUTATIONS):
        order=rng.sample(range(n),n)
        perm_bd={p:_jaccard(beetle_sets[order[p[0]]],beetle_sets[order[p[1]]]) for p in pairs}
        _,n_mse=_lopo(wd,perm_bd,geo,n)
        null.append(old-n_mse)
    null.sort()
    q95=_q(null,.95)
    rank=(1+sum(v>=gain for v in null))/(PERMUTATIONS+1)
    return {
       "status":"SOURCE_OBSERVED_COLOCATED_BETA_PREDICTIVE_CONGRUENCE_SCORED",
       "woody_plot_taxa_richness_min_max":[min(wr),max(wr)],
       "beetle_plot_taxa_richness_min_max":[min(br),max(br)],
       "woody_distinct_operational_taxa_all_plots":len(set.union(*woody_sets)),
       "beetle_distinct_operational_taxa_all_plots":len(set.union(*beetle_sets)),
       "plot_pair_n":45,"physically_independent_plot_n":10,
       "geographic_distance_km_min_max":[min(geo.values()),max(geo.values())],
       "woody_dissimilarity_nonzero_pairs":sum(v>0 for v in wd.values()),
       "beetle_dissimilarity_nonzero_pairs":sum(v>0 for v in bd.values()),
       "baseline_geo_only_LOPO_MSE":old,
       "added_beetle_LOPO_MSE":new,
       "primary_beetle_incremental_LOPO_MSE_gain":gain,
       "ratio_relative_mse_gain_of_baseline":gain/old if old>0 else None,
       "fixed_permutation_label_shuffle_n":PERMUTATIONS,
       "permutation_fixed_seed":SEED,
       "permutation_null_gain_95th_percentile":q95,
       "permutation_plot_label_exceedance_rank":rank,
       "descriptive_positive_cross_taxon_information":gain>0 and gain>q95,
       "not_plot_pair_independent_significance":True,
    }

def score_original(t_events,b_events,t_obs,b_obs,event_contract,method_contract,contract):
    if len(t_obs)!=402 or len(b_obs)!=539:
        raise ValueError("Original published source Occurrence counts not exact")
    original_event=physical_evaluate(t_events,b_events,method_contract,event_contract)
    pinned=contract["frozen_event_receipt"]
    if (original_event["status"]!="EXPLORATORY_TEN_PLOTS_SIX_COMMON_METHOD_BEETLE_EVENTS_EACH_RESPONSE_SEALED"
        or original_event["full_original_tree_beetle_Event_crosswalk_SHA256"]!=
            pinned["original_full_site_woody_beetle_crosswalk_sha256"]
        or original_event["selected_original_Event_coreids_sha256"]!=
            pinned["selected_beetle_Event_coreids_sha256"]
        or original_event["selected_cross_taxon_site_tree_beetle_method_fingerprint"]!=
            pinned["selected_tree_beetle_method_site_fingerprint"]):
        raise ValueError("Frozen original response-independent author Event inclusion fingerprint changed")
    ts=summarize_site_samples(t_events,"woody")
    bs=summarize_site_samples(b_events,"beetle")
    keys=sorted(ts)
    if len(keys)!=10 or set(keys)!=set(bs):
        raise ValueError("Original physical sites no longer matched")
    common=set.intersection(*(set(x["method"] for x in bs[k]) for k in keys))
    minimum={mode:min(sum(x["method"]==mode for x in bs[k]) for k in keys) for mode in common}
    selected_site={}
    selected_to_site={}
    tree_to_site={}
    for k in keys:
        orig=[]
        for mode in sorted(common):
            orig.extend(sorted(x["core"] for x in bs[k] if x["method"]==mode)[:minimum[mode]])
        selected_site[k]=orig
        for core in orig:selected_to_site[core]=k
        tree_to_site[ts[k][0]["core"]]=k
    if hashlib.sha256("\n".join(sorted(selected_to_site)).encode()).hexdigest()!=pinned["selected_beetle_Event_coreids_sha256"]:
        raise ValueError("Selected 60 original beetle Event coreids fingerprint fails before score")
    original_t_core={x["source_coreid"] for x in t_events}
    original_b_core={x["source_coreid"] for x in b_events}
    tmatched=sum(str(x.get("source_coreid","")) in original_t_core for x in t_obs)
    bmatched=sum(str(x.get("source_coreid","")) in original_b_core for x in b_obs)
    quality=contract["data_units"]
    cutoff=quality["original_occurrence_to_event_join_fraction_min"]
    result={
       "schema":"structural.biomoni_cross_taxon_beta_result.v1_300",
       "status":"STOP_FROZEN_ORIGINAL_TAXON_DATA_QUALITY",
       "original_woody_occurrence_rows_opened":len(t_obs),
       "original_beetle_occurrence_rows_opened":len(b_obs),
       "original_woody_coreid_join_fraction":tmatched/len(t_obs),
       "original_beetle_coreid_join_fraction":bmatched/len(b_obs),
       "original_matched_plot_n":len(keys),
       "original_woody_Event_rows":len(t_events),
       "original_beetle_Event_rows":len(b_events),
       "source_selected_equal_effort_beetle_Events":len(selected_to_site),
       "old_v1_298_original_full_method_gate_remains_TERMINAL":True,
       "same_island_retrospective_not_pristine_confirmation":True,
       "source_woody_and_beetle_original_archive_sha256":{i:SOURCE[i][1] for i in SOURCE},
       "no_plot_IDs_coordinates_taxon_names_or_original_raw_records_exported":True,
       "GEB_scientific_HOLD":True,
       "new_confirmatory_systems":0,"eBird_used":False,
    }
    if tmatched/len(t_obs)<cutoff or bmatched/len(b_obs)<cutoff:
        result["stop_reason"]="Original Event/Occurrence source identity joins below 98%"
        return result
    woody={k:set() for k in keys};beetle={k:set() for k in keys}
    invalid_selected_beetle=0;selected_beetle_count=0
    for row in t_obs:
        key=tree_to_site.get(str(row.get("source_coreid","")).strip())
        if key is None:continue
        rank=norm(row.get("taxonRank"))
        name=norm(row.get("scientificName"))
        if name and rank in WOODY_ALLOWED_RANK:
            woody[key].add(name)
    for row in b_obs:
        key=selected_to_site.get(str(row.get("source_coreid","")).strip())
        if key is None:continue
        selected_beetle_count+=1
        name=norm(row.get("scientificName"))
        if not name:
            invalid_selected_beetle+=1
        else:
            beetle[key].add(name)
    if selected_beetle_count==0:
        result["stop_reason"]="No selected beetle sampling records detected"
        return result
    invalid_fraction=invalid_selected_beetle/selected_beetle_count
    result["selected_beetle_occurrences_detected"]=selected_beetle_count
    result["selected_beetle_unresolved_taxon_fraction"]=invalid_fraction
    if invalid_fraction>.05:
        result["stop_reason"]="Above 5 percent unresolvable source beetle taxon names"
        return result
    coords=[(ts[k][0]["lat"],ts[k][0]["lon"]) for k in keys]
    scored=analyse_sets([woody[k] for k in keys],[beetle[k] for k in keys],coords,contract)
    result.update(scored)
    return result

def main():
    ap=argparse.ArgumentParser()
    for k in ("--contract","--event-contract","--method-contract"):
        ap.add_argument(k,type=Path,required=True)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    cfg=json.loads(args.contract.read_text(encoding="utf-8"))
    event=json.loads(args.event_contract.read_text(encoding="utf-8"))
    method=json.loads(args.method_contract.read_text(encoding="utf-8"))
    if (cfg.get("schema")!="structural.biomoni_terceira_woody_beetle_beta_transfer.v1_300"
        or cfg.get("status")!="FROZEN_BEFORE_FIRST_WOODY_AND_BEETLE_OCCURRENCE_BODY_ACCESS"
        or any(cfg["source"]["wood_sha256" if i=="woody" else "beetle_sha256"]!=SOURCE[i][1] for i in ("woody","beetle"))
        or event.get("schema")!="structural.biomoni_colocated_terceira_event_crosswalk.v1_298"
        or method.get("schema")!="structural.biomoni_shared_protocol_standardized_event_v1_299"):
        raise ValueError("Original cross-taxon source and ecological estimator not frozen")
    result={
       "schema":"structural.biomoni_cross_taxon_beta_result.v1_300",
       "status":"SOURCE_OR_RESPONSE_READER_TECHNICAL_STOP",
       "original_woody_occurrence_rows_opened":0,
       "original_beetle_occurrence_rows_opened":0,
       "old_v1_298_original_full_method_gate_remains_TERMINAL":True,
       "GEB_scientific_HOLD":True,"new_confirmatory_systems":0,"eBird_used":False
    }
    try:
        blobs={};ev={}
        for kind,(url,sha) in SOURCE.items():
            req=urllib.request.Request(url,headers={"User-Agent":"Structural-BioMonI-Original-EqualMode-CrossTaxon-v1.300"})
            with urllib.request.urlopen(req,timeout=55) as f:raw=f.read(MAX_BYTES+1)
            if len(raw)>MAX_BYTES or hashlib.sha256(raw).hexdigest()!=sha:
                raise ValueError("Original cross-taxon source ZIP SHA or cap mismatch")
            blobs[kind]=raw;ev[kind]=extract_event_core_only(raw)
        before=physical_evaluate(ev["woody"],ev["beetle"],method,event)
        if (before["status"]!="EXPLORATORY_TEN_PLOTS_SIX_COMMON_METHOD_BEETLE_EVENTS_EACH_RESPONSE_SEALED"
            or before["selected_original_Event_coreids_sha256"]!=
               cfg["frozen_event_receipt"]["selected_beetle_Event_coreids_sha256"]):
            raise ValueError("Source physical/sampling scheme ineligible; no biological response authorized")
        # FIRST actual opening of both source taxon response bodies happens here.
        w=original_occurrence_body(blobs["woody"])
        b=original_occurrence_body(blobs["beetle"])
        result["original_woody_occurrence_rows_opened"]=len(w)
        result["original_beetle_occurrence_rows_opened"]=len(b)
        result=score_original(ev["woody"],ev["beetle"],w,b,event,method,cfg)
    except Exception as err:
        result["stop_type"]=type(err).__name__
        result["stop_reason"]=str(err)[:320]
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:result.get(k) for k in (
       "status","original_woody_occurrence_rows_opened",
       "original_beetle_occurrence_rows_opened","original_matched_plot_n",
       "source_selected_equal_effort_beetle_Events",
       "woody_distinct_operational_taxa_all_plots",
       "beetle_distinct_operational_taxa_all_plots",
       "baseline_geo_only_LOPO_MSE","added_beetle_LOPO_MSE",
       "primary_beetle_incremental_LOPO_MSE_gain",
       "descriptive_positive_cross_taxon_information","permutation_plot_label_exceedance_rank",
       "stop_reason")},sort_keys=True))
    if result["status"]=="SOURCE_OR_RESPONSE_READER_TECHNICAL_STOP":
        raise SystemExit(2)

if __name__=="__main__":main()
