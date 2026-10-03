#!/usr/bin/env python3
"""Render Supplementary Figure S2 from the frozen v1.85 summary only."""
from __future__ import annotations
import argparse,json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

class Stop(RuntimeError): pass

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()

    x=json.loads(a.freeze.read_text())
    if x.get("schema")!="structural.global_mammals_prediction_behavior_freeze.v1_85":
        raise Stop("prediction-behavior freeze schema drift")

    bw=x["effect_scale"]["block_weighted"]
    oa=x["outcome_asymmetry"]
    ge=x["graph_empty_support"]
    rk=x["ranking_context"]

    fig,axes=plt.subplots(1,3,figsize=(14.5,4.6))

    # A: outcome asymmetry.
    labels=["Natural\nprevalence","True\nabsence","Realized\npresence","Class-\nbalanced"]
    vals=[
      float(bw["C_minus_R3"]),
      float(oa["absence"]["C_minus_R3"]),
      float(oa["presence"]["C_minus_R3"]),
      float(oa["class_balanced_equal_block_C_minus_R3"]),
    ]
    ax=axes[0]
    pos=list(range(len(vals)))
    ax.bar(pos,vals)
    ax.axhline(0,linewidth=1)
    ax.set_xticks(pos,labels)
    ax.set_ylabel("C−R3 log-loss difference")
    ax.set_title("A  Outcome asymmetry",loc="left")
    for i,v in enumerate(vals):
        offset=0.003 if v>=0 else -0.003
        va="bottom" if v>=0 else "top"
        ax.text(i,v+offset,f"{v:+.4f}",ha="center",va=va,fontsize=9)
    ax.text(0.02,0.98,"Negative favours C",transform=ax.transAxes,va="top",fontsize=9)

    # B: graph support.
    labels2=["Graph-source\nempty","Graph-source\nnonempty"]
    vals2=[float(ge["empty_cell_mean_C_minus_R3"]),float(ge["nonempty_cell_mean_C_minus_R3"])]
    ax=axes[1]
    pos2=[0,1]
    ax.bar(pos2,vals2)
    ax.axhline(0,linewidth=1)
    ax.set_xticks(pos2,labels2)
    ax.set_ylabel("Mean C−R3 log-loss difference")
    ax.set_title("B  Source support",loc="left")
    for i,v in enumerate(vals2):
        ax.text(i,v-0.0007,f"{v:+.4f}",ha="center",va="top",fontsize=9)
    ax.text(0.02,0.98,f"Empty cells = {100*float(ge['empty_fraction']):.1f}%\nBlock empty-fraction ρ = {float(ge['block_empty_fraction_vs_C_minus_R3_spearman_rho']):.3f}",transform=ax.transAxes,va="top",fontsize=9)

    # C: ranking context.
    ax=axes[2]
    metric_labels=["ROC-AUC","Average\nprecision"]
    r3=[float(rk["R3_ROC_AUC"]),float(rk["R3_average_precision"])]
    c=[float(rk["C_ROC_AUC"]),float(rk["C_average_precision"])]
    xs=[0,1]; width=0.34
    ax.bar([z-width/2 for z in xs],r3,width,label="R3")
    ax.bar([z+width/2 for z in xs],c,width,label="C")
    ax.set_xticks(xs,metric_labels)
    ax.set_ylim(0,1)
    ax.set_ylabel("Metric value")
    ax.set_title("C  Ranking diagnostics",loc="left")
    ax.legend(frameon=False)
    for z,v in zip([xs[0]-width/2,xs[1]-width/2],r3):
        ax.text(z,v+0.02,f"{v:.3f}",ha="center",va="bottom",fontsize=9)
    for z,v in zip([xs[0]+width/2,xs[1]+width/2],c):
        ax.text(z,v+0.02,f"{v:.3f}",ha="center",va="bottom",fontsize=9)

    fig.suptitle("Prediction behaviour of graph-path source topology",fontsize=15)
    fig.tight_layout(rect=(0,0,1,0.94))

    a.output_dir.mkdir(parents=True,exist_ok=True)
    stem=a.output_dir/"figS2_prediction_behavior"
    fig.savefig(stem.with_suffix(".png"),dpi=300,bbox_inches="tight")
    fig.savefig(stem.with_suffix(".svg"),bbox_inches="tight")
    plt.close(fig)

    receipt={
      "schema":"structural.macro_prediction_behavior_figure_result.v1_86",
      "status":"FROZEN_SUMMARY_ONLY_FIGURE_RENDERED",
      "source_schema":x["schema"],
      "new_response_accessed":False,
      "output_files":["figS2_prediction_behavior.png","figS2_prediction_behavior.svg"],
      "counts_as_empirical_evidence":False
    }
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))

if __name__=="__main__": main()
