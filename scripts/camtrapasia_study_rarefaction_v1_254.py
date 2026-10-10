#!/usr/bin/env python3
"""Published field positives only. Study-based rarefaction is POSTOUTCOME descriptive, not occupancy."""
import argparse,csv,io,json,math,random,statistics,sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from camtrapasia_four_island_field_positives_v1_250 import fetch,canon,SAFE_WILD
ID={"65554":("Java",25,18),"70378":("Sumatra",49,49)}
SEED=20261010
N_SAMPLES=20000
def quant(values,p):
    xs=sorted(values);z=(len(xs)-1)*p;i=int(z);j=min(i+1,len(xs)-1)
    return xs[i]*(j-z)+xs[j]*(z-i)
def found_prob(N,f,k):
    if f==0:return 0.
    if k>N-f:return 1.
    missing=1.
    for j in range(k):missing*=(N-f-j)/(N-j)
    return 1.-missing
def run(geo,taxa,meta,capture):
    if geo["status"]!="PASS_RESPONSE_SAFE_FULL239_POLYGON_IDENTITY_PRESCREEN" or taxa["exact_verified_taxon_overlaps"]!=38:
        raise ValueError("Original frozen source eligibility differs")
    names={canon(t["survey_verified_binomial"]):t["original_529_binomial"].replace("."," ")
            for t in taxa["exact_matched_binomials"]}
    if len(names)!=38:raise ValueError("Nonunique frozen binomial")
    groups=defaultdict(set)
    for record in geo["geography_only_candidate_studies"]:
        if record["candidate_original_heldout_ID"] in ID:
            groups[record["candidate_original_heldout_ID"]].add(record["survey_id"])
    if any(len(groups[iid])!=x[1] for iid,x in ID.items()):raise ValueError("Original study panel drift")
    by_study={sid:iid for iid,group in groups.items() for sid in group}
    if len(by_study)!=74:raise ValueError("Not 74 independent study identifiers")
    info={}
    with io.StringIO(meta.decode("utf-8-sig")) as f:
        r=csv.DictReader(f)
        if not {"survey_id","year_start","year_end","effort"}.issubset(r.fieldnames or []):
            raise ValueError("Metadata survey year/effort header absent")
        for x in r:
            sid=x["survey_id"]
            if sid not in by_study:continue
            if sid in info:raise ValueError("Duplicate study ID")
            start,end=int(x["year_start"]),int(x["year_end"])
            effort=float(x["effort"])
            if not(1980<=start<=end<=2026 and math.isfinite(effort) and effort>=0):
                raise ValueError("Invalid study year or field effort")
            info[sid]=(start,end,effort)
    if set(info)!=set(by_study):raise ValueError("Missing study metadata")
    pos=defaultdict(set)
    with io.StringIO(capture.decode("utf-8-sig")) as f:
        r=csv.DictReader(f)
        if not {"survey_id","records","class","binomial_verified","domestic"}.issubset(r.fieldnames or []):
            raise ValueError("Photo source schema drift")
        for x in r:
            sid=x["survey_id"]
            if sid not in by_study or (x["class"] or "").strip().casefold()!="mammalia":continue
            key=canon(x["binomial_verified"] or "")
            if key not in names or (x["domestic"] or "").strip().casefold() not in SAFE_WILD:continue
            count=float(x["records"])
            if not math.isfinite(count) or count<0 or int(count)!=count:
                raise ValueError("Invalid positive record")
            if count>0:pos[sid].add(names[key])
    full={name:set().union(*(pos[sid] for sid in groups[iid])) for iid,(name,n,k) in ID.items()}
    if (len(full["Java"]),len(full["Sumatra"]),len(full["Java"]&full["Sumatra"]))!=(15,17,10):
        raise ValueError("All-era v1.251 field positives cannot be replicated")
    results={}
    for label,k in (("pre2017",18),("all_eras",25)):
        study={}
        effort={}
        for iid,(name,n,pre) in ID.items():
            ids=sorted(sid for sid in groups[iid] if label=="all_eras" or info[sid][1]<2017)
            if len(ids)!=(n if label=="all_eras" else pre):raise ValueError("Campaign year opportunity drift")
            study[name]=[pos[sid] for sid in ids]
            effort[name]=[info[sid][2] for sid in ids]
        J=set().union(*study["Java"])
        S=study["Sumatra"];N=len(S)
        seen={name:sum(name in x for x in S) for name in names.values()}
        exact_sumatra=sum(found_prob(N,f,k) for f in seen.values())
        exact_overlap=sum(found_prob(N,seen[t],k) for t in J)
        rng=random.Random(SEED)
        richness,intersection,jaccard=[],[],[]
        for draw in range(N_SAMPLES):
            idx=rng.sample(range(N),k)
            taxa_sumatra=set().union(*(S[j] for j in idx))
            both=len(J&taxa_sumatra);union=len(J|taxa_sumatra)
            richness.append(len(taxa_sumatra));intersection.append(both)
            jaccard.append(both/union if union else 0.)
        results[label]={
            "java_eligible_studies":len(study["Java"]),"sumatra_eligible_studies":N,
            "standardized_study_count_k":k,
            "java_observed_wild_photo_positive_taxa":len(J),
            "sumatra_full_observed_wild_photo_positive_taxa":len(set().union(*S)),
            "sumatra_expected_positive_taxa_k_studies_exact":exact_sumatra,
            "expected_shared_positive_taxa_java_vs_rarefied_sumatra_exact":exact_overlap,
            "sumatra_subsample_positive_taxa_quantiles_5_50_95":[quant(richness,p) for p in (.05,.5,.95)],
            "shared_subsample_positive_taxa_quantiles_5_50_95":[quant(intersection,p) for p in (.05,.5,.95)],
            "detected_taxon_jaccard_subsample_quantiles_5_50_95":[quant(jaccard,p) for p in (.05,.5,.95)],
            "java_full_eligible_study_effort":sum(effort["Java"]),
            "sumatra_full_eligible_study_effort":sum(effort["Sumatra"]),
            "java_median_effort_per_study":statistics.median(effort["Java"]),
            "sumatra_median_effort_per_study":statistics.median(effort["Sumatra"]),
            "java_wild_photo_positive_names":sorted(J),
            "sumatra_wild_photo_positive_names":sorted(set().union(*S))
        }
    return {"schema":"structural.camtrapasia_study_positive_rarefaction_result.v1_254",
        "status":"PASS_EXPLORATORY_POSTOUTCOME_STUDY_BASED_WILD_POSITIVES_ONLY",
        "seed":SEED,"draws_per_era":N_SAMPLES,"outcomes":results,
        "finite_study_pool_subsample_quantiles_not_population_confidence_intervals":True,
        "source_campaign_year_not_photo_timestamp":True,"equal_study_ids_does_not_equal_trapnights":True,
        "non_detected_species_not_scored_as_absent":True,"same_geographic_heldout_block":True,
        "original_IUCN_heldout_data_reopened":False,"original_graph_prediction_scored":False}
def main():
    p=argparse.ArgumentParser();p.add_argument("geo",type=Path);p.add_argument("taxa",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=run(json.loads(a.geo.read_text()),json.loads(a.taxa.read_text()),
            fetch("CamTrapAsia_Metadata_20231031.csv"),fetch("CamTrapAsia_Captures_20231031.csv"))
    except Exception as e:
        result={"schema":"structural.camtrapasia_study_positive_rarefaction_result.v1_254",
            "status":"STOP_SOURCE_IDENTITIES_OR_FIELD_PROTOCOL","reason_type":type(e).__name__,
            "original_IUCN_heldout_data_reopened":False}
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,sort_keys=True))
    if result["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
