#!/usr/bin/env python3
"""Render Figure 4 from frozen original-layer and sealed-layer summaries only."""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def load_json(path):
    return json.loads(Path(path).read_text())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original-scoring-freeze",type=Path,required=True)
    ap.add_argument("--original-behavior-freeze",type=Path,required=True)
    ap.add_argument("--sealed-freeze",type=Path,required=True)
    ap.add_argument("--null-scores",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()

    original=load_json(a.original_scoring_freeze)
    behavior=load_json(a.original_behavior_freeze)
    sealed=load_json(a.sealed_freeze)

    op=original["primary_exploratory_result"]
    sp=sealed["P1_primary"]
    ob=behavior["outcome_asymmetry"]
    sb=sealed["P2_constraint_signature"]

    with a.null_scores.open("r",encoding="utf-8",newline="") as h:
        null_rows=list(csv.DictReader(h))
    if len(null_rows)!=20:
        raise SystemExit("null score count drift")
    nulls=[float(r["block_weighted_C_rewired_minus_R3"]) for r in null_rows]

    fig,axes=plt.subplots(1,3,figsize=(14.8,4.8))

    # A: overall C-R3
    ax=axes[0]
    labels=["Exploratory\n79 species","Sealed\n96 rare species"]
    vals=[float(op["point_estimate_C_minus_R3_logloss"]),float(sp["point_C_minus_R3"])]
    lows=[float(op["bootstrap_ci95_low"]),float(sp["bootstrap_ci95_low"])]
    highs=[float(op["bootstrap_ci95_high"]),float(sp["bootstrap_ci95_high"])]
    yerr=[[v-l for v,l in zip(vals,lows)],[h-v for v,h in zip(vals,highs)]]
    ax.errorbar([0,1],vals,yerr=yerr,fmt="o",capsize=5)
    ax.axhline(0,linewidth=1)
    ax.set_xticks([0,1],labels)
    ax.set_ylabel("Block-weighted C−R3 log-loss difference")
    ax.set_title("A  Overall held-out effect",loc="left")
    ax.text(0.02,0.02,"Negative values favour C",transform=ax.transAxes,va="bottom",fontsize=9)

    # B: asymmetry reversal
    ax=axes[1]
    groups=[0,1]
    width=0.32
    original_vals=[float(ob["absence"]["C_minus_R3"]),float(ob["presence"]["C_minus_R3"])]
    sealed_vals=[float(sb["absence_point"]),float(sb["presence_point"])]
    ax.bar([g-width/2 for g in groups],original_vals,width,label="Exploratory 79")
    ax.bar([g+width/2 for g in groups],sealed_vals,width,label="Sealed 96")
    ax.axhline(0,linewidth=1)
    ax.set_xticks(groups,["True absence","Realized presence"])
    ax.set_ylabel("C−R3 log-loss difference")
    ax.set_title("B  Prediction asymmetry reverses",loc="left")
    ax.legend(frameon=False,fontsize=9)

    # C: actual graph among rewired nulls
    ax=axes[2]
    ax.scatter(nulls,[1]*len(nulls),s=30,label="20 rewired graphs")
    actual=float(sp["point_C_minus_R3"])
    ax.scatter([actual],[1],s=95,marker="D",label="Actual graph")
    ax.axvline(actual,linewidth=1,linestyle="--")
    ax.set_yticks([])
    ax.set_xlabel("Block-weighted C−R3")
    ax.set_title("C  Actual topology is not exceptional",loc="left")
    ax.legend(frameon=False,fontsize=9,loc="lower left")
    ax.text(0.02,0.95,
            f"Actual better than {sealed['P4_topology_specificity']['actual_C_better_than_n_of_20_nulls']}/20 nulls\n"
            f"Actual−mean(null) = {sealed['P4_topology_specificity']['point_actualC_minus_mean_rewiredC']:+.2e}",
            transform=ax.transAxes,va="top",fontsize=9)

    fig.suptitle("Prospective sealed rare-species validation",fontsize=15)
    fig.tight_layout(rect=(0,0,1,0.94))
    a.output_dir.mkdir(parents=True,exist_ok=True)
    for ext in ("png","svg"):
        fig.savefig(a.output_dir/f"fig4_sealed_species_validation.{ext}",dpi=300 if ext=="png" else None,bbox_inches="tight")
    plt.close(fig)

    receipt={
      "schema":"structural.sealed_species_figure_result.v1_97",
      "status":"FROZEN_OUTPUT_ONLY_FIGURE_RENDERED",
      "null_graphs":20,
      "new_response_accessed":False,
      "counts_as_new_empirical_analysis":False
    }
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
