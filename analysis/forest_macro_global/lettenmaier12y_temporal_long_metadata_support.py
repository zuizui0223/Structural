#!/usr/bin/env python3
"""Lettenmaier long-table metadata temporal support ONLY.

Uses only already-author-identified plot/log/year/tree fields in the MD5-pinned
original long table. These are listed contexts, NOT verified sampled
opportunities; community-matrix crosswalk remains blocked. No abundance,
species or trait values accessed/scored, no data IDs exported.
"""
import argparse,csv,io,json,collections
from pathlib import Path
from lettenmaier_12year_source_log_method_gate import M,get_source,ScientificStop

YEARS=set(range(2013,2020))|set(range(2021,2025))
FIELDS={"plot":2,"log":3,"year":4,"tree":6}
def require(x,msg):
    if not x:raise ScientificStop(msg)

def original_contexts(blob):
    rd=csv.reader(io.StringIO(blob.decode("utf-8-sig",errors="strict"),newline=""),delimiter=";")
    h=next(rd)
    require(len(h)==15 and all(h[i]==k for k,i in FIELDS.items()),"ORIGINAL_METADATA_HEADER_DRIFT")
    contexts={};n=0
    for row in rd:
        n+=1
        require(len(row)==15,"ORIGINAL_ROW_WIDTH_DRIFT")
        p,l,y,t=(row[FIELDS[k]].strip() for k in ("plot","log","year","tree"))
        require(all(v and v.casefold() not in {"na","nan","none","null","missing","n/a"} for v in (p,l,y,t)) and y.isascii() and y.isdigit(),"ORIGINAL_ID_OR_YEAR_INVALID")
        y=int(y);require(y in YEARS,"ORIGINAL_YEAR_OUTSIDE_PIN")
        k=(p,l,y)
        require(k not in contexts or contexts[k]==t,"ORIGINAL_CONTEXT_HOST_CONFLICT")
        contexts[k]=t
    require(n==7738 and len(contexts)==522 and len({k[0] for k in contexts})==42 and len({k[:2] for k in contexts})==52 and set(k[2] for k in contexts)==YEARS,"ORIGINAL_FRAME_DRIFT")
    return contexts

def transitions(contexts):
    loghost={}
    for (p,l,y),t in contexts.items():
        require((p,l) not in loghost or loghost[(p,l)]==t,"ORIGINAL_LOG_HOST_CONFLICT")
        loghost[(p,l)]=t
    # Adjacent calendar years only; 2019->2021 is never a transition.
    return [(p,l,y,t) for (p,l,y),t in sorted(contexts.items()) if (p,l,y-1) in contexts]

def audit(contexts):
    pairs=transitions(contexts)
    byyear=[]
    for year in sorted({k[2] for k in contexts}):
        cohort=[v for v in pairs if v[2]==year]
        train_counts=[];train_plot_counts=[];host_train_plot_counts=[]
        for p,l,y,t in cohort:
            # No same-plot, same-target-year or future-year training transitions.
            train=[v for v in pairs if v[0]!=p and v[2]<y]
            train_counts.append(len(train))
            train_plot_counts.append(len({v[0] for v in train}))
            host_train_plot_counts.append(len({v[0] for v in train if v[3]==t}))
        span=lambda z:[min(z),max(z)] if z else None
        byyear.append({
            "target_calendar_year":year,
            "candidate_contexts":sum(k[2]==year for k in contexts),
            "adjacent_pairs":len(cohort),
            "candidate_plot_tokens":len({v[0] for v in cohort}),
            "pairs_with_any_earlier_other_plot_transition":sum(z>0 for z in train_counts),
            "pairs_with_any_earlier_other_plot_same_host_transition":sum(z>0 for z in host_train_plot_counts),
            "earlier_other_plot_training_pair_minmax":span(train_counts),
            "earlier_other_plot_training_plot_token_minmax":span(train_plot_counts),
            "earlier_other_plot_same_host_plot_token_minmax":span(host_train_plot_counts)
        })
    h={}
    for (p,l,y),t in contexts.items():h.setdefault((p,l),set()).add(y)
    gaps=collections.Counter(b-a for ys in h.values() for a,b in zip(sorted(ys),sorted(ys)[1:]))
    return {
        "candidate_long_table_contexts":len(contexts),
        "candidate_plot_tokens":len({k[0] for k in contexts}),
        "candidate_log_tokens_nested":len(h),
        "adjacent_calendar_year_candidate_pairs":len(pairs),
        "adjacent_pairs_with_any_earlier_other_plot_training":sum(z["pairs_with_any_earlier_other_plot_transition"] for z in byyear),
        "adjacent_pairs_with_any_earlier_other_plot_same_host_training":sum(z["pairs_with_any_earlier_other_plot_same_host_transition"] for z in byyear),
        "all_observed_log_context_gap_length_distribution":dict(sorted(gaps.items())),
        "per_target_year":byyear,
        "matrix_crosswalk_status":"UNCHANGED_359_OF_522_HOLD",
        "sampling_effort_and_zero_capture_status":"UNVERIFIED",
        "actual_predictive_estimability_claimed":False
    }

def test():
    x={("P1","a",2018):"h",("P1","a",2019):"h",("P1","a",2021):"h",("P1","a",2022):"h",
       ("P2","b",2018):"h",("P2","b",2019):"h",("P2","b",2021):"h",("P2","b",2022):"h",
       ("P3","c",2021):"j",("P3","c",2022):"j"}
    a=audit(x)
    assert a["adjacent_calendar_year_candidate_pairs"]==5
    assert a["adjacent_pairs_with_any_earlier_other_plot_training"]==3
    assert a["adjacent_pairs_with_any_earlier_other_plot_same_host_training"]==2
    assert a["all_observed_log_context_gap_length_distribution"][2]==2
    assert next(z for z in a["per_target_year"] if z["target_calendar_year"]==2019)["pairs_with_any_earlier_other_plot_training"]==0
    assert next(z for z in a["per_target_year"] if z["target_calendar_year"]==2021)["adjacent_pairs"]==0
    print("SYNTHETIC_NO_GAP_BRIDGE_NO_SAME_YEAR_NO_SAME_PLOT_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",default="lettenmaier_temporal_support/receipt.json")
    a=ap.parse_args();test()
    if a.test:return
    r={"schema":"structural.lettenmaier2026.temporal_long_metadata_support.v1",
       "original_species_counts_read":0,"original_trait_values_read":0,"new_ecological_effects_scored":0,
       "community_matrix_opened":False,"original_ids_exported":False}
    try:
        b=get_source(*M["raw"])
        r["long_table_md5_verified"]=True
        r["support"]=audit(original_contexts(b))
        r["status"]="LONG_METADATA_ADJACENT_SUPPORT_DONE_MATRIX_IDENTITY_HOLD"
    except ScientificStop as e:r["status"]="SOURCE_METADATA_STOP";r["reason"]=str(e)
    except Exception as e:r["status"]="SOURCE_METADATA_EXECUTION_STOP";r["error_type"]=type(e).__name__
    p=Path(a.out);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    print(json.dumps(r,sort_keys=True))
if __name__=="__main__":main()
