#!/usr/bin/env python3
"""v1.239 already-published Helgeland NATAL RESIGHT graph only.

All inputs frozen v1.231 source-locked observed first-year immigrants.
No new individual sightings opened, no reproductive/offspring records or
original Structural heldout opened. No causal source-loss simulation.
"""
import argparse,hashlib,json,math
from collections import defaultdict
from pathlib import Path

EXPECTED_SOURCE_SHA="955d58e958b2f241cda726706bec0260fea79dd5"
EXPECTED_COUNTS={"historical":259,"bridge":28,"later":173}

def git_sha(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()

def source_stats(counts):
    vals=[n for n in counts.values() if n>0]
    n=sum(vals)
    if n==0:
        return {"incoming":0,"source_richness":0,"hill_simpson":None,
                "prob_same_source_two_distinct_migrants":None,
                "hill_shannon":None,"dominant_id":None,
                "dominant_n":0,"dominant_fraction":None}
    sq=sum(x*x for x in vals)
    pairs=sum(x*(x-1) for x in vals)
    donor=max((k for k in counts if counts[k]>0),
              key=lambda k:(counts[k],-int(k)))
    proportions=[x/n for x in vals]
    return {"incoming":n,"source_richness":len(vals),
        "hill_simpson":n*n/sq,
        "hill_shannon":math.exp(-sum(p*math.log(p) for p in proportions)),
        "prob_same_source_two_distinct_migrants":pairs/(n*(n-1)) if n>1 else None,
        "dominant_id":int(donor),"dominant_n":counts[donor],
        "dominant_fraction":counts[donor]/n}

def source_sharing(source_a,source_b):
    a=sum(source_a.values());b=sum(source_b.values())
    if not a or not b:return None
    return sum((source_a.get(k,0)/a)*(source_b.get(k,0)/b)
               for k in set(source_a)|set(source_b))

def compute(source):
    if source["schema"]!="structural.helgeland_nestling_origin_nextyear_resight_freeze.v1_231":
        raise ValueError("Input is not v1.231 source-locked evidence")
    obj=source["data"]
    if obj["n_model_islands"]!=11 or obj["source_rows"]!=73593:
        raise ValueError("Original field-study universe was changed")
    roster={}
    for rec in obj["per_origin"]:
        if rec["origin"] not in roster:roster[rec["origin"]]=rec["island_name"]
    islands=sorted(roster)
    if len(islands)!=11:raise ValueError("Eleven islands required")
    out={}
    for era,total_expected in EXPECTED_COUNTS.items():
        edges={(o,d):0 for o in islands for d in islands if o!=d}
        for e in obj["observed_cross_island_edges"]:
            if e["era"]!=era:continue
            o=e["origin"];d=e["destination"];v=e["observed_n"]
            if (o,d) not in edges or not isinstance(v,int) or v<=0:
                raise ValueError("Invalid positive directed immigrant edge")
            if edges[(o,d)]:
                raise ValueError("Duplicate directional edge")
            edges[(o,d)]=v
        if sum(edges.values())!=total_expected:
            raise ValueError("Published cohort migration tally mismatch")
        sources={i:sum(v for (o,d),v in edges.items() if o==i) for i in islands}
        target_counts={j:{i:edges[(i,j)] for i in islands if i!=j} for j in islands}
        supply={x["origin"]:x for x in obj["per_origin"] if x["era"]==era}
        if set(supply)!=set(islands):
            raise ValueError("Missing whole eleven-island source roster")
        for i in islands:
            if supply[i]["exported"]!=sources[i]:
                raise ValueError("Frozen destination and origin export counts disagree")
        total_marked=sum(supply[i]["natalMarked"] for i in islands)
        recips=[]
        for target in islands:
            counts=target_counts[target];m=source_stats(counts)
            residents=supply[target]["retained"]
            marked_elsewhere=total_marked-supply[target]["natalMarked"]
            dominant=m["dominant_id"]
            baseline=(supply[dominant]["natalMarked"]/marked_elsewhere
                      if dominant is not None and marked_elsewhere>0 else None)
            obsfrac=m["incoming"]/(m["incoming"]+residents) if m["incoming"]+residents>0 else None
            recips.append({
                "island_id":target,"island_name":roster[target],
                **m,"observed_resident_nextyear_recruits":residents,
                "observed_immigrant_fraction_of_known_nextyear_recruits":obsfrac,
                "largest_donor_name":roster[dominant] if dominant is not None else None,
                "dominant_source_fraction_of_other_islands_marked_nestlings":baseline,
                "dominant_source_observed_vs_marked_volume_ratio":
                    m["dominant_fraction"]/baseline
                    if baseline is not None and baseline>0 else None,
                "source_counts_all_islands":{str(i):counts[i] for i in islands if i!=target}
            })
        sharing=[]
        for a_idx,a in enumerate(islands):
            for b in islands[a_idx+1:]:
                val=source_sharing(target_counts[a],target_counts[b])
                sharing.append({"recipient_A":a,"recipient_B":b,
                    "recipient_A_incoming":sum(target_counts[a].values()),
                    "recipient_B_incoming":sum(target_counts[b].values()),
                    "same_natal_source_between_one_recorded_arrival_each":val})
        all_sources=source_stats(sources)
        deleted=[]
        for i in islands:
            lost_by_recipient={str(j):edges.get((i,j),0) for j in islands if j!=i}
            deleted.append({"source_island_id":i,"source_island_name":roster[i],
                "outgoing_observed_immigrants":sources[i],
                "source_fraction_all_documented_immigrant_arrivals":sources[i]/total_expected,
                "recipient_islands_with_documented_arrival_from_source":
                    sum(1 for v in lost_by_recipient.values() if v>0),
                "recipient_documented_arrivals_lost_if_all_source_edges_deleted":lost_by_recipient,
                "interpretation":"Only removal of recorded migrant edges, NOT predicted extinction or true donor shutdown"})
        out[era]={"total_observed_firstyear_immigrants":total_expected,
            "total_marked_natal_individuals":total_marked,
            "observed_unique_donor_islands":sum(sources[i]>0 for i in islands),
            "global_source_simpson_effective_number":all_sources["hill_simpson"],
            "all_recipient_islands":recips,
            "every_recipient_pair_source_sharing":sharing,
            "all_hypothetical_observed_edge_deletions":deleted}
    return {
        "schema":"structural.helgeland_observed_source_diversity_v1_239",
        "status":"RETROSPECTIVE_PUBLISHED_RESIGHT_NETWORK_DESCRIPTIVE_NO_CAUSAL_RESCUE",
        "input":"development/helgeland_natal_resight_result_freeze_v1_231.json",
        "input_source_git_sha":EXPECTED_SOURCE_SHA,
        "periods":out,
        "recipient_sample_size_affects_observed_source_richness":True,
        "same_source_probability_for_pair_of_distinct_observed_immigrants_is_descriptive":True,
        "hypothetical_source_deletion_only_recounts_documented_edges":True,
        "source_size_proxy_is_marked_nestlings_not_true_source_population":True,
        "known_resident_and_immigrant_counts_are_observation_conditioned":True,
        "one_archipelago_already_published":True,
        "new_confirmatory_evidence":False,
        "GEB_scientific_HOLD":True,"eBird_used":False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("freeze",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    raw=a.freeze.read_bytes()
    if git_sha(raw)!=EXPECTED_SOURCE_SHA:raise ValueError("Frozen v231 JSON blob changed")
    result=compute(json.loads(raw))
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
    # Compact machine-checked headline only; detailed all-islands output in artifact.
    summary={"schema":result["schema"],"status":result["status"],
      "periods":{era:{"incoming":x["total_observed_firstyear_immigrants"],
                    "global_eff":x["global_source_simpson_effective_number"],
                    "recipients":[{"name":r["island_name"],"incoming":r["incoming"],
                                   "residents":r["observed_resident_nextyear_recruits"],
                                   "Neff":r["hill_simpson"],
                                   "main_donor":r["largest_donor_name"],
                                   "main_share":r["dominant_fraction"]}
                                  for r in x["all_recipient_islands"]]}
                 for era,x in result["periods"].items()}}
    print(json.dumps(summary,sort_keys=True,ensure_ascii=False))
if __name__=="__main__":main()
